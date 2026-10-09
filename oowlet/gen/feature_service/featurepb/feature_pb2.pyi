from oowlet.gen.feature_service.fscommonpb import fs_common_pb2 as _fs_common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FeatureSetRequest(_message.Message):
    __slots__ = ("entity_id", "entity_type", "caller", "refresh_if_stale")
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    REFRESH_IF_STALE_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    entity_type: str
    caller: _fs_common_pb2.CallerContext
    refresh_if_stale: bool
    def __init__(self, entity_id: _Optional[str] = ..., entity_type: _Optional[str] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ..., refresh_if_stale: bool = ...) -> None: ...

class FeatureSetResponse(_message.Message):
    __slots__ = ("status", "feature_set", "was_cached")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    FEATURE_SET_FIELD_NUMBER: _ClassVar[int]
    WAS_CACHED_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    feature_set: _fs_common_pb2.FeatureSet
    was_cached: bool
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., feature_set: _Optional[_Union[_fs_common_pb2.FeatureSet, _Mapping]] = ..., was_cached: bool = ...) -> None: ...

class FeaturesRequest(_message.Message):
    __slots__ = ("entity_id", "entity_type", "feature_ids", "caller")
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    FEATURE_IDS_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    entity_type: str
    feature_ids: _containers.RepeatedScalarFieldContainer[str]
    caller: _fs_common_pb2.CallerContext
    def __init__(self, entity_id: _Optional[str] = ..., entity_type: _Optional[str] = ..., feature_ids: _Optional[_Iterable[str]] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ...) -> None: ...

class FeaturesResponse(_message.Message):
    __slots__ = ("status", "entity_id", "features", "missing_feature_ids", "was_cached")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    MISSING_FEATURE_IDS_FIELD_NUMBER: _ClassVar[int]
    WAS_CACHED_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    entity_id: str
    features: _containers.RepeatedCompositeFieldContainer[_fs_common_pb2.FeatureValue]
    missing_feature_ids: _containers.RepeatedScalarFieldContainer[str]
    was_cached: bool
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., entity_id: _Optional[str] = ..., features: _Optional[_Iterable[_Union[_fs_common_pb2.FeatureValue, _Mapping]]] = ..., missing_feature_ids: _Optional[_Iterable[str]] = ..., was_cached: bool = ...) -> None: ...

class BatchFeatureSetRequest(_message.Message):
    __slots__ = ("entities", "caller", "refresh_if_stale")
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    REFRESH_IF_STALE_FIELD_NUMBER: _ClassVar[int]
    entities: _containers.RepeatedCompositeFieldContainer[EntityRef]
    caller: _fs_common_pb2.CallerContext
    refresh_if_stale: bool
    def __init__(self, entities: _Optional[_Iterable[_Union[EntityRef, _Mapping]]] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ..., refresh_if_stale: bool = ...) -> None: ...

class EntityRef(_message.Message):
    __slots__ = ("entity_id", "entity_type")
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    entity_type: str
    def __init__(self, entity_id: _Optional[str] = ..., entity_type: _Optional[str] = ...) -> None: ...

class BatchFeatureSetResponse(_message.Message):
    __slots__ = ("status", "results", "latency_ms", "hit_count", "miss_count")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    HIT_COUNT_FIELD_NUMBER: _ClassVar[int]
    MISS_COUNT_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    results: _containers.RepeatedCompositeFieldContainer[EntityFeatureSetResult]
    latency_ms: int
    hit_count: int
    miss_count: int
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., results: _Optional[_Iterable[_Union[EntityFeatureSetResult, _Mapping]]] = ..., latency_ms: _Optional[int] = ..., hit_count: _Optional[int] = ..., miss_count: _Optional[int] = ...) -> None: ...

class EntityFeatureSetResult(_message.Message):
    __slots__ = ("entity_id", "entity_type", "feature_set", "success", "error", "was_cached")
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    FEATURE_SET_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    WAS_CACHED_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    entity_type: str
    feature_set: _fs_common_pb2.FeatureSet
    success: bool
    error: str
    was_cached: bool
    def __init__(self, entity_id: _Optional[str] = ..., entity_type: _Optional[str] = ..., feature_set: _Optional[_Union[_fs_common_pb2.FeatureSet, _Mapping]] = ..., success: bool = ..., error: _Optional[str] = ..., was_cached: bool = ...) -> None: ...

class BatchFeaturesRequest(_message.Message):
    __slots__ = ("entities", "feature_ids", "caller")
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    FEATURE_IDS_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    entities: _containers.RepeatedCompositeFieldContainer[EntityRef]
    feature_ids: _containers.RepeatedScalarFieldContainer[str]
    caller: _fs_common_pb2.CallerContext
    def __init__(self, entities: _Optional[_Iterable[_Union[EntityRef, _Mapping]]] = ..., feature_ids: _Optional[_Iterable[str]] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ...) -> None: ...

