"""Regression tests for defects found in review: paging, privacy opt-outs,
blocks set in preferences, erasure, partial updates, feedback labels."""

from __future__ import annotations

import pytest
import pytest_asyncio

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.profilepb import profile_pb2 as ppb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb

from ruc import convert
from ruc.app import App
from ruc.candidates.generators import mutual_connections, social_activity
from ruc.domain import BLOCKED, CONTENT, Edge, Feedback, now
from ruc.engines.common import PageTokenError
from ruc.store.memory import MemoryStore
from ruc.training import trainer

from .helpers import E, ev, item, settings, user, world


@pytest_asyncio.fixture
async def app(tmp_path):
    a = App(settings(tmp_path))
    await world(a)
    yield a
    await a.close()


def feed(limit=3, token=""):
    r = rpb.RecommendContentRequest(limit=limit, page=cpb.PageRequest(page_token=token))
    r.context.surface = cpb.SURFACE_HOME_FEED
    return r


async def set_prefs(app, uid, **kw):
    def change(u):
        for k, v in kw.items():
            if hasattr(u.privacy, k):
                setattr(u.privacy, k, v)
            else:
                setattr(u.preferences, k, v)
        return u
    await app.update_user(uid, change)


@pytest.mark.asyncio
async def test_later_pages_keep_page_one_and_attribution(app):
    p1 = await app.content.recommend("dave", feed())
    first = [i.content_id for i in p1.items]
    await app.content.recommend("dave", feed(token=p1.page.next_page_token))
    served = await app.store.get_served(p1.recommendation_id)
    assert [i.target_id for i in served.items][:3] == first and len(served.items) == 6
    assert len(await app.store.served_for_user("dave", 0)) == 1           # one serve, not two
    await app.record_engagement([ev("dave", first[0], E.ENGAGEMENT_TYPE_LIKE, 0, rec=p1.recommendation_id)])
    assert (await app.store.get_served(p1.recommendation_id)).items[0].label == 1.0


@pytest.mark.asyncio
async def test_collaborative_opt_out_feeds_nothing_shared(tmp_path):
    a = App(settings(tmp_path))
    await world(a)
    await a.store.put_user(user("frank", contribute_to_collaborative=False))
    await a.upsert_content(item("solo-1", "c3", {"music": 1}))
    await a.upsert_content(item("solo-2", "c2", {"cooking": 1}))
    await a.record_engagement([ev("frank", "solo-1", E.ENGAGEMENT_TYPE_LIKE, 2),
                               ev("frank", "solo-2", E.ENGAGEMENT_TYPE_LIKE, 1)])
    assert "solo-1" not in dict(await a.store.co_engaged("solo-2", 50))
    await trainer.train_mf(a)
    assert "frank" not in a.content.mf.user_ids
    await a.close()


@pytest.mark.asyncio
async def test_mutual_count_hidden_for_people_who_disallow_it(app):
    await set_prefs(app, "carol", allow_mutual_connection_signal=False)
    resp = await app.people.recommend("alice", rpb.RecommendUsersRequest(limit=10, include_explanations=True))
    for r in resp.items:
        if r.user_id == "carol":
            assert r.mutual_connections == 0
            assert cpb.REASON_CODE_MUTUAL_CONNECTIONS not in [x.code for x in r.explanation.reasons]


@pytest.mark.asyncio
async def test_block_in_other_users_preferences(app):
    await set_prefs(app, "c2", blocked_user_ids=["dave"])
    resp = await app.content.recommend("dave", feed(limit=50))
    assert not [i.content_id for i in resp.items if i.content_id.startswith("cooking")]
    await set_prefs(app, "carol", show_activity_to_others=True, blocked_user_ids=["dave"])
    st = await app.intel.user_state("dave")
    assert not any("carol" in v for v in (await social_activity(st, app.intel)).values())
    # carol blocked dave by edge: dave is not in carol's mutual map
    await app.upsert_edges([Edge("carol", "dave", BLOCKED)])
    st = await app.intel.user_state("carol")
    assert "dave" not in await mutual_connections(st, app.intel)


@pytest.mark.asyncio
async def test_later_pages_and_explain_recheck_eligibility(app):
    p1 = await app.people.recommend("alice", rpb.RecommendUsersRequest(limit=1))
    rest = [x.key for x in app.people.pages.get(p1.recommendation_id, "alice").ranked[1:]]
    if not rest:
        pytest.skip("only one suggestion")
    victim = rest[0]
    await app.upsert_edges([Edge(victim, "alice", BLOCKED)])
    p2 = await app.people.recommend("alice", rpb.RecommendUsersRequest(
        limit=5, page=cpb.PageRequest(page_token=p1.page.next_page_token)))
    assert victim not in [i.user_id for i in p2.items]


@pytest.mark.asyncio
async def test_erasure_is_complete(tmp_path):
    a = App(settings(tmp_path), store=MemoryStore(max_events_per_user=3))
    await world(a)
    await a.record_engagement([ev("zed", f"music-{i}", E.ENGAGEMENT_TYPE_LIKE, 5 - i) for i in range(5)])
    p1 = await a.content.recommend("zed", feed(limit=2))
    await a.delete_user_data("zed")
    for i in range(5):
        assert all(e.user_id != "zed" for e in await a.store.content_engagers(f"music-{i}", None))
        assert (await a.store.content_counters(f"music-{i}", now() - 86400)).unique_users <= 1
    with pytest.raises(PageTokenError):
        await a.content.recommend("zed", feed(limit=2, token=p1.page.next_page_token))
    assert await a.store.served_for_user("zed", 0) == []
    await a.close()


@pytest.mark.asyncio
async def test_rejected_update_changes_nothing(app):
    before = await app.store.get_user("erin")
    with pytest.raises(convert.Invalid):
        await app.update_user("erin", lambda u: (setattr(u, "privacy", convert.apply_privacy(
            u.privacy, ppb.PrivacySettings(show_activity_to_others=True), ["show_activity_to_others", "bogus"])), u)[1])
    after = await app.store.get_user("erin")
    assert after.privacy.show_activity_to_others == before.privacy.show_activity_to_others
    assert after.version == before.version


@pytest.mark.asyncio
async def test_neutral_feedback_is_not_a_positive_label(app):
    resp = await app.content.recommend("dave", feed(limit=3))
    cid = resp.items[0].content_id
    await app.feedback(Feedback("dave", resp.recommendation_id, CONTENT, cid, rpb.FEEDBACK_TYPE_ALREADY_SEEN, "", now()))
    assert (await app.store.get_served(resp.recommendation_id)).items[0].label is None


@pytest.mark.asyncio
async def test_no_negative_inference_on_sensitive_topics(app):
    await app.record_engagement([ev("dave", "health-1", E.ENGAGEMENT_TYPE_HIDE, 1)])
    st = await app.intel.user_state("dave")
    assert not any(t.startswith("health") for t in st.negative_topics)


@pytest.mark.asyncio
async def test_legacy_posts_reach_adults_only(app):
    from ruc.policy import eligibility
    from ruc.context import RecContext
    legacy = item("legacy-1", "c1", {"sports": 1}, audience_unknown=True)
    minor = await app.intel.user_state("m1")
    adult = await app.intel.user_state("dave")
    assert cpb.EXCLUSION_REASON_AGE_RESTRICTED in eligibility.check_content(minor, legacy, RecContext(), app.s.policy)
    assert eligibility.check_content(adult, legacy, RecContext(), app.s.policy) == []
