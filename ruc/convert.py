"""Proto messages <-> internal records."""

from __future__ import annotations

import numpy as np
from google.protobuf import timestamp_pb2

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb
from oowlet.gen.recommenduc.graphpb import graph_pb2 as gpb
from oowlet.gen.recommenduc.profilepb import profile_pb2 as ppb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb

from .domain import (ContentRecord, Edge, Engagement, Preferences, Privacy, ServedRecommendation, Topic,
                     UserRecord, now)
from .intelligence.embeddings import unit
from .store.base import COUNTER_NAMES, Counters

MAX_ID = 128


class Invalid(ValueError):
    """A request field is unacceptable; becomes INVALID_ARGUMENT."""


def ts_of(t: timestamp_pb2.Timestamp, default: float = 0.0) -> float:
    return t.ToNanoseconds() / 1e9 if (t.seconds or t.nanos) else default


def to_ts(seconds: float) -> timestamp_pb2.Timestamp:
    t = timestamp_pb2.Timestamp()
    if seconds:
        t.FromNanoseconds(int(seconds * 1e9))
    return t


def _id(v: str, what: str) -> str:
    if not v or len(v) > MAX_ID:
        raise Invalid(f"{what} must be 1..{MAX_ID} characters")
    return v


# ── engagement ─────────────────────────────────────────────────────────────

def engagement_from_proto(e: epb.EngagementEvent, t_now: float | None = None) -> Engagement:
    t_now = t_now or now()
    _id(e.event_id, "event_id")
    _id(e.user_id, "user_id")
    if e.target.type not in (cpb.ENTITY_TYPE_CONTENT, cpb.ENTITY_TYPE_USER, cpb.ENTITY_TYPE_CREATOR):
        raise Invalid(f"event {e.event_id}: target must be CONTENT, USER or CREATOR")
    _id(e.target.id, "target.id")
    if e.type == epb.ENGAGEMENT_TYPE_UNSPECIFIED or e.type not in epb.EngagementType.values():
        raise Invalid(f"event {e.event_id}: unknown engagement type {e.type}")
    occurred = ts_of(e.occurred_at, t_now)
    if occurred > t_now + 300:
        raise Invalid(f"event {e.event_id}: occurred_at is in the future")
    if not 0.0 <= e.watch_fraction <= 1.0:
        raise Invalid(f"event {e.event_id}: watch_fraction must be 0..1")
    target_type = cpb.ENTITY_TYPE_USER if e.target.type == cpb.ENTITY_TYPE_CREATOR else e.target.type
    return Engagement(event_id=e.event_id, user_id=e.user_id, target_type=target_type, target_id=e.target.id,
                      type=e.type, ts=occurred, surface=e.surface, recommendation_id=e.recommendation_id[:64],
                      position=e.position, dwell_s=max(0.0, e.dwell.ToNanoseconds() / 1e9),
                      watch_fraction=e.watch_fraction, session_id=e.session_id[:128], device_type=e.device_type[:32],
                      country=e.country[:2].upper(), value=e.value, outcome=e.outcome[:64], reaction=e.reaction[:32])


def counters_to_proto(c: Counters) -> epb.EngagementCounters:
    m = epb.EngagementCounters(unique_users=c.unique_users, total_dwell_seconds=c.dwell_seconds)
    for k in COUNTER_NAMES:
        setattr(m, k, c.counts.get(k, 0))
    return m


# ── content ────────────────────────────────────────────────────────────────

def topic_from_proto(t: cpb.TopicAffinity) -> Topic:
    return Topic(topic_id=_id(t.topic_id, "topic_id"), weight=max(0.0, min(t.weight or 1.0, 1.0)),
                 sensitive=t.sensitivity == cpb.SENSITIVITY_SENSITIVE, label=t.label[:128], source=t.source)


def topic_to_proto(t: Topic) -> cpb.TopicAffinity:
    return cpb.TopicAffinity(topic_id=t.topic_id, label=t.label, weight=t.weight, source=t.source,
                             sensitivity=cpb.SENSITIVITY_SENSITIVE if t.sensitive else cpb.SENSITIVITY_GENERAL)


def embeddings_from_proto(es) -> dict[str, np.ndarray]:
    out = {}
    for e in es:
        if e.values and len(e.values) <= 4096:
            out[e.model_id] = unit(np.asarray(e.values, dtype=np.float32))
    return out


