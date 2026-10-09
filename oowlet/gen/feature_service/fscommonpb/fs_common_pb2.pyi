from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PaginationRequest(_message.Message):
    __slots__ = ("page", "page_size", "cursor")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    page: int
    page_size: int
    cursor: str
    def __init__(self, page: _Optional[int] = ..., page_size: _Optional[int] = ..., cursor: _Optional[str] = ...) -> None: ...

class PaginationResponse(_message.Message):
    __slots__ = ("page", "page_size", "has_next", "next_cursor", "total_count")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    HAS_NEXT_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    page: int
    page_size: int
    has_next: bool
    next_cursor: str
    total_count: int
    def __init__(self, page: _Optional[int] = ..., page_size: _Optional[int] = ..., has_next: bool = ..., next_cursor: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class CallerContext(_message.Message):
    __slots__ = ("caller_id", "caller_service", "caller_env", "request_id", "trace_id", "is_internal", "auth_token")
    CALLER_ID_FIELD_NUMBER: _ClassVar[int]
    CALLER_SERVICE_FIELD_NUMBER: _ClassVar[int]
    CALLER_ENV_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    IS_INTERNAL_FIELD_NUMBER: _ClassVar[int]
    AUTH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    caller_id: str
    caller_service: str
    caller_env: str
    request_id: str
    trace_id: str
    is_internal: bool
    auth_token: str
    def __init__(self, caller_id: _Optional[str] = ..., caller_service: _Optional[str] = ..., caller_env: _Optional[str] = ..., request_id: _Optional[str] = ..., trace_id: _Optional[str] = ..., is_internal: bool = ..., auth_token: _Optional[str] = ...) -> None: ...

class ResponseStatus(_message.Message):
    __slots__ = ("success", "errors", "latency_ms", "pipeline_id", "request_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errors: _containers.RepeatedCompositeFieldContainer[ErrorDetail]
    latency_ms: int
    pipeline_id: str
    request_id: str
    def __init__(self, success: bool = ..., errors: _Optional[_Iterable[_Union[ErrorDetail, _Mapping]]] = ..., latency_ms: _Optional[int] = ..., pipeline_id: _Optional[str] = ..., request_id: _Optional[str] = ...) -> None: ...

class ErrorDetail(_message.Message):
    __slots__ = ("code", "message", "field")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    code: str
    message: str
    field: str
    def __init__(self, code: _Optional[str] = ..., message: _Optional[str] = ..., field: _Optional[str] = ...) -> None: ...

class FeatureValue(_message.Message):
    __slots__ = ("feature_id", "feature_name", "float_value", "int_value", "bool_value", "string_value", "vector_value", "list_value", "data_type", "computed_at_ms", "expires_at_ms", "version", "model_version")
    FEATURE_ID_FIELD_NUMBER: _ClassVar[int]
    FEATURE_NAME_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    VECTOR_VALUE_FIELD_NUMBER: _ClassVar[int]
    LIST_VALUE_FIELD_NUMBER: _ClassVar[int]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    COMPUTED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_MS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    feature_id: str
    feature_name: str
    float_value: float
    int_value: int
    bool_value: bool
    string_value: str
    vector_value: FloatVector
    list_value: StringList
    data_type: str
    computed_at_ms: int
    expires_at_ms: int
    version: str
    model_version: str
    def __init__(self, feature_id: _Optional[str] = ..., feature_name: _Optional[str] = ..., float_value: _Optional[float] = ..., int_value: _Optional[int] = ..., bool_value: bool = ..., string_value: _Optional[str] = ..., vector_value: _Optional[_Union[FloatVector, _Mapping]] = ..., list_value: _Optional[_Union[StringList, _Mapping]] = ..., data_type: _Optional[str] = ..., computed_at_ms: _Optional[int] = ..., expires_at_ms: _Optional[int] = ..., version: _Optional[str] = ..., model_version: _Optional[str] = ...) -> None: ...

class FloatVector(_message.Message):
    __slots__ = ("values", "dimension", "model_version")
    VALUES_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    dimension: int
    model_version: str
    def __init__(self, values: _Optional[_Iterable[float]] = ..., dimension: _Optional[int] = ..., model_version: _Optional[str] = ...) -> None: ...

class StringList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, values: _Optional[_Iterable[str]] = ...) -> None: ...

class FeatureSet(_message.Message):
    __slots__ = ("entity_id", "entity_type", "features", "version", "computed_at_ms", "expires_at_ms", "pipeline_id", "is_partial", "missing_feature_ids")
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    COMPUTED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_MS_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    IS_PARTIAL_FIELD_NUMBER: _ClassVar[int]
    MISSING_FEATURE_IDS_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    entity_type: str
    features: _containers.RepeatedCompositeFieldContainer[FeatureValue]
    version: str
    computed_at_ms: int
    expires_at_ms: int
    pipeline_id: str
    is_partial: bool
    missing_feature_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, entity_id: _Optional[str] = ..., entity_type: _Optional[str] = ..., features: _Optional[_Iterable[_Union[FeatureValue, _Mapping]]] = ..., version: _Optional[str] = ..., computed_at_ms: _Optional[int] = ..., expires_at_ms: _Optional[int] = ..., pipeline_id: _Optional[str] = ..., is_partial: bool = ..., missing_feature_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class EntityTypeRef(_message.Message):
    __slots__ = ("entity_type",)
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    entity_type: str
    def __init__(self, entity_type: _Optional[str] = ...) -> None: ...
