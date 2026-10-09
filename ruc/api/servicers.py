"""gRPC services (recommenduc/service.proto). Every RPC authenticates the
caller first; access rules per RPC follow service.proto and history.proto."""

from __future__ import annotations

import functools
import logging
from datetime import datetime, timezone

import grpc

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.contentpb import content_pb2 as ctpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb
from oowlet.gen.recommenduc.graphpb import graph_pb2 as gpb
from oowlet.gen.recommenduc.historypb import history_pb2 as hpb
from oowlet.gen.recommenduc.profilepb import profile_pb2 as ppb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb
from oowlet.gen.recommenduc.servicepb import service_pb2_grpc as sg

from .. import convert, signals
from ..app import App
from ..context import RecContext
from ..domain import CONNECTED, CONTENT, USER, Feedback, Topic, now
from ..engines.common import PageTokenError
from ..policy import eligibility
from ..policy.diversity import Ranked
from ..store.base import COUNTER_OF, Counters, NotFound, VersionConflict
from .auth import AuthError, Principal, TokenAuthenticator, acting_user, require_scope

log = logging.getLogger("ruc.api")
DAY = 86400.0
WINDOW_SECONDS = {cpb.WINDOW_SIZE_1H: 3600, cpb.WINDOW_SIZE_24H: DAY, cpb.WINDOW_SIZE_7D: 7 * DAY,
                  cpb.WINDOW_SIZE_30D: 30 * DAY, cpb.WINDOW_SIZE_90D: 90 * DAY, cpb.WINDOW_SIZE_ALL_TIME: 3650 * DAY}
GRAN_SECONDS = {cpb.GRANULARITY_HOUR: 3600, cpb.GRANULARITY_DAY: int(DAY), cpb.GRANULARITY_WEEK: int(7 * DAY)}


def rpc(fn):
    """Authenticate, then map errors to status codes."""
    @functools.wraps(fn)
    async def wrapper(self, request, context):
        try:
            principal = self.auth.authenticate(context)
            return await fn(self, principal, request, context)
        except grpc.aio.AbortError:
            raise
        except AuthError as e:
            await context.abort(e.code, str(e))
        except (convert.Invalid, PageTokenError) as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except VersionConflict as e:
            await context.abort(grpc.StatusCode.ABORTED, str(e))
        except NotFound as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e).strip("'"))
        except Exception:  # noqa: BLE001
            log.exception("%s failed", fn.__name__)
            await context.abort(grpc.StatusCode.INTERNAL, "internal error")
    return wrapper


def _limit(n: int, cap: int, what: str) -> None:
    if n > cap:
        raise convert.Invalid(f"at most {cap} {what} per call")


def _page(page: cpb.PageRequest, default: int, cap: int) -> tuple[int, int]:
    size = max(1, min(page.page_size or default, cap))
    if not page.page_token:
        return 0, size
    try:
        off = int(page.page_token)
    except ValueError:
        raise convert.Invalid("malformed page_token") from None
    if off < 0:
        raise convert.Invalid("malformed page_token")
    return off, size


def _page_resp(off: int, size: int, total: int) -> cpb.PageResponse:
    nxt = off + size
    return cpb.PageResponse(next_page_token=str(nxt) if nxt < total else "", total_estimate=total)


def _window(w: cpb.TimeWindow, default_days: float = 30.0) -> tuple[float, float]:
    end = convert.ts_of(w.end, now()) if w.HasField("end") else now()
    start = convert.ts_of(w.start, end - default_days * DAY) if w.HasField("start") else end - default_days * DAY
    if start >= end:
        raise convert.Invalid("window: start must be before end")
    return start, end


class Base:
    def __init__(self, app: App, auth: TokenAuthenticator) -> None:
        self.app = app
        self.auth = auth


# ── RecommendationService ──────────────────────────────────────────────────

