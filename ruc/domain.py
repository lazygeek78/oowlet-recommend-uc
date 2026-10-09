"""Internal records of the engine. Enum fields hold the proto enum numbers
(oowlet.gen.recommenduc.*), so nothing is translated twice."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.graphpb import graph_pb2 as gpb
from oowlet.gen.recommenduc.profilepb import profile_pb2 as ppb

USER = cpb.ENTITY_TYPE_USER
CONTENT = cpb.ENTITY_TYPE_CONTENT


def now() -> float:
    return time.time()


@dataclass(frozen=True)
class Engagement:
    event_id: str
    user_id: str
    target_type: int            # common.EntityType
    target_id: str
    type: int                   # engagement.EngagementType
    ts: float                   # unix seconds
    surface: int = 0
    recommendation_id: str = ""
    position: int = -1
    dwell_s: float = 0.0
    watch_fraction: float = 0.0
    session_id: str = ""
    device_type: str = ""
    country: str = ""
    value: float = 0.0
    outcome: str = ""
    reaction: str = ""


@dataclass
class Topic:
    topic_id: str
    weight: float
    sensitive: bool = False
    label: str = ""
    source: int = 0             # common.AffinitySource


@dataclass
class ContentRecord:
    content_id: str
    creator_id: str
    kind: int = 0
    language: str = ""
    topics: list[Topic] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    embeddings: dict[str, np.ndarray] = field(default_factory=dict)   # model_id -> unit vector
    published_at: float = 0.0
    duration_s: float = 0.0
    visibility: int = ctpb.VISIBILITY_UNSPECIFIED
    community_id: str = ""
    adults_only: bool = False
    audience_unknown: bool = False      # producer gave no audience (legacy events): adults only
    allowed_countries: list[str] = field(default_factory=list)
    blocked_countries: list[str] = field(default_factory=list)
    safety_labels: list[tuple[str, float]] = field(default_factory=list)
    quality: float = 0.5
    trust: float = 0.5
    status: int = ctpb.CONTENT_STATUS_UNSPECIFIED
    updated_at: float = 0.0
    version: int = 0
    # enrichment from the feature service (ruc/intelligence/feature_client.py)
    entities: list[str] = field(default_factory=list)
    sentiment: float = 0.0
    intent: str = ""
    category: str = ""

    def topic_weights(self, include_sensitive: bool = True) -> dict[str, float]:
        return {t.topic_id: t.weight for t in self.topics if include_sensitive or not t.sensitive}

    def sensitive_topics(self) -> set[str]:
        return {t.topic_id for t in self.topics if t.sensitive}

    def primary_topic(self) -> str:
        return max(self.topics, key=lambda t: t.weight).topic_id if self.topics else ""


@dataclass
class Preferences:
    preferred_topic_ids: list[str] = field(default_factory=list)
    muted_topic_ids: list[str] = field(default_factory=list)
    muted_user_ids: list[str] = field(default_factory=list)
    blocked_user_ids: list[str] = field(default_factory=list)
    preferred_kinds: list[int] = field(default_factory=list)
    muted_kinds: list[int] = field(default_factory=list)
    content_languages: list[str] = field(default_factory=list)
    max_maturity: int = ppb.MATURITY_LEVEL_UNSPECIFIED
    open_to_connections: bool = False
    connection_purposes: list[int] = field(default_factory=list)
    connection_languages: list[str] = field(default_factory=list)
    same_country_only: bool = False


@dataclass
class Privacy:
    # False everywhere = the restrictive choice (see profile.proto)
    personalization_enabled: bool = False
    use_engagement_history: bool = False
    discoverable_in_suggestions: bool = False
    allow_mutual_connection_signal: bool = False
    allow_location_signal: bool = False
    show_activity_to_others: bool = False
    allow_declared_sensitive_topics: bool = False
    contribute_to_collaborative: bool = False
    updated_at: float = 0.0

    @classmethod
    def platform_defaults(cls) -> "Privacy":
        """Written explicitly when a profile is first created."""
        return cls(personalization_enabled=True, use_engagement_history=True, discoverable_in_suggestions=True,
                   allow_mutual_connection_signal=True, allow_location_signal=False, show_activity_to_others=False,
                   allow_declared_sensitive_topics=False, contribute_to_collaborative=True, updated_at=now())


@dataclass
class UserRecord:
    user_id: str
    age_band: int = cpb.AGE_BAND_UNSPECIFIED
    account_type: int = ppb.ACCOUNT_TYPE_UNSPECIFIED
    verified: bool = False
    languages: list[str] = field(default_factory=list)
    country: str = ""
    region: str = ""
    trust_score: float = 0.5
    declared_topics: list[Topic] = field(default_factory=list)       # from preferences: preferred + sensitive declared
    inferred_topics: list[Topic] = field(default_factory=list)       # written by the feature pipeline
    embeddings: dict[str, np.ndarray] = field(default_factory=dict)
    preferences: Preferences = field(default_factory=Preferences)
    privacy: Privacy = field(default_factory=Privacy.platform_defaults)
    created_at: float = 0.0
    updated_at: float = 0.0
    version: int = 0

    @property
    def is_adult(self) -> bool:
        # unknown age is treated as a minor (common.proto)
        return self.age_band == cpb.AGE_BAND_ADULT


@dataclass(frozen=True)
class Edge:
    from_user_id: str
    to_user_id: str
    type: int                   # graph.EdgeType
    weight: float = 1.0
    created_at: float = 0.0

    @property
    def key(self) -> tuple[str, str, int]:
        return (self.from_user_id, self.to_user_id, self.type)


FOLLOWS = gpb.EDGE_TYPE_FOLLOWS
CONNECTED = gpb.EDGE_TYPE_CONNECTED
REQUESTED = gpb.EDGE_TYPE_CONNECTION_REQUESTED
BLOCKED = gpb.EDGE_TYPE_BLOCKED
MUTED = gpb.EDGE_TYPE_MUTED
SAME_COMMUNITY = gpb.EDGE_TYPE_SAME_COMMUNITY
INTERACTED = gpb.EDGE_TYPE_INTERACTED
COMMUNITY_MEMBER = gpb.EDGE_TYPE_COMMUNITY_MEMBER


@dataclass
class ServedItem:
    target_type: int
    target_id: str
    rank: int
    score: float
    features: dict[str, float]          # ranking inputs at serve time (training data)
    sources: list[str] = field(default_factory=list)
    label: float | None = None          # set by attribution: 1 positive, 0 negative/ignored
    impressed: bool = False


@dataclass
class ServedRecommendation:
    recommendation_id: str
    user_id: str
    surface: int
    engine: str                         # "content" | "people"
    items: list[ServedItem]
    model_id: str
    model_version: str
    variant: str
    experiment_id: str
    personalized: bool
    served_at: float


@dataclass(frozen=True)
class Feedback:
    user_id: str
    recommendation_id: str
    target_type: int
    target_id: str
    type: int                           # recommendation.FeedbackType
    topic_id: str
    given_at: float
