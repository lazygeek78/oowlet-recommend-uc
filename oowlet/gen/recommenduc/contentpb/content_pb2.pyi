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

class Visibility(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    VISIBILITY_UNSPECIFIED: _ClassVar[Visibility]
    VISIBILITY_PUBLIC: _ClassVar[Visibility]
    VISIBILITY_FOLLOWERS: _ClassVar[Visibility]
    VISIBILITY_CONNECTIONS: _ClassVar[Visibility]
    VISIBILITY_COMMUNITY: _ClassVar[Visibility]
    VISIBILITY_UNLISTED: _ClassVar[Visibility]
    VISIBILITY_PRIVATE: _ClassVar[Visibility]

class ContentStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTENT_STATUS_UNSPECIFIED: _ClassVar[ContentStatus]
    CONTENT_STATUS_ACTIVE: _ClassVar[ContentStatus]
    CONTENT_STATUS_UNDER_REVIEW: _ClassVar[ContentStatus]
    CONTENT_STATUS_REMOVED: _ClassVar[ContentStatus]
    CONTENT_STATUS_DELETED: _ClassVar[ContentStatus]
VISIBILITY_UNSPECIFIED: Visibility
VISIBILITY_PUBLIC: Visibility
VISIBILITY_FOLLOWERS: Visibility
VISIBILITY_CONNECTIONS: Visibility
VISIBILITY_COMMUNITY: Visibility
VISIBILITY_UNLISTED: Visibility
VISIBILITY_PRIVATE: Visibility
CONTENT_STATUS_UNSPECIFIED: ContentStatus
CONTENT_STATUS_ACTIVE: ContentStatus
CONTENT_STATUS_UNDER_REVIEW: ContentStatus
CONTENT_STATUS_REMOVED: ContentStatus
CONTENT_STATUS_DELETED: ContentStatus

class AudienceRestriction(_message.Message):
    __slots__ = ("adults_only", "allowed_countries", "blocked_countries")
    ADULTS_ONLY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_COUNTRIES_FIELD_NUMBER: _ClassVar[int]
    BLOCKED_COUNTRIES_FIELD_NUMBER: _ClassVar[int]
    adults_only: bool
    allowed_countries: _containers.RepeatedScalarFieldContainer[str]
    blocked_countries: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, adults_only: bool = ..., allowed_countries: _Optional[_Iterable[str]] = ..., blocked_countries: _Optional[_Iterable[str]] = ...) -> None: ...

class SafetyLabel(_message.Message):
    __slots__ = ("label", "confidence", "source")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    label: str
    confidence: float
    source: str
    def __init__(self, label: _Optional[str] = ..., confidence: _Optional[float] = ..., source: _Optional[str] = ...) -> None: ...

class ContentItem(_message.Message):
    __slots__ = ("content_id", "creator_id", "kind", "language", "topics", "hashtags", "embeddings", "published_at", "duration", "visibility", "community_id", "audience", "safety_labels", "quality_score", "trust_score", "status", "updated_at", "version")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    CREATOR_ID_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    HASHTAGS_FIELD_NUMBER: _ClassVar[int]
    EMBEDDINGS_FIELD_NUMBER: _ClassVar[int]
    PUBLISHED_AT_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    AUDIENCE_FIELD_NUMBER: _ClassVar[int]
    SAFETY_LABELS_FIELD_NUMBER: _ClassVar[int]
    QUALITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    TRUST_SCORE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    creator_id: str
    kind: _common_pb2.ContentKind
    language: str
    topics: _containers.RepeatedCompositeFieldContainer[_common_pb2.TopicAffinity]
    hashtags: _containers.RepeatedScalarFieldContainer[str]
    embeddings: _containers.RepeatedCompositeFieldContainer[_common_pb2.Embedding]
    published_at: _timestamp_pb2.Timestamp
    duration: _duration_pb2.Duration
    visibility: Visibility
    community_id: str
    audience: AudienceRestriction
    safety_labels: _containers.RepeatedCompositeFieldContainer[SafetyLabel]
    quality_score: float
    trust_score: float
    status: ContentStatus
    updated_at: _timestamp_pb2.Timestamp
    version: int
    def __init__(self, content_id: _Optional[str] = ..., creator_id: _Optional[str] = ..., kind: _Optional[_Union[_common_pb2.ContentKind, str]] = ..., language: _Optional[str] = ..., topics: _Optional[_Iterable[_Union[_common_pb2.TopicAffinity, _Mapping]]] = ..., hashtags: _Optional[_Iterable[str]] = ..., embeddings: _Optional[_Iterable[_Union[_common_pb2.Embedding, _Mapping]]] = ..., published_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., duration: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., visibility: _Optional[_Union[Visibility, str]] = ..., community_id: _Optional[str] = ..., audience: _Optional[_Union[AudienceRestriction, _Mapping]] = ..., safety_labels: _Optional[_Iterable[_Union[SafetyLabel, _Mapping]]] = ..., quality_score: _Optional[float] = ..., trust_score: _Optional[float] = ..., status: _Optional[_Union[ContentStatus, str]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., version: _Optional[int] = ...) -> None: ...

class UpsertContentRequest(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ContentItem]
    def __init__(self, items: _Optional[_Iterable[_Union[ContentItem, _Mapping]]] = ...) -> None: ...

class UpsertContentResponse(_message.Message):
    __slots__ = ("upserted", "stale_ignored")
    UPSERTED_FIELD_NUMBER: _ClassVar[int]
    STALE_IGNORED_FIELD_NUMBER: _ClassVar[int]
    upserted: int
    stale_ignored: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, upserted: _Optional[int] = ..., stale_ignored: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveContentRequest(_message.Message):
    __slots__ = ("content_id", "status", "reason")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    status: ContentStatus
    reason: str
    def __init__(self, content_id: _Optional[str] = ..., status: _Optional[_Union[ContentStatus, str]] = ..., reason: _Optional[str] = ...) -> None: ...

class RemoveContentResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetContentRequest(_message.Message):
    __slots__ = ("content_ids", "include_embeddings")
    CONTENT_IDS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_EMBEDDINGS_FIELD_NUMBER: _ClassVar[int]
    content_ids: _containers.RepeatedScalarFieldContainer[str]
    include_embeddings: bool
    def __init__(self, content_ids: _Optional[_Iterable[str]] = ..., include_embeddings: bool = ...) -> None: ...

class GetContentResponse(_message.Message):
    __slots__ = ("items", "not_found")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NOT_FOUND_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ContentItem]
    not_found: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, items: _Optional[_Iterable[_Union[ContentItem, _Mapping]]] = ..., not_found: _Optional[_Iterable[str]] = ...) -> None: ...
