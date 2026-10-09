"""The engine's storage interface.

Everything the engines and APIs read or write goes through Store, so a
persistent backend (a database owned by this module, or the core's data path
like the dataset curator uses) replaces MemoryStore without touching the
engines. MemoryStore (memory.py) is the reference implementation.
"""

from __future__ import annotations

import abc
from collections.abc import Iterable
from dataclasses import dataclass, field

from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb

from ..domain import ContentRecord, Edge, Engagement, Feedback, ServedRecommendation, UserRecord

E = epb

# EngagementType -> counter name (EngagementCounters fields)
COUNTER_OF: dict[int, str] = {
    E.ENGAGEMENT_TYPE_IMPRESSION: "impressions",
    E.ENGAGEMENT_TYPE_OPEN: "opens",
    E.ENGAGEMENT_TYPE_VIEW: "views",
    E.ENGAGEMENT_TYPE_VIEW_COMPLETE: "completions",
    E.ENGAGEMENT_TYPE_LIKE: "likes",
    E.ENGAGEMENT_TYPE_REACTION: "likes",
    E.ENGAGEMENT_TYPE_COMMENT: "comments",
    E.ENGAGEMENT_TYPE_SHARE: "shares",
    E.ENGAGEMENT_TYPE_SAVE: "saves",
    E.ENGAGEMENT_TYPE_REPOST: "reposts",
    E.ENGAGEMENT_TYPE_SKIP: "skips",
    E.ENGAGEMENT_TYPE_HIDE: "hides",
    E.ENGAGEMENT_TYPE_REPORT: "reports",
    E.ENGAGEMENT_TYPE_CLICK: "clicks",
    E.ENGAGEMENT_TYPE_SEARCH_CLICK: "clicks",
    E.ENGAGEMENT_TYPE_PURCHASE: "purchases",
    E.ENGAGEMENT_TYPE_OUTCOME: "outcomes",
    E.ENGAGEMENT_TYPE_FOLLOW: "follows",
}
COUNTER_NAMES = ("impressions", "opens", "views", "completions", "likes", "comments", "shares", "saves",
                 "reposts", "skips", "hides", "reports", "clicks", "purchases", "outcomes", "follows")


@dataclass
class Counters:
    counts: dict[str, int] = field(default_factory=lambda: dict.fromkeys(COUNTER_NAMES, 0))
    unique_users: int = 0
    dwell_seconds: float = 0.0

    def add(self, other: "Counters") -> None:
        for k, v in other.counts.items():
            self.counts[k] = self.counts.get(k, 0) + v
        self.dwell_seconds += other.dwell_seconds

    @property
    def positives(self) -> int:
        c = self.counts
        return c["likes"] + c["comments"] + c["shares"] + c["saves"] + c["reposts"] + c["purchases"] + c["outcomes"]

    @property
    def negatives(self) -> int:
        return self.counts["hides"] + self.counts["reports"]


class VersionConflict(Exception):
    """expected_version did not match the stored version."""


class NotFound(KeyError):
    pass


