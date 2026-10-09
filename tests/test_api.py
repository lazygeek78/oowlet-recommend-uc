"""End to end over gRPC: authentication and scopes, every service, the event
layer (fake broker), and the feature service (fake server)."""

from __future__ import annotations

import asyncio

import grpc
import numpy as np
import pytest
import pytest_asyncio
from google.protobuf import field_mask_pb2

from oowlet.gen.eventlayer.posteventspb import post_events_pb2 as pepb
from oowlet.gen.feature_service.featurepb import feature_pb2 as fpb
from oowlet.gen.feature_service.featurepb import feature_pb2_grpc as fgrpc
from oowlet.gen.feature_service.fscommonpb import fs_common_pb2 as fcpb
from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb
from oowlet.gen.recommenduc.eventspb import events_pb2 as evpb
from oowlet.gen.recommenduc.graphpb import graph_pb2 as gpb
from oowlet.gen.recommenduc.historypb import history_pb2 as hpb
from oowlet.gen.recommenduc.profilepb import profile_pb2 as ppb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb
from oowlet.gen.recommenduc.servicepb import service_pb2_grpc as sg

from ruc.events.broker import BrokerClient, BrokerEndpoint
from ruc.events.fake_broker import FakeBroker
from ruc.server import Server

from .helpers import settings, write_tokens

S = cpb


class FakeFeatureService(fgrpc.FeatureServiceServicer):
    def __init__(self, dim: int):
        self.dim = dim
        self.writes: list[fpb.WriteFeaturesRequest] = []
        self.auth: list[str] = []

    async def BatchGetFeatures(self, request, context):
        self.auth.append(dict(context.invocation_metadata()).get("authorization", ""))
        out = []
        for e in request.entities:
            v = np.zeros(self.dim, np.float32)
            v[hash(e.entity_id) % self.dim] = 1.0
            feats = [
                fcpb.FeatureValue(feature_id="content.embedding",
                                  vector_value=fcpb.FloatVector(values=list(v), dimension=self.dim, model_version="hashing-v1")),
                fcpb.FeatureValue(feature_id="content.topics", list_value=fcpb.StringList(values=["fs.topic:0.9"])),
                fcpb.FeatureValue(feature_id="content.credibility", float_value=0.3),
                fcpb.FeatureValue(feature_id="content.category", string_value="tutorial"),
            ]
            out.append(fpb.EntityFeaturesResult(entity_id=e.entity_id, features=feats, success=True))
        return fpb.BatchFeaturesResponse(results=out)

    async def WriteFeatures(self, request, context):
        self.writes.append(request)
        return fpb.WriteFeaturesResponse(written_count=len(request.features))


