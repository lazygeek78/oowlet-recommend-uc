import datetime

from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from oowlet.gen.recommenduc.commonpb import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EngagementType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ENGAGEMENT_TYPE_UNSPECIFIED: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_IMPRESSION: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_OPEN: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_VIEW: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_VIEW_COMPLETE: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_LIKE: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_UNLIKE: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_REACTION: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_COMMENT: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_SHARE: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_SAVE: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_UNSAVE: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_REPOST: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_SEARCH_CLICK: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_CLICK: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_WATCH_TIME: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_PURCHASE: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_OUTCOME: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_SKIP: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_HIDE: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_REPORT: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_PROFILE_VISIT: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_FOLLOW: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_UNFOLLOW: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_CONNECT_REQUEST_SENT: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_CONNECT_ACCEPTED: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_CONNECT_DECLINED: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_CONNECT_REMOVED: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_MESSAGE_SENT: _ClassVar[EngagementType]
    ENGAGEMENT_TYPE_SUGGESTION_DISMISSED: _ClassVar[EngagementType]
ENGAGEMENT_TYPE_UNSPECIFIED: EngagementType
ENGAGEMENT_TYPE_IMPRESSION: EngagementType
ENGAGEMENT_TYPE_OPEN: EngagementType
ENGAGEMENT_TYPE_VIEW: EngagementType
ENGAGEMENT_TYPE_VIEW_COMPLETE: EngagementType
ENGAGEMENT_TYPE_LIKE: EngagementType
ENGAGEMENT_TYPE_UNLIKE: EngagementType
ENGAGEMENT_TYPE_REACTION: EngagementType
ENGAGEMENT_TYPE_COMMENT: EngagementType
ENGAGEMENT_TYPE_SHARE: EngagementType
ENGAGEMENT_TYPE_SAVE: EngagementType
ENGAGEMENT_TYPE_UNSAVE: EngagementType
ENGAGEMENT_TYPE_REPOST: EngagementType
ENGAGEMENT_TYPE_SEARCH_CLICK: EngagementType
ENGAGEMENT_TYPE_CLICK: EngagementType
ENGAGEMENT_TYPE_WATCH_TIME: EngagementType
ENGAGEMENT_TYPE_PURCHASE: EngagementType
ENGAGEMENT_TYPE_OUTCOME: EngagementType
ENGAGEMENT_TYPE_SKIP: EngagementType
ENGAGEMENT_TYPE_HIDE: EngagementType
ENGAGEMENT_TYPE_REPORT: EngagementType
ENGAGEMENT_TYPE_PROFILE_VISIT: EngagementType
ENGAGEMENT_TYPE_FOLLOW: EngagementType
ENGAGEMENT_TYPE_UNFOLLOW: EngagementType
ENGAGEMENT_TYPE_CONNECT_REQUEST_SENT: EngagementType
ENGAGEMENT_TYPE_CONNECT_ACCEPTED: EngagementType
ENGAGEMENT_TYPE_CONNECT_DECLINED: EngagementType
ENGAGEMENT_TYPE_CONNECT_REMOVED: EngagementType
ENGAGEMENT_TYPE_MESSAGE_SENT: EngagementType
ENGAGEMENT_TYPE_SUGGESTION_DISMISSED: EngagementType

