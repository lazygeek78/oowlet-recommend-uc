import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from oowlet.gen.recommenduc.commonpb import common_pb2 as _common_pb2
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as _engagement_pb2
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as _recommendation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RelationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RELATION_TYPE_UNSPECIFIED: _ClassVar[RelationType]
    RELATION_TYPE_SIMILAR: _ClassVar[RelationType]
    RELATION_TYPE_CO_ENGAGED: _ClassVar[RelationType]
    RELATION_TYPE_SAME_CREATOR: _ClassVar[RelationType]
    RELATION_TYPE_SAME_TOPIC: _ClassVar[RelationType]
    RELATION_TYPE_SEQUEL: _ClassVar[RelationType]

class SimilarityBasis(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SIMILARITY_BASIS_UNSPECIFIED: _ClassVar[SimilarityBasis]
    SIMILARITY_BASIS_CO_ENGAGEMENT: _ClassVar[SimilarityBasis]
    SIMILARITY_BASIS_INTERESTS: _ClassVar[SimilarityBasis]
    SIMILARITY_BASIS_GRAPH: _ClassVar[SimilarityBasis]
RELATION_TYPE_UNSPECIFIED: RelationType
RELATION_TYPE_SIMILAR: RelationType
RELATION_TYPE_CO_ENGAGED: RelationType
RELATION_TYPE_SAME_CREATOR: RelationType
RELATION_TYPE_SAME_TOPIC: RelationType
RELATION_TYPE_SEQUEL: RelationType
SIMILARITY_BASIS_UNSPECIFIED: SimilarityBasis
SIMILARITY_BASIS_CO_ENGAGEMENT: SimilarityBasis
SIMILARITY_BASIS_INTERESTS: SimilarityBasis
SIMILARITY_BASIS_GRAPH: SimilarityBasis

class HistoryEntry(_message.Message):
    __slots__ = ("event_id", "target", "type", "occurred_at", "surface", "recommendation_id")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OCCURRED_AT_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_ID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    target: _common_pb2.EntityRef
    type: _engagement_pb2.EngagementType
    occurred_at: _timestamp_pb2.Timestamp
    surface: _common_pb2.Surface
    recommendation_id: str
    def __init__(self, event_id: _Optional[str] = ..., target: _Optional[_Union[_common_pb2.EntityRef, _Mapping]] = ..., type: _Optional[_Union[_engagement_pb2.EngagementType, str]] = ..., occurred_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., surface: _Optional[_Union[_common_pb2.Surface, str]] = ..., recommendation_id: _Optional[str] = ...) -> None: ...

class GetUserHistoryRequest(_message.Message):
    __slots__ = ("user_id", "types", "target_types", "window", "page")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPES_FIELD_NUMBER: _ClassVar[int]
    TARGET_TYPES_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    types: _containers.RepeatedScalarFieldContainer[_engagement_pb2.EngagementType]
    target_types: _containers.RepeatedScalarFieldContainer[_common_pb2.EntityType]
    window: _common_pb2.TimeWindow
    page: _common_pb2.PageRequest
    def __init__(self, user_id: _Optional[str] = ..., types: _Optional[_Iterable[_Union[_engagement_pb2.EngagementType, str]]] = ..., target_types: _Optional[_Iterable[_Union[_common_pb2.EntityType, str]]] = ..., window: _Optional[_Union[_common_pb2.TimeWindow, _Mapping]] = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class GetUserHistoryResponse(_message.Message):
    __slots__ = ("entries", "page")
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[HistoryEntry]
    page: _common_pb2.PageResponse
    def __init__(self, entries: _Optional[_Iterable[_Union[HistoryEntry, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ...) -> None: ...

class TimelineBucket(_message.Message):
    __slots__ = ("start", "counters")
    START_FIELD_NUMBER: _ClassVar[int]
    COUNTERS_FIELD_NUMBER: _ClassVar[int]
    start: _timestamp_pb2.Timestamp
    counters: _engagement_pb2.EngagementCounters
    def __init__(self, start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., counters: _Optional[_Union[_engagement_pb2.EngagementCounters, _Mapping]] = ...) -> None: ...

class GetContentHistoryRequest(_message.Message):
    __slots__ = ("content_id", "window", "granularity")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FIELD_NUMBER: _ClassVar[int]
    GRANULARITY_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    window: _common_pb2.TimeWindow
    granularity: _common_pb2.Granularity
    def __init__(self, content_id: _Optional[str] = ..., window: _Optional[_Union[_common_pb2.TimeWindow, _Mapping]] = ..., granularity: _Optional[_Union[_common_pb2.Granularity, str]] = ...) -> None: ...

class GetContentHistoryResponse(_message.Message):
    __slots__ = ("content_id", "buckets")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    BUCKETS_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    buckets: _containers.RepeatedCompositeFieldContainer[TimelineBucket]
    def __init__(self, content_id: _Optional[str] = ..., buckets: _Optional[_Iterable[_Union[TimelineBucket, _Mapping]]] = ...) -> None: ...

class GetContentEngagersRequest(_message.Message):
    __slots__ = ("content_id", "viewer_id", "types", "connections_only", "page")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    VIEWER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPES_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONS_ONLY_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    viewer_id: str
    types: _containers.RepeatedScalarFieldContainer[_engagement_pb2.EngagementType]
    connections_only: bool
    page: _common_pb2.PageRequest
    def __init__(self, content_id: _Optional[str] = ..., viewer_id: _Optional[str] = ..., types: _Optional[_Iterable[_Union[_engagement_pb2.EngagementType, str]]] = ..., connections_only: bool = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class Engager(_message.Message):
    __slots__ = ("user_id", "type", "occurred_at")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OCCURRED_AT_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    type: _engagement_pb2.EngagementType
    occurred_at: _timestamp_pb2.Timestamp
    def __init__(self, user_id: _Optional[str] = ..., type: _Optional[_Union[_engagement_pb2.EngagementType, str]] = ..., occurred_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetContentEngagersResponse(_message.Message):
    __slots__ = ("engagers", "page")
    ENGAGERS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    engagers: _containers.RepeatedCompositeFieldContainer[Engager]
    page: _common_pb2.PageResponse
    def __init__(self, engagers: _Optional[_Iterable[_Union[Engager, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ...) -> None: ...

class GetRelatedContentRequest(_message.Message):
    __slots__ = ("content_id", "relations", "limit", "for_user_id")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    RELATIONS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FOR_USER_ID_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    relations: _containers.RepeatedScalarFieldContainer[RelationType]
    limit: int
    for_user_id: str
    def __init__(self, content_id: _Optional[str] = ..., relations: _Optional[_Iterable[_Union[RelationType, str]]] = ..., limit: _Optional[int] = ..., for_user_id: _Optional[str] = ...) -> None: ...

class RelatedContent(_message.Message):
    __slots__ = ("content_id", "relation", "score")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    RELATION_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    relation: RelationType
    score: float
    def __init__(self, content_id: _Optional[str] = ..., relation: _Optional[_Union[RelationType, str]] = ..., score: _Optional[float] = ...) -> None: ...

class GetRelatedContentResponse(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[RelatedContent]
    def __init__(self, items: _Optional[_Iterable[_Union[RelatedContent, _Mapping]]] = ...) -> None: ...

class GetSimilarUsersRequest(_message.Message):
    __slots__ = ("user_id", "bases", "limit")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    BASES_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    bases: _containers.RepeatedScalarFieldContainer[SimilarityBasis]
    limit: int
    def __init__(self, user_id: _Optional[str] = ..., bases: _Optional[_Iterable[_Union[SimilarityBasis, str]]] = ..., limit: _Optional[int] = ...) -> None: ...

class SimilarUser(_message.Message):
    __slots__ = ("user_id", "score", "basis")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    BASIS_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    score: float
    basis: SimilarityBasis
    def __init__(self, user_id: _Optional[str] = ..., score: _Optional[float] = ..., basis: _Optional[_Union[SimilarityBasis, str]] = ...) -> None: ...

class GetSimilarUsersResponse(_message.Message):
    __slots__ = ("users",)
    USERS_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedCompositeFieldContainer[SimilarUser]
    def __init__(self, users: _Optional[_Iterable[_Union[SimilarUser, _Mapping]]] = ...) -> None: ...

class GetRecommendationHistoryRequest(_message.Message):
    __slots__ = ("user_id", "surface", "window", "page")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    surface: _common_pb2.Surface
    window: _common_pb2.TimeWindow
    page: _common_pb2.PageRequest
    def __init__(self, user_id: _Optional[str] = ..., surface: _Optional[_Union[_common_pb2.Surface, str]] = ..., window: _Optional[_Union[_common_pb2.TimeWindow, _Mapping]] = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class GetRecommendationHistoryResponse(_message.Message):
    __slots__ = ("served", "page")
    SERVED_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    served: _containers.RepeatedCompositeFieldContainer[_recommendation_pb2.ServedRecommendation]
    page: _common_pb2.PageResponse
    def __init__(self, served: _Optional[_Iterable[_Union[_recommendation_pb2.ServedRecommendation, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ...) -> None: ...
