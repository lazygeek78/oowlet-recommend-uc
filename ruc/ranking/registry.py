"""Which ranker serves which user: the configured model per engine, plus an
optional challenger for a stable share of users (A/B by user-id hash)."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from ..config import RankingSettings
from .models import LogisticRanker, Ranker, WeightedRanker

log = logging.getLogger("ruc.ranking")


def bucket(user_id: str, experiment_id: str) -> int:
    h = hashlib.sha256(f"{experiment_id}:{user_id}".encode()).digest()
    return int.from_bytes(h[:4], "big") % 100


class ModelRegistry:
    def __init__(self, s: RankingSettings) -> None:
        self.s = s
        self.weighted = {e: WeightedRanker.from_file(e, s.weights_file) for e in ("content", "people")}
        self.logistic: dict[str, LogisticRanker] = {}
        self.reload()

    def path(self, engine: str) -> Path:
        return Path(self.s.model_dir) / f"{engine}-logistic.json"

    def reload(self) -> None:
        for e in ("content", "people"):
            p = self.path(e)
            if p.is_file():
                try:
                    self.logistic[e] = LogisticRanker.load(p)
                    log.info("loaded %s ranker %s v%s", e, p, self.logistic[e].version)
                except (ValueError, KeyError, OSError) as exc:
                    log.error("cannot load %s: %s; using the weighted ranker", p, exc)

    def _get(self, engine: str, name: str) -> Ranker:
        if name == "logistic":
            m = self.logistic.get(engine)
            if m is not None:
                return m
        return self.weighted[engine]

    def choose(self, engine: str, user_id: str) -> tuple[Ranker, str]:
        primary = self.s.content_model if engine == "content" else self.s.people_model
        if self.s.challenger_model and bucket(user_id, self.s.experiment_id) < self.s.challenger_percent:
            m = self._get(engine, self.s.challenger_model)
            return m, "challenger" if m.model_id == self.s.challenger_model else "challenger-fallback"
        m = self._get(engine, primary)
        return m, "control" if m.model_id == primary else "control-fallback"
