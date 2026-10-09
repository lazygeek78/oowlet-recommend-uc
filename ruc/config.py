"""Settings from RUC_* environment variables (see .env.example).

Nested settings use a double underscore: RUC_SERVER__PORT=50070.
Secrets are never values: settings ending in _FILE name a file to read.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, get_type_hints


class ConfigError(ValueError):
    pass


@dataclass
class ServerSettings:
    host: str = "0.0.0.0"
    port: int = 50070
    tls_enabled: bool = True
    tls_cert_file: str = ""
    tls_key_file: str = ""
    tls_client_ca_file: str = ""          # set: client certificates required (mTLS)
    max_message_bytes: int = 8 << 20
    shutdown_grace_seconds: float = 10.0


@dataclass
class AuthSettings:
    # JSON file of accepted tokens, stored as SHA-256 hashes, each with its
    # principal: {"tokens": [{"sha256": "...", "kind": "service", "principal": "svc:gateway",
    #   "scopes": ["recommend:on_behalf"]}, {"sha256": "...", "kind": "user", "user_id": "u1"}]}
    tokens_file: str = ""


@dataclass
class BrokerSettings:
    address: str = ""                     # empty: no event layer (API only)
    token_file: str = ""
    ca_file: str = ""
    cert_file: str = ""
    key_file: str = ""
    consumer_group: str = "recommend-uc"
    # Producers that publish the older eventlayer events (PostEngagementEvent,
    # BehaviorUpdatedEvent, Post*Event); mapped onto the engine's own types.
    legacy_topics: list[str] = field(default_factory=lambda: [
        "post.engagement", "post.created", "post.updated", "post.deleted", "behavior.updated"])
    publish_served: bool = True
    # legacy PostCreatedEvent has no visibility: posts are recommendable only
    # when this says every post is public
    legacy_posts_public: bool = False


@dataclass
class FeatureServiceSettings:
    address: str = ""                     # empty: no feature-service enrichment
    token_file: str = ""
    ca_file: str = ""
    timeout_seconds: float = 0.25         # enrichment is on the request path
    cache_ttl_seconds: float = 300.0
    write_back: bool = True               # publish the engine's user features back
    write_back_min_interval_seconds: float = 300.0
    content_entity_type: str = "content"
    user_entity_type: str = "user"
    # feature-service feature ids, per role; see ruc/intelligence/feature_client.py
    content_features: dict[str, str] = field(default_factory=lambda: {
        "embedding": "content.embedding",
        "semantic_embedding": "content.semantic_embedding",
        "visual_embedding": "content.visual_embedding",
        "audio_embedding": "content.audio_embedding",
        "topics": "content.topics",
        "entities": "content.entities",
        "sentiment": "content.sentiment",
        "intent": "content.intent",
        "category": "content.category",
        "quality": "content.quality",
        "credibility": "content.credibility",
    })
    user_features_out: dict[str, str] = field(default_factory=lambda: {
        "embedding": "recommend.user.embedding",
        "topic_affinity": "recommend.user.topic_affinity",
        "creator_affinity": "recommend.user.creator_affinity",
    })


@dataclass
class IntelligenceSettings:
    embedding_model: str = "hashing-v1"   # or a sentence-transformers model, e.g. "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 256              # hashing embedder only
    recent_half_life_hours: float = 6.0
    behavioral_half_life_days: float = 7.0
    historical_half_life_days: float = 90.0
    history_retention_days: int = 180
    session_gap_minutes: float = 30.0
    user_state_ttl_seconds: float = 30.0
    max_events_per_user: int = 5000


@dataclass
class PolicySettings:
    min_content_trust: float = 0.2
    min_user_trust: float = 0.2
    blocked_safety_labels: list[str] = field(default_factory=lambda: [
        "violence", "graphic", "spam", "misinformation", "hate", "self_harm", "sexual"])
    safety_label_threshold: float = 0.7
    seen_window_days: int = 30
    frequency_cap: int = 3                # impressions without engagement, per 7 days
    # Topic ids (or id prefixes before the first ".") always treated as
    # SENSITIVE, whatever the producer said: never inferred, never shown to others.
    sensitive_topic_prefixes: list[str] = field(default_factory=lambda: [
        "health", "medical", "religion", "politics", "sexuality", "sexual_orientation", "gender_identity",
        "ethnicity", "race", "disability", "trade_union", "criminal"])
    max_candidates: int = 1000


@dataclass
class RankingSettings:
    content_model: str = "weighted"       # weighted | logistic
    people_model: str = "weighted"
    challenger_model: str = ""            # served to challenger_percent of users
    challenger_percent: int = 0
    experiment_id: str = "ranking-v1"
    model_dir: str = "models"
    # weights of the score components (ruc/ranking/weighted.py); a JSON file overrides them
    weights_file: str = ""


@dataclass
class TrainingSettings:
    interval_minutes: float = 0           # 0: train only via `oowlet-recommend-uc train`
    min_examples: int = 500
    promote_min_auc_gain: float = 0.01
    mf_factors: int = 32
    mf_iterations: int = 10


@dataclass
class Settings:
    env: str = "production"
    instance_id: str = "recommend-uc-0"
    log_level: str = "INFO"
    server: ServerSettings = field(default_factory=ServerSettings)
    auth: AuthSettings = field(default_factory=AuthSettings)
    broker: BrokerSettings = field(default_factory=BrokerSettings)
    feature_service: FeatureServiceSettings = field(default_factory=FeatureServiceSettings)
    intelligence: IntelligenceSettings = field(default_factory=IntelligenceSettings)
    policy: PolicySettings = field(default_factory=PolicySettings)
    ranking: RankingSettings = field(default_factory=RankingSettings)
    training: TrainingSettings = field(default_factory=TrainingSettings)

    @classmethod
    def load(cls, environ: dict[str, str] | None = None, validate: bool = True) -> "Settings":
        env = dict(os.environ if environ is None else environ)
        s = cls()
        for key, raw in env.items():
            if not key.startswith("RUC_"):
                continue
            path = key[4:].lower().split("__")
            _assign(s, path, raw, key)
        if validate:
            s.validate()
        return s

    def validate(self) -> None:
        errors: list[str] = []
        if not self.auth.tokens_file:
            errors.append("RUC_AUTH__TOKENS_FILE is required: every RPC is authenticated")
        elif not Path(self.auth.tokens_file).is_file():
            errors.append(f"RUC_AUTH__TOKENS_FILE: {self.auth.tokens_file} not found")
        if self.server.tls_enabled and not (self.server.tls_cert_file and self.server.tls_key_file):
            errors.append("TLS is enabled: set RUC_SERVER__TLS_CERT_FILE and RUC_SERVER__TLS_KEY_FILE "
                          "(or RUC_SERVER__TLS_ENABLED=false outside production)")
        if self.env == "production" and not self.server.tls_enabled:
            errors.append("RUC_ENV=production requires TLS")
        for f in ("content_model", "people_model"):
            if getattr(self.ranking, f) not in ("weighted", "logistic"):
                errors.append(f"RUC_RANKING__{f.upper()} must be weighted or logistic")
        if self.ranking.challenger_model not in ("", "weighted", "logistic"):
            errors.append("RUC_RANKING__CHALLENGER_MODEL must be empty, weighted or logistic")
        if not 0 <= self.ranking.challenger_percent <= 100:
            errors.append("RUC_RANKING__CHALLENGER_PERCENT must be 0..100")
        if errors:
            raise ConfigError("invalid configuration:\n  - " + "\n  - ".join(errors))


def _assign(obj: Any, path: list[str], raw: str, key: str) -> None:
    name = path[0]
    names = {f.name for f in fields(obj)}
    if name not in names:
        raise ConfigError(f"{key}: unknown setting")
    hints = get_type_hints(type(obj))
    if len(path) > 1:
        sub = getattr(obj, name)
        if not is_dataclass(sub):
            raise ConfigError(f"{key}: {name} has no sub-settings")
        _assign(sub, path[1:], raw, key)
        return
    t = hints[name]
    setattr(obj, name, _parse(t, raw, key))


def _parse(t: Any, raw: str, key: str) -> Any:
    try:
        if t is bool:
            v = raw.strip().lower()
            if v not in ("1", "0", "true", "false", "yes", "no", "on", "off"):
                raise ValueError(raw)
            return v in ("1", "true", "yes", "on")
        if t is int:
            return int(raw)
        if t is float:
            return float(raw)
        if t is str:
            return raw
        origin = getattr(t, "__origin__", None)
        if origin in (list, dict):
            v = json.loads(raw) if raw.strip().startswith(("[", "{")) else [x.strip() for x in raw.split(",") if x.strip()]
            if origin is dict and not isinstance(v, dict):
                raise ValueError("expected a JSON object")
            return v
    except (ValueError, json.JSONDecodeError) as exc:
        raise ConfigError(f"{key}: cannot parse {raw!r}: {exc}") from None
    raise ConfigError(f"{key}: unsupported setting type")
