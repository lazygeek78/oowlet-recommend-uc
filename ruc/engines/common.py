"""Pieces both engines share: paging, serve logging, explanations."""

from __future__ import annotations

import asyncio
import base64
import json
import time
import uuid
from dataclasses import dataclass

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb

from ..domain import ServedItem, ServedRecommendation, now
from ..policy.diversity import Ranked


class PageTokenError(ValueError):
    pass


@dataclass
class _Page:
    user_id: str
    expires: float
    ranked: list[Ranked]
    served: ServedRecommendation


class PageCache:
    """Ranked lists of recent serves, so later pages continue the same
    ranking. In-process: a token from another instance or older than the TTL
    is refused (the client starts a new feed)."""

    def __init__(self, ttl_seconds: float = 1800, max_entries: int = 50_000) -> None:
        self.ttl, self.max = ttl_seconds, max_entries
        self._d: dict[str, _Page] = {}

    def put(self, rec_id: str, user_id: str, ranked: list[Ranked], served: ServedRecommendation) -> None:
        t = time.monotonic()
        if len(self._d) >= self.max:
            self._d = {k: v for k, v in self._d.items() if v.expires > t}
            while len(self._d) >= self.max:
                self._d.pop(next(iter(self._d)))
        self._d[rec_id] = _Page(user_id, t + self.ttl, ranked, served)

    def drop_user(self, user_id: str) -> None:
        self._d = {k: v for k, v in self._d.items() if v.user_id != user_id}

    def get(self, rec_id: str, user_id: str) -> _Page:
        p = self._d.get(rec_id)
        if p is None or p.expires < time.monotonic():
            raise PageTokenError("page token expired; request the first page again")
        if p.user_id != user_id:
            raise PageTokenError("page token belongs to another user")
        return p


def encode_token(rec_id: str, offset: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"r": rec_id, "o": offset}).encode()).decode().rstrip("=")


def decode_token(token: str) -> tuple[str, int]:
    try:
        d = json.loads(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)))
        rec_id, off = str(d["r"]), int(d["o"])
    except (ValueError, KeyError, TypeError) as exc:
        raise PageTokenError("malformed page token") from exc
    if off < 0 or len(rec_id) > 64:
        raise PageTokenError("malformed page token")
    return rec_id, off


def new_rec_id() -> str:
    return uuid.uuid4().hex


def served_record(rec_id: str, user_id: str, surface: int, engine: str, target_type: int,
                  items: list[Ranked], model_id: str, model_version: str, variant: str, experiment_id: str,
                  personalized: bool, offset: int = 0) -> ServedRecommendation:
    return ServedRecommendation(
        recommendation_id=rec_id, user_id=user_id, surface=surface, engine=engine,
        items=[ServedItem(target_type=target_type, target_id=r.key, rank=offset + i, score=r.score,
                          features=dict(r.features), sources=list(r.sources)) for i, r in enumerate(items)],
        model_id=model_id, model_version=model_version, variant=variant, experiment_id=experiment_id,
        personalized=personalized, served_at=now())


def reason(code: int, contribution: float, detail: str = "", evidence: list[cpb.EntityRef] | None = None) -> cpb.Reason:
    return cpb.Reason(code=code, detail=detail, contribution=max(0.0, min(contribution, 1.0)), evidence=evidence or [])


def top_reasons(reasons: list[cpb.Reason], n: int = 3) -> cpb.Explanation:
    reasons = sorted(reasons, key=lambda r: -r.contribution)[:n]
    return cpb.Explanation(reasons=reasons)


def share(contrib: dict[str, float], keys: tuple[str, ...]) -> float:
    pos = sum(v for v in contrib.values() if v > 0)
    return sum(max(contrib.get(k, 0.0), 0.0) for k in keys) / pos if pos > 0 else 0.0


class Background:
    """Fire-and-forget tasks that must not be garbage-collected mid-flight."""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    def spawn(self, coro) -> None:
        t = asyncio.ensure_future(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    async def drain(self, timeout: float = 5.0) -> None:
        if self._tasks:
            await asyncio.wait(set(self._tasks), timeout=timeout)
