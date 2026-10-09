from google.protobuf import empty_pb2 as _empty_pb2
from oowlet.gen.eventlayer.basepb import base_pb2 as _base_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PublishEventRequest(_message.Message):
    __slots__ = ("event", "wait_for_persistence")
    EVENT_FIELD_NUMBER: _ClassVar[int]
    WAIT_FOR_PERSISTENCE_FIELD_NUMBER: _ClassVar[int]
    event: _base_pb2.EventEnvelope
    wait_for_persistence: bool
    def __init__(self, event: _Optional[_Union[_base_pb2.EventEnvelope, _Mapping]] = ..., wait_for_persistence: bool = ...) -> None: ...

class PublishEventResponse(_message.Message):
    __slots__ = ("event_id", "partition", "offset", "persisted")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    PERSISTED_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    partition: str
    offset: int
    persisted: bool
    def __init__(self, event_id: _Optional[str] = ..., partition: _Optional[str] = ..., offset: _Optional[int] = ..., persisted: bool = ...) -> None: ...

class SubscribeRequest(_message.Message):
    __slots__ = ("consumer_group", "topics", "from_offset", "auto_commit")
    CONSUMER_GROUP_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    FROM_OFFSET_FIELD_NUMBER: _ClassVar[int]
    AUTO_COMMIT_FIELD_NUMBER: _ClassVar[int]
    consumer_group: str
    topics: _containers.RepeatedScalarFieldContainer[str]
    from_offset: int
    auto_commit: bool
    def __init__(self, consumer_group: _Optional[str] = ..., topics: _Optional[_Iterable[str]] = ..., from_offset: _Optional[int] = ..., auto_commit: bool = ...) -> None: ...

class SubscribeResponse(_message.Message):
    __slots__ = ("event",)
    EVENT_FIELD_NUMBER: _ClassVar[int]
    event: _base_pb2.EventEnvelope
    def __init__(self, event: _Optional[_Union[_base_pb2.EventEnvelope, _Mapping]] = ...) -> None: ...

class GetEventStatusRequest(_message.Message):
    __slots__ = ("event_id",)
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    def __init__(self, event_id: _Optional[str] = ...) -> None: ...

class EventStatus(_message.Message):
    __slots__ = ("event_id", "status", "partition", "offset", "processed_by")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    PROCESSED_BY_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    status: str
    partition: str
    offset: int
    processed_by: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, event_id: _Optional[str] = ..., status: _Optional[str] = ..., partition: _Optional[str] = ..., offset: _Optional[int] = ..., processed_by: _Optional[_Iterable[str]] = ...) -> None: ...

class TopicsResponse(_message.Message):
    __slots__ = ("topics",)
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    topics: _containers.RepeatedCompositeFieldContainer[TopicInfo]
    def __init__(self, topics: _Optional[_Iterable[_Union[TopicInfo, _Mapping]]] = ...) -> None: ...

class TopicInfo(_message.Message):
    __slots__ = ("name", "partition_count", "total_messages")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARTITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    name: str
    partition_count: int
    total_messages: int
    def __init__(self, name: _Optional[str] = ..., partition_count: _Optional[int] = ..., total_messages: _Optional[int] = ...) -> None: ...
