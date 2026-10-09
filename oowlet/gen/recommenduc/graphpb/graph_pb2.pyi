import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from oowlet.gen.recommenduc.commonpb import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EdgeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EDGE_TYPE_UNSPECIFIED: _ClassVar[EdgeType]
    EDGE_TYPE_FOLLOWS: _ClassVar[EdgeType]
    EDGE_TYPE_CONNECTED: _ClassVar[EdgeType]
    EDGE_TYPE_CONNECTION_REQUESTED: _ClassVar[EdgeType]
    EDGE_TYPE_BLOCKED: _ClassVar[EdgeType]
    EDGE_TYPE_MUTED: _ClassVar[EdgeType]
    EDGE_TYPE_SAME_COMMUNITY: _ClassVar[EdgeType]
    EDGE_TYPE_INTERACTED: _ClassVar[EdgeType]
    EDGE_TYPE_COMMUNITY_MEMBER: _ClassVar[EdgeType]
EDGE_TYPE_UNSPECIFIED: EdgeType
EDGE_TYPE_FOLLOWS: EdgeType
EDGE_TYPE_CONNECTED: EdgeType
EDGE_TYPE_CONNECTION_REQUESTED: EdgeType
EDGE_TYPE_BLOCKED: EdgeType
EDGE_TYPE_MUTED: EdgeType
EDGE_TYPE_SAME_COMMUNITY: EdgeType
EDGE_TYPE_INTERACTED: EdgeType
EDGE_TYPE_COMMUNITY_MEMBER: EdgeType

class Edge(_message.Message):
    __slots__ = ("from_user_id", "to_user_id", "type", "weight", "created_at")
    FROM_USER_ID_FIELD_NUMBER: _ClassVar[int]
    TO_USER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    from_user_id: str
    to_user_id: str
    type: EdgeType
    weight: float
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, from_user_id: _Optional[str] = ..., to_user_id: _Optional[str] = ..., type: _Optional[_Union[EdgeType, str]] = ..., weight: _Optional[float] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class UpsertEdgesRequest(_message.Message):
    __slots__ = ("edges",)
    EDGES_FIELD_NUMBER: _ClassVar[int]
    edges: _containers.RepeatedCompositeFieldContainer[Edge]
    def __init__(self, edges: _Optional[_Iterable[_Union[Edge, _Mapping]]] = ...) -> None: ...

class UpsertEdgesResponse(_message.Message):
    __slots__ = ("upserted",)
    UPSERTED_FIELD_NUMBER: _ClassVar[int]
    upserted: int
    def __init__(self, upserted: _Optional[int] = ...) -> None: ...

class RemoveEdgesRequest(_message.Message):
    __slots__ = ("edges",)
    EDGES_FIELD_NUMBER: _ClassVar[int]
    edges: _containers.RepeatedCompositeFieldContainer[Edge]
    def __init__(self, edges: _Optional[_Iterable[_Union[Edge, _Mapping]]] = ...) -> None: ...

class RemoveEdgesResponse(_message.Message):
    __slots__ = ("removed",)
    REMOVED_FIELD_NUMBER: _ClassVar[int]
    removed: int
    def __init__(self, removed: _Optional[int] = ...) -> None: ...

class GetConnectionsRequest(_message.Message):
    __slots__ = ("user_id", "types", "page")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPES_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    types: _containers.RepeatedScalarFieldContainer[EdgeType]
    page: _common_pb2.PageRequest
    def __init__(self, user_id: _Optional[str] = ..., types: _Optional[_Iterable[_Union[EdgeType, str]]] = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class GetConnectionsResponse(_message.Message):
    __slots__ = ("edges", "page")
    EDGES_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    edges: _containers.RepeatedCompositeFieldContainer[Edge]
    page: _common_pb2.PageResponse
    def __init__(self, edges: _Optional[_Iterable[_Union[Edge, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ...) -> None: ...

class GetMutualConnectionsRequest(_message.Message):
    __slots__ = ("user_id", "other_user_id", "sample_size")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    OTHER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_SIZE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    other_user_id: str
    sample_size: int
    def __init__(self, user_id: _Optional[str] = ..., other_user_id: _Optional[str] = ..., sample_size: _Optional[int] = ...) -> None: ...

class GetMutualConnectionsResponse(_message.Message):
    __slots__ = ("count", "sample_user_ids")
    COUNT_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_USER_IDS_FIELD_NUMBER: _ClassVar[int]
    count: int
    sample_user_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, count: _Optional[int] = ..., sample_user_ids: _Optional[_Iterable[str]] = ...) -> None: ...
