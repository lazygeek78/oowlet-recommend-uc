"""Diversity and exploration: the last stage before results are returned.

Greedy re-ranking over the scored list:
  - maximal marginal relevance: a candidate very similar to one already
    picked loses some of its score (no ten near-identical items in a row)
  - caps per creator and per primary topic (content), per community (people)
  - exploration: a share of the slots go to good candidates outside the
    user's known interests, so the feedback loop can learn new interests
    instead of narrowing them. Picked reproducibly per serve.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb


@dataclass
class Ranked:
    key: str
    score: float
    group_a: str = ""              # content: creator         people: (unused)
    group_b: str = ""              # content: primary topic   people: shared community
    vector: np.ndarray | None = None
    exploratory: bool = False      # eligible for an exploration slot
    explored: bool = False         # placed by exploration
    features: dict[str, float] = field(default_factory=dict)
    contributions: dict[str, float] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)


@dataclass
class DiversityOpts:
    max_per_a: int
    max_per_b: int
    exploration_ratio: float
    mmr_lambda: float = 0.25


def default_opts(surface: int, limit: int, max_per_creator: int = 0, max_per_topic: int = 0,
                 exploration_ratio: float = -1.0, people: bool = False) -> DiversityOpts:
    if people:
        return DiversityOpts(max_per_a=limit, max_per_b=max_per_topic or max(2, limit // 2),
                             exploration_ratio=0.0 if exploration_ratio < 0 else exploration_ratio)
    explore = 0.0 if surface in (cpb.SURFACE_CONTENT_DETAIL, cpb.SURFACE_SEARCH, cpb.SURFACE_PROFILE) else 0.1
    return DiversityOpts(
        max_per_a=max_per_creator or (limit if surface == cpb.SURFACE_PROFILE
                                      else max(3, limit // 2) if surface == cpb.SURFACE_CONTENT_DETAIL else 2),
        max_per_b=max_per_topic or max(2, (limit + 2) // 3),
        exploration_ratio=explore if exploration_ratio < 0 else min(exploration_ratio, 0.5))


def rerank(items: list[Ranked], limit: int, opts: DiversityOpts, seed: str) -> list[Ranked]:
    if not items or limit <= 0:
        return []
    items = sorted(items, key=lambda r: -r.score)
    hi = items[0].score
    lo = min(r.score for r in items)
    span = (hi - lo) or 1.0
    norm = {r.key: (r.score - lo) / span for r in items}

    n_explore = int(round(limit * opts.exploration_ratio))
    explore_pool = [r for r in items[: limit * 5] if r.exploratory]
    rng = random.Random(seed)
    explore = rng.sample(explore_pool, min(n_explore, len(explore_pool))) if n_explore else []
    explore_keys = {r.key for r in explore}

    picked: list[Ranked] = []
    count_a: dict[str, int] = {}
    count_b: dict[str, int] = {}
    vecs: list[np.ndarray] = []
    remaining = [r for r in items if r.key not in explore_keys]
    n_main = limit - len(explore)
    while remaining and len(picked) < n_main:
        best, best_val = None, -1e18
        for r in remaining[:300]:
            if r.group_a and count_a.get(r.group_a, 0) >= opts.max_per_a:
                continue
            if r.group_b and count_b.get(r.group_b, 0) >= opts.max_per_b:
                continue
            sim = max((float(np.dot(r.vector, v)) for v in vecs), default=0.0) if r.vector is not None else 0.0
            val = norm[r.key] - opts.mmr_lambda * max(sim, 0.0)
            if val > best_val:
                best, best_val = r, val
        if best is None:
            break
        remaining.remove(best)
        picked.append(best)
        if best.group_a:
            count_a[best.group_a] = count_a.get(best.group_a, 0) + 1
        if best.group_b:
            count_b[best.group_b] = count_b.get(best.group_b, 0) + 1
        if best.vector is not None:
            vecs.append(best.vector)
    # caps left slots empty: fill them in score order rather than return fewer
    if len(picked) < n_main:
        picked += remaining[: n_main - len(picked)]
    # interleave exploration slots evenly
    if explore:
        step = max(1, (len(picked) + len(explore)) // (len(explore) + 1))
        for i, r in enumerate(explore):
            r.explored = True
            picked.insert(min(len(picked), (i + 1) * step), r)
    return picked[:limit]
