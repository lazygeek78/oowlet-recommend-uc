import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EntityType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ENTITY_TYPE_UNSPECIFIED: _ClassVar[EntityType]
    ENTITY_TYPE_USER: _ClassVar[EntityType]
    ENTITY_TYPE_CONTENT: _ClassVar[EntityType]
    ENTITY_TYPE_CREATOR: _ClassVar[EntityType]
    ENTITY_TYPE_TOPIC: _ClassVar[EntityType]
    ENTITY_TYPE_COMMUNITY: _ClassVar[EntityType]
    ENTITY_TYPE_HASHTAG: _ClassVar[EntityType]

class ContentKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTENT_KIND_UNSPECIFIED: _ClassVar[ContentKind]
    CONTENT_KIND_TEXT: _ClassVar[ContentKind]
    CONTENT_KIND_IMAGE: _ClassVar[ContentKind]
    CONTENT_KIND_VIDEO: _ClassVar[ContentKind]
    CONTENT_KIND_AUDIO: _ClassVar[ContentKind]
    CONTENT_KIND_BLOG: _ClassVar[ContentKind]
    CONTENT_KIND_LIVE: _ClassVar[ContentKind]
    CONTENT_KIND_REEL: _ClassVar[ContentKind]
    CONTENT_KIND_GLIMPSE: _ClassVar[ContentKind]
    CONTENT_KIND_INSTANT: _ClassVar[ContentKind]