@pytest_asyncio.fixture
async def stack(tmp_path):
    broker = FakeBroker()
    bport = await broker.start("127.0.0.1:0")
    fs_server = grpc.aio.server()
    fake_fs = FakeFeatureService(256)
    fgrpc.add_FeatureServiceServicer_to_server(fake_fs, fs_server)
    fport = fs_server.add_insecure_port("127.0.0.1:0")
    await fs_server.start()
    (tmp_path / "fs.token").write_text("fs-secret")
    tokens = write_tokens(tmp_path / "tokens.json", [
        {"token": "t-alice", "kind": "user", "user_id": "alice"},
        {"token": "t-bob", "kind": "user", "user_id": "bob"},
        {"token": "t-gw", "kind": "service", "principal": "gateway",
         "scopes": ["recommend:on_behalf", "recommend:engagement:write"]},
        {"token": "t-sync", "kind": "service", "principal": "sync",
         "scopes": ["recommend:catalog:write", "recommend:catalog:read", "recommend:graph:write",
                    "recommend:profile:write", "recommend:features:write"]},
        {"token": "t-analytics", "kind": "service", "principal": "analytics", "scopes": ["recommend:history:read"]},
        {"token": "t-admin", "kind": "service", "principal": "admin", "scopes": ["recommend:admin"]},
    ])
    s = settings(tmp_path, RUC_AUTH__TOKENS_FILE=tmp_path / "tokens.json", RUC_SERVER__HOST="127.0.0.1",
                 RUC_SERVER__PORT=0, RUC_BROKER__ADDRESS=f"127.0.0.1:{bport}",
                 RUC_FEATURE_SERVICE__ADDRESS=f"127.0.0.1:{fport}",
                 RUC_FEATURE_SERVICE__TOKEN_FILE=tmp_path / "fs.token",
                 RUC_FEATURE_SERVICE__WRITE_BACK_MIN_INTERVAL_SECONDS=0, RUC_BROKER__LEGACY_POSTS_PUBLIC="true")
    srv = Server(s)
    port = await srv.start()
    for _ in range(100):
        if broker.subscribers("recommenduc.engagement.recorded"):
            break
        await asyncio.sleep(0.02)
    ch = grpc.aio.insecure_channel(f"127.0.0.1:{port}")
    stubs = {"rec": sg.RecommendationServiceStub(ch), "eng": sg.EngagementServiceStub(ch),
             "prof": sg.ProfileServiceStub(ch), "cat": sg.CatalogServiceStub(ch), "graph": sg.GraphServiceStub(ch),
             "hist": sg.HistoryServiceStub(ch)}
    yield stubs, tokens, srv, broker, fake_fs
    await ch.close()
    await srv.stop()
    await fs_server.stop(0)
    await broker.stop()


def md(token: str):
    return (("authorization", f"Bearer {token}"),)


def item(cid, creator, topic, **kw):
    m = ctpb.ContentItem(content_id=cid, creator_id=creator, kind=S.CONTENT_KIND_VIDEO, language="en",
                         topics=[S.TopicAffinity(topic_id=topic, weight=1.0)], visibility=ctpb.VISIBILITY_PUBLIC,
                         status=ctpb.CONTENT_STATUS_ACTIVE, quality_score=0.7, trust_score=0.9, version=1, **kw)
    m.published_at.GetCurrentTime()
    return m


def engagement(eid, uid, cid, t=epb.ENGAGEMENT_TYPE_LIKE, rec="", target=S.ENTITY_TYPE_CONTENT):
    e = epb.EngagementEvent(event_id=eid, user_id=uid, target=S.EntityRef(type=target, id=cid), type=t,
                            recommendation_id=rec)
    e.occurred_at.GetCurrentTime()
    return e


async def seed(stubs, tok):
    sync = md(tok["sync"])
    adult = ppb.UserAttributes(age_band=S.AGE_BAND_ADULT, country="IN", languages=["en"], trust_score=0.9)
    for u in ("alice", "bob", "carol", "c1", "c2"):
        await stubs["prof"].UpsertUserAttributes(ppb.UpsertUserAttributesRequest(user_id=u, attributes=adult), metadata=sync)
    for u in ("alice", "bob", "carol"):
        await stubs["prof"].UpdatePreferences(ppb.UpdatePreferencesRequest(
            user_id=u, preferences=ppb.Preferences(connections=ppb.ConnectionPreferences(open_to_connections=True)),
            update_mask=field_mask_pb2.FieldMask(paths=["connections.open_to_connections"])), metadata=md(tok["gateway"]))
    items = [item(f"s{i}", "c1", "sports") for i in range(6)] + [item(f"k{i}", "c2", "cooking") for i in range(6)]
    items.append(item("adult", "c1", "sports", audience=ctpb.AudienceRestriction(adults_only=True)))
    r = await stubs["cat"].UpsertContent(ctpb.UpsertContentRequest(items=items), metadata=sync)
    assert r.upserted == len(items)
    C = gpb.EDGE_TYPE_CONNECTED
    await stubs["graph"].UpsertEdges(gpb.UpsertEdgesRequest(edges=[
        gpb.Edge(from_user_id="alice", to_user_id="bob", type=C), gpb.Edge(from_user_id="bob", to_user_id="carol", type=C)]),
        metadata=sync)
    await stubs["eng"].RecordEngagement(epb.RecordEngagementRequest(events=[
        engagement(f"a{i}", "alice", f"s{i}") for i in range(3)] + [engagement(f"b{i}", "bob", f"k{i}") for i in range(3)]),
        metadata=md(tok["gateway"]))