def content_from_proto(c: ctpb.ContentItem) -> ContentRecord:
    _id(c.content_id, "content_id")
    _id(c.creator_id, "creator_id")
    if len(c.topics) > 64 or len(c.hashtags) > 64 or len(c.safety_labels) > 64:
        raise Invalid(f"content {c.content_id}: too many topics / hashtags / labels (max 64)")
    return ContentRecord(
        content_id=c.content_id, creator_id=c.creator_id, kind=c.kind, language=c.language[:16],
        topics=[topic_from_proto(t) for t in c.topics], hashtags=[h[:64] for h in c.hashtags],
        embeddings=embeddings_from_proto(c.embeddings), published_at=ts_of(c.published_at, now()),
        duration_s=c.duration.ToNanoseconds() / 1e9, visibility=c.visibility, community_id=c.community_id[:MAX_ID],
        adults_only=c.audience.adults_only, allowed_countries=[x.upper() for x in c.audience.allowed_countries],
        blocked_countries=[x.upper() for x in c.audience.blocked_countries],
        safety_labels=[(s.label.lower(), s.confidence) for s in c.safety_labels],
        quality=max(0.0, min(c.quality_score, 1.0)) if c.quality_score else 0.5,
        trust=max(0.0, min(c.trust_score, 1.0)) if c.trust_score else 0.5,
        status=c.status, updated_at=ts_of(c.updated_at, now()), version=c.version)


def content_to_proto(r: ContentRecord, embeddings: bool = False) -> ctpb.ContentItem:
    m = ctpb.ContentItem(
        content_id=r.content_id, creator_id=r.creator_id, kind=r.kind, language=r.language,
        topics=[topic_to_proto(t) for t in r.topics], hashtags=r.hashtags, published_at=to_ts(r.published_at),
        visibility=r.visibility, community_id=r.community_id,
        audience=ctpb.AudienceRestriction(adults_only=r.adults_only, allowed_countries=r.allowed_countries,
                                          blocked_countries=r.blocked_countries),
        safety_labels=[ctpb.SafetyLabel(label=lbl, confidence=c) for lbl, c in r.safety_labels],
        quality_score=r.quality, trust_score=r.trust, status=r.status, updated_at=to_ts(r.updated_at),
        version=r.version)
    m.duration.FromNanoseconds(int(r.duration_s * 1e9))
    if embeddings:
        for model, v in r.embeddings.items():
            m.embeddings.add(model_id=model, values=[float(x) for x in v])
    return m


# ── profile ────────────────────────────────────────────────────────────────

def prefs_to_proto(p: Preferences) -> ppb.Preferences:
    return ppb.Preferences(
        preferred_topic_ids=p.preferred_topic_ids, muted_topic_ids=p.muted_topic_ids,
        muted_user_ids=p.muted_user_ids, blocked_user_ids=p.blocked_user_ids, preferred_kinds=p.preferred_kinds,
        muted_kinds=p.muted_kinds, content_languages=p.content_languages, max_maturity=p.max_maturity,
        connections=ppb.ConnectionPreferences(open_to_connections=p.open_to_connections,
                                              purposes=p.connection_purposes, languages=p.connection_languages,
                                              same_country_only=p.same_country_only))


PREF_PATHS = {
    "preferred_topic_ids": "preferred_topic_ids", "muted_topic_ids": "muted_topic_ids",
    "muted_user_ids": "muted_user_ids", "blocked_user_ids": "blocked_user_ids",
    "preferred_kinds": "preferred_kinds", "muted_kinds": "muted_kinds", "content_languages": "content_languages",
    "max_maturity": "max_maturity", "connections.open_to_connections": "open_to_connections",
    "connections.purposes": "connection_purposes", "connections.languages": "connection_languages",
    "connections.same_country_only": "same_country_only",
}
PREF_LIST_LIMIT = 1000


def apply_prefs(cur: Preferences, m: ppb.Preferences, paths: list[str]) -> Preferences:
    src = {
        "preferred_topic_ids": list(m.preferred_topic_ids), "muted_topic_ids": list(m.muted_topic_ids),
        "muted_user_ids": list(m.muted_user_ids), "blocked_user_ids": list(m.blocked_user_ids),
        "preferred_kinds": list(m.preferred_kinds), "muted_kinds": list(m.muted_kinds),
        "content_languages": list(m.content_languages), "max_maturity": m.max_maturity,
        "open_to_connections": m.connections.open_to_connections,
        "connection_purposes": list(m.connections.purposes), "connection_languages": list(m.connections.languages),
        "same_country_only": m.connections.same_country_only,
    }
    paths = paths or list(PREF_PATHS)
    expanded = []
    for p in paths:
        if p == "connections":
            expanded += [k for k in PREF_PATHS if k.startswith("connections.")]
        elif p in PREF_PATHS:
            expanded.append(p)
        else:
            raise Invalid(f"update_mask: unknown preferences field {p!r}")
    for p in expanded:
        attr = PREF_PATHS[p]
        v = src[attr]
        if isinstance(v, list) and len(v) > PREF_LIST_LIMIT:
            raise Invalid(f"{p}: at most {PREF_LIST_LIMIT} entries")
        setattr(cur, attr, v)
    return cur