class Surface(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SURFACE_UNSPECIFIED: _ClassVar[Surface]
    SURFACE_HOME_FEED: _ClassVar[Surface]
    SURFACE_REELS: _ClassVar[Surface]
    SURFACE_GLIMPSE: _ClassVar[Surface]
    SURFACE_INSTANTS: _ClassVar[Surface]
    SURFACE_EXPLORE: _ClassVar[Surface]
    SURFACE_SEARCH: _ClassVar[Surface]
    SURFACE_PROFILE: _ClassVar[Surface]
    SURFACE_CONTENT_DETAIL: _ClassVar[Surface]
    SURFACE_PEOPLE_YOU_MAY_KNOW: _ClassVar[Surface]
    SURFACE_NOTIFICATION: _ClassVar[Surface]
    SURFACE_DIGEST: _ClassVar[Surface]

class AgeBand(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AGE_BAND_UNSPECIFIED: _ClassVar[AgeBand]
    AGE_BAND_MINOR: _ClassVar[AgeBand]
    AGE_BAND_ADULT: _ClassVar[AgeBand]

class Sensitivity(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SENSITIVITY_UNSPECIFIED: _ClassVar[Sensitivity]
    SENSITIVITY_GENERAL: _ClassVar[Sensitivity]
    SENSITIVITY_SENSITIVE: _ClassVar[Sensitivity]

class WindowSize(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WINDOW_SIZE_UNSPECIFIED: _ClassVar[WindowSize]
    WINDOW_SIZE_1H: _ClassVar[WindowSize]
    WINDOW_SIZE_24H: _ClassVar[WindowSize]
    WINDOW_SIZE_7D: _ClassVar[WindowSize]
    WINDOW_SIZE_30D: _ClassVar[WindowSize]
    WINDOW_SIZE_90D: _ClassVar[WindowSize]
    WINDOW_SIZE_ALL_TIME: _ClassVar[WindowSize]

class Granularity(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GRANULARITY_UNSPECIFIED: _ClassVar[Granularity]
    GRANULARITY_HOUR: _ClassVar[Granularity]
    GRANULARITY_DAY: _ClassVar[Granularity]
    GRANULARITY_WEEK: _ClassVar[Granularity]

class AffinitySource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AFFINITY_SOURCE_UNSPECIFIED: _ClassVar[AffinitySource]
    AFFINITY_SOURCE_DECLARED: _ClassVar[AffinitySource]
    AFFINITY_SOURCE_INFERRED: _ClassVar[AffinitySource]
    AFFINITY_SOURCE_EDITORIAL: _ClassVar[AffinitySource]

class ReasonCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    REASON_CODE_UNSPECIFIED: _ClassVar[ReasonCode]
    REASON_CODE_TOPIC_INTEREST: _ClassVar[ReasonCode]
    REASON_CODE_SIMILAR_TO_ENGAGED: _ClassVar[ReasonCode]
    REASON_CODE_FOLLOWED_CREATOR: _ClassVar[ReasonCode]
    REASON_CODE_COLLABORATIVE: _ClassVar[ReasonCode]
    REASON_CODE_TRENDING: _ClassVar[ReasonCode]
    REASON_CODE_FRESH: _ClassVar[ReasonCode]
    REASON_CODE_EDITORIAL: _ClassVar[ReasonCode]
    REASON_CODE_EXPLORATION: _ClassVar[ReasonCode]
    REASON_CODE_MUTUAL_CONNECTIONS: _ClassVar[ReasonCode]
    REASON_CODE_SHARED_INTERESTS: _ClassVar[ReasonCode]
    REASON_CODE_SAME_COMMUNITY: _ClassVar[ReasonCode]
    REASON_CODE_INTERACTED_WITH_CONTENT: _ClassVar[ReasonCode]
    REASON_CODE_NEARBY_REGION: _ClassVar[ReasonCode]
    REASON_CODE_POPULAR_IN_REGION: _ClassVar[ReasonCode]

class ExclusionReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXCLUSION_REASON_UNSPECIFIED: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_BLOCKED: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_MUTED: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_ALREADY_SEEN: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_ALREADY_CONNECTED: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_REQUEST_PENDING: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_DISMISSED: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_SELF: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_PRIVACY_SETTINGS: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_AGE_RESTRICTED: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_AUDIENCE_RESTRICTED: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_SAFETY_LABEL: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_LOW_TRUST: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_LANGUAGE_MISMATCH: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_UNAVAILABLE: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_FREQUENCY_CAP: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_SENSITIVE_TOPIC: _ClassVar[ExclusionReason]
    EXCLUSION_REASON_NOT_OPEN_TO_CONNECT: _ClassVar[ExclusionReason]
ENTITY_TYPE_UNSPECIFIED: EntityType
ENTITY_TYPE_USER: EntityType
ENTITY_TYPE_CONTENT: EntityType
ENTITY_TYPE_CREATOR: EntityType
ENTITY_TYPE_TOPIC: EntityType
ENTITY_TYPE_COMMUNITY: EntityType
ENTITY_TYPE_HASHTAG: EntityType
CONTENT_KIND_UNSPECIFIED: ContentKind
CONTENT_KIND_TEXT: ContentKind
CONTENT_KIND_IMAGE: ContentKind
CONTENT_KIND_VIDEO: ContentKind
CONTENT_KIND_AUDIO: ContentKind
CONTENT_KIND_BLOG: ContentKind
CONTENT_KIND_LIVE: ContentKind
CONTENT_KIND_REEL: ContentKind
CONTENT_KIND_GLIMPSE: ContentKind
CONTENT_KIND_INSTANT: ContentKind
SURFACE_UNSPECIFIED: Surface
SURFACE_HOME_FEED: Surface
SURFACE_REELS: Surface
SURFACE_GLIMPSE: Surface
SURFACE_INSTANTS: Surface
SURFACE_EXPLORE: Surface
SURFACE_SEARCH: Surface
SURFACE_PROFILE: Surface
SURFACE_CONTENT_DETAIL: Surface
SURFACE_PEOPLE_YOU_MAY_KNOW: Surface
SURFACE_NOTIFICATION: Surface
SURFACE_DIGEST: Surface
AGE_BAND_UNSPECIFIED: AgeBand
AGE_BAND_MINOR: AgeBand
AGE_BAND_ADULT: AgeBand
SENSITIVITY_UNSPECIFIED: Sensitivity
SENSITIVITY_GENERAL: Sensitivity
SENSITIVITY_SENSITIVE: Sensitivity
WINDOW_SIZE_UNSPECIFIED: WindowSize
WINDOW_SIZE_1H: WindowSize
WINDOW_SIZE_24H: WindowSize
WINDOW_SIZE_7D: WindowSize
WINDOW_SIZE_30D: WindowSize
WINDOW_SIZE_90D: WindowSize
WINDOW_SIZE_ALL_TIME: WindowSize
GRANULARITY_UNSPECIFIED: Granularity
GRANULARITY_HOUR: Granularity
GRANULARITY_DAY: Granularity
GRANULARITY_WEEK: Granularity
AFFINITY_SOURCE_UNSPECIFIED: AffinitySource
AFFINITY_SOURCE_DECLARED: AffinitySource
AFFINITY_SOURCE_INFERRED: AffinitySource
AFFINITY_SOURCE_EDITORIAL: AffinitySource
REASON_CODE_UNSPECIFIED: ReasonCode
REASON_CODE_TOPIC_INTEREST: ReasonCode
REASON_CODE_SIMILAR_TO_ENGAGED: ReasonCode
REASON_CODE_FOLLOWED_CREATOR: ReasonCode
REASON_CODE_COLLABORATIVE: ReasonCode
REASON_CODE_TRENDING: ReasonCode
REASON_CODE_FRESH: ReasonCode
REASON_CODE_EDITORIAL: ReasonCode
REASON_CODE_EXPLORATION: ReasonCode
REASON_CODE_MUTUAL_CONNECTIONS: ReasonCode
REASON_CODE_SHARED_INTERESTS: ReasonCode
REASON_CODE_SAME_COMMUNITY: ReasonCode
REASON_CODE_INTERACTED_WITH_CONTENT: ReasonCode
REASON_CODE_NEARBY_REGION: ReasonCode
REASON_CODE_POPULAR_IN_REGION: ReasonCode
EXCLUSION_REASON_UNSPECIFIED: ExclusionReason
EXCLUSION_REASON_BLOCKED: ExclusionReason
EXCLUSION_REASON_MUTED: ExclusionReason
EXCLUSION_REASON_ALREADY_SEEN: ExclusionReason
EXCLUSION_REASON_ALREADY_CONNECTED: ExclusionReason
EXCLUSION_REASON_REQUEST_PENDING: ExclusionReason
EXCLUSION_REASON_DISMISSED: ExclusionReason
EXCLUSION_REASON_SELF: ExclusionReason
EXCLUSION_REASON_PRIVACY_SETTINGS: ExclusionReason
EXCLUSION_REASON_AGE_RESTRICTED: ExclusionReason
EXCLUSION_REASON_AUDIENCE_RESTRICTED: ExclusionReason
EXCLUSION_REASON_SAFETY_LABEL: ExclusionReason
EXCLUSION_REASON_LOW_TRUST: ExclusionReason
EXCLUSION_REASON_LANGUAGE_MISMATCH: ExclusionReason
EXCLUSION_REASON_UNAVAILABLE: ExclusionReason
EXCLUSION_REASON_FREQUENCY_CAP: ExclusionReason
EXCLUSION_REASON_SENSITIVE_TOPIC: ExclusionReason
EXCLUSION_REASON_NOT_OPEN_TO_CONNECT: ExclusionReason

class EntityRef(_message.Message):
    __slots__ = ("type", "id")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    type: EntityType
    id: str
    def __init__(self, type: _Optional[_Union[EntityType, str]] = ..., id: _Optional[str] = ...) -> None: ...

class TimeWindow(_message.Message):
    __slots__ = ("start", "end")
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    start: _timestamp_pb2.Timestamp
    end: _timestamp_pb2.Timestamp
    def __init__(self, start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class PageRequest(_message.Message):
    __slots__ = ("page_size", "page_token")
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    page_size: int
    page_token: str
    def __init__(self, page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class PageResponse(_message.Message):
    __slots__ = ("next_page_token", "total_estimate")
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_ESTIMATE_FIELD_NUMBER: _ClassVar[int]
    next_page_token: str
    total_estimate: int
    def __init__(self, next_page_token: _Optional[str] = ..., total_estimate: _Optional[int] = ...) -> None: ...

class RequestContext(_message.Message):
    __slots__ = ("request_id", "tenant_id", "surface", "locale", "country", "device_type", "app_version", "session_id", "request_time", "attributes")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FIELD_NUMBER: _ClassVar[int]
    LOCALE_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    DEVICE_TYPE_FIELD_NUMBER: _ClassVar[int]
    APP_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_TIME_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    tenant_id: str
    surface: Surface
    locale: str
    country: str
    device_type: str
    app_version: str
    session_id: str
    request_time: _timestamp_pb2.Timestamp
    attributes: _containers.ScalarMap[str, str]
    def __init__(self, request_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., surface: _Optional[_Union[Surface, str]] = ..., locale: _Optional[str] = ..., country: _Optional[str] = ..., device_type: _Optional[str] = ..., app_version: _Optional[str] = ..., session_id: _Optional[str] = ..., request_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Embedding(_message.Message):
    __slots__ = ("model_id", "version", "values")
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    version: str
    values: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, model_id: _Optional[str] = ..., version: _Optional[str] = ..., values: _Optional[_Iterable[float]] = ...) -> None: ...

class TopicAffinity(_message.Message):
    __slots__ = ("topic_id", "label", "weight", "source", "sensitivity", "updated_at")
    TOPIC_ID_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    topic_id: str
    label: str
    weight: float
    source: AffinitySource
    sensitivity: Sensitivity
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, topic_id: _Optional[str] = ..., label: _Optional[str] = ..., weight: _Optional[float] = ..., source: _Optional[_Union[AffinitySource, str]] = ..., sensitivity: _Optional[_Union[Sensitivity, str]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Reason(_message.Message):
    __slots__ = ("code", "detail", "contribution", "evidence")
    CODE_FIELD_NUMBER: _ClassVar[int]
    DETAIL_FIELD_NUMBER: _ClassVar[int]
    CONTRIBUTION_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    code: ReasonCode
    detail: str
    contribution: float
    evidence: _containers.RepeatedCompositeFieldContainer[EntityRef]
    def __init__(self, code: _Optional[_Union[ReasonCode, str]] = ..., detail: _Optional[str] = ..., contribution: _Optional[float] = ..., evidence: _Optional[_Iterable[_Union[EntityRef, _Mapping]]] = ...) -> None: ...

class Explanation(_message.Message):
    __slots__ = ("reasons",)
    REASONS_FIELD_NUMBER: _ClassVar[int]
    reasons: _containers.RepeatedCompositeFieldContainer[Reason]
    def __init__(self, reasons: _Optional[_Iterable[_Union[Reason, _Mapping]]] = ...) -> None: ...

class ModelInfo(_message.Message):
    __slots__ = ("model_id", "model_version", "experiment_id", "variant")
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    model_version: str
    experiment_id: str
    variant: str
    def __init__(self, model_id: _Optional[str] = ..., model_version: _Optional[str] = ..., experiment_id: _Optional[str] = ..., variant: _Optional[str] = ...) -> None: ...