class BatchFeaturesResponse(_message.Message):
    __slots__ = ("status", "results", "latency_ms")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    results: _containers.RepeatedCompositeFieldContainer[EntityFeaturesResult]
    latency_ms: int
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., results: _Optional[_Iterable[_Union[EntityFeaturesResult, _Mapping]]] = ..., latency_ms: _Optional[int] = ...) -> None: ...

class EntityFeaturesResult(_message.Message):
    __slots__ = ("entity_id", "features", "missing_feature_ids", "success", "error")
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    MISSING_FEATURE_IDS_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    features: _containers.RepeatedCompositeFieldContainer[_fs_common_pb2.FeatureValue]
    missing_feature_ids: _containers.RepeatedScalarFieldContainer[str]
    success: bool
    error: str
    def __init__(self, entity_id: _Optional[str] = ..., features: _Optional[_Iterable[_Union[_fs_common_pb2.FeatureValue, _Mapping]]] = ..., missing_feature_ids: _Optional[_Iterable[str]] = ..., success: bool = ..., error: _Optional[str] = ...) -> None: ...

class FeatureStreamRequest(_message.Message):
    __slots__ = ("entities", "feature_ids", "caller", "min_staleness_ms")
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    FEATURE_IDS_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    MIN_STALENESS_MS_FIELD_NUMBER: _ClassVar[int]
    entities: _containers.RepeatedCompositeFieldContainer[EntityRef]
    feature_ids: _containers.RepeatedScalarFieldContainer[str]
    caller: _fs_common_pb2.CallerContext
    min_staleness_ms: int
    def __init__(self, entities: _Optional[_Iterable[_Union[EntityRef, _Mapping]]] = ..., feature_ids: _Optional[_Iterable[str]] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ..., min_staleness_ms: _Optional[int] = ...) -> None: ...

class FeatureUpdateEvent(_message.Message):
    __slots__ = ("event_id", "entity_id", "entity_type", "event_type", "updated_features", "event_at_ms")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    UPDATED_FEATURES_FIELD_NUMBER: _ClassVar[int]
    EVENT_AT_MS_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    entity_id: str
    entity_type: str
    event_type: str
    updated_features: _containers.RepeatedCompositeFieldContainer[_fs_common_pb2.FeatureValue]
    event_at_ms: int
    def __init__(self, event_id: _Optional[str] = ..., entity_id: _Optional[str] = ..., entity_type: _Optional[str] = ..., event_type: _Optional[str] = ..., updated_features: _Optional[_Iterable[_Union[_fs_common_pb2.FeatureValue, _Mapping]]] = ..., event_at_ms: _Optional[int] = ...) -> None: ...

class WriteFeatureSetRequest(_message.Message):
    __slots__ = ("feature_set", "caller", "overwrite", "pipeline_id")
    FEATURE_SET_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    OVERWRITE_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    feature_set: _fs_common_pb2.FeatureSet
    caller: _fs_common_pb2.CallerContext
    overwrite: bool
    pipeline_id: str
    def __init__(self, feature_set: _Optional[_Union[_fs_common_pb2.FeatureSet, _Mapping]] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ..., overwrite: bool = ..., pipeline_id: _Optional[str] = ...) -> None: ...

class WriteFeatureSetResponse(_message.Message):
    __slots__ = ("status", "entity_id", "version", "is_new")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    IS_NEW_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    entity_id: str
    version: str
    is_new: bool
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., entity_id: _Optional[str] = ..., version: _Optional[str] = ..., is_new: bool = ...) -> None: ...

class WriteFeaturesRequest(_message.Message):
    __slots__ = ("entity_id", "entity_type", "features", "caller", "pipeline_id")
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    entity_type: str
    features: _containers.RepeatedCompositeFieldContainer[_fs_common_pb2.FeatureValue]
    caller: _fs_common_pb2.CallerContext
    pipeline_id: str
    def __init__(self, entity_id: _Optional[str] = ..., entity_type: _Optional[str] = ..., features: _Optional[_Iterable[_Union[_fs_common_pb2.FeatureValue, _Mapping]]] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ..., pipeline_id: _Optional[str] = ...) -> None: ...

class WriteFeaturesResponse(_message.Message):
    __slots__ = ("status", "written_count", "skipped_count", "skipped_feature_ids")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    WRITTEN_COUNT_FIELD_NUMBER: _ClassVar[int]
    SKIPPED_COUNT_FIELD_NUMBER: _ClassVar[int]
    SKIPPED_FEATURE_IDS_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    written_count: int
    skipped_count: int
    skipped_feature_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., written_count: _Optional[int] = ..., skipped_count: _Optional[int] = ..., skipped_feature_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class ListFeatureCatalogRequest(_message.Message):
    __slots__ = ("entity_type", "caller", "pagination")
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    entity_type: str
    caller: _fs_common_pb2.CallerContext
    pagination: _fs_common_pb2.PaginationRequest
    def __init__(self, entity_type: _Optional[str] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ..., pagination: _Optional[_Union[_fs_common_pb2.PaginationRequest, _Mapping]] = ...) -> None: ...

