from oowlet.gen.eventlayer.basepb import base_pb2 as _base_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BehaviorUpdatedEvent(_message.Message):
    __slots__ = ("base", "user_id", "behavior_type", "resource_id", "resource_type", "duration_ms", "feature_vector", "session_id", "device_id", "geo_location")
    class FeatureVectorEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    BASE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    BEHAVIOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    FEATURE_VECTOR_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    GEO_LOCATION_FIELD_NUMBER: _ClassVar[int]
    base: _base_pb2.BaseEvent
    user_id: str
    behavior_type: str
    resource_id: str
    resource_type: str
    duration_ms: int
    feature_vector: _containers.ScalarMap[str, float]
    session_id: str
    device_id: str
    geo_location: str
    def __init__(self, base: _Optional[_Union[_base_pb2.BaseEvent, _Mapping]] = ..., user_id: _Optional[str] = ..., behavior_type: _Optional[str] = ..., resource_id: _Optional[str] = ..., resource_type: _Optional[str] = ..., duration_ms: _Optional[int] = ..., feature_vector: _Optional[_Mapping[str, float]] = ..., session_id: _Optional[str] = ..., device_id: _Optional[str] = ..., geo_location: _Optional[str] = ...) -> None: ...

class PreferenceSignalEvent(_message.Message):
    __slots__ = ("base", "user_id", "preference_type", "preference_value", "strength", "action")
    BASE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PREFERENCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    PREFERENCE_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    base: _base_pb2.BaseEvent
    user_id: str
    preference_type: str
    preference_value: str
    strength: float
    action: str
    def __init__(self, base: _Optional[_Union[_base_pb2.BaseEvent, _Mapping]] = ..., user_id: _Optional[str] = ..., preference_type: _Optional[str] = ..., preference_value: _Optional[str] = ..., strength: _Optional[float] = ..., action: _Optional[str] = ...) -> None: ...

class AnomalyDetectedEvent(_message.Message):
    __slots__ = ("base", "user_id", "anomaly_type", "anomaly_score", "description", "evidence")
    BASE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ANOMALY_TYPE_FIELD_NUMBER: _ClassVar[int]
    ANOMALY_SCORE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    base: _base_pb2.BaseEvent
    user_id: str
    anomaly_type: str
    anomaly_score: float
    description: str
    evidence: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, base: _Optional[_Union[_base_pb2.BaseEvent, _Mapping]] = ..., user_id: _Optional[str] = ..., anomaly_type: _Optional[str] = ..., anomaly_score: _Optional[float] = ..., description: _Optional[str] = ..., evidence: _Optional[_Iterable[str]] = ...) -> None: ...
