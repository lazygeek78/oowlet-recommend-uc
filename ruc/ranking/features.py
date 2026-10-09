"""Score components (ranking features), each 0..1, for one (user, candidate)
in one context. See models.py for how they combine."""

from __future__ import annotations

import numpy as np

from .. import signals
from ..context import RecContext, content_context_relevance
from ..domain import UserRecord
from ..intelligence.hub import ContentState, UserState
from .models import PERSONAL

COLLAB_SOURCES = ("collaborative", "matrix_factorization", "behavioral_similarity")


def _cos(a: np.ndarray | None, b: np.ndarray | None) -> float:
    if a is None or b is None:
        return 0.0
    return max(0.0, float(np.dot(a, b)))


def content_features(st: UserState, cs: ContentState, priors: dict[str, float], ctx: RecContext,
                     social_count: int, frequency_cap: int) -> dict[str, float]:
    item = cs.item
    # sensitive topics count only when the user declared them (they are then in
    # topic_affinity); inferred affinity never contains them
    tw = item.topic_weights(include_sensitive=True)
    total = sum(tw.values())
    interest = (sum(w * st.topic_affinity.get(t, 0.0) for t, w in tw.items()) / total) if total > 0 else 0.0
    neg_topic = (sum(w * st.negative_topics.get(t, 0.0) for t, w in tw.items()) / total) if total > 0 else 0.0
    x = {
        "user_interest": interest,
        "content_relevance": _cos(st.embedding, cs.vector),
        "behavioral_affinity": max((priors.get(s, 0.0) for s in COLLAB_SOURCES), default=0.0),
        "context_relevance": content_context_relevance(st, cs, ctx),
        "quality": cs.quality,
        "credibility": cs.credibility,
        "freshness": cs.freshness,
        "social_signal": signals.saturate(social_count, 3.0),
        "trend_signal": cs.trend,
        "creator_affinity": max(st.creator_affinity.get(item.creator_id, 0.0),
                                0.5 if item.creator_id in st.following else 0.0),
        "repetition": min(st.impressions.get(item.content_id, 0) / max(frequency_cap, 1), 1.0),
        "negative_feedback": max(neg_topic, st.negative_creators.get(item.creator_id, 0.0)),
    }
    if not st.personalized:
        for k in PERSONAL:
            x[k] = 0.0
    return x


def people_features(st: UserState, other: UserRecord, other_vec: np.ndarray | None, priors: dict[str, float],
                    mutual_count: int, other_communities: set[str], last_active: float, acceptance: float,
                    ctx: RecContext) -> dict[str, float]:
    viewer = st.user
    # interests: embedding similarity + overlap of non-sensitive topics only
    # (another user's sensitive topics are never used to match them)
    mine = {t: w for t, w in st.topic_affinity.items()}
    theirs = {t.topic_id: t.weight for t in other.inferred_topics + other.declared_topics if not t.sensitive}
    overlap = sum(min(mine.get(t, 0.0), w) for t, w in theirs.items())
    union = sum(max(mine.get(t, 0.0), w) for t, w in {**mine, **theirs}.items())
    topic_sim = overlap / union if union > 0 else 0.0
    shared = 0.6 * _cos(st.embedding, other_vec) + 0.4 * topic_sim if st.uses_history else 0.4 * topic_sim
    ctx_parts = []
    if ctx.community_id:
        ctx_parts.append(1.0 if ctx.community_id in other_communities else 0.0)
    if (viewer.privacy.allow_location_signal and other.privacy.allow_location_signal
            and viewer.region and other.region):
        ctx_parts.append(1.0 if viewer.region == other.region else 0.0)
    if ctx.seed_user_id:
        ctx_parts.append(priors.get("contextual", 0.0))
    langs = set(viewer.preferences.connection_languages or viewer.languages)
    if langs and other.languages:
        ctx_parts.append(1.0 if langs & set(other.languages) else 0.2)
    completeness = sum(bool(v) for v in (other.languages, other.country, other.declared_topics or other.inferred_topics)) / 3
    purpose_match = 1.0
    if viewer.preferences.connection_purposes and other.preferences.connection_purposes:
        purpose_match = 1.0 if set(viewer.preferences.connection_purposes) & set(other.preferences.connection_purposes) else 0.3
    x = {
        "mutual_connections": signals.saturate(mutual_count, 3.0),
        "shared_interests": max(0.0, min(shared, 1.0)),
        "community_overlap": signals.saturate(len(st.communities & other_communities), 1.5),
        "interaction": st.interacted_users.get(other.user_id, 0.0) if st.uses_history else 0.0,
        "context_relevance": sum(ctx_parts) / len(ctx_parts) if ctx_parts else 0.5,
        "profile_quality": 0.6 * other.trust_score + 0.2 * float(other.verified) + 0.2 * completeness,
        "activity": signals.decay(ctx.t - last_active, 7 * 86400.0) if last_active else 0.0,
        "reciprocity": max(0.0, min(0.5 * acceptance + 0.3 * purpose_match
                                    + 0.2 * float(other.user_id in st.followers), 1.0)),
    }
    return x
