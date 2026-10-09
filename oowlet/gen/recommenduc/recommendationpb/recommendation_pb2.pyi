import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from oowlet.gen.recommenduc.commonpb import common_pb2 as _common_pb2
from oowlet.gen.recommenduc.profilepb import profile_pb2 as _profile_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FeedbackType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FEEDBACK_TYPE_UNSPECIFIED: _ClassVar[FeedbackType]
    FEEDBACK_TYPE_NOT_INTERESTED: _ClassVar[FeedbackType]
    FEEDBACK_TYPE_SEE_MORE_LIKE_THIS: _ClassVar[FeedbackType]
    FEEDBACK_TYPE_SEE_LESS_FROM_CREATOR: _ClassVar[FeedbackType]
    FEEDBACK_TYPE_SEE_LESS_OF_TOPIC: _ClassVar[FeedbackType]
    FEEDBACK_TYPE_ALREADY_SEEN: _ClassVar[FeedbackType]
    FEEDBACK_TYPE_DONT_KNOW_PERSON: _ClassVar[FeedbackType]
    FEEDBACK_TYPE_ALREADY_KNOW_PERSON: _ClassVar[FeedbackType]
    FEEDBACK_TYPE_INAPPROPRIATE: _ClassVar[FeedbackType]
FEEDBACK_TYPE_UNSPECIFIED: FeedbackType
FEEDBACK_TYPE_NOT_INTERESTED: FeedbackType
FEEDBACK_TYPE_SEE_MORE_LIKE_THIS: FeedbackType
FEEDBACK_TYPE_SEE_LESS_FROM_CREATOR: FeedbackType
FEEDBACK_TYPE_SEE_LESS_OF_TOPIC: FeedbackType
FEEDBACK_TYPE_ALREADY_SEEN: FeedbackType
FEEDBACK_TYPE_DONT_KNOW_PERSON: FeedbackType
FEEDBACK_TYPE_ALREADY_KNOW_PERSON: FeedbackType
FEEDBACK_TYPE_INAPPROPRIATE: FeedbackType

class DiversityOptions(_message.Message):
    __slots__ = ("max_per_creator", "max_per_topic", "exploration_ratio")
    MAX_PER_CREATOR_FIELD_NUMBER: _ClassVar[int]
    MAX_PER_TOPIC_FIELD_NUMBER: _ClassVar[int]
    EXPLORATION_RATIO_FIELD_NUMBER: _ClassVar[int]
    max_per_creator: int
    max_per_topic: int
    exploration_ratio: float
    def __init__(self, max_per_creator: _Optional[int] = ..., max_per_topic: _Optional[int] = ..., exploration_ratio: _Optional[float] = ...) -> None: ...

class RecommendContentRequest(_message.Message):
    __slots__ = ("context", "user_id", "limit", "kinds", "topic_ids", "seed_content_id", "seed_creator_id", "exclude_content_ids", "page", "diversity", "include_explanations")
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    KINDS_FIELD_NUMBER: _ClassVar[int]
    TOPIC_IDS_FIELD_NUMBER: _ClassVar[int]
    SEED_CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    SEED_CREATOR_ID_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_CONTENT_IDS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    DIVERSITY_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_EXPLANATIONS_FIELD_NUMBER: _ClassVar[int]
    context: _common_pb2.RequestContext
    user_id: str
    limit: int
    kinds: _containers.RepeatedScalarFieldContainer[_common_pb2.ContentKind]
    topic_ids: _containers.RepeatedScalarFieldContainer[str]
    seed_content_id: str
    seed_creator_id: str
    exclude_content_ids: _containers.RepeatedScalarFieldContainer[str]
    page: _common_pb2.PageRequest
    diversity: DiversityOptions
    include_explanations: bool
    def __init__(self, context: _Optional[_Union[_common_pb2.RequestContext, _Mapping]] = ..., user_id: _Optional[str] = ..., limit: _Optional[int] = ..., kinds: _Optional[_Iterable[_Union[_common_pb2.ContentKind, str]]] = ..., topic_ids: _Optional[_Iterable[str]] = ..., seed_content_id: _Optional[str] = ..., seed_creator_id: _Optional[str] = ..., exclude_content_ids: _Optional[_Iterable[str]] = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ..., diversity: _Optional[_Union[DiversityOptions, _Mapping]] = ..., include_explanations: bool = ...) -> None: ...

