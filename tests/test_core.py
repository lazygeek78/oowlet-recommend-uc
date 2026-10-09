"""Store, signals, intelligence, policy, engines, feedback loop and training."""

from __future__ import annotations

import numpy as np
import pytest
import pytest_asyncio

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb

from ruc import signals
from ruc.app import App
from ruc.context import RecContext
from ruc.domain import CONTENT, Edge, Feedback, now
from ruc.policy import eligibility
from ruc.training import trainer
from ruc.training.mf import ImplicitALS
from ruc.ranking.models import LogisticRanker, auc

from .helpers import MINOR, E, ev, item, settings, world

X = cpb


@pytest_asyncio.fixture
async def app(tmp_path):
    a = App(settings(tmp_path))
    await world(a)
    yield a
    await a.close()


def content_req(**kw) -> rpb.RecommendContentRequest:
    r = rpb.RecommendContentRequest(limit=kw.pop("limit", 10), include_explanations=True, **kw)
    r.context.surface = r.context.surface or cpb.SURFACE_HOME_FEED
    return r


# ── signals / store ────────────────────────────────────────────────────────

def test_signal_funnel_and_decay():
    w = {t: signals.weight(ev("u", "c", t)) for t in (E.ENGAGEMENT_TYPE_IMPRESSION, E.ENGAGEMENT_TYPE_CLICK,
                                                     E.ENGAGEMENT_TYPE_VIEW, E.ENGAGEMENT_TYPE_LIKE,
                                                     E.ENGAGEMENT_TYPE_SHARE, E.ENGAGEMENT_TYPE_PURCHASE)}
    vals = list(w.values())
    assert vals == sorted(vals) and vals[0] == 0.0                # deeper in the funnel = stronger
    assert signals.weight(ev("u", "c", E.ENGAGEMENT_TYPE_HIDE)) < 0
    assert signals.weight(ev("u", "c", E.ENGAGEMENT_TYPE_VIEW, dwell_s=60, watch_fraction=1.0)) == 3.0
    assert signals.decay(7 * 86400, 7 * 86400) == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_store_idempotent_counters_coengagement(app):
    s = app.store
    e = ev("dave", "sports-0", E.ENGAGEMENT_TYPE_LIKE)
    assert await s.add_engagements([e, e]) == ([e], 1)
    assert (await s.add_engagements([e]))[1] == 1
    c = await s.content_counters("sports-0", now() - 86400)
    assert c.counts["likes"] == 3 and c.unique_users == 3          # alice, carol, dave
    co = dict(await s.co_engaged("sports-0", 20))
    assert "sports-1" in co and "cooking-0" not in co              # alice and carol liked both
    assert (await s.trending(now() - 86400, 5))[0][1] > 0


@pytest.mark.asyncio
async def test_delete_user_data(app):
    await app.delete_user_data("alice")
    assert await app.store.user_events("alice") == []
    assert await app.store.get_user("alice") is None
    assert all(e.user_id != "alice" for e in await app.store.content_engagers("sports-0", None))


# ── intelligence ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_state_affinity_and_sensitive_topics(app):
    st = await app.intel.user_state("alice")
    assert st.topic_affinity.get("sports") == 1.0
    assert "health.diabetes" not in st.topic_affinity              # liked, but sensitive: never inferred
    assert st.embedding is not None and st.recent_positive
    carol = await app.intel.user_state("carol")
    assert {"sports", "music"} <= set(carol.topic_affinity)

    # declared sensitive topic counts only with the user's explicit permission
    await app.update_user("bob", lambda u: (setattr(u.preferences, "preferred_topic_ids", ["health.fitness"]), u)[1])
    from ruc.domain import Topic
    await app.update_user("bob", lambda u: (setattr(u, "declared_topics", [Topic("health.fitness", 1.0)]), u)[1])
    assert "health.fitness" not in (await app.intel.user_state("bob")).topic_affinity
    await app.update_user("bob", lambda u: (setattr(u.privacy, "allow_declared_sensitive_topics", True), u)[1])
    assert "health.fitness" in (await app.intel.user_state("bob")).topic_affinity


