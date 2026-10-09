"""Matrix factorization for candidate generation: implicit-feedback ALS
(Hu, Koren, Volinsky 2008). Confidence c = 1 + alpha * signal strength.

Trained offline from the engagement history (`oowlet-recommend-uc train`, or
on RUC_TRAINING__INTERVAL_MINUTES); serves a user's top items by dot product.
Users who turned off personalization or history use are left out of the
training data entirely. Dense numpy: fits up to a few hundred thousand
users x items on one machine; beyond that, train elsewhere and load factors.
"""

from __future__ import annotations

import numpy as np


class ImplicitALS:
    def __init__(self, factors: int = 32, reg: float = 0.1, alpha: float = 10.0, iterations: int = 10,
                 seed: int = 7) -> None:
        self.factors, self.reg, self.alpha, self.iterations = factors, reg, alpha, iterations
        self.rng = np.random.default_rng(seed)
        self.user_ids: list[str] = []
        self.item_ids: list[str] = []
        self.U = np.zeros((0, factors), np.float32)
        self.V = np.zeros((0, factors), np.float32)
        self._upos: dict[str, int] = {}
        self._seen: list[set[int]] = []

    def fit(self, triples: list[tuple[str, str, float]]) -> "ImplicitALS":
        """triples: (user_id, item_id, strength > 0)."""
        users = sorted({u for u, _, _ in triples})
        items = sorted({i for _, i, _ in triples})
        if not users or not items:
            return self
        up = {u: k for k, u in enumerate(users)}
        ip = {i: k for k, i in enumerate(items)}
        n_u, n_i, f = len(users), len(items), self.factors
        by_user: list[list[tuple[int, float]]] = [[] for _ in range(n_u)]
        by_item: list[list[tuple[int, float]]] = [[] for _ in range(n_i)]
        for u, i, s in triples:
            if s > 0:
                by_user[up[u]].append((ip[i], s))
                by_item[ip[i]].append((up[u], s))
        U = self.rng.normal(0, 0.01, (n_u, f))
        V = self.rng.normal(0, 0.01, (n_i, f))
        eye = self.reg * np.eye(f)

        def solve(fixed: np.ndarray, rows: list[list[tuple[int, float]]], out: np.ndarray) -> None:
            gram = fixed.T @ fixed
            for r, obs in enumerate(rows):
                if not obs:
                    out[r] = 0
                    continue
                idx = np.array([o[0] for o in obs])
                conf = 1.0 + self.alpha * np.array([o[1] for o in obs])
                Y = fixed[idx]
                A = gram + (Y.T * (conf - 1.0)) @ Y + eye
                b = (Y.T * conf).sum(axis=1)
                out[r] = np.linalg.solve(A, b)

        for _ in range(self.iterations):
            solve(V, by_user, U)
            solve(U, by_item, V)
        self.user_ids, self.item_ids = users, items
        self.U, self.V = U.astype(np.float32), V.astype(np.float32)
        self._upos = up
        self._seen = [{i for i, _ in obs} for obs in by_user]
        return self

    def forget(self, user_id: str) -> None:
        """Erasure: the user's factors are no longer served (item factors are aggregates)."""
        r = self._upos.pop(user_id, None)
        if r is not None:
            self.U[r] = 0
            self._seen[r] = set()

    def recommend(self, user_id: str, k: int) -> list[tuple[str, float]]:
        r = self._upos.get(user_id)
        if r is None or k <= 0:
            return []
        scores = self.V @ self.U[r]
        for i in self._seen[r]:
            scores[i] = -np.inf
        n = min(k, len(scores))
        top = np.argpartition(-scores, n - 1)[:n]
        top = top[np.argsort(-scores[top])]
        return [(self.item_ids[i], float(scores[i])) for i in top if np.isfinite(scores[i]) and scores[i] > 0]