@pytest.mark.asyncio
async def test_authentication_and_scopes(stack):
    stubs, tok, *_ = stack
    req = rpb.RecommendContentRequest(user_id="alice", limit=3)
    with pytest.raises(grpc.aio.AioRpcError) as e:
        await stubs["rec"].RecommendContent(req)
    assert e.value.code() == grpc.StatusCode.UNAUTHENTICATED
    with pytest.raises(grpc.aio.AioRpcError) as e:
        await stubs["rec"].RecommendContent(req, metadata=md("wrong"))
    assert e.value.code() == grpc.StatusCode.UNAUTHENTICATED
    with pytest.raises(grpc.aio.AioRpcError) as e:              # bob may not ask for alice
        await stubs["rec"].RecommendContent(req, metadata=md(tok["bob"]))
    assert e.value.code() == grpc.StatusCode.PERMISSION_DENIED
    with pytest.raises(grpc.aio.AioRpcError) as e:              # members never write the catalog
        await stubs["cat"].UpsertContent(ctpb.UpsertContentRequest(items=[item("x", "c1", "a")]), metadata=md(tok["alice"]))
    assert e.value.code() == grpc.StatusCode.PERMISSION_DENIED
    with pytest.raises(grpc.aio.AioRpcError) as e:              # analytics may not act for users
        await stubs["rec"].RecommendContent(req, metadata=md(tok["analytics"]))
    assert e.value.code() == grpc.StatusCode.PERMISSION_DENIED
    r = await stubs["eng"].RecordEngagement(epb.RecordEngagementRequest(events=[
        engagement("x1", "bob", "s1"), engagement("x2", "alice", "s1")]), metadata=md(tok["alice"]))
    assert r.accepted == 1 and r.rejected[0].event_id == "x1"   # a member records only their own events


