"""Nearest-neighbour search over unit vectors (cosine similarity).

ExactIndex scans a contiguous matrix with one matrix-vector product: exact,
and fast enough into the low millions of vectors at dimension 256 on one
core (~10 ms per million). Rows live in a buffer that doubles when full and
removals swap the last row in, so updates never copy the whole matrix.
Above a few million vectors, an approximate index (HNSW via hnswlib or
FAISS) implements the same methods.
"""

from __future__ import annotations

import numpy as np


class ExactIndex:
    def __init__(self, dim: int, capacity: int = 1024) -> None:
        self.dim = dim
        self._ids: list[str] = []
        self._pos: dict[str, int] = {}
        self._mat = np.zeros((capacity, dim), dtype=np.float32)

    def __len__(self) -> int:
        return len(self._ids)

    def upsert(self, key: str, vec: np.ndarray) -> None:
        if vec.shape != (self.dim,):
            raise ValueError(f"vector of dimension {vec.shape}, index has {self.dim}")
        i = self._pos.get(key)
        if i is None:
            i = len(self._ids)
            if i >= len(self._mat):
                grown = np.zeros((max(2 * len(self._mat), 1024), self.dim), dtype=np.float32)
                grown[:i] = self._mat[:i]
                self._mat = grown
            self._ids.append(key)
            self._pos[key] = i
        self._mat[i] = vec

    def remove(self, key: str) -> None:
        i = self._pos.pop(key, None)
        if i is None:
            return
        last = len(self._ids) - 1
        if i != last:
            moved = self._ids[last]
            self._ids[i] = moved
            self._pos[moved] = i
            self._mat[i] = self._mat[last]
        self._ids.pop()
        self._mat[last] = 0

    def get(self, key: str) -> np.ndarray | None:
        i = self._pos.get(key)
        return None if i is None else self._mat[i].copy()

    def search(self, query: np.ndarray, k: int, exclude: set[str] | frozenset[str] = frozenset()) -> list[tuple[str, float]]:
        n_rows = len(self._ids)
        if not n_rows or k <= 0 or not np.any(query):
            return []
        sims = self._mat[:n_rows] @ query.astype(np.float32, copy=False)
        n = min(n_rows, k + len(exclude))
        top = np.argpartition(-sims, n - 1)[:n] if n < n_rows else np.arange(n_rows)
        top = top[np.argsort(-sims[top])]
        out = []
        for i in top:
            key = self._ids[i]
            if key in exclude:
                continue
            out.append((key, float(sims[i])))
            if len(out) >= k:
                break
        return out