class Store(abc.ABC):
    # ── engagement ─────────────────────────────────────────────────────────
    @abc.abstractmethod
    async def add_engagements(self, events: Iterable[Engagement],
                              collaborative: frozenset[str] | None = None) -> tuple[list[Engagement], int]:
        """Record events. Returns (newly recorded events, number of duplicate event_ids).
        Only users in `collaborative` (None: everyone) feed item-item
        co-engagement, which other users' recommendations are built from."""

    @abc.abstractmethod
    async def user_events(self, user_id: str, since: float = 0.0, until: float | None = None,
                          types: frozenset[int] | None = None, target_type: int = 0,
                          limit: int = 0, newest_first: bool = True) -> list[Engagement]:
        ...

    @abc.abstractmethod
    async def inbound_user_events(self, target_user_id: str, since: float = 0.0) -> list[Engagement]:
        """Events whose target is this user (profile visits, follows, requests)."""

    @abc.abstractmethod
    async def content_counters(self, content_id: str, since: float, until: float | None = None) -> Counters:
        ...

    @abc.abstractmethod
    async def content_timeline(self, content_id: str, start: float, end: float,
                               bucket_seconds: int) -> list[tuple[float, Counters]]:
        ...

    @abc.abstractmethod
    async def content_engagers(self, content_id: str, types: frozenset[int] | None,
                               since: float = 0.0) -> list[Engagement]:
        """Non-impression events on the item, newest first."""

    @abc.abstractmethod
    async def co_engaged(self, content_id: str, k: int) -> list[tuple[str, float]]:
        """Items engaged by the same users (positive engagement), strongest first."""

    @abc.abstractmethod
    async def trending(self, since: float, k: int) -> list[tuple[str, float]]:
        """(content_id, trend score) by recent positive engagement velocity."""

    @abc.abstractmethod
    async def delete_user_data(self, user_id: str) -> None:
        """Erase the user's events, served log, feedback and record."""

    # ── content ────────────────────────────────────────────────────────────
    @abc.abstractmethod
    async def upsert_content(self, item: ContentRecord) -> bool:
        """False when the stored version is not older (stale update ignored)."""

    @abc.abstractmethod
    async def get_content(self, ids: Iterable[str]) -> dict[str, ContentRecord]:
        ...

    @abc.abstractmethod
    async def set_content_status(self, content_id: str, status: int) -> bool:
        ...

    @abc.abstractmethod
    async def recent_content(self, since: float, k: int) -> list[ContentRecord]:
        ...

    @abc.abstractmethod
    async def content_by_creators(self, creator_ids: Iterable[str], since: float, k: int) -> list[ContentRecord]:
        ...

    @abc.abstractmethod
    async def content_by_topics(self, topic_ids: Iterable[str], k: int) -> list[ContentRecord]:
        ...

    @abc.abstractmethod
    async def content_by_community(self, community_id: str, k: int) -> list[ContentRecord]:
        ...

    @abc.abstractmethod
    async def iter_content(self) -> list[ContentRecord]:
        """All active items (vector index rebuilds, training)."""

    # ── users ──────────────────────────────────────────────────────────────
    @abc.abstractmethod
    async def get_user(self, user_id: str) -> UserRecord | None:
        ...

    @abc.abstractmethod
    async def get_users(self, ids: Iterable[str]) -> dict[str, UserRecord]:
        ...

    @abc.abstractmethod
    async def put_user(self, user: UserRecord, expected_version: int = 0) -> UserRecord:
        """Store with version + 1; VersionConflict when expected_version > 0 and differs."""

    @abc.abstractmethod
    async def iter_users(self) -> list[UserRecord]:
        ...

    # ── graph ──────────────────────────────────────────────────────────────
    @abc.abstractmethod
    async def upsert_edges(self, edges: Iterable[Edge]) -> int:
        ...

    @abc.abstractmethod
    async def remove_edges(self, edges: Iterable[Edge]) -> int:
        ...

    @abc.abstractmethod
    async def out_edges(self, user_id: str, types: frozenset[int]) -> list[Edge]:
        ...

    @abc.abstractmethod
    async def in_edges(self, user_id: str, types: frozenset[int]) -> list[Edge]:
        ...

    @abc.abstractmethod
    async def has_edge(self, from_id: str, to_id: str, type_: int) -> bool:
        ...

    # ── served recommendations and feedback ───────────────────────────────
    @abc.abstractmethod
    async def log_served(self, rec: ServedRecommendation) -> None:
        """A later page of the same recommendation_id adds its items to the record."""

    @abc.abstractmethod
    async def get_served(self, recommendation_id: str) -> ServedRecommendation | None:
        ...

    @abc.abstractmethod
    async def update_served_item(self, recommendation_id: str, target_type: int, target_id: str,
                                 label: float | None = None, impressed: bool | None = None) -> bool:
        """Attribution: set the outcome of one served item. False if unknown."""

    @abc.abstractmethod
    async def served_for_user(self, user_id: str, since: float, until: float | None = None,
                              surface: int = 0) -> list[ServedRecommendation]:
        """Newest first."""

    @abc.abstractmethod
    async def served_since(self, since: float) -> list[ServedRecommendation]:
        """All serves since (training / evaluation)."""

    @abc.abstractmethod
    async def add_feedback(self, fb: Feedback) -> None:
        ...

    @abc.abstractmethod
    async def feedback_for_user(self, user_id: str, since: float = 0.0) -> list[Feedback]:
        ...