@pytest.mark.asyncio
async def test_full_flow(stack):
    stubs, tok, srv, broker, fake_fs = stack
    await seed(stubs, tok)
    alice = md(tok["alice"])
    # feature service: enrichment at upsert (credibility lowers trust; topics kept from the catalog)
    got = await stubs["cat"].GetContent(ctpb.GetContentRequest(content_ids=["s5"]), metadata=md(tok["sync"]))
    assert got.items[0].trust_score == pytest.approx(0.3)
    assert fake_fs.auth and fake_fs.auth[0] == "Bearer fs-secret"

    resp = await stubs["rec"].RecommendContent(rpb.RecommendContentRequest(
        user_id="alice", limit=5, include_explanations=True,
        context=S.RequestContext(surface=S.SURFACE_HOME_FEED)), metadata=alice)
    ids = [i.content_id for i in resp.items]
    assert ids and resp.personalized and "adult" not in ids and not {"s0", "s1", "s2"} & set(ids)
    # attribution: alice likes the first item from this serve
    await stubs["eng"].RecordEngagement(epb.RecordEngagementRequest(events=[
        engagement("imp1", "alice", ids[0], epb.ENGAGEMENT_TYPE_IMPRESSION, resp.recommendation_id),
        engagement("lk1", "alice", ids[0], epb.ENGAGEMENT_TYPE_LIKE, resp.recommendation_id)]), metadata=alice)
    hist = await stubs["hist"].GetRecommendationHistory(hpb.GetRecommendationHistoryRequest(user_id="alice"), metadata=alice)
    assert hist.served[0].recommendation_id == resp.recommendation_id
    ex = await stubs["rec"].Explain(rpb.ExplainRequest(user_id="alice", recommendation_id=resp.recommendation_id,
                                                       item=S.EntityRef(type=S.ENTITY_TYPE_CONTENT, id=ids[0])), metadata=alice)
    assert ex.explanation.reasons
    with pytest.raises(grpc.aio.AioRpcError) as e:              # bob cannot read alice's serve
        await stubs["rec"].Explain(rpb.ExplainRequest(user_id="bob", recommendation_id=resp.recommendation_id,
                                                      item=S.EntityRef(type=S.ENTITY_TYPE_CONTENT, id=ids[0])), metadata=md(tok["bob"]))
    assert e.value.code() == grpc.StatusCode.NOT_FOUND

    ppl = await stubs["rec"].RecommendUsers(rpb.RecommendUsersRequest(user_id="alice", limit=5, include_explanations=True),
                                            metadata=alice)
    assert [u.user_id for u in ppl.items][:1] == ["carol"] and ppl.items[0].mutual_connections == 1

    elig = await stubs["rec"].CheckEligibility(rpb.CheckEligibilityRequest(user_id="alice", include_score=True, candidates=[
        S.EntityRef(type=S.ENTITY_TYPE_CONTENT, id="adult"), S.EntityRef(type=S.ENTITY_TYPE_CONTENT, id="k5"),
        S.EntityRef(type=S.ENTITY_TYPE_USER, id="bob"), S.EntityRef(type=S.ENTITY_TYPE_USER, id="carol")]), metadata=alice)
    assert [r.eligible for r in elig.results] == [False, True, False, True]
    assert S.EXCLUSION_REASON_AGE_RESTRICTED in elig.results[0].reasons
    assert S.EXCLUSION_REASON_ALREADY_CONNECTED in elig.results[2].reasons

    await stubs["rec"].SubmitFeedback(rpb.FeedbackRequest(user_id="alice", recommendation_id=resp.recommendation_id,
                                                          item=S.EntityRef(type=S.ENTITY_TYPE_CONTENT, id=ids[1]),
                                                          type=rpb.FEEDBACK_TYPE_NOT_INTERESTED), metadata=alice)
    again = await stubs["rec"].RecommendContent(rpb.RecommendContentRequest(user_id="alice", limit=20), metadata=alice)
    assert ids[1] not in [i.content_id for i in again.items]

    # history, engagement stats, trending, related
    uh = await stubs["hist"].GetUserHistory(hpb.GetUserHistoryRequest(user_id="alice"), metadata=alice)
    assert {e.event_id for e in uh.entries} >= {"a0", "lk1"}
    with pytest.raises(grpc.aio.AioRpcError):
        await stubs["hist"].GetUserHistory(hpb.GetUserHistoryRequest(user_id="bob"), metadata=alice)
    assert (await stubs["hist"].GetUserHistory(hpb.GetUserHistoryRequest(user_id="bob"), metadata=md(tok["analytics"]))).entries
    st = await stubs["eng"].GetContentEngagement(epb.GetContentEngagementRequest(content_ids=["s0"]), metadata=alice)
    assert st.stats[0].counters.likes == 1
    tr = await stubs["eng"].GetTrending(epb.GetTrendingRequest(), metadata=alice)
    assert tr.items and "adult" not in [i.content_id for i in tr.items]
    ch = await stubs["hist"].GetContentHistory(hpb.GetContentHistoryRequest(content_id="s0", granularity=S.GRANULARITY_HOUR),
                                               metadata=alice)
    assert sum(b.counters.likes for b in ch.buckets) == 1
    rel = await stubs["hist"].GetRelatedContent(hpb.GetRelatedContentRequest(content_id="s0", limit=5), metadata=alice)
    assert rel.items and "adult" not in [i.content_id for i in rel.items]
    summ = await stubs["eng"].GetUserEngagementSummary(epb.GetUserEngagementSummaryRequest(user_id="alice"), metadata=alice)
    assert summ.summary.counters.likes >= 4 and summ.summary.top_topics

    # engagers: alice's like is listed only once she allows her activity to be shown
    eng = await stubs["hist"].GetContentEngagers(hpb.GetContentEngagersRequest(content_id="s0", viewer_id="bob"),
                                                 metadata=md(tok["bob"]))
    assert not eng.engagers
    await stubs["prof"].UpdatePrivacySettings(ppb.UpdatePrivacySettingsRequest(
        user_id="alice", privacy=ppb.PrivacySettings(show_activity_to_others=True),
        update_mask=field_mask_pb2.FieldMask(paths=["show_activity_to_others"])), metadata=alice)
    eng = await stubs["hist"].GetContentEngagers(hpb.GetContentEngagersRequest(content_id="s0", viewer_id="bob"),
                                                 metadata=md(tok["bob"]))
    assert [e.user_id for e in eng.engagers] == ["alice"]
    prof = await stubs["prof"].GetProfile(ppb.GetProfileRequest(user_id="alice"), metadata=alice)
    assert prof.profile.privacy.show_activity_to_others and prof.profile.privacy.personalization_enabled

    # the engine's user features were written back to the feature service
    await asyncio.sleep(0.2)
    assert any(w.entity_id == "alice" and w.entity_type == "user" for w in fake_fs.writes)

    # served recommendations went to the event layer
    assert any(e.event_type == "recommenduc.recommendation.served" for e in broker.published)

    # erasure
    await stubs["prof"].DeleteUserData(ppb.DeleteUserDataRequest(user_id="alice"), metadata=alice)
    assert not (await stubs["hist"].GetUserHistory(hpb.GetUserHistoryRequest(user_id="alice"), metadata=alice)).entries
    with pytest.raises(grpc.aio.AioRpcError) as e:
        await stubs["prof"].GetProfile(ppb.GetProfileRequest(user_id="alice"), metadata=alice)
    assert e.value.code() == grpc.StatusCode.NOT_FOUND


