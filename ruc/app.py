"""The engine's core: one object the gRPC API and the event consumer share.

Feedback loop:
    Recommendation → User → Behavior → Event Collection → Feature Update
    → Model Evaluation → Recommendation Model → ...
  record_engagement()  event collection + attribution to the serve it came from
  (intelligence)       feature update: the user's state is rebuilt on next use,
                       and written back to the feature service
  training.run()       model evaluation and retraining from served items and
                       their outcomes; a better model is promoted
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable

from google.protobuf.message import Message

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb
from oowlet.gen.recommenduc.eventspb import events_pb2 as evpb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb

from . import convert, signals
from .config import Settings
from .domain import USER, ContentRecord, Edge, Engagement, Feedback, Privacy, ServedRecommendation, UserRecord, now
from .engines.common import Background
from .engines.content import ContentEngine
from .engines.people import PeopleEngine
from .intelligence.feature_client import FeatureServiceClient
from .intelligence.hub import Intelligence
from .ranking.registry import ModelRegistry
from .store.base import Store, VersionConflict
from .store.memory import MemoryStore

log = logging.getLogger("ruc.app")
Publish = Callable[[str, Message, str], Awaitable[None]]

TOPIC_SERVED = "recommenduc.recommendation.served"
TOPIC_FEEDBACK = "recommenduc.feedback.received"
TOPIC_ERASED = "recommenduc.user.data_erased"
POSITIVE_FEEDBACK = frozenset({rpb.FEEDBACK_TYPE_SEE_MORE_LIKE_THIS})
NEGATIVE_FEEDBACK = frozenset({rpb.FEEDBACK_TYPE_NOT_INTERESTED, rpb.FEEDBACK_TYPE_SEE_LESS_FROM_CREATOR,
                               rpb.FEEDBACK_TYPE_SEE_LESS_OF_TOPIC, rpb.FEEDBACK_TYPE_DONT_KNOW_PERSON,
                               rpb.FEEDBACK_TYPE_INAPPROPRIATE})


class App:
    def __init__(self, settings: Settings, store: Store | None = None,
                 features: FeatureServiceClient | None = None) -> None:
        self.s = settings
        self.store = store or MemoryStore(retention_days=settings.intelligence.history_retention_days,
                                          max_events_per_user=settings.intelligence.max_events_per_user)
        self.features = features
        self.intel = Intelligence(settings, self.store, features=features)
        self.models = ModelRegistry(settings.ranking)
        self.publish: Publish | None = None
        self.bg = Background()
        self.content = ContentEngine(settings, self.intel, self.models, on_served=self._served)
        self.people = PeopleEngine(settings, self.intel, self.models, on_served=self._served)
        self.metrics: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))

    async def start(self) -> None:
        await self.intel.rebuild_indexes()

    async def close(self) -> None:
        await self.bg.drain()
        await self.intel.close()
        if self.features is not None:
            await self.features.close()

    # ── outgoing events ────────────────────────────────────────────────────
    def _emit(self, topic: str, msg: Message, key: str) -> None:
        if self.publish is not None:
            self.bg.spawn(self._safe_publish(topic, msg, key))

    async def _safe_publish(self, topic: str, msg: Message, key: str) -> None:
        try:
            await self.publish(topic, msg, key)
        except Exception as exc:  # noqa: BLE001 - events are best effort; the store has the record
            log.warning("publish %s failed: %s", topic, exc)

    async def _served(self, served: ServedRecommendation) -> None:
        m = self.metrics[(served.engine, served.variant)]
        m["serves"] += 1
        m["items"] += len(served.items)
        if self.s.broker.publish_served:
            self._emit(TOPIC_SERVED, evpb.RecommendationServed(served=convert.served_to_proto(served)), served.user_id)

    # ── event collection + attribution ────────────────────────────────────
    async def record_engagement(self, events: list[Engagement]) -> tuple[int, int]:
        # only users who allow it feed the co-engagement others are recommended from
        actors = {e.user_id for e in events}
        known = await self.store.get_users(actors)
        collaborative = frozenset(u for u in actors
                                  if (known[u].privacy.contribute_to_collaborative if u in known
                                      else Privacy.platform_defaults().contribute_to_collaborative))
        added, dupes = await self.store.add_engagements(events, collaborative)
        touched = set()
        for ev in added:
            touched.add(ev.user_id)
            if ev.target_type == USER:
                touched.add(ev.target_id)
            if ev.recommendation_id:
                await self._attribute(ev)
        for u in touched:
            self.intel.invalidate(u)
        return len(added), dupes

    async def _attribute(self, ev: Engagement) -> None:
        served = await self.store.get_served(ev.recommendation_id)
        if served is None or served.user_id != ev.user_id:
            return                                   # someone else's serve: never attributed
        w = signals.weight(ev)
        label = None
        if ev.type == epb.ENGAGEMENT_TYPE_IMPRESSION:
            await self.store.update_served_item(ev.recommendation_id, ev.target_type, ev.target_id, impressed=True)
        elif w >= signals.POSITIVE_LABEL_MIN_WEIGHT:
            label = 1.0
        elif w < 0:
            label = 0.0
        if label is not None:
            ok = await self.store.update_served_item(ev.recommendation_id, ev.target_type, ev.target_id,
                                                     label=label, impressed=True)
            if ok:
                self.metrics[(served.engine, served.variant)]["positives" if label > 0 else "negatives"] += 1
        elif ev.type == epb.ENGAGEMENT_TYPE_IMPRESSION:
            self.metrics[(served.engine, served.variant)]["impressions"] += 1

    async def feedback(self, fb: Feedback) -> None:
        await self.store.add_feedback(fb)
        if fb.recommendation_id:
            served = await self.store.get_served(fb.recommendation_id)
            if served is not None and served.user_id == fb.user_id:
                # neutral feedback (already seen, already know them) is no label at all
                label = 0.0 if fb.type in NEGATIVE_FEEDBACK else 1.0 if fb.type in POSITIVE_FEEDBACK else None
                await self.store.update_served_item(fb.recommendation_id, fb.target_type, fb.target_id,
                                                    label=label, impressed=True)
        self.intel.invalidate(fb.user_id)
        msg = rpb.FeedbackRequest(user_id=fb.user_id, recommendation_id=fb.recommendation_id,
                                  item=cpb.EntityRef(type=fb.target_type, id=fb.target_id), type=fb.type,
                                  topic_id=fb.topic_id, given_at=convert.to_ts(fb.given_at))
        self._emit(TOPIC_FEEDBACK, evpb.FeedbackReceived(feedback=msg), fb.user_id)

    # ── catalog / graph / profiles ─────────────────────────────────────────
    async def upsert_content(self, item: ContentRecord) -> bool:
        self.intel.classify(item)
        try:
            await asyncio.wait_for(self.intel.enrich(item), timeout=max(self.s.feature_service.timeout_seconds, 2.0))
        except asyncio.TimeoutError:
            log.warning("feature enrichment of %s timed out; stored without it", item.content_id)
        self.intel.classify(item)                    # enrichment may have added topics
        if not await self.store.upsert_content(item):
            return False
        stored = (await self.store.get_content([item.content_id]))[item.content_id]
        await self.intel.index_content(stored)
        return True

    async def set_content_status(self, content_id: str, status: int) -> None:
        if status not in (ctpb.CONTENT_STATUS_REMOVED, ctpb.CONTENT_STATUS_DELETED):
            raise convert.Invalid("status must be REMOVED or DELETED")
        await self.store.set_content_status(content_id, status)
        self.intel.content_index.remove(content_id)

    async def upsert_edges(self, edges: list[Edge]) -> int:
        n = await self.store.upsert_edges(edges)
        for e in edges:
            self.intel.invalidate(e.from_user_id)
            self.intel.invalidate(e.to_user_id)
        return n

    async def remove_edges(self, edges: list[Edge]) -> int:
        n = await self.store.remove_edges(edges)
        for e in edges:
            self.intel.invalidate(e.from_user_id)
            self.intel.invalidate(e.to_user_id)
        return n

    async def update_user(self, user_id: str, change: Callable[[UserRecord], UserRecord],
                          expected_version: int = 0, attempts: int = 5) -> UserRecord:
        """Read-modify-write with compare-and-set; retried when expected_version is 0."""
        for _ in range(attempts):
            cur, _known = await self.intel.user_record(user_id)
            if expected_version and cur.version != expected_version:
                raise VersionConflict(f"version is {cur.version}, expected {expected_version}")
            new = change(cur)
            try:
                stored = await self.store.put_user(new, expected_version=cur.version or 0)
            except VersionConflict:
                if expected_version:
                    raise
                continue
            self.intel.invalidate(user_id)
            if not self.intel._user_indexable(stored):           # privacy changed: leave the people index now
                self.intel.user_index.remove(user_id)
            return stored
        raise VersionConflict("concurrent updates; retry")

    async def delete_user_data(self, user_id: str) -> float:
        """Erases the user's events, profile, serves and feedback, and every
        cache and index holding them. Item-item co-engagement totals are
        aggregates and stay. The feature service learns of the erasure from
        the recommenduc.user.data_erased event (its API has no delete)."""
        await self.store.delete_user_data(user_id)
        self.intel.invalidate(user_id)
        self.intel.user_index.remove(user_id)
        self.content.pages.drop_user(user_id)
        self.people.pages.drop_user(user_id)
        if self.content.mf is not None:
            self.content.mf.forget(user_id)
        if self.features is not None:
            self.features.forget(user_id)
        t = now()
        self._emit(TOPIC_ERASED, evpb.UserDataErased(user_id=user_id, erased_at=convert.to_ts(t)), user_id)
        return t

    def metrics_snapshot(self) -> dict[str, dict[str, float]]:
        out = {}
        for (engine, variant), m in self.metrics.items():
            d = dict(m)
            d["positive_rate"] = d.get("positives", 0) / d["items"] if d.get("items") else 0.0
            out[f"{engine}/{variant}"] = d
        return out