class RecommendationServicer(Base, sg.RecommendationServiceServicer):
    @rpc
    async def RecommendContent(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        _limit(len(req.exclude_content_ids), 1000, "exclude_content_ids")
        return await self.app.content.recommend(uid, req)

    @rpc
    async def RecommendUsers(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        _limit(len(req.exclude_user_ids), 1000, "exclude_user_ids")
        return await self.app.people.recommend(uid, req)

    @rpc
    async def CheckEligibility(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        _limit(len(req.candidates), 100, "candidates")
        ctx = RecContext.from_proto(req.context)
        st = await self.app.intel.user_state(uid, ctx.session_id, ctx.utc_offset_minutes, ctx.t)
        contents = [c.id for c in req.candidates if c.type == cpb.ENTITY_TYPE_CONTENT]
        users = [c.id for c in req.candidates if c.type in (cpb.ENTITY_TYPE_USER, cpb.ENTITY_TYPE_CREATOR)]
        if len(contents) + len(users) != len(req.candidates):
            raise convert.Invalid("candidates must be CONTENT or USER")
        got: dict[tuple[int, str], rpb.EligibilityResult] = {}
        for r in await self.app.content.check(st, ctx, contents, req.include_score, req.include_explanations):
            got[(CONTENT, r.candidate.id)] = r
        for r in await self.app.people.check(st, ctx, users, req.include_score, req.include_explanations):
            got[(USER, r.candidate.id)] = r
        out = []
        for c in req.candidates:
            r = got[(CONTENT if c.type == cpb.ENTITY_TYPE_CONTENT else USER, c.id)]
            r.candidate.CopyFrom(c)
            out.append(r)
        model, variant = self.app.models.choose("content", uid)
        return rpb.CheckEligibilityResponse(results=out, model=cpb.ModelInfo(
            model_id=model.model_id, model_version=model.version, experiment_id=self.app.s.ranking.experiment_id,
            variant=variant))

    @rpc
    async def Explain(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        served = await self.app.store.get_served(req.recommendation_id)
        if served is None or served.user_id != uid:
            raise NotFound("recommendation not found")
        item = next((i for i in served.items if i.target_id == req.item.id
                     and (i.target_type == CONTENT) == (req.item.type == cpb.ENTITY_TYPE_CONTENT)), None)
        if item is None:
            raise NotFound("item was not part of this recommendation")
        engine = served.engine
        model = (self.app.models.logistic.get(engine) if served.model_id == "logistic" else None) \
            or self.app.models.weighted[engine]
        sc = model.score(item.features, served.surface)
        r = Ranked(key=item.target_id, score=item.score, features=item.features, contributions=sc.contributions,
                   sources=item.sources)
        st = await self.app.intel.user_state(uid)
        ctx = RecContext(surface=served.surface)
        # explained only while still eligible: nothing about someone who has
        # since blocked the viewer, or content that was removed
        if engine == "content":
            if not await self.app.content.still_eligible(st, ctx, [r], hard_only=True):
                raise NotFound("item no longer available")
            rec = (await self.app.store.get_content([item.target_id])).get(item.target_id)
            expl = self.app.content.explain(st, r, rec, ctx, set())
        else:
            if not await self.app.people.still_eligible(st, [r], hard_only=True):
                raise NotFound("user no longer available")
            other = await self.app.store.get_user(item.target_id)
            expl = self.app.people.explain(st, r, other, ctx, set(), self.app.people.shared_topics(st, other))
        return rpb.ExplainResponse(explanation=expl)

    @rpc
    async def SubmitFeedback(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        if req.type == rpb.FEEDBACK_TYPE_UNSPECIFIED or req.type not in rpb.FeedbackType.values():
            raise convert.Invalid("feedback type is required")
        if req.item.type not in (cpb.ENTITY_TYPE_CONTENT, cpb.ENTITY_TYPE_USER) or not req.item.id:
            raise convert.Invalid("item must be a CONTENT or USER reference")
        if req.type == rpb.FEEDBACK_TYPE_SEE_LESS_OF_TOPIC and not req.topic_id:
            raise convert.Invalid("topic_id is required for SEE_LESS_OF_TOPIC")
        if len(req.comment) > 500:
            raise convert.Invalid("comment: at most 500 characters")
        await self.app.feedback(Feedback(
            user_id=uid, recommendation_id=req.recommendation_id[:64],
            target_type=CONTENT if req.item.type == cpb.ENTITY_TYPE_CONTENT else USER, target_id=req.item.id[:128],
            type=req.type, topic_id=req.topic_id[:128], given_at=now()))
        return rpb.FeedbackResponse()


# ── EngagementService ──────────────────────────────────────────────────────

class EngagementServicer(Base, sg.EngagementServiceServicer):
    async def _record(self, p: Principal, events) -> epb.RecordEngagementResponse:
        accepted, rejected = [], []
        t = now()
        for e in events:
            if p.kind == "user" and e.user_id != p.user_id:
                rejected.append(epb.RejectedEngagement(event_id=e.event_id, reason="user_id does not match the caller"))
                continue
            if p.kind == "service" and not p.has("recommend:engagement:write"):
                raise AuthError(grpc.StatusCode.PERMISSION_DENIED, "requires scope recommend:engagement:write")
            try:
                accepted.append(convert.engagement_from_proto(e, t))
            except convert.Invalid as exc:
                rejected.append(epb.RejectedEngagement(event_id=e.event_id, reason=str(exc)))
        n, dupes = await self.app.record_engagement(accepted)
        return epb.RecordEngagementResponse(accepted=n, duplicates=dupes, rejected=rejected)

    @rpc
    async def RecordEngagement(self, p: Principal, req, context):
        _limit(len(req.events), 500, "events")
        return await self._record(p, req.events)

    async def RecordEngagementStream(self, request_iterator, context):
        try:
            p = self.auth.authenticate(context)
            total = epb.RecordEngagementResponse()
            async for req in request_iterator:
                if len(req.events) > 500:
                    raise convert.Invalid("at most 500 events per message")
                r = await self._record(p, req.events)
                total.accepted += r.accepted
                total.duplicates += r.duplicates
                total.rejected.extend(r.rejected)
            return total
        except grpc.aio.AbortError:
            raise
        except AuthError as e:
            await context.abort(e.code, str(e))
        except convert.Invalid as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

    @rpc
    async def GetContentEngagement(self, p: Principal, req, context):
        _limit(len(req.content_ids), 200, "content_ids")
        windows = list(req.windows) or [cpb.WINDOW_SIZE_24H, cpb.WINDOW_SIZE_7D]
        t = now()
        out = []
        known = await self.app.store.get_content(req.content_ids)
        for cid in req.content_ids:
            if cid not in known:
                continue
            for w in windows:
                if w not in WINDOW_SECONDS:
                    raise convert.Invalid(f"unknown window {w}")
                span = WINDOW_SECONDS[w]
                c = await self.app.store.content_counters(cid, t - span)
                recent = await self.app.store.content_counters(cid, t - min(span, 6 * 3600))
                views = c.counts["views"] + c.counts["opens"]
                hours = max(span / 3600.0, 1.0)
                stats = epb.ContentEngagementStats(
                    content_id=cid, window=w, counters=convert.counters_to_proto(c),
                    open_rate=c.counts["opens"] / c.counts["impressions"] if c.counts["impressions"] else 0.0,
                    completion_rate=c.counts["completions"] / c.counts["views"] if c.counts["views"] else 0.0,
                    engagement_rate=c.positives / views if views else 0.0,
                    negative_rate=c.negatives / c.counts["impressions"] if c.counts["impressions"] else 0.0,
                    velocity=recent.positives / min(hours, 6.0) - c.positives / hours,
                    avg_dwell_seconds=c.dwell_seconds / views if views else 0.0)
                stats.computed_at.GetCurrentTime()
                out.append(stats)
        return epb.GetContentEngagementResponse(stats=out)

    @rpc
    async def GetUserEngagementSummary(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id, scope="recommend:history:read")
        w = req.window or cpb.WINDOW_SIZE_30D
        if w not in WINDOW_SECONDS:
            raise convert.Invalid(f"unknown window {w}")
        t = now()
        events = await self.app.store.user_events(uid, since=t - WINDOW_SECONDS[w])
        st = await self.app.intel.user_state(uid)
        counters = Counters()
        hours = [0] * 24
        for ev in events:
            k = COUNTER_OF.get(ev.type)
            if k:
                counters.counts[k] += 1
            counters.dwell_seconds += ev.dwell_s
            hours[datetime.fromtimestamp(ev.ts, tz=timezone.utc).hour] += 1
        counters.unique_users = 1 if events else 0
        topics = [convert.topic_to_proto(Topic(tid, wt)) for tid, wt in
                  sorted(st.topic_affinity.items(), key=lambda kv: -kv[1])[:20]]
        creators = [epb.CreatorAffinity(creator_id=c, weight=wt) for c, wt in
                    sorted(st.creator_affinity.items(), key=lambda kv: -kv[1])[:20]]
        summary = epb.UserEngagementSummary(
            user_id=uid, window=w, counters=convert.counters_to_proto(counters), top_topics=topics,
            top_creators=creators,
            kind_mix=[epb.ContentKindShare(kind=k, share=v) for k, v in sorted(st.kind_affinity.items())],
            activity_by_hour=hours, last_active_at=convert.to_ts(events[0].ts if events else 0))
        summary.computed_at.GetCurrentTime()
        return epb.GetUserEngagementSummaryResponse(summary=summary)

    @rpc
    async def GetTrending(self, p: Principal, req, context):
        off, size = _page(req.page, 20, 100)
        w = req.window or cpb.WINDOW_SIZE_24H
        t = now()
        scores = await self.app.intel.trending_window(WINDOW_SECONDS.get(w, DAY), t)
        recs = await self.app.store.get_content([c for c, _ in scores])
        anon = await self.app.intel.user_state("\x00anonymous")     # unknown user: strictest rules
        ctx = RecContext.from_proto(req.context)
        if req.country:
            ctx.country = req.country.upper()
        kinds, topics = set(req.kinds), set(req.topic_ids)
        mx = scores[0][1] if scores else 1.0
        items = []
        for cid, s in scores:
            rec = recs.get(cid)
            if rec is None or (kinds and rec.kind not in kinds) or (topics and not topics & set(rec.topic_weights())):
                continue
            if eligibility.check_content(anon, rec, ctx, self.app.s.policy):
                continue
            items.append((cid, s / mx))
        page = items[off: off + size]
        stats = {}
        for cid, _ in page:
            c = await self.app.store.content_counters(cid, t - WINDOW_SECONDS.get(w, DAY))
            stats[cid] = epb.ContentEngagementStats(content_id=cid, window=w, counters=convert.counters_to_proto(c))
        return epb.GetTrendingResponse(items=[epb.TrendingItem(content_id=c, score=s, stats=stats[c]) for c, s in page],
                                       page=_page_resp(off, size, len(items)))


# ── ProfileService ─────────────────────────────────────────────────────────

class ProfileServicer(Base, sg.ProfileServiceServicer):
    @rpc
    async def GetProfile(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        u, known = await self.app.intel.user_record(uid)
        if not known:
            raise NotFound("no profile")
        return ppb.GetProfileResponse(profile=convert.profile_to_proto(u, embeddings="embeddings" in req.read_mask.paths))

    @rpc
    async def UpdatePreferences(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        paths = list(req.update_mask.paths)

        def change(u):
            u.preferences = convert.apply_prefs(u.preferences, req.preferences, paths)
            u.declared_topics = [Topic(t, 1.0, sensitive=self.app.intel.is_sensitive(t), source=cpb.AFFINITY_SOURCE_DECLARED)
                                 for t in u.preferences.preferred_topic_ids]
            return u
        u = await self.app.update_user(uid, change, req.expected_version)
        return ppb.UpdatePreferencesResponse(profile=convert.profile_to_proto(u))

    @rpc
    async def UpdatePrivacySettings(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        paths = list(req.update_mask.paths)

        def change(u):
            u.privacy = convert.apply_privacy(u.privacy, req.privacy, paths)
            return u
        u = await self.app.update_user(uid, change, req.expected_version)
        return ppb.UpdatePrivacySettingsResponse(profile=convert.profile_to_proto(u))

    @rpc
    async def UpsertUserAttributes(self, p: Principal, req, context):
        require_scope(p, "recommend:profile:write")
        convert._id(req.user_id, "user_id")
        paths = list(req.update_mask.paths)
        u = await self.app.update_user(req.user_id, lambda u: convert.apply_attributes(u, req.attributes, paths))
        return ppb.UpsertUserAttributesResponse(version=u.version)

    @rpc
    async def UpsertProfileFeatures(self, p: Principal, req, context):
        require_scope(p, "recommend:features:write")
        convert._id(req.user_id, "user_id")
        _limit(len(req.inferred_interests), 200, "inferred_interests")
        topics = [convert.topic_from_proto(t) for t in req.inferred_interests]
        if any(t.sensitive or self.app.intel.is_sensitive(t.topic_id) for t in topics):
            raise convert.Invalid("sensitive topics are never inferred: remove them from inferred_interests")
        embs = convert.embeddings_from_proto(req.embeddings)

        def change(u):
            u.inferred_topics = topics
            u.embeddings.update(embs)
            return u
        u = await self.app.update_user(req.user_id, change, req.expected_version)
        return ppb.UpsertProfileFeaturesResponse(version=u.version)

    @rpc
    async def DeleteUserData(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id, scope="recommend:admin")
        t = await self.app.delete_user_data(uid)
        log.info("erased data of a user (%s) by %s", req.reason[:64] or "unspecified", p.principal_id)
        return ppb.DeleteUserDataResponse(erased_at=convert.to_ts(t))


# ── CatalogService ─────────────────────────────────────────────────────────

class CatalogServicer(Base, sg.CatalogServiceServicer):
    @rpc
    async def UpsertContent(self, p: Principal, req, context):
        require_scope(p, "recommend:catalog:write")
        _limit(len(req.items), 100, "items")
        items = [convert.content_from_proto(i) for i in req.items]
        stale, n = [], 0
        for it in items:
            if await self.app.upsert_content(it):
                n += 1
            else:
                stale.append(it.content_id)
        return ctpb.UpsertContentResponse(upserted=n, stale_ignored=stale)

    @rpc
    async def RemoveContent(self, p: Principal, req, context):
        require_scope(p, "recommend:catalog:write")
        convert._id(req.content_id, "content_id")
        await self.app.set_content_status(req.content_id, req.status)
        return ctpb.RemoveContentResponse()

    @rpc
    async def GetContent(self, p: Principal, req, context):
        if not (p.has("recommend:catalog:read") or p.has("recommend:catalog:write")):
            raise AuthError(grpc.StatusCode.PERMISSION_DENIED, "requires scope recommend:catalog:read")
        _limit(len(req.content_ids), 200, "content_ids")
        got = await self.app.store.get_content(req.content_ids)
        return ctpb.GetContentResponse(items=[convert.content_to_proto(got[c], req.include_embeddings) for c in req.content_ids if c in got],
                                       not_found=[c for c in req.content_ids if c not in got])


# ── GraphService ───────────────────────────────────────────────────────────

class GraphServicer(Base, sg.GraphServiceServicer):
    @rpc
    async def UpsertEdges(self, p: Principal, req, context):
        require_scope(p, "recommend:graph:write")
        _limit(len(req.edges), 500, "edges")
        return gpb.UpsertEdgesResponse(upserted=await self.app.upsert_edges([convert.edge_from_proto(e) for e in req.edges]))

    @rpc
    async def RemoveEdges(self, p: Principal, req, context):
        require_scope(p, "recommend:graph:write")
        _limit(len(req.edges), 500, "edges")
        return gpb.RemoveEdgesResponse(removed=await self.app.remove_edges([convert.edge_from_proto(e) for e in req.edges]))

    @rpc
    async def GetConnections(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id, scope="recommend:history:read")
        types = frozenset(req.types) or frozenset({CONNECTED})
        edges = await self.app.store.out_edges(uid, types)
        if CONNECTED in types:
            seen = {(e.to_user_id, e.type) for e in edges}
            edges += [e for e in await self.app.store.in_edges(uid, frozenset({CONNECTED}))
                      if (e.from_user_id, e.type) not in seen]
        off, size = _page(req.page, 100, 500)
        return gpb.GetConnectionsResponse(edges=[convert.edge_to_proto(e) for e in edges[off: off + size]],
                                          page=_page_resp(off, size, len(edges)))

    @rpc
    async def GetMutualConnections(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id)
        from ..candidates.generators import mutual_connections
        st = await self.app.intel.user_state(uid)
        other, known = await self.app.intel.user_record(req.other_user_id)
        if (not known or req.other_user_id in st.blocked or not other.privacy.allow_mutual_connection_signal):
            return gpb.GetMutualConnectionsResponse()
        mutual = sorted((await mutual_connections(st, self.app.intel)).get(req.other_user_id, set()))
        return gpb.GetMutualConnectionsResponse(count=len(mutual),
                                                sample_user_ids=mutual[: max(0, min(req.sample_size, 10))])


# ── HistoryService ─────────────────────────────────────────────────────────

class HistoryServicer(Base, sg.HistoryServiceServicer):
    @rpc
    async def GetUserHistory(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id, scope="recommend:history:read")
        start, end = _window(req.window, 30)
        off, size = _page(req.page, 100, 500)
        types = frozenset(req.types) or None
        # stored targets are CONTENT or USER (a CREATOR target is stored as USER)
        wanted = {CONTENT if x == cpb.ENTITY_TYPE_CONTENT else USER for x in req.target_types}
        evs = await self.app.store.user_events(uid, since=start, until=end, types=types)
        if wanted:
            evs = [e for e in evs if e.target_type in wanted]
        page = evs[off: off + size]
        return hpb.GetUserHistoryResponse(entries=[hpb.HistoryEntry(
            event_id=e.event_id, target=cpb.EntityRef(type=e.target_type, id=e.target_id), type=e.type,
            occurred_at=convert.to_ts(e.ts), surface=e.surface, recommendation_id=e.recommendation_id) for e in page],
            page=_page_resp(off, size, len(evs)))

    @rpc
    async def GetContentHistory(self, p: Principal, req, context):
        convert._id(req.content_id, "content_id")
        start, end = _window(req.window, 7)
        gran = GRAN_SECONDS.get(req.granularity or cpb.GRANULARITY_DAY)
        if gran is None:
            raise convert.Invalid("unknown granularity")
        if (end - start) / gran > 2000:
            raise convert.Invalid("too many buckets: widen the granularity or shorten the window")
        rows = await self.app.store.content_timeline(req.content_id, start, end, gran)
        return hpb.GetContentHistoryResponse(content_id=req.content_id, buckets=[
            hpb.TimelineBucket(start=convert.to_ts(s), counters=convert.counters_to_proto(c)) for s, c in rows])

    @rpc
    async def GetContentEngagers(self, p: Principal, req, context):
        viewer = acting_user(p, req.viewer_id)
        convert._id(req.content_id, "content_id")
        off, size = _page(req.page, 50, 200)
        st = await self.app.intel.user_state(viewer)
        types = frozenset(req.types) or frozenset({epb.ENGAGEMENT_TYPE_LIKE, epb.ENGAGEMENT_TYPE_COMMENT,
                                                   epb.ENGAGEMENT_TYPE_SHARE, epb.ENGAGEMENT_TYPE_REPOST})
        evs = await self.app.store.content_engagers(req.content_id, types)
        users = await self.app.store.get_users({e.user_id for e in evs})
        out, seen = [], set()
        for e in evs:
            u = users.get(e.user_id)
            if (u is None or e.user_id in seen or not u.privacy.show_activity_to_others or e.user_id in st.blocked
                    or viewer in u.preferences.blocked_user_ids or (req.connections_only and e.user_id not in st.connections)):
                continue
            seen.add(e.user_id)
            out.append(hpb.Engager(user_id=e.user_id, type=e.type, occurred_at=convert.to_ts(e.ts)))
        return hpb.GetContentEngagersResponse(engagers=out[off: off + size], page=_page_resp(off, size, len(out)))

    @rpc
    async def GetRelatedContent(self, p: Principal, req, context):
        convert._id(req.content_id, "content_id")
        k = max(1, min(req.limit or 20, 100))
        rels = set(req.relations) or {hpb.RELATION_TYPE_SIMILAR, hpb.RELATION_TYPE_CO_ENGAGED}
        store, intel = self.app.store, self.app.intel
        seed = (await store.get_content([req.content_id])).get(req.content_id)
        if seed is None:
            raise NotFound("content not found")
        found: dict[str, tuple[int, float]] = {}

        def add(cid, rel, s):
            if cid != req.content_id and (cid not in found or found[cid][1] < s):
                found[cid] = (rel, s)
        if hpb.RELATION_TYPE_SIMILAR in rels:
            v = intel.content_index.get(req.content_id)
            if v is not None:
                for cid, s in intel.content_index.search(v, k * 2, exclude={req.content_id}):
                    add(cid, hpb.RELATION_TYPE_SIMILAR, max(s, 0.0))
        if hpb.RELATION_TYPE_CO_ENGAGED in rels:
            nb = await store.co_engaged(req.content_id, k * 2)
            mx = nb[0][1] if nb else 1.0
            for cid, s in nb:
                add(cid, hpb.RELATION_TYPE_CO_ENGAGED, s / mx)
        if rels & {hpb.RELATION_TYPE_SAME_CREATOR, hpb.RELATION_TYPE_SEQUEL}:
            for it in await store.content_by_creators([seed.creator_id], 0.0, k * 2):
                rel = hpb.RELATION_TYPE_SEQUEL if it.published_at > seed.published_at and hpb.RELATION_TYPE_SEQUEL in rels \
                    else hpb.RELATION_TYPE_SAME_CREATOR
                if rel in rels:
                    add(it.content_id, rel, 0.5)
        if hpb.RELATION_TYPE_SAME_TOPIC in rels and seed.primary_topic():
            for it in await store.content_by_topics([seed.primary_topic()], k * 2):
                add(it.content_id, hpb.RELATION_TYPE_SAME_TOPIC, 0.4)
        # filtered with the viewer's rules, or the strictest (anonymous) ones
        if req.for_user_id:
            viewer = acting_user(p, req.for_user_id)
        else:
            viewer = "\x00anonymous"
        st = await intel.user_state(viewer)
        recs = await store.get_content(found)
        creators = await store.get_users({r.creator_id for r in recs.values()})
        ctx = RecContext()
        items = [hpb.RelatedContent(content_id=c, relation=rel, score=s)
                 for c, (rel, s) in sorted(found.items(), key=lambda kv: -kv[1][1])
                 if not eligibility.check_content(st, recs.get(c), ctx, self.app.s.policy,
                                                  creators.get(recs[c].creator_id) if c in recs else None)]
        return hpb.GetRelatedContentResponse(items=items[:k])

    @rpc
    async def GetSimilarUsers(self, p: Principal, req, context):
        require_scope(p, "recommend:history:read")
        convert._id(req.user_id, "user_id")
        from ..candidates.generators import GenInput, similar_users
        k = max(1, min(req.limit or 50, 200))
        st = await self.app.intel.user_state(req.user_id)
        bases = set(req.bases)
        sims = await similar_users(GenInput(st=st, ctx=RecContext(), intel=self.app.intel, k=k), n=k)
        out = [hpb.SimilarUser(user_id=u, score=s, basis=hpb.SIMILARITY_BASIS_CO_ENGAGEMENT) for u, s in sims.items()]
        if not bases or hpb.SIMILARITY_BASIS_GRAPH in bases:
            from ..candidates.generators import mutual_connections
            graph = sorted((await mutual_connections(st, self.app.intel)).items(), key=lambda kv: -len(kv[1]))[:k]
            recs = await self.app.store.get_users([u for u, _ in graph])
            for u, m in graph:
                if u in recs and recs[u].privacy.contribute_to_collaborative:      # history.proto
                    out.append(hpb.SimilarUser(user_id=u, score=signals.saturate(len(m), 3.0),
                                               basis=hpb.SIMILARITY_BASIS_GRAPH))
        if bases:
            out = [s for s in out if s.basis in bases or (s.basis == hpb.SIMILARITY_BASIS_CO_ENGAGEMENT
                                                          and hpb.SIMILARITY_BASIS_INTERESTS in bases)]
        out.sort(key=lambda s: -s.score)
        return hpb.GetSimilarUsersResponse(users=out[:k])

    @rpc
    async def GetRecommendationHistory(self, p: Principal, req, context):
        uid = acting_user(p, req.user_id, scope="recommend:history:read")
        start, end = _window(req.window, 7)
        off, size = _page(req.page, 20, 100)
        served = await self.app.store.served_for_user(uid, start, end, req.surface)
        return hpb.GetRecommendationHistoryResponse(served=[convert.served_to_proto(s) for s in served[off: off + size]],
                                                    page=_page_resp(off, size, len(served)))


def add_all(server: grpc.aio.Server, app: App, auth: TokenAuthenticator) -> None:
    sg.add_RecommendationServiceServicer_to_server(RecommendationServicer(app, auth), server)
    sg.add_EngagementServiceServicer_to_server(EngagementServicer(app, auth), server)
    sg.add_ProfileServiceServicer_to_server(ProfileServicer(app, auth), server)
    sg.add_CatalogServiceServicer_to_server(CatalogServicer(app, auth), server)
    sg.add_GraphServiceServicer_to_server(GraphServicer(app, auth), server)
    sg.add_HistoryServiceServicer_to_server(HistoryServicer(app, auth), server)