class ContentRecommendation(_message.Message):
    __slots__ = ("content_id", "score", "rank", "candidate_sources", "explanation")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    RANK_FIELD_NUMBER: _ClassVar[int]
    CANDIDATE_SOURCES_FIELD_NUMBER: _ClassVar[int]
    EXPLANATION_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    score: float
    rank: int
    candidate_sources: _containers.RepeatedScalarFieldContainer[str]
    explanation: _common_pb2.Explanation
    def __init__(self, content_id: _Optional[str] = ..., score: _Optional[float] = ..., rank: _Optional[int] = ..., candidate_sources: _Optional[_Iterable[str]] = ..., explanation: _Optional[_Union[_common_pb2.Explanation, _Mapping]] = ...) -> None: ...

class RecommendContentResponse(_message.Message):
    __slots__ = ("recommendation_id", "items", "page", "model", "personalized", "generated_at")
    RECOMMENDATION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    PERSONALIZED_FIELD_NUMBER: _ClassVar[int]
    GENERATED_AT_FIELD_NUMBER: _ClassVar[int]
    recommendation_id: str
    items: _containers.RepeatedCompositeFieldContainer[ContentRecommendation]
    page: _common_pb2.PageResponse
    model: _common_pb2.ModelInfo
    personalized: bool
    generated_at: _timestamp_pb2.Timestamp
    def __init__(self, recommendation_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ContentRecommendation, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ..., model: _Optional[_Union[_common_pb2.ModelInfo, _Mapping]] = ..., personalized: bool = ..., generated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class RecommendUsersRequest(_message.Message):
    __slots__ = ("context", "user_id", "limit", "purpose", "exclude_user_ids", "seed_user_id", "community_id", "page", "include_explanations")
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    PURPOSE_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_USER_IDS_FIELD_NUMBER: _ClassVar[int]
    SEED_USER_ID_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_EXPLANATIONS_FIELD_NUMBER: _ClassVar[int]
    context: _common_pb2.RequestContext
    user_id: str
    limit: int
    purpose: _profile_pb2.ConnectionPurpose
    exclude_user_ids: _containers.RepeatedScalarFieldContainer[str]
    seed_user_id: str
    community_id: str
    page: _common_pb2.PageRequest
    include_explanations: bool
    def __init__(self, context: _Optional[_Union[_common_pb2.RequestContext, _Mapping]] = ..., user_id: _Optional[str] = ..., limit: _Optional[int] = ..., purpose: _Optional[_Union[_profile_pb2.ConnectionPurpose, str]] = ..., exclude_user_ids: _Optional[_Iterable[str]] = ..., seed_user_id: _Optional[str] = ..., community_id: _Optional[str] = ..., page: _Optional[_Union[_common_pb2.PageRequest, _Mapping]] = ..., include_explanations: bool = ...) -> None: ...

class UserRecommendation(_message.Message):
    __slots__ = ("user_id", "score", "rank", "mutual_connections", "shared_topic_ids", "candidate_sources", "explanation")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    RANK_FIELD_NUMBER: _ClassVar[int]
    MUTUAL_CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    SHARED_TOPIC_IDS_FIELD_NUMBER: _ClassVar[int]
    CANDIDATE_SOURCES_FIELD_NUMBER: _ClassVar[int]
    EXPLANATION_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    score: float
    rank: int
    mutual_connections: int
    shared_topic_ids: _containers.RepeatedScalarFieldContainer[str]
    candidate_sources: _containers.RepeatedScalarFieldContainer[str]
    explanation: _common_pb2.Explanation
    def __init__(self, user_id: _Optional[str] = ..., score: _Optional[float] = ..., rank: _Optional[int] = ..., mutual_connections: _Optional[int] = ..., shared_topic_ids: _Optional[_Iterable[str]] = ..., candidate_sources: _Optional[_Iterable[str]] = ..., explanation: _Optional[_Union[_common_pb2.Explanation, _Mapping]] = ...) -> None: ...

class RecommendUsersResponse(_message.Message):
    __slots__ = ("recommendation_id", "items", "page", "model", "generated_at")
    RECOMMENDATION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    GENERATED_AT_FIELD_NUMBER: _ClassVar[int]
    recommendation_id: str
    items: _containers.RepeatedCompositeFieldContainer[UserRecommendation]
    page: _common_pb2.PageResponse
    model: _common_pb2.ModelInfo
    generated_at: _timestamp_pb2.Timestamp
    def __init__(self, recommendation_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[UserRecommendation, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageResponse, _Mapping]] = ..., model: _Optional[_Union[_common_pb2.ModelInfo, _Mapping]] = ..., generated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CheckEligibilityRequest(_message.Message):
    __slots__ = ("context", "user_id", "candidates", "include_score", "include_explanations")
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_SCORE_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_EXPLANATIONS_FIELD_NUMBER: _ClassVar[int]
    context: _common_pb2.RequestContext
    user_id: str
    candidates: _containers.RepeatedCompositeFieldContainer[_common_pb2.EntityRef]
    include_score: bool
    include_explanations: bool
    def __init__(self, context: _Optional[_Union[_common_pb2.RequestContext, _Mapping]] = ..., user_id: _Optional[str] = ..., candidates: _Optional[_Iterable[_Union[_common_pb2.EntityRef, _Mapping]]] = ..., include_score: bool = ..., include_explanations: bool = ...) -> None: ...

class EligibilityResult(_message.Message):
    __slots__ = ("candidate", "eligible", "reasons", "score", "explanation")
    CANDIDATE_FIELD_NUMBER: _ClassVar[int]
    ELIGIBLE_FIELD_NUMBER: _ClassVar[int]
    REASONS_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    EXPLANATION_FIELD_NUMBER: _ClassVar[int]
    candidate: _common_pb2.EntityRef
    eligible: bool
    reasons: _containers.RepeatedScalarFieldContainer[_common_pb2.ExclusionReason]
    score: float
    explanation: _common_pb2.Explanation
    def __init__(self, candidate: _Optional[_Union[_common_pb2.EntityRef, _Mapping]] = ..., eligible: bool = ..., reasons: _Optional[_Iterable[_Union[_common_pb2.ExclusionReason, str]]] = ..., score: _Optional[float] = ..., explanation: _Optional[_Union[_common_pb2.Explanation, _Mapping]] = ...) -> None: ...

class CheckEligibilityResponse(_message.Message):
    __slots__ = ("results", "model")
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[EligibilityResult]
    model: _common_pb2.ModelInfo
    def __init__(self, results: _Optional[_Iterable[_Union[EligibilityResult, _Mapping]]] = ..., model: _Optional[_Union[_common_pb2.ModelInfo, _Mapping]] = ...) -> None: ...

class ExplainRequest(_message.Message):
    __slots__ = ("user_id", "recommendation_id", "item")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    recommendation_id: str
    item: _common_pb2.EntityRef
    def __init__(self, user_id: _Optional[str] = ..., recommendation_id: _Optional[str] = ..., item: _Optional[_Union[_common_pb2.EntityRef, _Mapping]] = ...) -> None: ...

class ExplainResponse(_message.Message):
    __slots__ = ("explanation",)
    EXPLANATION_FIELD_NUMBER: _ClassVar[int]
    explanation: _common_pb2.Explanation
    def __init__(self, explanation: _Optional[_Union[_common_pb2.Explanation, _Mapping]] = ...) -> None: ...

class FeedbackRequest(_message.Message):
    __slots__ = ("user_id", "recommendation_id", "item", "type", "topic_id", "comment", "given_at")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TOPIC_ID_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    GIVEN_AT_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    recommendation_id: str
    item: _common_pb2.EntityRef
    type: FeedbackType
    topic_id: str
    comment: str
    given_at: _timestamp_pb2.Timestamp
    def __init__(self, user_id: _Optional[str] = ..., recommendation_id: _Optional[str] = ..., item: _Optional[_Union[_common_pb2.EntityRef, _Mapping]] = ..., type: _Optional[_Union[FeedbackType, str]] = ..., topic_id: _Optional[str] = ..., comment: _Optional[str] = ..., given_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class FeedbackResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ServedItem(_message.Message):
    __slots__ = ("item", "rank", "score")
    ITEM_FIELD_NUMBER: _ClassVar[int]
    RANK_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    item: _common_pb2.EntityRef
    rank: int
    score: float
    def __init__(self, item: _Optional[_Union[_common_pb2.EntityRef, _Mapping]] = ..., rank: _Optional[int] = ..., score: _Optional[float] = ...) -> None: ...

class ServedRecommendation(_message.Message):
    __slots__ = ("recommendation_id", "user_id", "surface", "items", "model", "personalized", "served_at")
    RECOMMENDATION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    PERSONALIZED_FIELD_NUMBER: _ClassVar[int]
    SERVED_AT_FIELD_NUMBER: _ClassVar[int]
    recommendation_id: str
    user_id: str
    surface: _common_pb2.Surface
    items: _containers.RepeatedCompositeFieldContainer[ServedItem]
    model: _common_pb2.ModelInfo
    personalized: bool
    served_at: _timestamp_pb2.Timestamp
    def __init__(self, recommendation_id: _Optional[str] = ..., user_id: _Optional[str] = ..., surface: _Optional[_Union[_common_pb2.Surface, str]] = ..., items: _Optional[_Iterable[_Union[ServedItem, _Mapping]]] = ..., model: _Optional[_Union[_common_pb2.ModelInfo, _Mapping]] = ..., personalized: bool = ..., served_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
