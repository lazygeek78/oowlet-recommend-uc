"""How much each engagement says about interest, and how fast it fades.

The funnel IMPRESSION → CLICK → OPEN → VIEW → WATCH TIME → COMPLETION → LIKE →
COMMENT → SHARE → SAVE → FOLLOW → PURCHASE → OUTCOME is weighted by depth:
the further down, the stronger the signal. Negative actions subtract.
"""

from __future__ import annotations

import math

from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb

from .domain import USER, Engagement

E = epb

# Content-targeted signal weights. IMPRESSION is exposure, not interest: it
# feeds repetition and click-through, never affinity.
CONTENT_WEIGHTS: dict[int, float] = {
    E.ENGAGEMENT_TYPE_IMPRESSION: 0.0,
    E.ENGAGEMENT_TYPE_CLICK: 0.5,
    E.ENGAGEMENT_TYPE_SEARCH_CLICK: 0.8,
    E.ENGAGEMENT_TYPE_OPEN: 0.6,
    E.ENGAGEMENT_TYPE_VIEW: 1.0,
    E.ENGAGEMENT_TYPE_WATCH_TIME: 0.0,          # carried by dwell / watch_fraction
    E.ENGAGEMENT_TYPE_VIEW_COMPLETE: 2.0,
    E.ENGAGEMENT_TYPE_LIKE: 3.0,
    E.ENGAGEMENT_TYPE_REACTION: 3.0,
    E.ENGAGEMENT_TYPE_COMMENT: 4.0,
    E.ENGAGEMENT_TYPE_SHARE: 5.0,
    E.ENGAGEMENT_TYPE_SAVE: 5.0,
    E.ENGAGEMENT_TYPE_REPOST: 5.0,
    E.ENGAGEMENT_TYPE_FOLLOW: 6.0,               # follow from the item: creator affinity
    E.ENGAGEMENT_TYPE_PURCHASE: 8.0,
    E.ENGAGEMENT_TYPE_OUTCOME: 8.0,
    # negative
    E.ENGAGEMENT_TYPE_SKIP: -0.5,
    E.ENGAGEMENT_TYPE_UNLIKE: -3.0,
    E.ENGAGEMENT_TYPE_UNSAVE: -2.0,
    E.ENGAGEMENT_TYPE_UNFOLLOW: -4.0,
    E.ENGAGEMENT_TYPE_HIDE: -6.0,
    E.ENGAGEMENT_TYPE_REPORT: -10.0,
}

# User-targeted signals (people recommendations).
USER_WEIGHTS: dict[int, float] = {
    E.ENGAGEMENT_TYPE_IMPRESSION: 0.0,
    E.ENGAGEMENT_TYPE_PROFILE_VISIT: 1.0,
    E.ENGAGEMENT_TYPE_FOLLOW: 6.0,
    E.ENGAGEMENT_TYPE_CONNECT_REQUEST_SENT: 5.0,
    E.ENGAGEMENT_TYPE_CONNECT_ACCEPTED: 8.0,
    E.ENGAGEMENT_TYPE_MESSAGE_SENT: 3.0,
    E.ENGAGEMENT_TYPE_UNFOLLOW: -4.0,
    E.ENGAGEMENT_TYPE_CONNECT_DECLINED: -6.0,
    E.ENGAGEMENT_TYPE_CONNECT_REMOVED: -6.0,
    E.ENGAGEMENT_TYPE_SUGGESTION_DISMISSED: -5.0,
    E.ENGAGEMENT_TYPE_REPORT: -10.0,
}

# Engagements that mean the item was consumed (not shown again for a while).
CONSUMED = frozenset({E.ENGAGEMENT_TYPE_VIEW, E.ENGAGEMENT_TYPE_VIEW_COMPLETE, E.ENGAGEMENT_TYPE_LIKE,
                      E.ENGAGEMENT_TYPE_COMMENT, E.ENGAGEMENT_TYPE_SHARE, E.ENGAGEMENT_TYPE_SAVE,
                      E.ENGAGEMENT_TYPE_REPOST, E.ENGAGEMENT_TYPE_PURCHASE})
DISMISSED = frozenset({E.ENGAGEMENT_TYPE_HIDE, E.ENGAGEMENT_TYPE_REPORT})
# Label for training: did the user engage after the item was served?
POSITIVE_LABEL_MIN_WEIGHT = 0.5


def weight(ev: Engagement) -> float:
    """Signal strength of one engagement, including watch depth."""
    table = USER_WEIGHTS if ev.target_type == USER else CONTENT_WEIGHTS
    w = table.get(ev.type, 0.0)
    if w >= 0 and ev.target_type != USER:
        # watch time: up to +1 for 30 s of dwell, up to +1 for watching it all
        if ev.dwell_s > 0:
            w += min(ev.dwell_s / 30.0, 1.0)
        if ev.watch_fraction > 0:
            w += max(0.0, min(ev.watch_fraction, 1.0))
    return w


def decay(age_seconds: float, half_life_seconds: float) -> float:
    """Exponential time decay: 1 now, 0.5 after one half-life."""
    if age_seconds <= 0:
        return 1.0
    return math.pow(0.5, age_seconds / half_life_seconds)


def saturate(x: float, scale: float) -> float:
    """0..1, ~0.63 at x == scale; for counts (mutual connections, social proof)."""
    return 1.0 - math.exp(-max(x, 0.0) / scale) if scale > 0 else 0.0