@pytest.mark.asyncio
async def test_validation(stack):
    stubs, tok, *_ = stack
    sync = md(tok["sync"])
    with pytest.raises(grpc.aio.AioRpcError) as e:
        await stubs["prof"].UpsertProfileFeatures(ppb.UpsertProfileFeaturesRequest(
            user_id="bob", inferred_interests=[S.TopicAffinity(topic_id="health.diabetes", weight=0.9)]), metadata=sync)
    assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT                 # sensitive is never inferred
    with pytest.raises(grpc.aio.AioRpcError) as e:
        await stubs["prof"].UpdatePreferences(ppb.UpdatePreferencesRequest(
            user_id="bob", update_mask=field_mask_pb2.FieldMask(paths=["nope"])), metadata=md(tok["bob"]))
    assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    with pytest.raises(grpc.aio.AioRpcError) as e:
        await stubs["rec"].RecommendContent(rpb.RecommendContentRequest(user_id="bob", page=S.PageRequest(page_token="zz")),
                                            metadata=md(tok["bob"]))
    assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    r = await stubs["eng"].RecordEngagement(epb.RecordEngagementRequest(events=[
        epb.EngagementEvent(event_id="bad", user_id="bob", target=S.EntityRef(type=S.ENTITY_TYPE_CONTENT, id="s1"))]),
        metadata=md(tok["bob"]))
    assert r.accepted == 0 and "engagement type" in r.rejected[0].reason


