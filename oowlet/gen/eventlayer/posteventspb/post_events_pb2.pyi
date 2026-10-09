from google.protobuf import timestamp_pb2 as _timestamp_pb2
from oowlet.gen.eventlayer.basepb import base_pb2 as _base_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PostCreatedEvent(_message.Message):
    __slots__ = ("base", "post_id", "user_id", "title", "content", "content_type", "tags", "initial_engagement_score")
    BASE_FIELD_NUMBER: _ClassVar[int]
    POST_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    INITIAL_ENGAGEMENT_SCORE_FIELD_NUMBER: _ClassVar[int]
    base: _base_pb2.BaseEvent
    post_id: str
    user_id: str
    title: str
    content: str
    content_type: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    initial_engagement_score: int
    def __init__(self, base: _Optional[_Union[_base_pb2.BaseEvent, _Mapping]] = ..., post_id: _Optional[str] = ..., user_id: _Optional[str] = ..., title: _Optional[str] = ..., content: _Optional[str] = ..., content_type: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ..., initial_engagement_score: _Optional[int] = ...) -> None: ...

class PostUpdatedEvent(_message.Message):
    __slots__ = ("base", "post_id", "user_id", "previous_state", "new_state")
    BASE_FIELD_NUMBER: _ClassVar[int]
    POST_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_STATE_FIELD_NUMBER: _ClassVar[int]
    NEW_STATE_FIELD_NUMBER: _ClassVar[int]
    base: _base_pb2.BaseEvent
    post_id: str
    user_id: str
    previous_state: str
    new_state: str
    def __init__(self, base: _Optional[_Union[_base_pb2.BaseEvent, _Mapping]] = ..., post_id: _Optional[str] = ..., user_id: _Optional[str] = ..., previous_state: _Optional[str] = ..., new_state: _Optional[str] = ...) -> None: ...

class PostDeletedEvent(_message.Message):
    __slots__ = ("base", "post_id", "user_id", "reason")
    BASE_FIELD_NUMBER: _ClassVar[int]
    POST_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    base: _base_pb2.BaseEvent
    post_id: str
    user_id: str
    reason: str
    def __init__(self, base: _Optional[_Union[_base_pb2.BaseEvent, _Mapping]] = ..., post_id: _Optional[str] = ..., user_id: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class PostEngagementEvent(_message.Message):
    __slots__ = ("base", "post_id", "user_id", "engagement_type", "timestamp_ms", "metadata_json")
    BASE_FIELD_NUMBER: _ClassVar[int]
    POST_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ENGAGEMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    METADATA_JSON_FIELD_NUMBER: _ClassVar[int]
    base: _base_pb2.BaseEvent
    post_id: str
    user_id: str
    engagement_type: str
    timestamp_ms: int
    metadata_json: str
    def __init__(self, base: _Optional[_Union[_base_pb2.BaseEvent, _Mapping]] = ..., post_id: _Optional[str] = ..., user_id: _Optional[str] = ..., engagement_type: _Optional[str] = ..., timestamp_ms: _Optional[int] = ..., metadata_json: _Optional[str] = ...) -> None: ...
