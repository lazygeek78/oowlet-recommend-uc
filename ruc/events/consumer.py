"""Event-layer consumer and publisher (recommenduc/events.proto).

Consumed (dispatched by payload type, whatever the topic):
  EngagementRecorded, ContentChanged, GraphChanged, ProfileChanged
  legacy eventlayer events, mapped onto the engine's types:
    PostEngagementEvent  engagement_type string  -> EngagementEvent
    BehaviorUpdatedEvent behavior_type string    -> EngagementEvent
    PostCreated/DeletedEvent                     -> catalog (PostUpdatedEvent: nothing structured, ignored)
Producers on these topics are platform services: restrict who may publish
to them with broker ACLs (user ids in events are trusted as the producer
states them).

Delivery: the broker commits on delivery (at most once). Engagement is
idempotent by event_id, so a producer may re-send safely.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging

from google.protobuf import symbol_database
from google.protobuf.message import Message

from oowlet.gen.eventlayer.behavioreventspb import behavior_events_pb2 as bpb
from oowlet.gen.eventlayer.posteventspb import post_events_pb2 as pepb
from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb
from oowlet.gen.recommenduc.eventspb import events_pb2 as evpb

from .. import convert
from ..app import App
from ..domain import CONTENT, USER, ContentRecord, Engagement, Topic, now
from .broker import BrokerClient

log = logging.getLogger("ruc.events")
E = epb

TOPICS = ["recommenduc.engagement.recorded", "recommenduc.content.changed", "recommenduc.graph.changed",
          "recommenduc.profile.changed"]

# legacy free-text engagement names -> EngagementType
LEGACY_TYPES = {
    "impression": E.ENGAGEMENT_TYPE_IMPRESSION, "view": E.ENGAGEMENT_TYPE_VIEW, "open": E.ENGAGEMENT_TYPE_OPEN,
    "click": E.ENGAGEMENT_TYPE_CLICK, "complete": E.ENGAGEMENT_TYPE_VIEW_COMPLETE,
    "view_complete": E.ENGAGEMENT_TYPE_VIEW_COMPLETE, "watch": E.ENGAGEMENT_TYPE_WATCH_TIME,
    "like": E.ENGAGEMENT_TYPE_LIKE, "unlike": E.ENGAGEMENT_TYPE_UNLIKE, "reaction": E.ENGAGEMENT_TYPE_REACTION,
    "react": E.ENGAGEMENT_TYPE_REACTION, "comment": E.ENGAGEMENT_TYPE_COMMENT, "share": E.ENGAGEMENT_TYPE_SHARE,
    "save": E.ENGAGEMENT_TYPE_SAVE, "bookmark": E.ENGAGEMENT_TYPE_SAVE, "unsave": E.ENGAGEMENT_TYPE_UNSAVE,
    "repost": E.ENGAGEMENT_TYPE_REPOST, "follow": E.ENGAGEMENT_TYPE_FOLLOW, "unfollow": E.ENGAGEMENT_TYPE_UNFOLLOW,
    "hide": E.ENGAGEMENT_TYPE_HIDE, "not_interested": E.ENGAGEMENT_TYPE_HIDE, "report": E.ENGAGEMENT_TYPE_REPORT,
    "skip": E.ENGAGEMENT_TYPE_SKIP, "purchase": E.ENGAGEMENT_TYPE_PURCHASE, "outcome": E.ENGAGEMENT_TYPE_OUTCOME,
    "profile_visit": E.ENGAGEMENT_TYPE_PROFILE_VISIT, "search_click": E.ENGAGEMENT_TYPE_SEARCH_CLICK,
}
LEGACY_KINDS = {"text": cpb.CONTENT_KIND_TEXT, "image": cpb.CONTENT_KIND_IMAGE, "video": cpb.CONTENT_KIND_VIDEO,
                "audio": cpb.CONTENT_KIND_AUDIO, "blog": cpb.CONTENT_KIND_BLOG, "reel": cpb.CONTENT_KIND_REEL,
                "glimpse": cpb.CONTENT_KIND_GLIMPSE, "instant": cpb.CONTENT_KIND_INSTANT, "live": cpb.CONTENT_KIND_LIVE}


def _legacy_event_id(*parts: str) -> str:
    return "legacy-" + hashlib.sha256("\x00".join(parts).encode()).hexdigest()[:32]


class EventConsumer:
    def __init__(self, app: App, broker: BrokerClient) -> None:
        self.app = app
        self.broker = broker
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None
        self.handled = 0
        self.skipped = 0

    async def start(self) -> None:
        topics = TOPICS + [t for t in self.app.s.broker.legacy_topics if t not in TOPICS]
        self._task = asyncio.create_task(self._loop(topics), name="ruc-events")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(asyncio.shield(self._task), 10)
            except asyncio.TimeoutError:
                self._task.cancel()
                await asyncio.gather(self._task, return_exceptions=True)

    async def _loop(self, topics: list[str]) -> None:
        async for env in self.broker.subscribe(self.app.s.broker.consumer_group, topics, self._stop):
            try:
                if await self.handle(env):
                    self.handled += 1
                else:
                    self.skipped += 1
            except convert.Invalid as exc:
                self.skipped += 1
                log.warning("event %s (%s) rejected: %s", env.event_id, env.event_type, exc)
            except Exception:  # noqa: BLE001 - one bad event never stops the consumer
                self.skipped += 1
                log.exception("event %s (%s) failed", env.event_id, env.event_type)

    async def handle(self, env) -> bool:
        """Apply one event; False when the engine does not use it."""
        anyp = env.payload
        name = anyp.type_url.rsplit("/", 1)[-1]
        try:
            cls = symbol_database.Default().GetSymbol(name)
        except KeyError:
            log.debug("event %s: unknown payload %s", env.event_id, name)
            return False
        msg = cls()
        if not anyp.Unpack(msg):
            raise convert.Invalid(f"payload is not a valid {name}")
        app = self.app
        if isinstance(msg, evpb.EngagementRecorded):
            if len(msg.events) > 500:
                raise convert.Invalid("at most 500 events")
            evs = []
            for e in msg.events:
                try:
                    evs.append(convert.engagement_from_proto(e))
                except convert.Invalid as exc:
                    log.warning("engagement %s rejected: %s", e.event_id, exc)
            await app.record_engagement(evs)
        elif isinstance(msg, evpb.ContentChanged):
            if msg.change == evpb.CHANGE_TYPE_REMOVED:
                await app.set_content_status(msg.item.content_id, msg.item.status or ctpb.CONTENT_STATUS_REMOVED)
            else:
                await app.upsert_content(convert.content_from_proto(msg.item))
        elif isinstance(msg, evpb.GraphChanged):
            await app.upsert_edges([convert.edge_from_proto(e) for e in msg.upserted])
            await app.remove_edges([convert.edge_from_proto(e) for e in msg.removed])
        elif isinstance(msg, evpb.ProfileChanged):
            convert._id(msg.user_id, "user_id")
            if msg.HasField("attributes"):
                paths = list(msg.changed.paths)
                await app.update_user(msg.user_id, lambda u: convert.apply_attributes(u, msg.attributes, paths))
            app.intel.invalidate(msg.user_id)
        elif isinstance(msg, pepb.PostEngagementEvent):
            t = LEGACY_TYPES.get(msg.engagement_type.strip().lower())
            if t is None:
                raise convert.Invalid(f"unknown engagement_type {msg.engagement_type!r}")
            ts = msg.timestamp_ms / 1000.0 if msg.timestamp_ms else now()
            eid = msg.base.id or _legacy_event_id(msg.user_id, msg.post_id, msg.engagement_type, str(msg.timestamp_ms))
            await app.record_engagement([Engagement(event_id=eid, user_id=convert._id(msg.user_id, "user_id"),
                                                    target_type=CONTENT, target_id=convert._id(msg.post_id, "post_id"),
                                                    type=t, ts=min(ts, now()))])
        elif isinstance(msg, bpb.BehaviorUpdatedEvent):
            t = LEGACY_TYPES.get(msg.behavior_type.strip().lower())
            if t is None:
                return False                             # behaviour kinds the engine does not use
            target = USER if msg.resource_type.lower() in ("user", "profile", "creator") else CONTENT
            ts = convert.ts_of(msg.base.created_at, now())
            eid = msg.base.id or _legacy_event_id(msg.user_id, msg.resource_id, msg.behavior_type, str(ts))
            await app.record_engagement([Engagement(
                event_id=eid, user_id=convert._id(msg.user_id, "user_id"), target_type=target,
                target_id=convert._id(msg.resource_id, "resource_id"), type=t, ts=min(ts, now()),
                dwell_s=max(msg.duration_ms, 0) / 1000.0, session_id=msg.session_id[:128])])
        elif isinstance(msg, pepb.PostCreatedEvent):
            # legacy posts carry no visibility: they are recommended only when
            # RUC_BROKER__LEGACY_POSTS_PUBLIC=true says posts are public
            public = app.s.broker.legacy_posts_public
            await app.upsert_content(ContentRecord(
                content_id=convert._id(msg.post_id, "post_id"), creator_id=convert._id(msg.user_id, "user_id"),
                kind=LEGACY_KINDS.get(msg.content_type.strip().lower(), cpb.CONTENT_KIND_TEXT),
                topics=[Topic(t.strip().lower()[:128], 1.0) for t in msg.tags[:32] if t.strip()],
                hashtags=[t[:64] for t in msg.tags[:32]], published_at=convert.ts_of(msg.base.created_at, now()),
                visibility=ctpb.VISIBILITY_PUBLIC if public else ctpb.VISIBILITY_UNSPECIFIED,
                audience_unknown=True,                   # no audience in the event: adults only
                status=ctpb.CONTENT_STATUS_ACTIVE, updated_at=now()))
        elif isinstance(msg, pepb.PostDeletedEvent):
            await app.set_content_status(convert._id(msg.post_id, "post_id"), ctpb.CONTENT_STATUS_DELETED)
        else:
            # includes PostUpdatedEvent: its free-text states carry nothing the engine can apply
            return False
        return True


class EventPublisher:
    def __init__(self, broker: BrokerClient) -> None:
        self.broker = broker

    async def publish(self, topic: str, msg: Message, key: str) -> None:
        await self.broker.publish(self.broker.envelope(topic, msg, partition_key=key), wait_for_persistence=False)