@pytest.mark.asyncio
async def test_events_from_the_event_layer(stack):
    stubs, tok, srv, broker, _ = stack
    pub = BrokerClient(BrokerEndpoint(address=f"127.0.0.1:{broker._server and srv.s.broker.address.split(':')[1]}"),
                       source="test")
    it = item("ev1", "c9", "travel")
    await pub.publish(pub.envelope("recommenduc.content.changed", evpb.ContentChanged(change=evpb.CHANGE_TYPE_UPSERTED, item=it)))
    await pub.publish(pub.envelope("recommenduc.profile.changed", evpb.ProfileChanged(
        user_id="zed", changed=field_mask_pb2.FieldMask(paths=["age_band", "country"]),
        attributes=ppb.UserAttributes(age_band=S.AGE_BAND_ADULT, country="US"))))
    await pub.publish(pub.envelope("recommenduc.engagement.recorded", evpb.EngagementRecorded(
        events=[engagement("ev-e1", "zed", "ev1")])))
    await pub.publish(pub.envelope("recommenduc.graph.changed", evpb.GraphChanged(
        upserted=[gpb.Edge(from_user_id="zed", to_user_id="c9", type=gpb.EDGE_TYPE_FOLLOWS)])))
    # legacy producers
    await pub.publish(pub.envelope("post.created", pepb.PostCreatedEvent(post_id="p1", user_id="c9", content_type="image",
                                                                         tags=["travel"])))
    await pub.publish(pub.envelope("post.engagement", pepb.PostEngagementEvent(post_id="p1", user_id="zed",
                                                                             engagement_type="like")))
    app = srv.app
    for _ in range(100):
        if len(await app.store.user_events("zed")) >= 2 and await app.store.has_edge("zed", "c9", gpb.EDGE_TYPE_FOLLOWS):
            break
        await asyncio.sleep(0.02)
    assert (await app.store.get_user("zed")).country == "US"
    assert {e.target_id for e in await app.store.user_events("zed")} == {"ev1", "p1"}
    assert "p1" in await app.store.get_content(["p1"])
    assert srv.consumer.handled >= 6
    await pub.close()


@pytest.mark.asyncio
async def test_cli_serve_process(tmp_path):
    """The real entry point, as a separate process: channels must be built on
    the server's own event loop (events arrive, the API answers)."""
    import os
    import socket
    import sys
    broker = FakeBroker()
    bport = await broker.start("127.0.0.1:0")
    tok = write_tokens(tmp_path / "tokens.json", [{"token": "t-u1", "kind": "user", "user_id": "u1"}])
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    sport = s.getsockname()[1]
    s.close()
    env = {**os.environ, "RUC_ENV": "development", "RUC_SERVER__TLS_ENABLED": "false", "RUC_SERVER__HOST": "127.0.0.1",
           "RUC_SERVER__PORT": str(sport), "RUC_AUTH__TOKENS_FILE": str(tmp_path / "tokens.json"),
           "RUC_BROKER__ADDRESS": f"127.0.0.1:{bport}", "RUC_RANKING__MODEL_DIR": str(tmp_path / "m"),
           "RUC_LOG_LEVEL": "WARNING"}
    proc = await asyncio.create_subprocess_exec(sys.executable, "-m", "ruc.cli", "serve", env=env)
    pub = BrokerClient(BrokerEndpoint(address=f"127.0.0.1:{bport}"), source="test")
    ch = grpc.aio.insecure_channel(f"127.0.0.1:{sport}")
    try:
        await asyncio.wait_for(ch.channel_ready(), 30)
        for _ in range(200):
            if broker.subscribers("recommenduc.engagement.recorded"):
                break
            await asyncio.sleep(0.05)
        await pub.publish(pub.envelope("recommenduc.engagement.recorded", evpb.EngagementRecorded(
            events=[engagement("p-e1", "u1", "x1")])))
        hist = sg.HistoryServiceStub(ch)
        entries = []
        for _ in range(100):
            entries = (await hist.GetUserHistory(hpb.GetUserHistoryRequest(user_id="u1"), metadata=md(tok["u1"]))).entries
            if entries:
                break
            await asyncio.sleep(0.05)
        assert [e.event_id for e in entries] == ["p-e1"]
    finally:
        await ch.close()
        await pub.close()
        proc.terminate()
        assert await asyncio.wait_for(proc.wait(), 30) == 0
        await broker.stop()
