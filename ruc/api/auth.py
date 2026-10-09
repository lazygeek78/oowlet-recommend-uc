"""Who is calling: from the bearer token only, never from a request field.

RUC_AUTH__TOKENS_FILE (JSON) lists accepted tokens by SHA-256, each with its
principal:
    {"tokens": [
      {"sha256": "<hex>", "kind": "service", "principal": "svc:gateway",
       "scopes": ["recommend:on_behalf", "recommend:engagement:write"]},
      {"sha256": "<hex>", "kind": "user", "user_id": "u-123"}
    ]}
Member tokens normally come from the security service; a verifier for those
plugs in as another Authenticator.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import grpc

SCOPES = frozenset({
    "recommend:on_behalf", "recommend:engagement:write", "recommend:catalog:write", "recommend:catalog:read",
    "recommend:graph:write", "recommend:features:write", "recommend:profile:write", "recommend:history:read",
    "recommend:admin",
})


@dataclass(frozen=True)
class Principal:
    kind: str                      # "user" | "service"
    principal_id: str
    user_id: str = ""
    scopes: frozenset[str] = field(default_factory=frozenset)

    def has(self, scope: str) -> bool:
        return self.kind == "service" and scope in self.scopes


class AuthError(Exception):
    def __init__(self, code: grpc.StatusCode, msg: str) -> None:
        super().__init__(msg)
        self.code = code


class TokenAuthenticator:
    def __init__(self, path: str) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self._by_hash: dict[str, Principal] = {}
        for i, t in enumerate(data.get("tokens", [])):
            h = str(t.get("sha256", "")).lower()
            if len(h) != 64:
                raise ValueError(f"{path}: token {i}: sha256 must be 64 hex characters")
            kind = t.get("kind")
            if kind == "user":
                uid = str(t.get("user_id", ""))
                if not uid:
                    raise ValueError(f"{path}: token {i}: user token needs user_id")
                self._by_hash[h] = Principal("user", f"user:{uid}", user_id=uid)
            elif kind == "service":
                scopes = frozenset(t.get("scopes", []))
                unknown = scopes - SCOPES
                if unknown:
                    raise ValueError(f"{path}: token {i}: unknown scopes {sorted(unknown)}")
                self._by_hash[h] = Principal("service", str(t.get("principal") or f"svc:{i}"), scopes=scopes)
            else:
                raise ValueError(f"{path}: token {i}: kind must be user or service")
        if not self._by_hash:
            raise ValueError(f"{path}: no tokens")

    def authenticate(self, context: grpc.aio.ServicerContext) -> Principal:
        token = ""
        for k, v in context.invocation_metadata() or ():
            if k == "authorization" and isinstance(v, str) and v.startswith("Bearer "):
                token = v[7:].strip()
                break
        if not token:
            raise AuthError(grpc.StatusCode.UNAUTHENTICATED, "missing bearer token")
        # looked up by its hash: lookup timing reveals nothing about the token
        p = self._by_hash.get(hashlib.sha256(token.encode()).hexdigest())
        if p is None:
            raise AuthError(grpc.StatusCode.UNAUTHENTICATED, "invalid token")
        return p


def acting_user(p: Principal, user_id: str, scope: str = "recommend:on_behalf") -> str:
    """The user a request acts for: a member acts for themself only; a service
    needs `scope` and must name the user."""
    if p.kind == "user":
        if user_id and user_id != p.user_id:
            raise AuthError(grpc.StatusCode.PERMISSION_DENIED, "user_id must be the authenticated user")
        return p.user_id
    if not p.has(scope):
        raise AuthError(grpc.StatusCode.PERMISSION_DENIED, f"service lacks scope {scope}")
    if not user_id:
        raise AuthError(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
    return user_id


def require_scope(p: Principal, scope: str) -> None:
    if not p.has(scope):
        raise AuthError(grpc.StatusCode.PERMISSION_DENIED, f"requires service scope {scope}")