PRIVACY_FIELDS = ("personalization_enabled", "use_engagement_history", "discoverable_in_suggestions",
                  "allow_mutual_connection_signal", "allow_location_signal", "show_activity_to_others",
                  "allow_declared_sensitive_topics", "contribute_to_collaborative")


def privacy_to_proto(p: Privacy) -> ppb.PrivacySettings:
    m = ppb.PrivacySettings(**{f: getattr(p, f) for f in PRIVACY_FIELDS})
    m.updated_at.CopyFrom(to_ts(p.updated_at))
    return m


def apply_privacy(cur: Privacy, m: ppb.PrivacySettings, paths: list[str]) -> Privacy:
    for p in paths or PRIVACY_FIELDS:
        if p not in PRIVACY_FIELDS:
            raise Invalid(f"update_mask: unknown privacy field {p!r}")
        setattr(cur, p, getattr(m, p))
    cur.updated_at = now()
    return cur


ATTR_FIELDS = ("age_band", "account_type", "verified", "languages", "country", "region", "trust_score", "created_at")


def apply_attributes(u: UserRecord, a: ppb.UserAttributes, paths: list[str]) -> UserRecord:
    for p in paths or ATTR_FIELDS:
        if p not in ATTR_FIELDS:
            raise Invalid(f"update_mask: unknown attribute {p!r}")
        if p == "languages":
            u.languages = [x[:16] for x in a.languages][:20]
        elif p == "country":
            u.country = a.country[:2].upper()
        elif p == "region":
            u.region = a.region[:64]
        elif p == "trust_score":
            u.trust_score = max(0.0, min(a.trust_score, 1.0))
        elif p == "created_at":
            u.created_at = ts_of(a.created_at, u.created_at)
        else:
            setattr(u, p, getattr(a, p))
    return u


def profile_to_proto(u: UserRecord, embeddings: bool = False) -> ppb.UserProfile:
    m = ppb.UserProfile(
        user_id=u.user_id, age_band=u.age_band, account_type=u.account_type, verified=u.verified,
        languages=u.languages, country=u.country, region=u.region, trust_score=u.trust_score,
        interests=[topic_to_proto(t) for t in u.declared_topics + u.inferred_topics],
        preferences=prefs_to_proto(u.preferences), privacy=privacy_to_proto(u.privacy),
        created_at=to_ts(u.created_at), updated_at=to_ts(u.updated_at), version=u.version)
    if embeddings:
        for model, v in u.embeddings.items():
            m.embeddings.add(model_id=model, values=[float(x) for x in v])
    return m


# ── graph ──────────────────────────────────────────────────────────────────

def edge_from_proto(e: gpb.Edge) -> Edge:
    _id(e.from_user_id, "from_user_id")
    _id(e.to_user_id, "to_user_id")
    if e.type == gpb.EDGE_TYPE_UNSPECIFIED or e.type not in gpb.EdgeType.values():
        raise Invalid("edge type is required")
    return Edge(from_user_id=e.from_user_id, to_user_id=e.to_user_id, type=e.type, weight=e.weight or 1.0,
                created_at=ts_of(e.created_at, now()))


def edge_to_proto(e: Edge) -> gpb.Edge:
    return gpb.Edge(from_user_id=e.from_user_id, to_user_id=e.to_user_id, type=e.type, weight=e.weight,
                    created_at=to_ts(e.created_at))


# ── served ─────────────────────────────────────────────────────────────────

def served_to_proto(s: ServedRecommendation) -> rpb.ServedRecommendation:
    return rpb.ServedRecommendation(
        recommendation_id=s.recommendation_id, user_id=s.user_id, surface=s.surface,
        items=[rpb.ServedItem(item=cpb.EntityRef(type=i.target_type, id=i.target_id), rank=i.rank, score=i.score)
               for i in s.items],
        model=cpb.ModelInfo(model_id=s.model_id, model_version=s.model_version, experiment_id=s.experiment_id,
                            variant=s.variant),
        personalized=s.personalized, served_at=to_ts(s.served_at))
