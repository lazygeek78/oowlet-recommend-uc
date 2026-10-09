"""In-memory Store: the reference implementation (development, tests, and a
single instance that may lose its state on restart).

All methods run on the event loop thread without awaiting in between, so
each call is atomic with respect to other coroutines.
"""

from __future__ import annotations

import bisect
import copy
import math
from collections import defaultdict
from collections.abc import Iterable

from .. import signals
from ..domain import (CONTENT, USER, ContentRecord, Edge, Engagement, Feedback, ServedRecommendation,
                      UserRecord, now)
from .base import COUNTER_OF, Counters, Store, VersionConflict

from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb

HOUR = 3600
ACTIVE = ctpb.CONTENT_STATUS_ACTIVE


class _Bucket:
    __slots__ = ("counts", "dwell", "score")

    def __init__(self) -> None:
        self.counts: dict[str, int] = defaultdict(int)
        self.dwell = 0.0
        self.score = 0.0        # sum of positive signal weights (trending)


class MemoryStore(Store):
    def __init__(self, retention_days: int = 180, max_events_per_user: int = 5000,
                 co_window_items: int = 50, co_max_neighbors: int = 300) -> None:
        self.retention_s = retention_days * 86400
        self.max_events_per_user = max_events_per_user
        self.co_window_items = co_window_items
        self.co_max_neighbors = co_max_neighbors
        self._event_ids: dict[str, tuple[float, str]] = {}                  # event id -> (ts, user)
        self._next_prune = now() + HOUR
        self._user_events: dict[str, list[Engagement]] = defaultdict(list)      # sorted by ts
        self._inbound: dict[str, list[Engagement]] = defaultdict(list)          # target user -> events
        self._content_events: dict[str, list[Engagement]] = defaultdict(list)   # non-impression, sorted
        self._buckets: dict[str, dict[int, _Bucket]] = defaultdict(dict)
        self._content_users: dict[str, dict[str, float]] = defaultdict(dict)    # item -> user -> last ts
        self._co: dict[str, dict[str, float]] = defaultdict(dict)
        self._content: dict[str, ContentRecord] = {}
        self._by_creator: dict[str, set[str]] = defaultdict(set)
        self._by_topic: dict[str, set[str]] = defaultdict(set)
        self._by_community: dict[str, set[str]] = defaultdict(set)
        self._by_published: list[tuple[float, str]] = []                        # sorted (published_at, id)
        self._users: dict[str, UserRecord] = {}
        self._out: dict[str, dict[int, dict[str, Edge]]] = defaultdict(lambda: defaultdict(dict))
        self._in: dict[str, dict[int, dict[str, Edge]]] = defaultdict(lambda: defaultdict(dict))
        self._served: dict[str, ServedRecommendation] = {}
        self._served_by_user: dict[str, list[str]] = defaultdict(list)
        self._served_order: list[tuple[float, str]] = []
        self._feedback: dict[str, list[Feedback]] = defaultdict(list)

    # ── engagement ─────────────────────────────────────────────────────────
    async def add_engagements(self, events: Iterable[Engagement],
                              collaborative: frozenset[str] | None = None) -> tuple[list[Engagement], int]:
        added: list[Engagement] = []
        dupes = 0
        cutoff = now() - self.retention_s
        for ev in events:
            if ev.event_id in self._event_ids:
                dupes += 1
                continue
            if ev.ts < cutoff:
                continue                                  # older than retention: nothing to keep
            self._event_ids[ev.event_id] = (ev.ts, ev.user_id)
            self._insert(self._user_events[ev.user_id], ev)
            if len(self._user_events[ev.user_id]) > self.max_events_per_user:
                del self._user_events[ev.user_id][0]
            if ev.target_type == USER:
                self._insert(self._inbound[ev.target_id], ev)
            elif ev.target_type == CONTENT:
                self._count(ev, collaborative is None or ev.user_id in collaborative)
            added.append(ev)
        if now() >= self._next_prune:              # at most hourly: drops what left the retention window
            self._prune()
            self._next_prune = now() + HOUR
        return added, dupes

    @staticmethod
    def _insert(lst: list[Engagement], ev: Engagement) -> None:
        if not lst or lst[-1].ts <= ev.ts:
            lst.append(ev)
        else:
            bisect.insort(lst, ev, key=lambda e: e.ts)

    def _count(self, ev: Engagement, collaborative: bool = True) -> None:
        cid = ev.target_id
        b = self._buckets[cid].get(int(ev.ts // HOUR) * HOUR)
        if b is None:
            b = self._buckets[cid][int(ev.ts // HOUR) * HOUR] = _Bucket()
        name = COUNTER_OF.get(ev.type)
        if name:
            b.counts[name] += 1
        b.dwell += max(ev.dwell_s, 0.0)
        w = signals.weight(ev)
        if w > 0:
            b.score += w
        if ev.type != epb.ENGAGEMENT_TYPE_IMPRESSION:
            self._insert(self._content_events[cid], ev)
            prev = self._content_users[cid].get(ev.user_id, 0.0)
            self._content_users[cid][ev.user_id] = max(prev, ev.ts)
        if w >= signals.POSITIVE_LABEL_MIN_WEIGHT and collaborative:
            self._co_engage(ev, w)

    def _co_engage(self, ev: Engagement, w: float) -> None:
        """Item-item co-engagement from this user's recent positive items."""
        recent: list[str] = []
        seen = {ev.target_id}
        horizon = ev.ts - 30 * 86400
        for other in reversed(self._user_events[ev.user_id]):
            if other.ts < horizon or len(recent) >= self.co_window_items:
                break
            if (other.target_type == CONTENT and other.target_id not in seen
                    and signals.weight(other) >= signals.POSITIVE_LABEL_MIN_WEIGHT):
                seen.add(other.target_id)
                recent.append(other.target_id)
        a = ev.target_id
        for b in recent:
            inc = math.log1p(w)
            self._co[a][b] = self._co[a].get(b, 0.0) + inc
            self._co[b][a] = self._co[b].get(a, 0.0) + inc
            for x in (a, b):
                if len(self._co[x]) > self.co_max_neighbors * 2:
                    keep = sorted(self._co[x].items(), key=lambda kv: -kv[1])[: self.co_max_neighbors]
                    self._co[x] = dict(keep)

    def _prune(self) -> None:
        cutoff = now() - self.retention_s
        self._event_ids = {k: v for k, v in self._event_ids.items() if v[0] >= cutoff}
        for d in (self._user_events, self._inbound, self._content_events):
            for k in list(d):
                lst = d[k]
                i = bisect.bisect_left(lst, cutoff, key=lambda e: e.ts)
                if i:
                    del lst[:i]
                if not lst:
                    del d[k]
        hcut = int(cutoff // HOUR) * HOUR
        for cid in list(self._buckets):
            kept = {h: b for h, b in self._buckets[cid].items() if h >= hcut}
            if kept:
                self._buckets[cid] = kept
            else:
                del self._buckets[cid]
        for cid in list(self._content_users):
            kept_u = {u: ts for u, ts in self._content_users[cid].items() if ts >= cutoff}
            if kept_u:
                self._content_users[cid] = kept_u
            else:
                del self._content_users[cid]
        for cid in [c for c in self._co if c not in self._content]:
            del self._co[cid]                      # neighbours of items no longer in the catalog

    async def user_events(self, user_id, since=0.0, until=None, types=None, target_type=0, limit=0,
                          newest_first=True):
        lst = self._user_events.get(user_id, [])
        lo = bisect.bisect_left(lst, since, key=lambda e: e.ts)
        hi = len(lst) if until is None else bisect.bisect_left(lst, until, key=lambda e: e.ts)
        rng = range(hi - 1, lo - 1, -1) if newest_first else range(lo, hi)
        out = []
        for i in rng:
            e = lst[i]
            if types is not None and e.type not in types:
                continue
            if target_type and e.target_type != target_type:
                continue
            out.append(e)
            if limit and len(out) >= limit:
                break
        return out

    async def inbound_user_events(self, target_user_id, since=0.0):
        lst = self._inbound.get(target_user_id, [])
        return lst[bisect.bisect_left(lst, since, key=lambda e: e.ts):]

    async def content_counters(self, content_id, since, until=None):
        c = Counters()
        until = until if until is not None else now() + HOUR
        for h, b in self._buckets.get(content_id, {}).items():
            if h < until and h + HOUR > since:          # bucket [h, h+1h) overlaps the window
                for k, v in b.counts.items():
                    c.counts[k] = c.counts.get(k, 0) + v
                c.dwell_seconds += b.dwell
        c.unique_users = sum(1 for ts in self._content_users.get(content_id, {}).values() if since <= ts < until)
        return c

    async def content_timeline(self, content_id, start, end, bucket_seconds):
        bucket_seconds = max(HOUR, bucket_seconds)
        n = max(0, math.ceil((end - start) / bucket_seconds))
        if n > 10000:
            raise ValueError("timeline too long")
        out = [(start + i * bucket_seconds, Counters()) for i in range(n)]
        for h, b in self._buckets.get(content_id, {}).items():
            if start <= h < end:
                i = int((h - start) // bucket_seconds)
                for k, v in b.counts.items():
                    out[i][1].counts[k] = out[i][1].counts.get(k, 0) + v
                out[i][1].dwell_seconds += b.dwell
        return out

    async def content_engagers(self, content_id, types, since=0.0):
        lst = self._content_events.get(content_id, [])
        out = [e for e in reversed(lst) if e.ts >= since and (types is None or e.type in types)]
        return out

    async def co_engaged(self, content_id, k):
        nb = self._co.get(content_id, {})
        return sorted(nb.items(), key=lambda kv: -kv[1])[:k]

    async def trending(self, since, k):
        t_now = now()
        scores: list[tuple[str, float]] = []
        for cid, buckets in self._buckets.items():
            s = 0.0
            for h, b in buckets.items():
                if h + HOUR > since and b.score > 0:
                    s += b.score * signals.decay(t_now - (h + HOUR / 2), 6 * HOUR)
            if s > 0:
                scores.append((cid, s))
        scores.sort(key=lambda kv: -kv[1])
        return scores[:k]

    async def delete_user_data(self, user_id):
        # full scans: erasure is rare, and per-user lists may have dropped
        # (capped) events whose traces live on in the per-item indexes
        self._user_events.pop(user_id, None)
        self._event_ids = {k: v for k, v in self._event_ids.items() if v[1] != user_id}
        for d in (self._content_events, self._inbound):
            for k in list(d):
                if any(x.user_id == user_id for x in d[k]):
                    d[k] = [x for x in d[k] if x.user_id != user_id]
        for users in self._content_users.values():
            users.pop(user_id, None)
        self._inbound.pop(user_id, None)
        for rid in self._served_by_user.pop(user_id, []):
            self._served.pop(rid, None)
        self._served_order = [(t, r) for t, r in self._served_order if r in self._served]
        self._feedback.pop(user_id, None)
        self._users.pop(user_id, None)

    # ── content ────────────────────────────────────────────────────────────
    async def upsert_content(self, item):
        old = self._content.get(item.content_id)
        if old is not None and item.version and old.version >= item.version:
            return False
        if old is not None:
            self._unindex(old)
        self._content[item.content_id] = copy.deepcopy(item)
        self._index(item)
        if old is not None:
            i = bisect.bisect_left(self._by_published, (old.published_at, old.content_id))
            if i < len(self._by_published) and self._by_published[i] == (old.published_at, old.content_id):
                del self._by_published[i]
        bisect.insort(self._by_published, (item.published_at, item.content_id))
        return True

    def _index(self, item: ContentRecord) -> None:
        self._by_creator[item.creator_id].add(item.content_id)
        for t in item.topics:
            self._by_topic[t.topic_id].add(item.content_id)
        if item.community_id:
            self._by_community[item.community_id].add(item.content_id)

    def _unindex(self, item: ContentRecord) -> None:
        self._by_creator[item.creator_id].discard(item.content_id)
        for t in item.topics:
            self._by_topic[t.topic_id].discard(item.content_id)
        if item.community_id:
            self._by_community[item.community_id].discard(item.content_id)

    async def get_content(self, ids):
        return {i: self._content[i] for i in ids if i in self._content}

    async def set_content_status(self, content_id, status):
        item = self._content.get(content_id)
        if item is None:
            return False
        item.status = status
        item.updated_at = now()
        return True

    def _active(self, ids: Iterable[str]) -> list[ContentRecord]:
        return [self._content[i] for i in ids if i in self._content and self._content[i].status == ACTIVE]

    async def recent_content(self, since, k):
        out = []
        lo = bisect.bisect_left(self._by_published, (since, ""))
        for i in range(len(self._by_published) - 1, lo - 1, -1):     # newest first, no full scan
            c = self._content.get(self._by_published[i][1])
            if c is not None and c.status == ACTIVE:
                out.append(c)
                if len(out) >= k:
                    break
        return out

    async def content_by_creators(self, creator_ids, since, k):
        items = [c for cr in creator_ids for c in self._active(self._by_creator.get(cr, ())) if c.published_at >= since]
        items.sort(key=lambda c: -c.published_at)
        return items[:k]

    async def content_by_topics(self, topic_ids, k):
        seen: set[str] = set()
        items: list[ContentRecord] = []
        for t in topic_ids:
            for c in self._active(self._by_topic.get(t, ())):
                if c.content_id not in seen:
                    seen.add(c.content_id)
                    items.append(c)
        items.sort(key=lambda c: -c.published_at)
        return items[:k]

    async def content_by_community(self, community_id, k):
        items = self._active(self._by_community.get(community_id, ()))
        items.sort(key=lambda c: -c.published_at)
        return items[:k]

    async def iter_content(self):
        return [c for c in self._content.values() if c.status == ACTIVE]

    # ── users ──────────────────────────────────────────────────────────────
    async def get_user(self, user_id):
        u = self._users.get(user_id)
        return copy.deepcopy(u) if u is not None else None      # callers may modify their copy

    async def get_users(self, ids):
        # read-only fan-out reads (candidates): not copied, for speed
        return {i: self._users[i] for i in ids if i in self._users}

    async def put_user(self, user, expected_version=0):
        old = self._users.get(user.user_id)
        cur = old.version if old else 0
        if expected_version and expected_version != cur:
            raise VersionConflict(f"user {user.user_id}: version {cur}, expected {expected_version}")
        stored = copy.deepcopy(user)
        stored.version = cur + 1
        stored.updated_at = now()
        if not stored.created_at:
            stored.created_at = stored.updated_at
        self._users[user.user_id] = stored
        return copy.deepcopy(stored)

    async def iter_users(self):
        return list(self._users.values())

    # ── graph ──────────────────────────────────────────────────────────────
    async def upsert_edges(self, edges):
        n = 0
        for e in edges:
            self._out[e.from_user_id][e.type][e.to_user_id] = e
            self._in[e.to_user_id][e.type][e.from_user_id] = e
            n += 1
        return n

    async def remove_edges(self, edges):
        n = 0
        for e in edges:
            if self._out[e.from_user_id][e.type].pop(e.to_user_id, None) is not None:
                n += 1
            self._in[e.to_user_id][e.type].pop(e.from_user_id, None)
        return n

    async def out_edges(self, user_id, types):
        d = self._out.get(user_id)
        return [e for t in types for e in (d.get(t, {}).values() if d else ())]

    async def in_edges(self, user_id, types):
        d = self._in.get(user_id)
        return [e for t in types for e in (d.get(t, {}).values() if d else ())]

    async def has_edge(self, from_id, to_id, type_):
        d = self._out.get(from_id)
        return bool(d) and to_id in d.get(type_, {})

    # ── served / feedback ──────────────────────────────────────────────────
    async def log_served(self, rec):
        old = self._served.get(rec.recommendation_id)
        if old is not None:
            if old.user_id != rec.user_id:
                raise ValueError("recommendation_id belongs to another user")
            have = {(i.target_type, i.target_id) for i in old.items}
            old.items.extend(i for i in rec.items if (i.target_type, i.target_id) not in have)
            return
        self._served[rec.recommendation_id] = rec
        self._served_by_user[rec.user_id].append(rec.recommendation_id)
        self._served_order.append((rec.served_at, rec.recommendation_id))
        cutoff = now() - 30 * 86400
        if self._served_order and self._served_order[0][0] < cutoff and len(self._served_order) % 1000 == 0:
            keep = [(t, r) for t, r in self._served_order if t >= cutoff]
            gone = {r for t, r in self._served_order if t < cutoff}
            self._served_order = keep
            for r in gone:
                old = self._served.pop(r, None)
                if old:
                    lst = self._served_by_user.get(old.user_id, [])
                    if r in lst:
                        lst.remove(r)

    async def get_served(self, recommendation_id):
        return self._served.get(recommendation_id)

    async def update_served_item(self, recommendation_id, target_type, target_id, label=None, impressed=None):
        rec = self._served.get(recommendation_id)
        if rec is None:
            return False
        for it in rec.items:
            if it.target_type == target_type and it.target_id == target_id:
                if label is not None:
                    # a positive outcome wins over a negative one, whichever came first
                    it.label = label if it.label is None else max(it.label, label)
                if impressed:
                    it.impressed = True
                return True
        return False

    async def served_for_user(self, user_id, since, until=None, surface=0):
        out = []
        for rid in reversed(self._served_by_user.get(user_id, [])):
            r = self._served.get(rid)
            if r is None or r.served_at < since or (until is not None and r.served_at >= until):
                continue
            if surface and r.surface != surface:
                continue
            out.append(r)
        return out

    async def served_since(self, since):
        i = bisect.bisect_left(self._served_order, (since, ""))
        return [self._served[r] for _, r in self._served_order[i:] if r in self._served]

    async def add_feedback(self, fb):
        self._feedback[fb.user_id].append(fb)

    async def feedback_for_user(self, user_id, since=0.0):
        return [f for f in self._feedback.get(user_id, []) if f.given_at >= since]
