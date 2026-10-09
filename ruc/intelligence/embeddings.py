"""Embeddings: one vector space shared by content and users.

The engine uses a single embedding model (RUC_INTELLIGENCE__EMBEDDING_MODEL)
so user and content vectors are comparable:
  - "hashing-v1" (default): feature hashing of topics, hashtags, entities,
    category and creator. No model download, deterministic, good enough to
    start; similarity means "talks about the same things".
  - any sentence-transformers model (BGE, E5, ...), when that package is
    installed: content is embedded from the same descriptive text.
Content that arrives with a vector of the configured model (ContentItem.
embeddings or the feature service) uses it as-is. A user's vector is derived
from the vectors of what they engaged with (user_intelligence.py), so it is
always in the content space.
"""

from __future__ import annotations

import hashlib
import logging
import re

import numpy as np

from ..domain import ContentRecord

log = logging.getLogger("ruc.embeddings")
_TOKEN = re.compile(r"[a-z0-9_#:.-]+")


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


class Embedder:
    model_id: str
    dim: int

    def embed_texts(self, texts: list[str]) -> np.ndarray:  # pragma: no cover - interface
        raise NotImplementedError

    def describe(self, item: ContentRecord) -> str:
        """The text a content item is embedded from."""
        parts = []
        for t in item.topics:
            parts.extend([f"topic:{t.topic_id}"] * max(1, round(t.weight * 3)))
            if t.label:
                parts.append(t.label)
        parts += [h if h.startswith("#") else f"#{h}" for h in item.hashtags]
        parts += [f"entity:{e}" for e in item.entities]
        if item.category:
            parts.append(f"category:{item.category}")
        if item.intent:
            parts.append(f"intent:{item.intent}")
        parts.append(f"creator:{item.creator_id}")
        return " ".join(parts)

    def embed_content(self, item: ContentRecord) -> np.ndarray:
        v = item.embeddings.get(self.model_id)
        if v is not None and v.shape == (self.dim,):
            return v
        return self.embed_texts([self.describe(item)])[0]


class HashingEmbedder(Embedder):
    def __init__(self, dim: int = 256, model_id: str = "hashing-v1") -> None:
        self.dim = dim
        self.model_id = model_id

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in _TOKEN.findall(text.lower()):
            h = hashlib.blake2b(tok.encode(), digest_size=8).digest()
            idx = int.from_bytes(h[:4], "little") % self.dim
            sign = 1.0 if h[4] & 1 else -1.0
            v[idx] += sign
        return unit(v)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._vec(t) for t in texts]) if texts else np.zeros((0, self.dim), np.float32)


class SentenceTransformerEmbedder(Embedder):  # pragma: no cover - needs the optional package
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # optional dependency
        self._m = SentenceTransformer(model_name)
        self.model_id = model_name
        self.dim = int(self._m.get_sentence_embedding_dimension())

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self._m.encode(texts, normalize_embeddings=True), dtype=np.float32)


def make_embedder(model: str, dim: int) -> Embedder:
    if model.startswith("hashing"):
        return HashingEmbedder(dim=dim, model_id=model)
    try:
        return SentenceTransformerEmbedder(model)
    except ImportError as exc:
        raise RuntimeError(f"embedding model {model!r} needs the sentence-transformers package "
                           f"(pip install sentence-transformers), or use hashing-v1") from exc
