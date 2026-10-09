import datetime

from google.protobuf import field_mask_pb2 as _field_mask_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from oowlet.gen.recommenduc.commonpb import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AccountType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ACCOUNT_TYPE_UNSPECIFIED: _ClassVar[AccountType]
    ACCOUNT_TYPE_PERSONAL: _ClassVar[AccountType]
    ACCOUNT_TYPE_CREATOR: _ClassVar[AccountType]
    ACCOUNT_TYPE_BUSINESS: _ClassVar[AccountType]

class MaturityLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MATURITY_LEVEL_UNSPECIFIED: _ClassVar[MaturityLevel]
    MATURITY_LEVEL_GENERAL: _ClassVar[MaturityLevel]
    MATURITY_LEVEL_MATURE: _ClassVar[MaturityLevel]

class ConnectionPurpose(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONNECTION_PURPOSE_UNSPECIFIED: _ClassVar[ConnectionPurpose]
    CONNECTION_PURPOSE_FRIENDS: _ClassVar[ConnectionPurpose]
    CONNECTION_PURPOSE_PROFESSIONAL: _ClassVar[ConnectionPurpose]
    CONNECTION_PURPOSE_MENTORSHIP: _ClassVar[ConnectionPurpose]
    CONNECTION_PURPOSE_COLLABORATION: _ClassVar[ConnectionPurpose]
    CONNECTION_PURPOSE_COMMUNITY: _ClassVar[ConnectionPurpose]
ACCOUNT_TYPE_UNSPECIFIED: AccountType
ACCOUNT_TYPE_PERSONAL: AccountType
ACCOUNT_TYPE_CREATOR: AccountType
ACCOUNT_TYPE_BUSINESS: AccountType
MATURITY_LEVEL_UNSPECIFIED: MaturityLevel
MATURITY_LEVEL_GENERAL: MaturityLevel
MATURITY_LEVEL_MATURE: MaturityLevel
CONNECTION_PURPOSE_UNSPECIFIED: ConnectionPurpose
CONNECTION_PURPOSE_FRIENDS: ConnectionPurpose
CONNECTION_PURPOSE_PROFESSIONAL: ConnectionPurpose
CONNECTION_PURPOSE_MENTORSHIP: ConnectionPurpose
CONNECTION_PURPOSE_COLLABORATION: ConnectionPurpose
CONNECTION_PURPOSE_COMMUNITY: ConnectionPurpose

class ConnectionPreferences(_message.Message):
    __slots__ = ("open_to_connections", "purposes", "languages", "same_country_only")
    OPEN_TO_CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    PURPOSES_FIELD_NUMBER: _ClassVar[int]
    LANGUAGES_FIELD_NUMBER: _ClassVar[int]
    SAME_COUNTRY_ONLY_FIELD_NUMBER: _ClassVar[int]
    open_to_connections: bool
    purposes: _containers.RepeatedScalarFieldContainer[ConnectionPurpose]
    languages: _containers.RepeatedScalarFieldContainer[str]
    same_country_only: bool
    def __init__(self, open_to_connections: bool = ..., purposes: _Optional[_Iterable[_Union[ConnectionPurpose, str]]] = ..., languages: _Optional[_Iterable[str]] = ..., same_country_only: bool = ...) -> None: ...

class Preferences(_message.Message):
    __slots__ = ("preferred_topic_ids", "muted_topic_ids", "muted_user_ids", "blocked_user_ids", "preferred_kinds", "muted_kinds", "content_languages", "max_maturity", "connections")
    PREFERRED_TOPIC_IDS_FIELD_NUMBER: _ClassVar[int]
    MUTED_TOPIC_IDS_FIELD_NUMBER: _ClassVar[int]
    MUTED_USER_IDS_FIELD_NUMBER: _ClassVar[int]
    BLOCKED_USER_IDS_FIELD_NUMBER: _ClassVar[int]
    PREFERRED_KINDS_FIELD_NUMBER: _ClassVar[int]
    MUTED_KINDS_FIELD_NUMBER: _ClassVar[int]
    CONTENT_LANGUAGES_FIELD_NUMBER: _ClassVar[int]
    MAX_MATURITY_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    preferred_topic_ids: _containers.RepeatedScalarFieldContainer[str]
    muted_topic_ids: _containers.RepeatedScalarFieldContainer[str]
    muted_user_ids: _containers.RepeatedScalarFieldContainer[str]
    blocked_user_ids: _containers.RepeatedScalarFieldContainer[str]
    preferred_kinds: _containers.RepeatedScalarFieldContainer[_common_pb2.ContentKind]
    muted_kinds: _containers.RepeatedScalarFieldContainer[_common_pb2.ContentKind]
    content_languages: _containers.RepeatedScalarFieldContainer[str]
    max_maturity: MaturityLevel
    connections: ConnectionPreferences
    def __init__(self, preferred_topic_ids: _Optional[_Iterable[str]] = ..., muted_topic_ids: _Optional[_Iterable[str]] = ..., muted_user_ids: _Optional[_Iterable[str]] = ..., blocked_user_ids: _Optional[_Iterable[str]] = ..., preferred_kinds: _Optional[_Iterable[_Union[_common_pb2.ContentKind, str]]] = ..., muted_kinds: _Optional[_Iterable[_Union[_common_pb2.ContentKind, str]]] = ..., content_languages: _Optional[_Iterable[str]] = ..., max_maturity: _Optional[_Union[MaturityLevel, str]] = ..., connections: _Optional[_Union[ConnectionPreferences, _Mapping]] = ...) -> None: ...

class PrivacySettings(_message.Message):
    __slots__ = ("personalization_enabled", "use_engagement_history", "discoverable_in_suggestions", "allow_mutual_connection_signal", "allow_location_signal", "show_activity_to_others", "allow_declared_sensitive_topics", "contribute_to_collaborative", "updated_at")
    PERSONALIZATION_ENABLED_FIELD_NUMBER: _ClassVar[int]
    USE_ENGAGEMENT_HISTORY_FIELD_NUMBER: _ClassVar[int]
    DISCOVERABLE_IN_SUGGESTIONS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MUTUAL_CONNECTION_SIGNAL_FIELD_NUMBER: _ClassVar[int]
    ALLOW_LOCATION_SIGNAL_FIELD_NUMBER: _ClassVar[int]
    SHOW_ACTIVITY_TO_OTHERS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_DECLARED_SENSITIVE_TOPICS_FIELD_NUMBER: _ClassVar[int]
    CONTRIBUTE_TO_COLLABORATIVE_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    personalization_enabled: bool
    use_engagement_history: bool
    discoverable_in_suggestions: bool
    allow_mutual_connection_signal: bool
    allow_location_signal: bool
    show_activity_to_others: bool
    allow_declared_sensitive_topics: bool
    contribute_to_collaborative: bool
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, personalization_enabled: bool = ..., use_engagement_history: bool = ..., discoverable_in_suggestions: bool = ..., allow_mutual_connection_signal: bool = ..., allow_location_signal: bool = ..., show_activity_to_others: bool = ..., allow_declared_sensitive_topics: bool = ..., contribute_to_collaborative: bool = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class UserProfile(_message.Message):
    __slots__ = ("user_id", "age_band", "account_type", "verified", "languages", "country", "region", "trust_score", "interests", "embeddings", "preferences", "privacy", "created_at", "updated_at", "version")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    AGE_BAND_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_TYPE_FIELD_NUMBER: _ClassVar[int]
    VERIFIED_FIELD_NUMBER: _ClassVar[int]
    LANGUAGES_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    TRUST_SCORE_FIELD_NUMBER: _ClassVar[int]
    INTERESTS_FIELD_NUMBER: _ClassVar[int]
    EMBEDDINGS_FIELD_NUMBER: _ClassVar[int]
    PREFERENCES_FIELD_NUMBER: _ClassVar[int]
    PRIVACY_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    age_band: _common_pb2.AgeBand
    account_type: AccountType
    verified: bool
    languages: _containers.RepeatedScalarFieldContainer[str]
    country: str
    region: str
    trust_score: float
    interests: _containers.RepeatedCompositeFieldContainer[_common_pb2.TopicAffinity]
    embeddings: _containers.RepeatedCompositeFieldContainer[_common_pb2.Embedding]
    preferences: Preferences
    privacy: PrivacySettings
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    version: int
    def __init__(self, user_id: _Optional[str] = ..., age_band: _Optional[_Union[_common_pb2.AgeBand, str]] = ..., account_type: _Optional[_Union[AccountType, str]] = ..., verified: bool = ..., languages: _Optional[_Iterable[str]] = ..., country: _Optional[str] = ..., region: _Optional[str] = ..., trust_score: _Optional[float] = ..., interests: _Optional[_Iterable[_Union[_common_pb2.TopicAffinity, _Mapping]]] = ..., embeddings: _Optional[_Iterable[_Union[_common_pb2.Embedding, _Mapping]]] = ..., preferences: _Optional[_Union[Preferences, _Mapping]] = ..., privacy: _Optional[_Union[PrivacySettings, _Mapping]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., version: _Optional[int] = ...) -> None: ...

class UserAttributes(_message.Message):
    __slots__ = ("age_band", "account_type", "verified", "languages", "country", "region", "trust_score", "created_at")
    AGE_BAND_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_TYPE_FIELD_NUMBER: _ClassVar[int]
    VERIFIED_FIELD_NUMBER: _ClassVar[int]
    LANGUAGES_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    TRUST_SCORE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    age_band: _common_pb2.AgeBand
    account_type: AccountType
    verified: bool
    languages: _containers.RepeatedScalarFieldContainer[str]
    country: str
    region: str
    trust_score: float
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, age_band: _Optional[_Union[_common_pb2.AgeBand, str]] = ..., account_type: _Optional[_Union[AccountType, str]] = ..., verified: bool = ..., languages: _Optional[_Iterable[str]] = ..., country: _Optional[str] = ..., region: _Optional[str] = ..., trust_score: _Optional[float] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetProfileRequest(_message.Message):
    __slots__ = ("user_id", "read_mask")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    READ_MASK_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    read_mask: _field_mask_pb2.FieldMask
    def __init__(self, user_id: _Optional[str] = ..., read_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...) -> None: ...

class GetProfileResponse(_message.Message):
    __slots__ = ("profile",)
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    profile: UserProfile
    def __init__(self, profile: _Optional[_Union[UserProfile, _Mapping]] = ...) -> None: ...

class UpdatePreferencesRequest(_message.Message):
    __slots__ = ("user_id", "preferences", "update_mask", "expected_version")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PREFERENCES_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_VERSION_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    preferences: Preferences
    update_mask: _field_mask_pb2.FieldMask
    expected_version: int
    def __init__(self, user_id: _Optional[str] = ..., preferences: _Optional[_Union[Preferences, _Mapping]] = ..., update_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ..., expected_version: _Optional[int] = ...) -> None: ...

class UpdatePreferencesResponse(_message.Message):
    __slots__ = ("profile",)
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    profile: UserProfile
    def __init__(self, profile: _Optional[_Union[UserProfile, _Mapping]] = ...) -> None: ...

class UpdatePrivacySettingsRequest(_message.Message):
    __slots__ = ("user_id", "privacy", "update_mask", "expected_version")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PRIVACY_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_VERSION_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    privacy: PrivacySettings
    update_mask: _field_mask_pb2.FieldMask
    expected_version: int
    def __init__(self, user_id: _Optional[str] = ..., privacy: _Optional[_Union[PrivacySettings, _Mapping]] = ..., update_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ..., expected_version: _Optional[int] = ...) -> None: ...

class UpdatePrivacySettingsResponse(_message.Message):
    __slots__ = ("profile",)
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    profile: UserProfile
    def __init__(self, profile: _Optional[_Union[UserProfile, _Mapping]] = ...) -> None: ...

class UpsertUserAttributesRequest(_message.Message):
    __slots__ = ("user_id", "attributes", "update_mask")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    attributes: UserAttributes
    update_mask: _field_mask_pb2.FieldMask
    def __init__(self, user_id: _Optional[str] = ..., attributes: _Optional[_Union[UserAttributes, _Mapping]] = ..., update_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...) -> None: ...

class UpsertUserAttributesResponse(_message.Message):
    __slots__ = ("version",)
    VERSION_FIELD_NUMBER: _ClassVar[int]
    version: int
    def __init__(self, version: _Optional[int] = ...) -> None: ...

class UpsertProfileFeaturesRequest(_message.Message):
    __slots__ = ("user_id", "inferred_interests", "embeddings", "expected_version")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    INFERRED_INTERESTS_FIELD_NUMBER: _ClassVar[int]
    EMBEDDINGS_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_VERSION_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    inferred_interests: _containers.RepeatedCompositeFieldContainer[_common_pb2.TopicAffinity]
    embeddings: _containers.RepeatedCompositeFieldContainer[_common_pb2.Embedding]
    expected_version: int
    def __init__(self, user_id: _Optional[str] = ..., inferred_interests: _Optional[_Iterable[_Union[_common_pb2.TopicAffinity, _Mapping]]] = ..., embeddings: _Optional[_Iterable[_Union[_common_pb2.Embedding, _Mapping]]] = ..., expected_version: _Optional[int] = ...) -> None: ...

class UpsertProfileFeaturesResponse(_message.Message):
    __slots__ = ("version",)
    VERSION_FIELD_NUMBER: _ClassVar[int]
    version: int
    def __init__(self, version: _Optional[int] = ...) -> None: ...

class DeleteUserDataRequest(_message.Message):
    __slots__ = ("user_id", "reason")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    reason: str
    def __init__(self, user_id: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class DeleteUserDataResponse(_message.Message):
    __slots__ = ("erased_at",)
    ERASED_AT_FIELD_NUMBER: _ClassVar[int]
    erased_at: _timestamp_pb2.Timestamp
    def __init__(self, erased_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