class EngagementEvent(_message.Message):
    __slots__ = ("event_id", "user_id", "target", "type", "occurred_at", "surface", "recommendation_id", "position", "dwell", "watch_fraction", "reaction", "session_id", "device_type", "country", "attributes", "value", "currency", "outcome")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OCCURRED_AT_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_ID_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    DWELL_FIELD_NUMBER: _ClassVar[int]
    WATCH_FRACTION_FIELD_NUMBER: _ClassVar[int]
    REACTION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_TYPE_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_id: str
    target: _common_pb2.EntityRef
    type: EngagementType
    occurred_at: _timestamp_pb2.Timestamp
    surface: _common_pb2.Surface
    recommendation_id: str
    position: int
    dwell: _duration_pb2.Duration
    watch_fraction: float
    reaction: str
    session_id: str
    device_type: str
    country: str
    attributes: _containers.ScalarMap[str, str]
    value: float
    currency: str
    outcome: str
    def __init__(self, event_id: _Optional[str] = ..., user_id: _Optional[str] = ..., target: _Optional[_Union[_common_pb2.EntityRef, _Mapping]] = ..., type: _Optional[_Union[EngagementType, str]] = ..., occurred_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., surface: _Optional[_Union[_common_pb2.Surface, str]] = ..., recommendation_id: _Optional[str] = ..., position: _Optional[int] = ..., dwell: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., watch_fraction: _Optional[float] = ..., reaction: _Optional[str] = ..., session_id: _Optional[str] = ..., device_type: _Optional[str] = ..., country: _Optional[str] = ..., attributes: _Optional[_Mapping[str, str]] = ..., value: _Optional[float] = ..., currency: _Optional[str] = ..., outcome: _Optional[str] = ...) -> None: ...

class RecordEngagementRequest(_message.Message):
    __slots__ = ("events",)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[EngagementEvent]
    def __init__(self, events: _Optional[_Iterable[_Union[EngagementEvent, _Mapping]]] = ...) -> None: ...

