"""Client of oowlet-feature-service (feature_service/feature.proto, FeatureService).

Reads:  BatchGetFeatures for content: embeddings (semantic, visual, audio),
        topics, entities, sentiment, intent, category, quality, credibility.
Writes: WriteFeatures for users: the engine's user embedding and topic /
        creator affinities, so other modules (ads, feeds, ML) share them.

Feature ids come from RUC_FEATURE_SERVICE__CONTENT_FEATURES /
USER_FEATURES_OUT (role -> feature id). Enrichment is on the request path,
so a slow or failing feature service degrades results (features missing)
instead of failing the request; failures are counted and logged.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Any

import grpc
import numpy as np

from oowlet.gen.feature_service.featurepb import feature_pb2 as fpb
from oowlet.gen.feature_service.featurepb import feature_pb2_grpc as fgrpc
from oowlet.gen.feature_service.fscommonpb import fs_common_pb2 as fcpb

from ..config import FeatureServiceSettings

log = logging.getLogger("ruc.feature_service")
MAX_BATCH = 500


def value_of(fv: fcpb.FeatureValue) -> Any:
    kind = fv.WhichOneof("value")
    if kind == "vector_value":
        return np.asarray(fv.vector_value.values, dtype=np.float32), fv.vector_value.model_version
    if kind == "list_value":
        return list(fv.list_value.values)
    if kind in ("float_value", "int_value", "bool_value", "string_value"):
        return getattr(fv, kind)
    return None


class FeatureServiceClient:
    def __init__(self, s: FeatureServiceSettings, source: str = "oowlet-recommend-uc") -> None:
        self.s = s
        self.source = source
        token = Path(s.token_file).read_text(encoding="utf-8").strip() if s.token_file else ""
        self._md = (("authorization", f"Bearer {token}"),) if token else ()
        if s.ca_file:
            creds = grpc.ssl_channel_credentials(root_certificates=Path(s.ca_file).read_bytes())
            self._ch = grpc.aio.secure_channel(s.address, creds)
        else:
            self._ch = grpc.aio.insecure_channel(s.address)
        self._stub = fgrpc.FeatureServiceStub(self._ch)
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._role_of = {fid: role for role, fid in s.content_features.items()}
        self._last_write: dict[str, float] = {}
        self.errors = 0
        self._last_error_log = 0.0

    async def close(self) -> None:
        await self._ch.close()

    def _caller(self) -> fcpb.CallerContext:
        # identity travels in the authorization header, never in the message
        return fcpb.CallerContext(caller_service=self.source, request_id=str(uuid.uuid4()), is_internal=True)

    def _fail(self, what: str, exc: BaseException) -> None:
        self.errors += 1
        t = time.monotonic()
        if t - self._last_error_log > 30:
            self._last_error_log = t
            detail = exc.code().name if isinstance(exc, grpc.aio.AioRpcError) else type(exc).__name__
            log.warning("feature service %s failed (%s); continuing without it (errors so far: %d)",
                        what, detail, self.errors)

    async def content_features(self, content_ids: list[str]) -> dict[str, dict[str, Any]]:
        """content_id -> {role: value}; cached for cache_ttl_seconds."""
        t = time.monotonic()
        out: dict[str, dict[str, Any]] = {}
        need = []
        for cid in dict.fromkeys(content_ids):
            hit = self._cache.get(cid)
            if hit and t - hit[0] < self.s.cache_ttl_seconds:
                out[cid] = hit[1]
            else:
                need.append(cid)
        if not need:
            return out
        feature_ids = list(self.s.content_features.values())
        calls = []
        for i in range(0, len(need), MAX_BATCH):
            chunk = need[i:i + MAX_BATCH]
            req = fpb.BatchFeaturesRequest(
                entities=[fpb.EntityRef(entity_id=c, entity_type=self.s.content_entity_type) for c in chunk],
                feature_ids=feature_ids, caller=self._caller())
            calls.append(self._stub.BatchGetFeatures(req, metadata=self._md, timeout=self.s.timeout_seconds))
        results = await asyncio.gather(*calls, return_exceptions=True)
        for res in results:
            if isinstance(res, BaseException):
                self._fail("BatchGetFeatures", res)
                continue
            for r in res.results:
                if not r.success:
                    continue
                vals = {}
                for fv in r.features:
                    role = self._role_of.get(fv.feature_id)
                    if role:
                        v = value_of(fv)
                        if v is not None:
                            vals[role] = v
                out[r.entity_id] = vals
                self._cache[r.entity_id] = (t, vals)
        if len(self._cache) > 200_000:
            cutoff = t - self.s.cache_ttl_seconds
            self._cache = {k: v for k, v in self._cache.items() if v[0] >= cutoff}
        return out

    def forget(self, user_id: str) -> None:
        self._last_write.pop(user_id, None)

    async def write_user_features(self, user_id: str, embedding: np.ndarray | None, model_id: str,
                                  topic_affinity: dict[str, float], creator_affinity: dict[str, float],
                                  force: bool = False) -> bool:
        """Publish the engine's view of a user; at most once per interval per user."""
        if not self.s.write_back:
            return False
        t = time.monotonic()
        if not force and t - self._last_write.get(user_id, -1e9) < self.s.write_back_min_interval_seconds:
            return False
        self._last_write[user_id] = t
        if len(self._last_write) > 200_000:
            cutoff = t - self.s.write_back_min_interval_seconds
            self._last_write = {k: v for k, v in self._last_write.items() if v >= cutoff}
        ids = self.s.user_features_out
        now_ms = int(time.time() * 1000)
        feats = []
        if embedding is not None and "embedding" in ids:
            feats.append(fcpb.FeatureValue(
                feature_id=ids["embedding"], data_type="vector", computed_at_ms=now_ms,
                vector_value=fcpb.FloatVector(values=[float(x) for x in embedding], dimension=len(embedding),
                                              model_version=model_id)))
        for role, aff in (("topic_affinity", topic_affinity), ("creator_affinity", creator_affinity)):
            if role in ids and aff:
                top = sorted(aff.items(), key=lambda kv: -kv[1])[:50]
                feats.append(fcpb.FeatureValue(
                    feature_id=ids[role], data_type="string_list", computed_at_ms=now_ms,
                    list_value=fcpb.StringList(values=[f"{k}:{v:.4f}" for k, v in top])))
        if not feats:
            return False
        req = fpb.WriteFeaturesRequest(entity_id=user_id, entity_type=self.s.user_entity_type, features=feats,
                                       caller=self._caller(), pipeline_id="recommend-uc")
        try:
            await self._stub.WriteFeatures(req, metadata=self._md, timeout=max(self.s.timeout_seconds, 2.0))
            return True
        except Exception as exc:  # noqa: BLE001 - write-back is best effort
            self._fail("WriteFeatures", exc)
            return False