class ListFeatureCatalogResponse(_message.Message):
    __slots__ = ("status", "entries", "pagination")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    entries: _containers.RepeatedCompositeFieldContainer[FeatureCatalogEntry]
    pagination: _fs_common_pb2.PaginationResponse
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., entries: _Optional[_Iterable[_Union[FeatureCatalogEntry, _Mapping]]] = ..., pagination: _Optional[_Union[_fs_common_pb2.PaginationResponse, _Mapping]] = ...) -> None: ...

class SearchFeatureCatalogRequest(_message.Message):
    __slots__ = ("query", "entity_type", "tags", "data_type", "caller", "pagination")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    query: str
    entity_type: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    data_type: str
    caller: _fs_common_pb2.CallerContext
    pagination: _fs_common_pb2.PaginationRequest
    def __init__(self, query: _Optional[str] = ..., entity_type: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ..., data_type: _Optional[str] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ..., pagination: _Optional[_Union[_fs_common_pb2.PaginationRequest, _Mapping]] = ...) -> None: ...

class SearchFeatureCatalogResponse(_message.Message):
    __slots__ = ("status", "entries", "total", "pagination")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    entries: _containers.RepeatedCompositeFieldContainer[FeatureCatalogEntry]
    total: int
    pagination: _fs_common_pb2.PaginationResponse
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., entries: _Optional[_Iterable[_Union[FeatureCatalogEntry, _Mapping]]] = ..., total: _Optional[int] = ..., pagination: _Optional[_Union[_fs_common_pb2.PaginationResponse, _Mapping]] = ...) -> None: ...

class RegisterFeatureRequest(_message.Message):
    __slots__ = ("entry", "caller")
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    entry: FeatureCatalogEntry
    caller: _fs_common_pb2.CallerContext
    def __init__(self, entry: _Optional[_Union[FeatureCatalogEntry, _Mapping]] = ..., caller: _Optional[_Union[_fs_common_pb2.CallerContext, _Mapping]] = ...) -> None: ...

class RegisterFeatureResponse(_message.Message):
    __slots__ = ("status", "feature_id", "is_new")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    FEATURE_ID_FIELD_NUMBER: _ClassVar[int]
    IS_NEW_FIELD_NUMBER: _ClassVar[int]
    status: _fs_common_pb2.ResponseStatus
    feature_id: str
    is_new: bool
    def __init__(self, status: _Optional[_Union[_fs_common_pb2.ResponseStatus, _Mapping]] = ..., feature_id: _Optional[str] = ..., is_new: bool = ...) -> None: ...

class FeatureCatalogEntry(_message.Message):
    __slots__ = ("feature_id", "feature_name", "description", "entity_type", "data_type", "pipeline_stage", "source_module", "consumer_ids", "tags", "ttl_seconds", "version", "status", "registered_at_ms", "updated_at_ms")
    FEATURE_ID_FIELD_NUMBER: _ClassVar[int]
    FEATURE_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_STAGE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_MODULE_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_IDS_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    TTL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    REGISTERED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    feature_id: str
    feature_name: str
    description: str
    entity_type: str
    data_type: str
    pipeline_stage: str
    source_module: str
    consumer_ids: _containers.RepeatedScalarFieldContainer[str]
    tags: _containers.RepeatedScalarFieldContainer[str]
    ttl_seconds: int
    version: str
    status: str
    registered_at_ms: int
    updated_at_ms: int
    def __init__(self, feature_id: _Optional[str] = ..., feature_name: _Optional[str] = ..., description: _Optional[str] = ..., entity_type: _Optional[str] = ..., data_type: _Optional[str] = ..., pipeline_stage: _Optional[str] = ..., source_module: _Optional[str] = ..., consumer_ids: _Optional[_Iterable[str]] = ..., tags: _Optional[_Iterable[str]] = ..., ttl_seconds: _Optional[int] = ..., version: _Optional[str] = ..., status: _Optional[str] = ..., registered_at_ms: _Optional[int] = ..., updated_at_ms: _Optional[int] = ...) -> None: ...

class FeatureHealthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FeatureHealthResponse(_message.Message):
    __slots__ = ("healthy", "status", "uptime_seconds", "checks")
    class ChecksEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    HEALTHY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CHECKS_FIELD_NUMBER: _ClassVar[int]
    healthy: bool
    status: str
    uptime_seconds: int
    checks: _containers.ScalarMap[str, str]
    def __init__(self, healthy: bool = ..., status: _Optional[str] = ..., uptime_seconds: _Optional[int] = ..., checks: _Optional[_Mapping[str, str]] = ...) -> None: ...