class RejectedEngagement(_message.Message):
    __slots__ = ("event_id", "reason")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    reason: str
    def __init__(self, event_id: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class RecordEngagementResponse(_message.Message):
    __slots__ = ("accepted", "duplicates", "rejected")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    DUPLICATES_FIELD_NUMBER: _ClassVar[int]
    REJECTED_FIELD_NUMBER: _ClassVar[int]
    accepted: int
    duplicates: int
    rejected: _containers.RepeatedCompositeFieldContainer[RejectedEngagement]
    def __init__(self, accepted: _Optional[int] = ..., duplicates: _Optional[int] = ..., rejected: _Optional[_Iterable[_Union[RejectedEngagement, _Mapping]]] = ...) -> None: ...

class EngagementCounters(_message.Message):
    __slots__ = ("impressions", "opens", "views", "completions", "likes", "comments", "shares", "saves", "reposts", "skips", "hides", "reports", "unique_users", "total_dwell_seconds", "clicks", "purchases", "outcomes", "follows")
    IMPRESSIONS_FIELD_NUMBER: _ClassVar[int]
    OPENS_FIELD_NUMBER: _ClassVar[int]
    VIEWS_FIELD_NUMBER: _ClassVar[int]
    COMPLETIONS_FIELD_NUMBER: _ClassVar[int]
    LIKES_FIELD_NUMBER: _ClassVar[int]
    COMMENTS_FIELD_NUMBER: _ClassVar[int]
    SHARES_FIELD_NUMBER: _ClassVar[int]
    SAVES_FIELD_NUMBER: _ClassVar[int]
    REPOSTS_FIELD_NUMBER: _ClassVar[int]
    SKIPS_FIELD_NUMBER: _ClassVar[int]
    HIDES_FIELD_NUMBER: _ClassVar[int]
    REPORTS_FIELD_NUMBER: _ClassVar[int]
    UNIQUE_USERS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_DWELL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CLICKS_FIELD_NUMBER: _ClassVar[int]
    PURCHASES_FIELD_NUMBER: _ClassVar[int]
    OUTCOMES_FIELD_NUMBER: _ClassVar[int]
    FOLLOWS_FIELD_NUMBER: _ClassVar[int]
    impressions: int
    opens: int
    views: int
    completions: int
    likes: int
    comments: int
    shares: int
    saves: int
    reposts: int
    skips: int
    hides: int
    reports: int
    unique_users: int
    total_dwell_seconds: float
    clicks: int
    purchases: int
    outcomes: int
    follows: int
    def __init__(self, impressions: _Optional[int] = ..., opens: _Optional[int] = ..., views: _Optional[int] = ..., completions: _Optional[int] = ..., likes: _Optional[int] = ..., comments: _Optional[int] = ..., shares: _Optional[int] = ..., saves: _Optional[int] = ..., reposts: _Optional[int] = ..., skips: _Optional[int] = ..., hides: _Optional[int] = ..., reports: _Optional[int] = ..., unique_users: _Optional[int] = ..., total_dwell_seconds: _Optional[float] = ..., clicks: _Optional[int] = ..., purchases: _Optional[int] = ..., outcomes: _Optional[int] = ..., follows: _Optional[int] = ...) -> None: ...

class ContentEngagementStats(_message.Message):
    __slots__ = ("content_id", "window", "counters", "open_rate", "completion_rate", "engagement_rate", "negative_rate", "velocity", "avg_dwell_seconds", "computed_at")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FIELD_NUMBER: _ClassVar[int]
    COUNTERS_FIELD_NUMBER: _ClassVar[int]
    OPEN_RATE_FIELD_NUMBER: _ClassVar[int]
    COMPLETION_RATE_FIELD_NUMBER: _ClassVar[int]
    ENGAGEMENT_RATE_FIELD_NUMBER: _ClassVar[int]
    NEGATIVE_RATE_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_FIELD_NUMBER: _ClassVar[int]
    AVG_DWELL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    COMPUTED_AT_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    window: _common_pb2.WindowSize
    counters: EngagementCounters
    open_rate: float
    completion_rate: float
    engagement_rate: float
    negative_rate: float
    velocity: float
    avg_dwell_seconds: float
    computed_at: _timestamp_pb2.Timestamp
    def __init__(self, content_id: _Optional[str] = ..., window: _Optional[_Union[_common_pb2.WindowSize, str]] = ..., counters: _Optional[_Union[EngagementCounters, _Mapping]] = ..., open_rate: _Optional[float] = ..., completion_rate: _Optional[float] = ..., engagement_rate: _Optional[float] = ..., negative_rate: _Optional[float] = ..., velocity: _Optional[float] = ..., avg_dwell_seconds: _Optional[float] = ..., computed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreatorAffinity(_message.Message):
    __slots__ = ("creator_id", "weight", "interactions", "last_interaction_at")
    CREATOR_ID_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    INTERACTIONS_FIELD_NUMBER: _ClassVar[int]
    LAST_INTERACTION_AT_FIELD_NUMBER: _ClassVar[int]
    creator_id: str
    weight: float
    interactions: int
    last_interaction_at: _timestamp_pb2.Timestamp
    def __init__(self, creator_id: _Optional[str] = ..., weight: _Optional[float] = ..., interactions: _Optional[int] = ..., last_interaction_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ContentKindShare(_message.Message):
    __slots__ = ("kind", "share")
    KIND_FIELD_NUMBER: _ClassVar[int]
    SHARE_FIELD_NUMBER: _ClassVar[int]
    kind: _common_pb2.ContentKind
    share: float
    def __init__(self, kind: _Optional[_Union[_common_pb2.ContentKind, str]] = ..., share: _Optional[float] = ...) -> None: ...

class UserEngagementSummary(_message.Message):
    __slots__ = ("user_id", "window", "counters", "top_topics", "top_creators", "kind_mix", "activity_by_hour", "last_active_at", "computed_at")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FIELD_NUMBER: _ClassVar[int]
    COUNTERS_FIELD_NUMBER: _ClassVar[int]
    TOP_TOPICS_FIELD_NUMBER: _ClassVar[int]
    TOP_CREATORS_FIELD_NUMBER: _ClassVar[int]
    KIND_MIX_FIELD_NUMBER: _ClassVar[int]
    ACTIVITY_BY_HOUR_FIELD_NUMBER: _ClassVar[int]
    LAST_ACTIVE_AT_FIELD_NUMBER: _ClassVar[int]
    COMPUTED_AT_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    window: _common_pb2.WindowSize
    counters: EngagementCounters
    top_topics: _containers.RepeatedCompositeFieldContainer[_common_pb2.TopicAffinity]
    top_creators: _containers.RepeatedCompositeFieldContainer[CreatorAffinity]
    kind_mix: _containers.RepeatedCompositeFieldContainer[ContentKindShare]
    activity_by_hour: _containers.RepeatedScalarFieldContainer[int]
    last_active_at: _timestamp_pb2.Timestamp
    computed_at: _timestamp_pb2.Timestamp
    def __init__(self, user_id: _Optional[str] = ..., window: _Optional[_Union[_common_pb2.WindowSize, str]] = ..., counters: _Optional[_Union[EngagementCounters, _Mapping]] = ..., top_topics: _Optional[_Iterable[_Union[_common_pb2.TopicAffinity, _Mapping]]] = ..., top_creators: _Optional[_Iterable[_Union[CreatorAffinity, _Mapping]]] = ..., kind_mix: _Optional[_Iterable[_Union[ContentKindShare, _Mapping]]] = ..., activity_by_hour: _Optional[_Iterable[int]] = ..., last_active_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., computed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetContentEngagementRequest(_message.Message):
    __slots__ = ("content_ids", "windows")
    CONTENT_IDS_FIELD_NUMBER: _ClassVar[int]
    WINDOWS_FIELD_NUMBER: _ClassVar[int]
    content_ids: _containers.RepeatedScalarFieldContainer[str]
    windows: _containers.RepeatedScalarFieldContainer[_common_pb2.WindowSize]
    def __init__(self, content_ids: _Optional[_Iterable[str]] = ..., windows: _Optional[_Iterable[_Union[_common_pb2.WindowSize, str]]] = ...) -> None: ...

class GetContentEngagementResponse(_message.Message):
    __slots__ = ("stats",)
    STATS_FIELD_NUMBER: _ClassVar[int]
    stats: _containers.RepeatedCompositeFieldContainer[ContentEngagementStats]
    def __init__(self, stats: _Optional[_Iterable[_Union[ContentEngagementStats, _Mapping]]] = ...) -> None: ...

class GetUserEngagementSummaryRequest(_message.Message):
    __slots__ = ("user_id", "window")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    window: _common_pb2.WindowSize
    def __init__(self, user_id: _Optional[str] = ..., window: _Optional[_Union[_common_pb2.WindowSize, str]] = ...) -> None: ...

class GetUserEngagementSummaryResponse(_message.Message):
    __slots__ = ("summary",)
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    summary: UserEngagementSummary
    def __init__(self, summary: _Optional[_Union[UserEngagementSummary, _Mapping]] = ...) -> None: ...

class GetTrendingRequest(_message.Message):
    __slots__ = ("context", "kinds", "topic_ids", "country", "window", "page")
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    KINDS_FIELD_NUMBER: _ClassVar[int]
    TOPIC_IDS_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    context: _common_pb2.RequestContext
    kinds: _containers.RepeatedScalarFieldContainer[_common_pb2.ContentKind]
    topic_ids: _containers.RepeatedScalarFieldContainer[str]
    country: str
    window: _common_pb2.WindowSize
    page: _common_pb2.PageRequest
    def __init__(self, context: _Optional[_Union[_common_pb2.RequestContext, _Mapping]] = ..., kinds: _Optional[_Iterable[_Union[_common_pb2.ContentKind, str]]] = ..., topic_ids: _Optional[_Iterable[str]] = ..., country: _Optional[str] = ..., window: _Optional[_Union[_common_pb2.WindowSize, str]] = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class TrendingItem(_message.Message):
    __slots__ = ("content_id", "score", "stats")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    score: float
    stats: ContentEngagementStats
    def __init__(self, content_id: _Optional[str] = ..., score: _Optional[float] = ..., stats: _Optional[_Union[ContentEngagementStats, _Mapping]] = ...) -> None: ...

class GetTrendingResponse(_message.Message):
    __slots__ = ("items", "page")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[TrendingItem]
    page: _common_pb2.PageResponse
    def __init__(self, items: _Optional[_Iterable[_Union[TrendingItem, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ...) -> None: ...
