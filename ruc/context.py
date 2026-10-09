"""Request context: where, when and how a recommendation is asked for, and
how it moves the ranking (contextual recommendation).

Context = historical preferences (UserState) + current session + location +
device + time + activity (surface) + current topic + current community +
recent interactions. context_relevance() turns it into one 0..1 component of
the score; the surface also picks the content kinds and ranking weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb

from .domain import now
from .intelligence.hub import ContentState, UserState, daypart

SURFACE_KINDS: dict[int, tuple[int, ...]] = {
    cpb.SURFACE_REELS: (cpb.CONTENT_KIND_REEL,),
    cpb.SURFACE_GLIMPSE: (cpb.CONTENT_KIND_GLIMPSE,),
    cpb.SURFACE_INSTANTS: (cpb.CONTENT_KIND_INSTANT,),
}


@dataclass
class RecContext:
    surface: int = cpb.SURFACE_UNSPECIFIED
    device_type: str = ""
    country: str = ""
    language: str = ""
    utc_offset_minutes: int = 0
    session_id: str = ""
    request_id: str = ""
    topics: list[str] = field(default_factory=list)       # current topic(s)
    community_id: str = ""
    seed_content_id: str = ""
    seed_creator_id: str = ""
    seed_user_id: str = ""
    seed_vector: np.ndarray | None = None                 # set by the engine from seed_content_id
    t: float = field(default_factory=now)

    @property
    def daypart(self) -> str:
        return daypart(self.t, self.utc_offset_minutes)

    @classmethod
    def from_proto(cls, rc: cpb.RequestContext, **kw) -> "RecContext":
        attrs = dict(rc.attributes)
        try:
            offset = int(attrs.get("utc_offset_minutes", "0"))
        except ValueError:
            offset = 0
        offset = max(-14 * 60, min(offset, 14 * 60))
        t = rc.request_time.ToSeconds() if rc.HasField("request_time") else now()
        # a client clock is a hint only: never more than 5 minutes off the server's
        t = t if abs(t - now()) < 300 else now()
        topics = list(kw.pop("topics", []) or [])
        if attrs.get("current_topic"):
            topics.append(attrs["current_topic"])
        community = kw.pop("community_id", "") or attrs.get("community_id", "")
        return cls(surface=rc.surface, device_type=rc.device_type, country=rc.country.upper(),
                   language=(rc.locale.split("-", 1)[0].lower() if rc.locale else ""),
                   utc_offset_minutes=offset, session_id=rc.session_id, request_id=rc.request_id,
                   topics=topics, community_id=community, t=t, **kw)

    def kinds(self, requested: list[int]) -> set[int]:
        if requested:
            return set(requested)
        return set(SURFACE_KINDS.get(self.surface, ()))


def _sim(a: np.ndarray | None, b: np.ndarray | None) -> float | None:
    """Cosine similarity of unit vectors, floored at 0 (unrelated = 0, not 0.5)."""
    if a is None or b is None:
        return None
    return max(0.0, float(np.dot(a, b)))


def content_context_relevance(st: UserState, cs: ContentState, ctx: RecContext) -> float:
    """0..1: how well the item fits this moment. Missing context counts as neutral."""
    parts: list[tuple[float, float]] = []           # (value, weight)
    item = cs.item
    tw = item.topic_weights(include_sensitive=False)
    if ctx.topics:
        parts.append((max((tw.get(tp, 0.0) for tp in ctx.topics), default=0.0), 3.0))
    if ctx.community_id:
        parts.append((1.0 if item.community_id == ctx.community_id else 0.0, 2.0))
    if ctx.seed_creator_id:
        parts.append((1.0 if item.creator_id == ctx.seed_creator_id else 0.0, 2.0))
    seed = _sim(ctx.seed_vector, cs.vector)
    if seed is not None:
        parts.append((seed, 4.0))                         # "related to this item" dominates
    if st.recent_topics:
        parts.append((max((st.recent_topics.get(tp, 0.0) * w for tp, w in tw.items()), default=0.0), 1.5))
    sess = _sim(st.session_embedding, cs.vector)
    if sess is not None:
        parts.append((sess, 1.5))
    shares = st.context_kind_affinity.get((ctx.daypart, ctx.device_type))
    if shares and st.kind_affinity:
        base = st.kind_affinity.get(item.kind, 0.0)
        here = shares.get(item.kind, 0.0)
        # > 0.5 when this kind is more popular with the user at this daypart / device than overall
        parts.append((0.5 + 0.5 * max(-1.0, min((here - base) / max(base, 0.05), 1.0)), 1.0))
    if ctx.language and item.language:
        parts.append((1.0 if item.language.split("-", 1)[0].lower() == ctx.language else 0.3, 0.5))
    if not parts:
        return 0.5
    return sum(v * w for v, w in parts) / sum(w for _, w in parts)
