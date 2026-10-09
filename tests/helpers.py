"""Test data: a small world of users, content, graph and engagement."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb

from ruc.app import App
from ruc.config import Settings
from ruc.domain import CONTENT, USER, ContentRecord, Edge, Engagement, Preferences, Privacy, Topic, UserRecord, now

E = epb
_ids = itertools.count(1)
ADULT, MINOR = cpb.AGE_BAND_ADULT, cpb.AGE_BAND_MINOR


def settings(tmp: Path, **over) -> Settings:
    if not (tmp / "tokens.json").exists():
        (tmp / "tokens.json").write_text(json.dumps({"tokens": []}))
    env = {"RUC_ENV": "development", "RUC_SERVER__TLS_ENABLED": "false",
           "RUC_AUTH__TOKENS_FILE": str(tmp / "tokens.json"), "RUC_RANKING__MODEL_DIR": str(tmp / "models")}
    env.update({k: str(v) for k, v in over.items()})
    return Settings.load(env, validate=False)


def write_tokens(path: Path, entries: list[dict]) -> dict[str, str]:
    """entries carry a plain 'token'; the file stores only its hash. Returns name -> token."""
    out, rows = {}, []
    for e in entries:
        tok = e.pop("token")
        out[e.get("principal") or e.get("user_id")] = tok
        rows.append({"sha256": hashlib.sha256(tok.encode()).hexdigest(), **e})
    path.write_text(json.dumps({"tokens": rows}))
    return out


def user(uid: str, age=ADULT, country="IN", open_=True, discoverable=True, **kw) -> UserRecord:
    priv = Privacy.platform_defaults()
    priv.discoverable_in_suggestions = discoverable
    for k in list(kw):
        if hasattr(priv, k):
            setattr(priv, k, kw.pop(k))
    prefs = Preferences(open_to_connections=open_, **kw.pop("prefs", {}))
    return UserRecord(user_id=uid, age_band=age, country=country, languages=["en"], trust_score=0.8,
                      preferences=prefs, privacy=priv, **kw)


def item(cid: str, creator: str, topics: dict[str, float], kind=cpb.CONTENT_KIND_VIDEO, age_h: float = 5,
         visibility=ctpb.VISIBILITY_PUBLIC, **kw) -> ContentRecord:
    return ContentRecord(content_id=cid, creator_id=creator, kind=kind, language="en",
                         topics=[Topic(t, w) for t, w in topics.items()], published_at=now() - age_h * 3600,
                         visibility=visibility, status=ctpb.CONTENT_STATUS_ACTIVE, quality=0.7, trust=0.8, **kw)


def ev(uid: str, cid: str, type_=E.ENGAGEMENT_TYPE_LIKE, ago_h: float = 1, target=CONTENT, rec="", **kw) -> Engagement:
    return Engagement(event_id=f"e{next(_ids)}", user_id=uid, target_type=target, target_id=cid, type=type_,
                      ts=now() - ago_h * 3600, recommendation_id=rec, **kw)


async def world(app: App) -> None:
    """Users a..f (adults), m1 (minor), creators c1 (sports), c2 (cooking), c3 (music).
    alice likes sports; bob likes cooking; carol likes sports + music."""
    for u in [user("alice"), user("bob"), user("carol"), user("dave"), user("erin"), user("frank"),
              user("m1", age=MINOR), user("c1"), user("c2"), user("c3"),
              user("shy", discoverable=False), user("closed", open_=False)]:
        await app.store.put_user(u)
    n = 0
    for creator, topic, k in (("c1", "sports", 8), ("c2", "cooking", 8), ("c3", "music", 8)):
        for i in range(k):
            n += 1
            await app.upsert_content(item(f"{topic}-{i}", creator, {topic: 1.0, f"{topic}.sub{i % 2}": 0.5},
                                          age_h=2 + i * 6))
    await app.upsert_content(item("adult-1", "c1", {"sports": 1.0}, adults_only=True))
    await app.upsert_content(item("private-1", "c1", {"sports": 1.0}, visibility=ctpb.VISIBILITY_PRIVATE))
    await app.upsert_content(item("health-1", "c2", {"health.diabetes": 1.0}))
    evs = []
    for i in range(4):
        evs += [ev("alice", f"sports-{i}", E.ENGAGEMENT_TYPE_LIKE, ago_h=i + 1),
                ev("bob", f"cooking-{i}", E.ENGAGEMENT_TYPE_SAVE, ago_h=i + 1),
                ev("carol", f"sports-{i}", E.ENGAGEMENT_TYPE_LIKE, ago_h=i + 2),
                ev("carol", f"music-{i}", E.ENGAGEMENT_TYPE_SHARE, ago_h=i + 2)]
    evs += [ev("carol", "sports-6", E.ENGAGEMENT_TYPE_SHARE, ago_h=3), ev("carol", "sports-7", E.ENGAGEMENT_TYPE_LIKE, ago_h=3)]
    evs += [ev("alice", "health-1", E.ENGAGEMENT_TYPE_LIKE, ago_h=1)]
    await app.record_engagement(evs)
    C = 2  # EDGE_TYPE_CONNECTED
    await app.upsert_edges([Edge("alice", "bob", C), Edge("bob", "carol", C), Edge("bob", "dave", C),
                            Edge("carol", "dave", C), Edge("alice", "c1", 1), Edge("bob", "m1", C),
                            Edge("bob", "shy", C), Edge("bob", "closed", C), Edge("carol", "erin", C)])


__all__ = ["ADULT", "MINOR", "CONTENT", "USER", "E", "ev", "item", "settings", "user", "world", "write_tokens"]
