"""Eligibility: may this content / this person be recommended to this user?

One set of rules, used before ranking by both engines and by
CheckEligibility, so a candidate the rules exclude is never scored, explained
or returned. Each check returns the ExclusionReasons that apply; empty means
eligible.
"""

from __future__ import annotations

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.profilepb import profile_pb2 as ppb

from ..config import PolicySettings
from ..context import RecContext
from ..domain import ContentRecord, UserRecord
from ..intelligence.hub import UserState

X = cpb  # ExclusionReason values live in common

# Reasons that make an item unshowable, as opposed to "not now" (already seen,
# frequency cap, dismissed): Explain refuses only for these.
HARD = frozenset({X.EXCLUSION_REASON_BLOCKED, X.EXCLUSION_REASON_UNAVAILABLE, X.EXCLUSION_REASON_PRIVACY_SETTINGS,
                  X.EXCLUSION_REASON_AGE_RESTRICTED, X.EXCLUSION_REASON_AUDIENCE_RESTRICTED,
                  X.EXCLUSION_REASON_SAFETY_LABEL, X.EXCLUSION_REASON_SELF})


def viewer_country(st: UserState, ctx: RecContext) -> str:
    return (st.user.country or ctx.country or "").upper()


def check_content(st: UserState, item: ContentRecord | None, ctx: RecContext, p: PolicySettings,
                  creator: UserRecord | None = None) -> list[int]:
    if item is None:
        return [X.EXCLUSION_REASON_UNAVAILABLE]
    r: list[int] = []
    viewer = st.user
    if item.status != ctpb.CONTENT_STATUS_ACTIVE:
        r.append(X.EXCLUSION_REASON_UNAVAILABLE)
    if item.creator_id == viewer.user_id:
        r.append(X.EXCLUSION_REASON_SELF)
    # visibility: who may see the item at all
    vis = item.visibility
    if vis in (ctpb.VISIBILITY_UNSPECIFIED, ctpb.VISIBILITY_PRIVATE, ctpb.VISIBILITY_UNLISTED):
        r.append(X.EXCLUSION_REASON_PRIVACY_SETTINGS)
    elif vis == ctpb.VISIBILITY_FOLLOWERS and item.creator_id not in st.following and item.creator_id not in st.connections:
        r.append(X.EXCLUSION_REASON_AUDIENCE_RESTRICTED)
    elif vis == ctpb.VISIBILITY_CONNECTIONS and item.creator_id not in st.connections:
        r.append(X.EXCLUSION_REASON_AUDIENCE_RESTRICTED)
    elif vis == ctpb.VISIBILITY_COMMUNITY and (not item.community_id or item.community_id not in st.communities):
        r.append(X.EXCLUSION_REASON_AUDIENCE_RESTRICTED)
    if item.creator_id in st.blocked or (creator is not None and viewer.user_id in creator.preferences.blocked_user_ids):
        r.append(X.EXCLUSION_REASON_BLOCKED)
    prefs = st.prefs
    if (item.creator_id in st.muted_users
            or item.kind in prefs.muted_kinds
            or any(t.topic_id in prefs.muted_topic_ids for t in item.topics)):
        r.append(X.EXCLUSION_REASON_MUTED)
    # age: adult-only content never reaches a minor or an unknown age;
    # content whose audience is unknown (legacy producers) reaches adults only
    if item.adults_only and (not viewer.is_adult or prefs.max_maturity != ppb.MATURITY_LEVEL_MATURE):
        r.append(X.EXCLUSION_REASON_AGE_RESTRICTED)
    elif item.audience_unknown and not viewer.is_adult:
        r.append(X.EXCLUSION_REASON_AGE_RESTRICTED)
    country = viewer_country(st, ctx)
    if item.allowed_countries and country not in {c.upper() for c in item.allowed_countries}:
        r.append(X.EXCLUSION_REASON_AUDIENCE_RESTRICTED)
    if country and country in {c.upper() for c in item.blocked_countries}:
        r.append(X.EXCLUSION_REASON_AUDIENCE_RESTRICTED)
    blocked_labels = set(p.blocked_safety_labels)
    if any(lbl in blocked_labels and conf >= p.safety_label_threshold for lbl, conf in item.safety_labels):
        r.append(X.EXCLUSION_REASON_SAFETY_LABEL)
    if item.trust < p.min_content_trust or (creator is not None and creator.trust_score < p.min_user_trust):
        r.append(X.EXCLUSION_REASON_LOW_TRUST)
    langs = prefs.content_languages or viewer.languages
    if prefs.content_languages and item.language and \
            item.language.split("-", 1)[0].lower() not in {lang.split("-", 1)[0].lower() for lang in langs}:
        r.append(X.EXCLUSION_REASON_LANGUAGE_MISMATCH)
    if item.content_id in st.dismissed:
        r.append(X.EXCLUSION_REASON_DISMISSED)
    elif item.content_id in st.consumed:
        r.append(X.EXCLUSION_REASON_ALREADY_SEEN)
    elif (st.impressions.get(item.content_id, 0) >= p.frequency_cap
          and item.content_id not in st.engaged_recently):
        r.append(X.EXCLUSION_REASON_FREQUENCY_CAP)
    return _dedup(r)


def check_person(st: UserState, other: UserRecord | None, other_known: bool, p: PolicySettings,
                 purpose: int = 0) -> list[int]:
    viewer = st.user
    if other is None or not other_known:
        return [X.EXCLUSION_REASON_UNAVAILABLE]
    r: list[int] = []
    oid = other.user_id
    if oid == viewer.user_id:
        r.append(X.EXCLUSION_REASON_SELF)
    if oid in st.blocked or viewer.user_id in other.preferences.blocked_user_ids:
        r.append(X.EXCLUSION_REASON_BLOCKED)
    if oid in st.muted_users:
        r.append(X.EXCLUSION_REASON_MUTED)
    if oid in st.connections:
        r.append(X.EXCLUSION_REASON_ALREADY_CONNECTED)
    if oid in st.requests_out or oid in st.requests_in:
        r.append(X.EXCLUSION_REASON_REQUEST_PENDING)
    if oid in st.dismissed_users:
        r.append(X.EXCLUSION_REASON_DISMISSED)
    if not other.privacy.discoverable_in_suggestions:
        r.append(X.EXCLUSION_REASON_PRIVACY_SETTINGS)
    if not other.preferences.open_to_connections:
        r.append(X.EXCLUSION_REASON_NOT_OPEN_TO_CONNECT)
    elif purpose and other.preferences.connection_purposes and purpose not in other.preferences.connection_purposes:
        r.append(X.EXCLUSION_REASON_NOT_OPEN_TO_CONNECT)
    # adults and minors are never suggested to each other; unknown age counts as minor
    if viewer.is_adult != other.is_adult:
        r.append(X.EXCLUSION_REASON_AGE_RESTRICTED)
    if other.trust_score < p.min_user_trust:
        r.append(X.EXCLUSION_REASON_LOW_TRUST)
    vc, oc = viewer.country.upper(), other.country.upper()
    if (other.preferences.same_country_only or viewer.preferences.same_country_only) and (not vc or vc != oc):
        r.append(X.EXCLUSION_REASON_AUDIENCE_RESTRICTED)
    return _dedup(r)


def _dedup(r: list[int]) -> list[int]:
    return list(dict.fromkeys(r))
