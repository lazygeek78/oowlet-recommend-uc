"""Rankers. Both engines score candidates from named components (0..1 each):

Content:  Recommendation Score = User Interest + Content Relevance
          + Behavioral Affinity + Context Relevance + Quality + Credibility
          + Freshness + Social Signal + Trend Signal + Creator Affinity
          - Repetition - Negative Feedback
People:   Mutual Connections + Shared Interests + Community Overlap
          + Interaction + Context Relevance + Profile Quality + Activity
          + Reciprocity

WeightedRanker applies configurable weights (start here). LogisticRanker is
the first learned model: trained on served items labelled by what users did
(ruc/feedback/training.py); it reads the same components, so it can replace
the weighted ranker per engine, or run as a challenger for a share of users.
Gradient-boosted trees or deep rankers (Wide & Deep, DeepFM, DLRM) plug in
the same way: implement score() over these components (or a richer vector).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb

CONTENT_FEATURES = ("user_interest", "content_relevance", "behavioral_affinity", "context_relevance", "quality",
                    "credibility", "freshness", "social_signal", "trend_signal", "creator_affinity", "repetition",
                    "negative_feedback")
PEOPLE_FEATURES = ("mutual_connections", "shared_interests", "community_overlap", "interaction",
                   "context_relevance", "profile_quality", "activity", "reciprocity")
# Components that describe the user's own history: zero when personalization is off.
PERSONAL = frozenset({"user_interest", "content_relevance", "behavioral_affinity", "context_relevance",
                      "social_signal", "creator_affinity", "negative_feedback"})

DEFAULT_CONTENT_WEIGHTS = {
    "user_interest": 1.0, "content_relevance": 0.8, "behavioral_affinity": 1.0, "context_relevance": 0.6,
    "quality": 0.6, "credibility": 0.5, "freshness": 0.5, "social_signal": 0.5, "trend_signal": 0.4,
    "creator_affinity": 0.7, "repetition": -0.8, "negative_feedback": -1.5,
}
SURFACE_CONTENT_OVERRIDES: dict[int, dict[str, float]] = {
    cpb.SURFACE_REELS: {"freshness": 0.9, "trend_signal": 0.7},
    cpb.SURFACE_GLIMPSE: {"freshness": 0.9, "trend_signal": 0.7},
    cpb.SURFACE_INSTANTS: {"freshness": 1.2, "trend_signal": 0.6},
    cpb.SURFACE_EXPLORE: {"user_interest": 0.6, "content_relevance": 0.5, "trend_signal": 0.8, "quality": 0.8},
    cpb.SURFACE_CONTENT_DETAIL: {"context_relevance": 1.5},
    cpb.SURFACE_DIGEST: {"quality": 1.0, "freshness": 0.7},
}
DEFAULT_PEOPLE_WEIGHTS = {
    "mutual_connections": 1.2, "shared_interests": 1.0, "community_overlap": 0.7, "interaction": 0.8,
    "context_relevance": 0.6, "profile_quality": 0.5, "activity": 0.4, "reciprocity": 0.6,
}


@dataclass
class Scored:
    score: float
    contributions: dict[str, float]


class Ranker:
    model_id: str = ""
    version: str = ""
    features: tuple[str, ...] = ()

    def score(self, x: dict[str, float], surface: int = 0) -> Scored:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class WeightedRanker(Ranker):
    engine: str = "content"
    weights: dict[str, float] = field(default_factory=dict)
    surface_overrides: dict[int, dict[str, float]] = field(default_factory=dict)
    model_id: str = "weighted"
    version: str = "1"

    def __post_init__(self) -> None:
        if self.engine == "content":
            self.features = CONTENT_FEATURES
            self.weights = {**DEFAULT_CONTENT_WEIGHTS, **self.weights}
            self.surface_overrides = {**SURFACE_CONTENT_OVERRIDES, **self.surface_overrides}
        else:
            self.features = PEOPLE_FEATURES
            self.weights = {**DEFAULT_PEOPLE_WEIGHTS, **self.weights}

    def score(self, x: dict[str, float], surface: int = 0) -> Scored:
        w = {**self.weights, **self.surface_overrides.get(surface, {})}
        contrib = {k: w.get(k, 0.0) * x.get(k, 0.0) for k in self.features}
        return Scored(sum(contrib.values()), contrib)

    @classmethod
    def from_file(cls, engine: str, path: str) -> "WeightedRanker":
        """JSON: {"content": {"weights": {...}, "surfaces": {"SURFACE_REELS": {...}}}, "people": {...}}"""
        if not path:
            return cls(engine=engine)
        data = json.loads(Path(path).read_text(encoding="utf-8")).get(engine, {})
        overrides = {cpb.Surface.Value(k): v for k, v in data.get("surfaces", {}).items()}
        unknown = set(data.get("weights", {})) - set(CONTENT_FEATURES if engine == "content" else PEOPLE_FEATURES)
        if unknown:
            raise ValueError(f"{path}: unknown {engine} components {sorted(unknown)}")
        return cls(engine=engine, weights=data.get("weights", {}), surface_overrides=overrides,
                   version=str(data.get("version", "1")))


@dataclass
class LogisticRanker(Ranker):
    engine: str = "content"
    coef: dict[str, float] = field(default_factory=dict)
    intercept: float = 0.0
    model_id: str = "logistic"
    version: str = "0"
    trained_at: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.features = CONTENT_FEATURES if self.engine == "content" else PEOPLE_FEATURES

    def score(self, x: dict[str, float], surface: int = 0) -> Scored:
        contrib = {k: self.coef.get(k, 0.0) * x.get(k, 0.0) for k in self.features}
        z = self.intercept + sum(contrib.values())
        return Scored(1.0 / (1.0 + math.exp(-max(min(z, 40.0), -40.0))), contrib)

    def to_json(self) -> str:
        return json.dumps({"engine": self.engine, "model_id": self.model_id, "version": self.version,
                           "coef": self.coef, "intercept": self.intercept, "trained_at": self.trained_at,
                           "metrics": self.metrics}, indent=2)

    @classmethod
    def load(cls, path: Path) -> "LogisticRanker":
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(engine=d["engine"], coef=d["coef"], intercept=d["intercept"], version=d["version"],
                   trained_at=d.get("trained_at", 0.0), metrics=d.get("metrics", {}))

    @classmethod
    def fit(cls, engine: str, X: np.ndarray, y: np.ndarray, l2: float = 1.0, iters: int = 50) -> "LogisticRanker":
        """L2-regularised logistic regression by Newton's method (IRLS)."""
        names = CONTENT_FEATURES if engine == "content" else PEOPLE_FEATURES
        n, d = X.shape
        Xb = np.hstack([np.ones((n, 1)), X])
        w = np.zeros(d + 1)
        reg = np.full(d + 1, l2)
        reg[0] = 0.0                                   # no penalty on the intercept
        for _ in range(iters):
            p = 1.0 / (1.0 + np.exp(-np.clip(Xb @ w, -40, 40)))
            g = Xb.T @ (p - y) + reg * w
            h = (Xb * (p * (1 - p))[:, None]).T @ Xb + np.diag(reg) + 1e-9 * np.eye(d + 1)
            step = np.linalg.solve(h, g)
            w -= step
            if np.max(np.abs(step)) < 1e-6:
                break
        return cls(engine=engine, coef={k: float(v) for k, v in zip(names, w[1:])}, intercept=float(w[0]))


# ── evaluation metrics ─────────────────────────────────────────────────────

def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    pos, neg = labels == 1, labels == 0
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores))
    s = scores[order]
    i = 0
    while i < len(s):                                  # average ranks over ties
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def logloss(probs: np.ndarray, labels: np.ndarray) -> float:
    p = np.clip(probs, 1e-7, 1 - 1e-7)
    return float(-np.mean(labels * np.log(p) + (1 - labels) * np.log(1 - p)))


def ndcg_at_k(groups: list[tuple[np.ndarray, np.ndarray]], k: int = 10) -> float:
    """Mean NDCG@k over serves: each group is (scores, labels) of one response."""
    vals = []
    for scores, labels in groups:
        if labels.sum() == 0:
            continue
        order = np.argsort(-scores)[:k]
        gains = labels[order]
        dcg = float(np.sum(gains / np.log2(np.arange(2, len(gains) + 2))))
        ideal = np.sort(labels)[::-1][:k]
        idcg = float(np.sum(ideal / np.log2(np.arange(2, len(ideal) + 2))))
        vals.append(dcg / idcg if idcg > 0 else 0.0)
    return float(np.mean(vals)) if vals else float("nan")