@pytest.mark.asyncio
async def test_personalization_off_uses_no_history(app):
    await app.update_user("alice", lambda u: (setattr(u.privacy, "personalization_enabled", False), u)[1])
    st = await app.intel.user_state("alice")
    assert not st.personalized and not st.topic_affinity and st.embedding is None
    assert "sports-0" in st.consumed                              # dedup still applies
    resp = await app.content.recommend("alice", content_req())
    assert not resp.personalized
    assert {s for r in resp.items for s in r.candidate_sources} <= {"trending", "fresh", "contextual"}


# ── policy ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_content_eligibility_rules(app):
    p = app.s.policy
    ctx = RecContext()
    alice = await app.intel.user_state("alice")
    minor = await app.intel.user_state("m1")
    unknown = await app.intel.user_state("nobody")
    recs = await app.store.get_content(["adult-1", "private-1", "sports-0", "sports-5", "music-1"])
    assert X.EXCLUSION_REASON_AGE_RESTRICTED in eligibility.check_content(minor, recs["adult-1"], ctx, p)
    assert X.EXCLUSION_REASON_AGE_RESTRICTED in eligibility.check_content(unknown, recs["adult-1"], ctx, p)
    # adult, but maturity preference not set to MATURE
    assert X.EXCLUSION_REASON_AGE_RESTRICTED in eligibility.check_content(alice, recs["adult-1"], ctx, p)
    assert X.EXCLUSION_REASON_PRIVACY_SETTINGS in eligibility.check_content(alice, recs["private-1"], ctx, p)
    assert X.EXCLUSION_REASON_ALREADY_SEEN in eligibility.check_content(alice, recs["sports-0"], ctx, p)
    assert eligibility.check_content(alice, recs["sports-5"], ctx, p) == []
    blocked = recs["music-1"]
    await app.upsert_edges([Edge("c3", "alice", 4)])               # c3 blocks alice
    st = await app.intel.user_state("alice")
    assert X.EXCLUSION_REASON_BLOCKED in eligibility.check_content(st, blocked, ctx, p)
    labelled = item("x", "c2", {"cooking": 1}, safety_labels=[("violence", 0.9)], allowed_countries=["US"])
    r = eligibility.check_content(st, labelled, ctx, p)
    assert X.EXCLUSION_REASON_SAFETY_LABEL in r and X.EXCLUSION_REASON_AUDIENCE_RESTRICTED in r
    community = item("y", "c2", {"cooking": 1}, visibility=ctpb.VISIBILITY_COMMUNITY, community_id="chefs")
    assert X.EXCLUSION_REASON_AUDIENCE_RESTRICTED in eligibility.check_content(st, community, ctx, p)
    await app.upsert_edges([Edge("alice", "chefs", 8)])            # member of the community
    st = await app.intel.user_state("alice")
    assert eligibility.check_content(st, community, ctx, p) == []


@pytest.mark.asyncio
async def test_people_eligibility_rules(app):
    p = app.s.policy
    alice = await app.intel.user_state("alice")
    users = await app.store.get_users(["m1", "shy", "closed", "bob", "dave"])
    assert X.EXCLUSION_REASON_AGE_RESTRICTED in eligibility.check_person(alice, users["m1"], True, p)
    assert X.EXCLUSION_REASON_PRIVACY_SETTINGS in eligibility.check_person(alice, users["shy"], True, p)
    assert X.EXCLUSION_REASON_NOT_OPEN_TO_CONNECT in eligibility.check_person(alice, users["closed"], True, p)
    assert X.EXCLUSION_REASON_ALREADY_CONNECTED in eligibility.check_person(alice, users["bob"], True, p)
    assert eligibility.check_person(alice, users["dave"], True, p) == []
    minor = await app.intel.user_state("m1")
    assert X.EXCLUSION_REASON_AGE_RESTRICTED in eligibility.check_person(minor, users["dave"], True, p)
    await app.update_user("dave", lambda u: (setattr(u.preferences, "blocked_user_ids", ["alice"]), u)[1])
    dave = await app.store.get_user("dave")
    assert X.EXCLUSION_REASON_BLOCKED in eligibility.check_person(alice, dave, True, p)


