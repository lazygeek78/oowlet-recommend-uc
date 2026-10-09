"""Candidate generation: many cheap sources, each proposing up to `k` items
with a prior in 0..1. The engine merges them into one pool (an item proposed
by several sources keeps all its priors), filters it with the eligibility
rules, then ranks it.

Content sources                         People sources
  collaborative        item-item co-engagement      friends_of_friends   mutual connections
  matrix_factorization implicit ALS (when trained)  shared_interests     user-embedding neighbours
  content_similarity   vector search (embeddings)   same_community       shared communities
  behavioral_similarity users with similar taste    interacted           people whose content you engage with
  social_graph         what your network engaged    co_engagement        people who engage like you
  trending             engagement velocity          follows_you          follow-back
  fresh                new and good                 contextual           current community / seed person
  followed_creators    creators you follow
  interest_topics      your declared / learned topics
  contextual           current topic, community, seed item / creator, session
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from .. import signals
from ..context import RecContext
from ..domain import COMMUNITY_MEMBER, CONNECTED, CONTENT, now
from ..intelligence.hub import Intelligence, UserState

log = logging.getLogger("ruc.candidates")
DAY = 86400.0


@dataclass
class Candidate:
    key: str
    priors: dict[str, float] = field(default_factory=dict)       # source -> 0..1

    @property
    def sources(self) -> list[str]:
        return sorted(self.priors, key=lambda s: -self.priors[s])


@dataclass
class GenInput:
    st: UserState
    ctx: RecContext
    intel: Intelligence
    k: int
    social: dict[str, set[str]] = field(default_factory=dict)     # content_id -> network users who engaged
    mf: object | None = None


Generator = Callable[[GenInput], Awaitable[dict[str, float]]]


def _top(scores: dict[str, float], k: int) -> dict[str, float]:
    top = sorted(scores.items(), key=lambda kv: -kv[1])[:k]
    mx = top[0][1] if top else 0.0
    return {i: (s / mx if mx > 0 else 0.0) for i, s in top if s > 0}


async def social_activity(st: UserState, intel: Intelligence, t: float | None = None) -> dict[str, set[str]]:
    """Items your network engaged with positively in the last 7 days. Only
    people who allow their activity to be shown (show_activity_to_others)
    and whom you have not blocked or muted count."""
    t = t or now()
    network = (st.following | st.connections) - st.blocked - st.muted_users
    if not network or not st.personalized:
        return {}
    users = await intel.store.get_users(list(network)[:500])
    out: dict[str, set[str]] = defaultdict(set)
    for uid, u in users.items():
        if not u.privacy.show_activity_to_others or st.user.user_id in u.preferences.blocked_user_ids:
            continue
        for ev in await intel.store.user_events(uid, since=t - 7 * DAY, target_type=CONTENT, limit=100):
            if signals.weight(ev) >= 3.0:                 # like or stronger
                out[ev.target_id].add(uid)
    return out


# ── content sources ────────────────────────────────────────────────────────

async def collaborative(g: GenInput) -> dict[str, float]:
    if not g.st.uses_history:
        return {}
    scores: dict[str, float] = defaultdict(float)
    for item, w in g.st.recent_positive[:20]:
        for nb, s in await g.intel.store.co_engaged(item, 50):
            scores[nb] += w * s
    return _top(scores, g.k)


async def matrix_factorization(g: GenInput) -> dict[str, float]:
    if not g.st.uses_history or g.mf is None:
        return {}
    return _top(dict(g.mf.recommend(g.st.user.user_id, g.k * 2)), g.k)


async def content_similarity(g: GenInput) -> dict[str, float]:
    out: dict[str, float] = {}
    exclude = g.st.consumed | g.st.dismissed
    queries = []
    if g.st.uses_history and g.st.embedding is not None:
        queries.append((g.st.embedding, 1.0))
    if g.st.personalized and g.st.session_embedding is not None:
        queries.append((g.st.session_embedding, 0.8))
    if g.ctx.seed_content_id:
        v = g.intel.content_index.get(g.ctx.seed_content_id)
        if v is not None:
            queries.append((v, 1.2))
            exclude = exclude | {g.ctx.seed_content_id}
    for q, w in queries:
        for cid, sim in g.intel.content_index.search(q, g.k, exclude=exclude):
            out[cid] = max(out.get(cid, 0.0), w * max(sim, 0.0))
    return _top(out, g.k)


async def similar_users(g: GenInput, n: int = 30) -> dict[str, float]:
    """Users with similar taste: co-engaged items, then embedding neighbours.
    Only users who allow contribute_to_collaborative."""
    st, store = g.st, g.intel.store
    sims: dict[str, float] = defaultdict(float)
    t = g.ctx.t
    for item, w in st.recent_positive[:10]:
        for ev in (await store.content_engagers(item, None, since=t - 30 * DAY))[:200]:
            if ev.user_id != st.user.user_id and signals.weight(ev) >= signals.POSITIVE_LABEL_MIN_WEIGHT:
                sims[ev.user_id] += w
    if st.embedding is not None:
        for uid, s in g.intel.user_index.search(st.embedding, n, exclude={st.user.user_id}):
            sims[uid] += max(s, 0.0) * 2.0
    for uid in list(sims):
        if uid in st.blocked:
            del sims[uid]
    users = await store.get_users(list(sims))
    sims = {u: s for u, s in sims.items() if u in users and users[u].privacy.contribute_to_collaborative}
    return _top(sims, n)


async def behavioral_similarity(g: GenInput) -> dict[str, float]:
    if not g.st.uses_history:
        return {}
    scores: dict[str, float] = defaultdict(float)
    for uid, sim in (await similar_users(g)).items():
        for ev in await g.intel.store.user_events(uid, since=g.ctx.t - 14 * DAY, target_type=CONTENT, limit=60):
            w = signals.weight(ev)
            if w >= signals.POSITIVE_LABEL_MIN_WEIGHT:
                scores[ev.target_id] += sim * w * signals.decay(g.ctx.t - ev.ts, 7 * DAY)
    return _top(scores, g.k)


async def social_graph(g: GenInput) -> dict[str, float]:
    return _top({cid: float(len(users)) for cid, users in g.social.items()}, g.k)


async def trending(g: GenInput) -> dict[str, float]:
    return dict(list((await g.intel.trend_scores(g.ctx.t)).items())[: g.k])


async def fresh(g: GenInput) -> dict[str, float]:
    items = await g.intel.store.recent_content(g.ctx.t - 2 * DAY, g.k * 3)
    aff = g.st.topic_affinity if g.st.personalized else {}
    out = {}
    for it in items:
        if it.quality < 0.4:
            continue
        match = max((aff.get(t.topic_id, 0.0) * t.weight for t in it.topics), default=0.0)
        out[it.content_id] = 0.4 + 0.6 * match
    return _top(out, g.k)


async def followed_creators(g: GenInput) -> dict[str, float]:
    if not g.st.personalized:
        return {}
    creators = g.st.following | g.st.connections
    if not creators:
        return {}
    items = await g.intel.store.content_by_creators(list(creators), g.ctx.t - 14 * DAY, g.k * 2)
    return _top({i.content_id: 0.5 + g.st.creator_affinity.get(i.creator_id, 0.0) +
                 signals.decay(g.ctx.t - i.published_at, 2 * DAY) for i in items}, g.k)


async def interest_topics(g: GenInput) -> dict[str, float]:
    if not g.st.personalized or not g.st.topic_affinity:
        return {}
    top = sorted(g.st.topic_affinity.items(), key=lambda kv: -kv[1])[:5]
    out: dict[str, float] = {}
    for tid, w in top:
        for it in await g.intel.store.content_by_topics([tid], g.k // 2 + 1):
            out[it.content_id] = max(out.get(it.content_id, 0.0), w)
    return _top(out, g.k)


async def contextual(g: GenInput) -> dict[str, float]:
    ctx, store = g.ctx, g.intel.store
    out: dict[str, float] = defaultdict(float)
    if ctx.topics:
        for it in await store.content_by_topics(ctx.topics, g.k):
            out[it.content_id] += 1.0
    if ctx.community_id:
        for it in await store.content_by_community(ctx.community_id, g.k):
            out[it.content_id] += 1.0
    if ctx.seed_creator_id:
        for it in await store.content_by_creators([ctx.seed_creator_id], 0.0, g.k):
            out[it.content_id] += 1.0
    if ctx.seed_content_id:
        for cid, s in await store.co_engaged(ctx.seed_content_id, g.k):
            out[cid] += min(1.0, s)
    if g.st.personalized and g.st.recent_topics:
        top = sorted(g.st.recent_topics.items(), key=lambda kv: -kv[1])[:3]
        for it in await store.content_by_topics([t for t, _ in top], g.k // 2 + 1):
            out[it.content_id] += 0.5
    out.pop(ctx.seed_content_id, None)
    return _top(out, g.k)


CONTENT_SOURCES: dict[str, Generator] = {
    "collaborative": collaborative,
    "matrix_factorization": matrix_factorization,
    "content_similarity": content_similarity,
    "behavioral_similarity": behavioral_similarity,
    "social_graph": social_graph,
    "trending": trending,
    "fresh": fresh,
    "followed_creators": followed_creators,
    "interest_topics": interest_topics,
    "contextual": contextual,
}
# sources that do not depend on the user's history (cold start, personalization off)
NON_PERSONAL_SOURCES = frozenset({"trending", "fresh", "contextual"})


# ── people sources ─────────────────────────────────────────────────────────

async def mutual_connections(st: UserState, intel: Intelligence) -> dict[str, set[str]]:
    """other user -> mutual connections that may be counted. Nothing is
    computed when the viewer disallows the signal; a connection in the
    middle counts only if it allows the signal; a person at the far end is
    included only if they allow it too and neither side blocked the other."""
    if not st.user.privacy.allow_mutual_connection_signal or not st.connections:
        return {}
    store = intel.store
    me = st.user.user_id
    via = await store.get_users(list(st.connections)[:1000])
    out: dict[str, set[str]] = defaultdict(set)
    for c, rec in via.items():
        if not rec.privacy.allow_mutual_connection_signal or me in rec.preferences.blocked_user_ids:
            continue
        nbrs = ({e.to_user_id for e in await store.out_edges(c, frozenset({CONNECTED}))}
                | {e.from_user_id for e in await store.in_edges(c, frozenset({CONNECTED}))})
        for f in list(nbrs)[:2000]:
            if f != me and f not in st.blocked:
                out[f].add(c)
    far = await store.get_users(list(out))
    return {f: m for f, m in out.items()
            if f in far and far[f].privacy.allow_mutual_connection_signal
            and me not in far[f].preferences.blocked_user_ids}


@dataclass
class PeopleInput:
    st: UserState
    ctx: RecContext
    intel: Intelligence
    k: int
    mutuals: dict[str, set[str]] = field(default_factory=dict)


async def p_friends_of_friends(g: PeopleInput) -> dict[str, float]:
    return _top({u: float(len(m)) for u, m in g.mutuals.items()}, g.k)


async def p_shared_interests(g: PeopleInput) -> dict[str, float]:
    if not g.st.uses_history or g.st.embedding is None:
        return {}
    hits = g.intel.user_index.search(g.st.embedding, g.k, exclude={g.st.user.user_id})
    return _top({u: max(s, 0.0) for u, s in hits}, g.k)


async def p_same_community(g: PeopleInput) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for cid in list(g.st.communities)[:20]:
        for e in (await g.intel.store.in_edges(cid, frozenset({COMMUNITY_MEMBER})))[:300]:
            out[e.from_user_id] += 1.0
    out.pop(g.st.user.user_id, None)
    return _top(out, g.k)


async def p_interacted(g: PeopleInput) -> dict[str, float]:
    if not g.st.uses_history:
        return {}
    return _top(dict(g.st.interacted_users), g.k)


async def p_co_engagement(g: PeopleInput) -> dict[str, float]:
    if not g.st.uses_history:
        return {}
    return await similar_users(GenInput(st=g.st, ctx=g.ctx, intel=g.intel, k=g.k), n=g.k)


async def p_follows_you(g: PeopleInput) -> dict[str, float]:
    return _top({u: 1.0 for u in g.st.followers - g.st.following}, g.k)


async def p_contextual(g: PeopleInput) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    store = g.intel.store
    if g.ctx.community_id:
        for e in (await store.in_edges(g.ctx.community_id, frozenset({COMMUNITY_MEMBER})))[:500]:
            out[e.from_user_id] += 1.0
    if g.ctx.seed_user_id:
        v = g.intel.user_index.get(g.ctx.seed_user_id)
        if v is not None:
            for u, s in g.intel.user_index.search(v, g.k, exclude={g.st.user.user_id, g.ctx.seed_user_id}):
                out[u] += max(s, 0.0)
    out.pop(g.st.user.user_id, None)
    return _top(out, g.k)


PEOPLE_SOURCES: dict[str, Callable[[PeopleInput], Awaitable[dict[str, float]]]] = {
    "friends_of_friends": p_friends_of_friends,
    "shared_interests": p_shared_interests,
    "same_community": p_same_community,
    "interacted": p_interacted,
    "co_engagement": p_co_engagement,
    "follows_you": p_follows_you,
    "contextual": p_contextual,
}


async def run_sources(sources: dict, arg, max_total: int) -> dict[str, Candidate]:
    names = list(sources)
    results = await asyncio.gather(*(sources[n](arg) for n in names), return_exceptions=True)
    pool: dict[str, Candidate] = {}
    for name, res in zip(names, results):
        if isinstance(res, BaseException):
            log.warning("candidate source %s failed: %s: %s", name, type(res).__name__, res)
            continue
        for key, prior in res.items():
            c = pool.get(key)
            if c is None:
                if len(pool) >= max_total:
                    continue
                c = pool[key] = Candidate(key)
            c.priors[name] = max(c.priors.get(name, 0.0), prior)
    return pool

