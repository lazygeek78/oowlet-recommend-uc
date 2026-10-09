"""The shared user / content intelligence layer.

Both engines (content and people) read users and content only through this
layer, so they share one understanding: the same embeddings, affinities,
history and feedback. It is built from the store and kept current by the
feedback loop (every recorded engagement invalidates that user's state).

User profile, as the engines see it (UserState):
  explicit preferences   declared topics, kinds, languages, mutes, blocks
  behavioral preferences decayed affinities from engagement (7-day half-life)
  historical preferences the same over a long horizon (90-day half-life)
  contextual preferences what the user engages with by daypart and device
  session                what they engaged with in the current session
  user embedding         decayed mean of the vectors of engaged content
Content (ContentState): vector, quality, credibility, freshness, trend,
engagement statistics.
Time-awareness: every history-derived number is exponentially decayed.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb

from .. import signals
from ..config import Settings
from ..domain import (BLOCKED, COMMUNITY_MEMBER, CONNECTED, CONTENT, FOLLOWS, MUTED, REQUESTED, USER,
                      ContentRecord, Preferences, Privacy, Topic, UserRecord, now)
from ..store.base import Counters, Store
from .embeddings import Embedder, make_embedder, unit
from .feature_client import FeatureServiceClient
from .vector_index import ExactIndex

log = logging.getLogger("ruc.intelligence")
E = epb
DAY = 86400.0
FRESH_HALF_LIFE_DAYS = {
    cpb.CONTENT_KIND_REEL: 1.0, cpb.CONTENT_KIND_GLIMPSE: 1.0, cpb.CONTENT_KIND_INSTANT: 0.5,
    cpb.CONTENT_KIND_LIVE: 0.25, cpb.CONTENT_KIND_TEXT: 2.0, cpb.CONTENT_KIND_IMAGE: 3.0,
    cpb.CONTENT_KIND_VIDEO: 3.0, cpb.CONTENT_KIND_AUDIO: 7.0, cpb.CONTENT_KIND_BLOG: 7.0,
}


def daypart(ts: float, utc_offset_minutes: int = 0) -> str:
    h = datetime.fromtimestamp(ts, tz=timezone(timedelta(minutes=utc_offset_minutes))).hour
    return "night" if h < 6 else "morning" if h < 12 else "afternoon" if h < 18 else "evening"


def _norm(d: dict[str, float]) -> dict[str, float]:
    m = max(d.values(), default=0.0)
    return {k: v / m for k, v in d.items() if v > 0} if m > 0 else {}


@dataclass
class UserState:
    user: UserRecord
    known: bool                                   # a profile exists
    personalized: bool                            # privacy allows personalization at all
    uses_history: bool                            # ... and the engagement history
    topic_affinity: dict[str, float] = field(default_factory=dict)       # 0..1, declared + behavioral + historical
    recent_topics: dict[str, float] = field(default_factory=dict)        # current session / last hours
    negative_topics: dict[str, float] = field(default_factory=dict)
    creator_affinity: dict[str, float] = field(default_factory=dict)
    negative_creators: dict[str, float] = field(default_factory=dict)
    kind_affinity: dict[int, float] = field(default_factory=dict)
    context_kind_affinity: dict[tuple[str, str], dict[int, float]] = field(default_factory=dict)
    embedding: np.ndarray | None = None
    session_embedding: np.ndarray | None = None
    recent_positive: list[tuple[str, float]] = field(default_factory=list)   # (content_id, weight)
    consumed: set[str] = field(default_factory=set)
    dismissed: set[str] = field(default_factory=set)
    impressions: dict[str, int] = field(default_factory=dict)                # last 7 days
    engaged_recently: set[str] = field(default_factory=set)
    following: set[str] = field(default_factory=set)
    followers: set[str] = field(default_factory=set)
    connections: set[str] = field(default_factory=set)
    requests_out: set[str] = field(default_factory=set)
    requests_in: set[str] = field(default_factory=set)
    blocked: set[str] = field(default_factory=set)                         # either direction
    muted_users: set[str] = field(default_factory=set)
    communities: set[str] = field(default_factory=set)
    interacted_users: dict[str, float] = field(default_factory=dict)       # outbound, decayed
    dismissed_users: set[str] = field(default_factory=set)
    built_at: float = 0.0

    @property
    def prefs(self) -> Preferences:
        return self.user.preferences

    @property
    def privacy(self) -> Privacy:
        return self.user.privacy


@dataclass
class ContentState:
    item: ContentRecord
    vector: np.ndarray | None
    stats_24h: Counters
    stats_7d: Counters
    quality: float
    credibility: float
    freshness: float
    trend: float
    negative_rate: float


class Intelligence:
    def __init__(self, settings: Settings, store: Store, embedder: Embedder | None = None,
                 features: FeatureServiceClient | None = None) -> None:
        self.s = settings
        self.store = store
        self.embedder = embedder or make_embedder(settings.intelligence.embedding_model,
                                                  settings.intelligence.embedding_dim)
        self.features = features
        self.content_index = ExactIndex(self.embedder.dim)
        self.user_index = ExactIndex(self.embedder.dim)
        self._user_cache: dict[str, dict[str, tuple[float, UserState]]] = {}
        self._trend: tuple[float, dict[str, float]] = (0.0, {})
        self._trend_windows: dict[float, tuple[float, list[tuple[str, float]]]] = {}
        self._sensitive_prefixes = tuple(p.lower() for p in settings.policy.sensitive_topic_prefixes)
        self._bg: set[asyncio.Task] = set()

    # ── content ────────────────────────────────────────────────────────────
    def is_sensitive(self, topic_id: str, flagged: bool = False) -> bool:
        if flagged:
            return True
        head = topic_id.lower().split(".", 1)[0].split("/", 1)[0]
        return head in self._sensitive_prefixes

    def classify(self, item: ContentRecord) -> ContentRecord:
        for t in item.topics:
            t.sensitive = self.is_sensitive(t.topic_id, t.sensitive)
        return item

    async def enrich(self, item: ContentRecord) -> ContentRecord:
        """Fill features from the feature service (off the request path: at upsert)."""
        if self.features is None:
            return item
        got = (await self.features.content_features([item.content_id])).get(item.content_id, {})
        emb = got.get("embedding")
        if emb is not None:
            vec, model = emb
            if model == self.embedder.model_id and vec.shape == (self.embedder.dim,):
                item.embeddings[model] = unit(vec)
        for role in ("semantic_embedding", "visual_embedding", "audio_embedding"):
            if role in got:
                vec, model = got[role]
                item.embeddings[f"{role}:{model}"] = unit(vec)
        if not item.topics and isinstance(got.get("topics"), list):
            for raw in got["topics"][:32]:
                tid, _, w = str(raw).partition(":")
                try:
                    weight = float(w) if w else 1.0
                except ValueError:
                    weight = 1.0
                item.topics.append(Topic(tid, max(0.0, min(weight, 1.0)), source=cpb.AFFINITY_SOURCE_INFERRED))
        if isinstance(got.get("entities"), list):
            item.entities = [str(e) for e in got["entities"][:64]]
        if isinstance(got.get("sentiment"), (int, float)):
            item.sentiment = float(got["sentiment"])
        for role in ("intent", "category"):
            if isinstance(got.get(role), str):
                setattr(item, role, got[role])
        if isinstance(got.get("quality"), (int, float)):
            item.quality = max(0.0, min(float(got["quality"]), 1.0))
        if isinstance(got.get("credibility"), (int, float)):
            # the trust module's score stays authoritative: take the stricter of the two
            item.trust = min(item.trust, max(0.0, min(float(got["credibility"]), 1.0)))
        return item

    async def index_content(self, item: ContentRecord) -> None:
        if item.status == ctpb.CONTENT_STATUS_ACTIVE:
            self.content_index.upsert(item.content_id, self.embedder.embed_content(item))
        else:
            self.content_index.remove(item.content_id)

    async def rebuild_indexes(self) -> None:
        for item in await self.store.iter_content():
            await self.index_content(item)
        for u in await self.store.iter_users():
            v = u.embeddings.get(self.embedder.model_id)
            if v is not None and self._user_indexable(u):
                self.user_index.upsert(u.user_id, v)

    async def content_states(self, ids: list[str], t: float | None = None) -> dict[str, ContentState]:
        t = t or now()
        items = await self.store.get_content(ids)
        trend = await self.trend_scores(t)
        out: dict[str, ContentState] = {}
        for cid, item in items.items():
            s24 = await self.store.content_counters(cid, t - DAY)
            s7 = await self.store.content_counters(cid, t - 7 * DAY)
            views = max(s7.counts["views"] + s7.counts["opens"], 0)
            # engagement quality with a Bayesian prior: few views say little
            eng_rate = (s7.positives + 10 * 0.05) / (views + 10)
            completion = (s7.counts["completions"] + 10 * 0.3) / (s7.counts["views"] + 10)
            neg_rate = (s7.negatives + 0.0) / (s7.counts["impressions"] + 20)
            q = 0.5 * item.quality + 0.3 * min(eng_rate / 0.2, 1.0) + 0.2 * completion - min(neg_rate * 5, 0.5)
            hl = FRESH_HALF_LIFE_DAYS.get(item.kind, 3.0) * DAY
            fresh = signals.decay(t - item.published_at, hl) if item.published_at else 0.0
            vec = self.content_index.get(cid)
            out[cid] = ContentState(item=item, vector=vec, stats_24h=s24, stats_7d=s7,
                                    quality=max(0.0, min(q, 1.0)), credibility=item.trust, freshness=fresh,
                                    trend=trend.get(cid, 0.0), negative_rate=neg_rate)
        return out

    async def trending_window(self, seconds: float, t: float | None = None) -> list[tuple[str, float]]:
        """Raw trending list for a window, cached for a minute (GetTrending)."""
        t = t or now()
        hit = self._trend_windows.get(seconds)
        if hit and t - hit[0] < 60:
            return hit[1]
        top = await self.store.trending(t - seconds, 1000)
        self._trend_windows[seconds] = (t, top)
        return top

    async def trend_scores(self, t: float | None = None) -> dict[str, float]:
        t = t or now()
        if t - self._trend[0] < 60:
            return self._trend[1]
        top = await self.store.trending(t - DAY, 500)
        mx = top[0][1] if top else 0.0
        scores = {cid: s / mx for cid, s in top} if mx > 0 else {}
        self._trend = (t, scores)
        return scores

    # ── users ──────────────────────────────────────────────────────────────
    def invalidate(self, user_id: str) -> None:
        self._user_cache.pop(user_id, None)           # every session of this user

    async def user_record(self, user_id: str) -> tuple[UserRecord, bool]:
        u = await self.store.get_user(user_id)
        if u is None:
            # unknown user: platform-default privacy, unknown age (= treated as minor)
            return UserRecord(user_id=user_id, privacy=Privacy.platform_defaults()), False
        return u, True

    @staticmethod
    def _user_indexable(u: UserRecord) -> bool:
        p = u.privacy
        return p.discoverable_in_suggestions and p.personalization_enabled and p.use_engagement_history

    async def user_state(self, user_id: str, session_id: str = "", utc_offset_minutes: int = 0,
                         t: float | None = None) -> UserState:
        t = t or now()
        key = f"{session_id}\x00{utc_offset_minutes}"
        hit = self._user_cache.get(user_id, {}).get(key)
        ttl = self.s.intelligence.user_state_ttl_seconds
        if hit and t - hit[0] < ttl:
            return hit[1]
        st = await self._build_user_state(user_id, session_id, utc_offset_minutes, t)
        if len(self._user_cache) > 100_000:
            self._user_cache.clear()
        sessions = self._user_cache.setdefault(user_id, {})
        if len(sessions) > 8:
            sessions.clear()
        sessions[key] = (t, st)
        return st

    async def _build_user_state(self, user_id: str, session_id: str, utc_offset: int, t: float) -> UserState:
        cfg = self.s.intelligence
        user, known = await self.user_record(user_id)
        p = user.privacy
        st = UserState(user=user, known=known, personalized=p.personalization_enabled,
                       uses_history=p.personalization_enabled and p.use_engagement_history, built_at=t)
        await self._load_graph(st)
        st.muted_users |= set(user.preferences.muted_user_ids)
        st.blocked |= set(user.preferences.blocked_user_ids)

        events = await self.store.user_events(user_id, since=t - cfg.history_retention_days * DAY,
                                              newest_first=False)
        feedback = await self.store.feedback_for_user(user_id, since=t - 90 * DAY)
        # dedup and frequency state is kept even without personalization:
        # it only stops repeats, it does not rank
        seen_cut = t - self.s.policy.seen_window_days * DAY
        for ev in events:
            if ev.target_type == CONTENT:
                if ev.type in signals.CONSUMED and ev.ts >= seen_cut:
                    st.consumed.add(ev.target_id)
                if ev.type in signals.DISMISSED:
                    st.dismissed.add(ev.target_id)
                if ev.ts >= t - 7 * DAY:
                    if ev.type == E.ENGAGEMENT_TYPE_IMPRESSION:
                        st.impressions[ev.target_id] = st.impressions.get(ev.target_id, 0) + 1
                    elif signals.weight(ev) > 0:
                        st.engaged_recently.add(ev.target_id)
            elif ev.target_type == USER and ev.type in (E.ENGAGEMENT_TYPE_SUGGESTION_DISMISSED,
                                                         E.ENGAGEMENT_TYPE_CONNECT_DECLINED,
                                                         E.ENGAGEMENT_TYPE_CONNECT_REMOVED):
                st.dismissed_users.add(ev.target_id)
        for fb in feedback:
            if fb.target_type == CONTENT and fb.type in (rpb.FEEDBACK_TYPE_NOT_INTERESTED, rpb.FEEDBACK_TYPE_INAPPROPRIATE):
                st.dismissed.add(fb.target_id)
            elif fb.target_type == CONTENT and fb.type == rpb.FEEDBACK_TYPE_ALREADY_SEEN:
                st.consumed.add(fb.target_id)
            elif fb.target_type == USER and fb.type in (rpb.FEEDBACK_TYPE_DONT_KNOW_PERSON, rpb.FEEDBACK_TYPE_INAPPROPRIATE):
                st.dismissed_users.add(fb.target_id)

        if not st.personalized:
            return st
        declared = self._declared_topics(user)
        if not st.uses_history:
            st.topic_affinity = declared
            st.kind_affinity = {k: 1.0 for k in user.preferences.preferred_kinds}
            st.embedding = await self._cold_start_embedding(declared)
            return st

        content_ids = {e.target_id for e in events if e.target_type == CONTENT}
        items = await self.store.get_content(content_ids)
        beh_hl, hist_hl = cfg.behavioral_half_life_days * DAY, cfg.historical_half_life_days * DAY
        recent_hl = cfg.recent_half_life_hours * 3600
        session_cut = t - cfg.session_gap_minutes * 60
        beh: dict[str, float] = defaultdict(float)
        hist: dict[str, float] = defaultdict(float)
        recent: dict[str, float] = defaultdict(float)
        neg_t: dict[str, float] = defaultdict(float)
        cre: dict[str, float] = defaultdict(float)
        neg_c: dict[str, float] = defaultdict(float)
        kinds: dict[int, float] = defaultdict(float)
        ctx_kinds: dict[tuple[str, str], dict[int, float]] = defaultdict(lambda: defaultdict(float))
        pos_items: dict[str, float] = defaultdict(float)
        vec_sum = np.zeros(self.embedder.dim, dtype=np.float64)
        sess_sum = np.zeros(self.embedder.dim, dtype=np.float64)
        inter: dict[str, float] = defaultdict(float)
        for ev in events:
            w = signals.weight(ev)
            if w == 0:
                continue
            age = t - ev.ts
            if ev.target_type == USER:
                inter[ev.target_id] += w * signals.decay(age, beh_hl)
                continue
            item = items.get(ev.target_id)
            if item is None:
                continue
            d_beh, d_hist = signals.decay(age, beh_hl), signals.decay(age, hist_hl)
            in_session = (session_id and ev.session_id == session_id) or ev.ts >= session_cut
            if w > 0:
                for tp in item.topics:
                    if tp.sensitive:
                        continue        # sensitive topics are never inferred from behaviour
                    beh[tp.topic_id] += w * tp.weight * d_beh
                    hist[tp.topic_id] += w * tp.weight * d_hist
                    if in_session:
                        recent[tp.topic_id] += w * tp.weight * signals.decay(age, recent_hl)
                cre[item.creator_id] += w * d_beh
                inter[item.creator_id] += 0.5 * w * d_beh
                kinds[item.kind] += w * d_hist
                ctx_kinds[(daypart(ev.ts, utc_offset), ev.device_type or "")][item.kind] += w * d_hist
                pos_items[item.content_id] += w * d_beh
                v = self.content_index.get(item.content_id)
                if v is not None:
                    vec_sum += w * d_beh * v
                    if in_session:
                        sess_sum += w * v
            else:
                for tp in item.topics:
                    if not tp.sensitive:      # nothing is inferred about sensitive topics, not even dislike
                        neg_t[tp.topic_id] += -w * tp.weight * d_beh
                neg_c[item.creator_id] += -w * d_beh
        for fb in feedback:
            if fb.type == rpb.FEEDBACK_TYPE_SEE_LESS_OF_TOPIC and fb.topic_id:
                neg_t[fb.topic_id] += 6.0 * signals.decay(t - fb.given_at, hist_hl)
            elif fb.type == rpb.FEEDBACK_TYPE_SEE_LESS_FROM_CREATOR:
                item = (await self.store.get_content([fb.target_id])).get(fb.target_id)
                creator = item.creator_id if item else fb.target_id
                neg_c[creator] += 6.0 * signals.decay(t - fb.given_at, hist_hl)
            elif fb.type == rpb.FEEDBACK_TYPE_SEE_MORE_LIKE_THIS and fb.target_type == CONTENT:
                item = (await self.store.get_content([fb.target_id])).get(fb.target_id)
                if item:
                    for tp in item.topics:
                        if not tp.sensitive:
                            beh[tp.topic_id] += 4.0 * tp.weight * signals.decay(t - fb.given_at, beh_hl)

        behavioral, historical = _norm(beh), _norm(hist)
        affinity: dict[str, float] = defaultdict(float)
        for k, v in declared.items():
            affinity[k] += 0.35 * v
        for k, v in behavioral.items():
            affinity[k] += 0.40 * v
        for k, v in historical.items():
            affinity[k] += 0.25 * v
        for tp in user.inferred_topics:
            if not self.is_sensitive(tp.topic_id, tp.sensitive):
                affinity[tp.topic_id] = max(affinity[tp.topic_id], 0.5 * tp.weight)
        st.topic_affinity = _norm(affinity)
        st.recent_topics = _norm(recent)
        st.negative_topics = _norm(neg_t)
        st.creator_affinity = _norm(cre)
        st.negative_creators = _norm(neg_c)
        total = sum(kinds.values())
        st.kind_affinity = {k: v / total for k, v in kinds.items()} if total > 0 else {}
        for key, d in ctx_kinds.items():
            s = sum(d.values())
            if s > 0:
                st.context_kind_affinity[key] = {k: v / s for k, v in d.items()}
        st.recent_positive = sorted(pos_items.items(), key=lambda kv: -kv[1])[:30]
        st.interacted_users = _norm(inter)
        if np.any(vec_sum):
            st.embedding = unit(vec_sum.astype(np.float32))
        else:
            st.embedding = await self._cold_start_embedding(declared)
        if np.any(sess_sum):
            st.session_embedding = unit(sess_sum.astype(np.float32))
        self._after_build(st)
        return st

    def _after_build(self, st: UserState) -> None:
        u = st.user
        if st.embedding is not None and st.known:
            if self._user_indexable(u):
                self.user_index.upsert(u.user_id, st.embedding)
            else:
                self.user_index.remove(u.user_id)
        if self.features is not None and st.known:
            task = asyncio.ensure_future(self.features.write_user_features(
                u.user_id, st.embedding, self.embedder.model_id, st.topic_affinity, st.creator_affinity))
            self._bg.add(task)
            task.add_done_callback(self._bg.discard)

    def _declared_topics(self, user: UserRecord) -> dict[str, float]:
        out: dict[str, float] = {}
        allow_sensitive = user.privacy.allow_declared_sensitive_topics
        for tid in user.preferences.preferred_topic_ids:
            if self.is_sensitive(tid) and not allow_sensitive:
                continue
            out[tid] = 1.0
        for tp in user.declared_topics:
            if self.is_sensitive(tp.topic_id, tp.sensitive) and not allow_sensitive:
                continue
            out[tp.topic_id] = max(out.get(tp.topic_id, 0.0), tp.weight or 1.0)
        return out

    async def _cold_start_embedding(self, declared: dict[str, float]) -> np.ndarray | None:
        if not declared:
            return None
        items = await self.store.content_by_topics(list(declared)[:20], 50)
        vecs = [self.content_index.get(i.content_id) for i in items]
        vecs = [v for v in vecs if v is not None]
        return unit(np.mean(vecs, axis=0).astype(np.float32)) if vecs else None

    async def _load_graph(self, st: UserState) -> None:
        uid = st.user.user_id
        s = self.store
        st.following = {e.to_user_id for e in await s.out_edges(uid, frozenset({FOLLOWS}))}
        st.followers = {e.from_user_id for e in await s.in_edges(uid, frozenset({FOLLOWS}))}
        st.connections = ({e.to_user_id for e in await s.out_edges(uid, frozenset({CONNECTED}))}
                          | {e.from_user_id for e in await s.in_edges(uid, frozenset({CONNECTED}))})
        st.requests_out = {e.to_user_id for e in await s.out_edges(uid, frozenset({REQUESTED}))}
        st.requests_in = {e.from_user_id for e in await s.in_edges(uid, frozenset({REQUESTED}))}
        st.blocked = ({e.to_user_id for e in await s.out_edges(uid, frozenset({BLOCKED}))}
                      | {e.from_user_id for e in await s.in_edges(uid, frozenset({BLOCKED}))})
        st.muted_users = {e.to_user_id for e in await s.out_edges(uid, frozenset({MUTED}))}
        st.communities = {e.to_user_id for e in await s.out_edges(uid, frozenset({COMMUNITY_MEMBER}))}

    async def close(self) -> None:
        for task in list(self._bg):
            task.cancel()
        if self._bg:
            await asyncio.gather(*self._bg, return_exceptions=True)