# ── engines ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_content_recommendations_follow_interest(app):
    resp = await app.content.recommend("alice", content_req(limit=6))
    ids = [r.content_id for r in resp.items]
    assert resp.personalized and resp.recommendation_id and len(ids) == 6
    assert not {"sports-0", "sports-1", "sports-2", "sports-3"} & set(ids)        # already consumed
    assert not {"adult-1", "private-1", "health-1"} & set(ids)
    assert sum(i.startswith("sports-") for i in ids[:3]) >= 2                     # interest leads
    by_creator = {}
    for i in ids:
        c = i.split("-")[0]
        by_creator[c] = by_creator.get(c, 0) + 1
    explained = [r for r in resp.items if r.explanation.reasons]
    assert explained
    for r in resp.items:
        for rs in r.explanation.reasons:
            for e in rs.evidence:
                assert not e.id.startswith("health")                               # sensitive never shown
    served = await app.store.get_served(resp.recommendation_id)
    assert served.items[0].features and set(served.items[0].features) >= {"user_interest", "freshness"}


@pytest.mark.asyncio
async def test_content_paging_and_seed(app):
    first = await app.content.recommend("bob", content_req(limit=3))
    assert first.page.next_page_token
    second = await app.content.recommend("bob", content_req(limit=3, page=cpb.PageRequest(page_token=first.page.next_page_token)))
    a, b = [r.content_id for r in first.items], [r.content_id for r in second.items]
    assert not set(a) & set(b) and second.recommendation_id == first.recommendation_id
    assert [r.rank for r in second.items] == [3, 4, 5]
    from ruc.engines.common import PageTokenError
    with pytest.raises(PageTokenError):
        await app.content.recommend("alice", content_req(limit=3, page=cpb.PageRequest(page_token=first.page.next_page_token)))
    rel = await app.content.recommend("dave", content_req(limit=5, seed_content_id="music-0",
                                                          context=cpb.RequestContext(surface=cpb.SURFACE_CONTENT_DETAIL)))
    assert rel.items and "music-0" not in [r.content_id for r in rel.items]
    rel_ids = [r.content_id for r in rel.items]
    assert sum(i.startswith("music-") for i in rel_ids[:3]) >= 2, rel_ids        # related to the seed


@pytest.mark.asyncio
async def test_people_recommendations(app):
    resp = await app.people.recommend("alice", rpb.RecommendUsersRequest(limit=10, include_explanations=True))
    ids = [r.user_id for r in resp.items]
    assert "carol" in ids or "dave" in ids
    assert not {"alice", "bob", "m1", "shy", "closed"} & set(ids)        # self, connected, minor, private, closed
    top = resp.items[0]
    if top.user_id in ("carol", "dave"):
        assert top.mutual_connections >= 1
        codes = [r.code for r in top.explanation.reasons]
        assert X.REASON_CODE_MUTUAL_CONNECTIONS in codes
    minor = await app.people.recommend("m1", rpb.RecommendUsersRequest(limit=10))
    got = await app.store.get_users([r.user_id for r in minor.items])
    assert all(u.age_band == MINOR for u in got.values())


@pytest.mark.asyncio
async def test_mutual_signal_respects_privacy(app):
    # bob (the only path alice -> carol/dave) turns the mutual-connection signal off
    await app.update_user("bob", lambda u: (setattr(u.privacy, "allow_mutual_connection_signal", False), u)[1])
    resp = await app.people.recommend("alice", rpb.RecommendUsersRequest(limit=10, include_explanations=True))
    assert all(r.mutual_connections == 0 for r in resp.items)


