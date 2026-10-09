import datetime

from google.protobuf import field_mask_pb2 as _field_mask_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from oowlet.gen.recommenduc.contentpb import content_pb2 as _content_pb2
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as _engagement_pb2
from oowlet.gen.recommenduc.graphpb import graph_pb2 as _graph_pb2
from oowlet.gen.recommenduc.profilepb import profile_pb2 as _profile_pb2
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as _recommendation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChangeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CHANGE_TYPE_UNSPECIFIED: _ClassVar[ChangeType]
    CHANGE_TYPE_UPSERTED: _ClassVar[ChangeType]
    CHANGE_TYPE_REMOVED: _ClassVar[ChangeType]
CHANGE_TYPE_UNSPECIFIED: ChangeType
CHANGE_TYPE_UPSERTED: ChangeType
CHANGE_TYPE_REMOVED: ChangeType

class EngagementRecorded(_message.Message):
    __slots__ = ("events",)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[_engagement_pb2.EngagementEvent]
    def __init__(self, events: _Optional[_Iterable[_Union[_engagement_pb2.EngagementEvent, _Mapping]]] = ...) -> None: ...

class ContentChanged(_message.Message):
    __slots__ = ("change", "item")
    CHANGE_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    change: ChangeType
    item: _content_pb2.ContentItem
    def __init__(self, change: _Optional[_Union[ChangeType, str]] = ..., item: _Optional[_Union[_content_pb2.ContentItem, _Mapping]] = ...) -> None: ...

class GraphChanged(_message.Message):
    __slots__ = ("upserted", "removed")
    UPSERTED_FIELD_NUMBER: _ClassVar[int]
    REMOVED_FIELD_NUMBER: _ClassVar[int]
    upserted: _containers.RepeatedCompositeFieldContainer[_graph_pb2.Edge]
    removed: _containers.RepeatedCompositeFieldContainer[_graph_pb2.Edge]
    def __init__(self, upserted: _Optional[_Iterable[_Union[_graph_pb2.Edge, _Mapping]]] = ..., removed: _Optional[_Iterable[_Union[_graph_pb2.Edge, _Mapping]]] = ...) -> None: ...

class ProfileChanged(_message.Message):
    __slots__ = ("user_id", "changed", "version", "attributes")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CHANGED_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    changed: _field_mask_pb2.FieldMask
    version: int
    attributes: _profile_pb2.UserAttributes
    def __init__(self, user_id: _Optional[str] = ..., changed: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ..., version: _Optional[int] = ..., attributes: _Optional[_Union[_profile_pb2.UserAttributes, _Mapping]] = ...) -> None: ...

class RecommendationServed(_message.Message):
    __slots__ = ("served",)
    SERVED_FIELD_NUMBER: _ClassVar[int]
    served: _recommendation_pb2.ServedRecommendation
    def __init__(self, served: _Optional[_Union[_recommendation_pb2.ServedRecommendation, _Mapping]] = ...) -> None: ...

class FeedbackReceived(_message.Message):
    __slots__ = ("feedback",)
    FEEDBACK_FIELD_NUMBER: _ClassVar[int]
    feedback: _recommendation_pb2.FeedbackRequest
    def __init__(self, feedback: _Optional[_Union[_recommendation_pb2.FeedbackRequest, _Mapping]] = ...) -> None: ...

class UserDataErased(_message.Message):
    __slots__ = ("user_id", "erased_at")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ERASED_AT_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    erased_at: _timestamp_pb2.Timestamp
    def __init__(self, user_id: _Optional[str] = ..., erased_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