@pytest.mark.asyncio
async def test_check_eligibility_matches_engine(app):
    st = await app.intel.user_state("alice")
    res = await app.content.check(st, RecContext(), ["sports-5", "adult-1", "sports-0", "nope"], True, True)
    assert [r.eligible for r in res] == [True, False, False, False]
    assert res[0].score != 0 and res[3].reasons == [X.EXCLUSION_REASON_UNAVAILABLE]


# ── feedback loop and training ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_attribution_and_feedback(app):
    resp = await app.content.recommend("dave", content_req(limit=5))
    rid, first, second = resp.recommendation_id, resp.items[0].content_id, resp.items[1].content_id
    await app.record_engagement([ev("dave", first, E.ENGAGEMENT_TYPE_IMPRESSION, 0, rec=rid),
                                 ev("dave", first, E.ENGAGEMENT_TYPE_LIKE, 0, rec=rid),
                                 ev("dave", second, E.ENGAGEMENT_TYPE_IMPRESSION, 0, rec=rid),
                                 ev("erin", second, E.ENGAGEMENT_TYPE_LIKE, 0, rec=rid)])    # not dave's serve
    served = await app.store.get_served(rid)
    by = {i.target_id: i for i in served.items}
    assert by[first].label == 1.0 and by[first].impressed
    assert by[second].label is None and by[second].impressed
    await app.feedback(Feedback("dave", rid, CONTENT, second, rpb.FEEDBACK_TYPE_NOT_INTERESTED, "", now()))
    assert (await app.store.get_served(rid)).items[1].label == 0.0
    again = await app.content.recommend("dave", content_req(limit=20))
    assert second not in [r.content_id for r in again.items]


@pytest.mark.asyncio
async def test_logistic_training_promotes_better_model(tmp_path):
    rng = np.random.default_rng(1)
    from ruc.domain import ServedItem, ServedRecommendation
    from ruc.ranking.models import CONTENT_FEATURES
    a = App(settings(tmp_path, RUC_TRAINING__MIN_EXAMPLES=200))
    t0 = now() - 86400
    for r in range(300):
        items = []
        for k in range(5):
            x = {f: float(rng.random()) for f in CONTENT_FEATURES}
            # truth: freshness and social signal drive engagement, not interest
            p = 1 / (1 + np.exp(-(4 * x["freshness"] + 3 * x["social_signal"] - 4)))
            items.append(ServedItem(CONTENT, f"c{r}-{k}", k, 0.0, x, impressed=True,
                                    label=1.0 if rng.random() < p else 0.0))
        await a.store.log_served(ServedRecommendation(f"r{r}", "u", 1, "content", items, "weighted", "1", "control",
                                                      "x", True, t0 + r * 60))
    report = await trainer.train_ranker(a, "content")
    assert report["result"].startswith("promoted"), report
    assert report["candidate"]["auc"] > report["current"]["auc"]
    m = a.models.logistic["content"]
    assert m.coef["freshness"] > 1 and m.coef["social_signal"] > 1
    loaded = LogisticRanker.load(a.models.path("content"))
    assert loaded.coef == m.coef
    await a.close()


def test_auc_and_mf():
    assert auc(np.array([0.1, 0.4, 0.35, 0.8]), np.array([0, 0, 1, 1])) == 0.75
    triples = [(f"u{u}", f"i{i}", 1.0) for u in range(6) for i in range(4) if (u < 3) == (i < 2)]
    triples += [("u0", "i1", 1.0), ("new", "i0", 1.0)]
    m = ImplicitALS(factors=4, iterations=15).fit(triples)
    rec = dict(m.recommend("new", 3))
    assert "i1" in rec and max(rec, key=rec.get) == "i1"                 # same cluster as i0


@pytest.mark.asyncio
async def test_mf_feeds_candidates(app):
    report = await trainer.train_mf(app)
    assert "trained" in report["mf"] and app.content.mf is not None
    resp = await app.content.recommend("alice", content_req(limit=10))
    assert resp.items

