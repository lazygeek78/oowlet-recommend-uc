"""People Recommendation Engine — which people should this member connect with?

Same shared intelligence as the content engine (user embeddings, affinities,
interactions, feedback), different candidates and ranking: graph proximity
(mutual connections), shared interests, communities, interactions and the
likelihood the other person accepts.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.engagementpb import engagement_pb2 as epb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb

from ..candidates.generators import PEOPLE_SOURCES, PeopleInput, mutual_connections, run_sources
from ..config import Settings
from ..context import RecContext
from ..domain import COMMUNITY_MEMBER, USER, ServedRecommendation, UserRecord
from ..intelligence.hub import Intelligence, UserState
from ..policy import eligibility
from ..policy.diversity import Ranked, default_opts, rerank
from ..ranking.features import people_features
from ..ranking.registry import ModelRegistry
from .common import (PageCache, decode_token, encode_token, new_rec_id, reason, served_record, share,
                     top_reasons)

log = logging.getLogger("ruc.engine.people")
X = cpb
E = epb
MAX_LIMIT = 50
RANKED_DEPTH = 100


class PeopleEngine:
    def __init__(self, settings: Settings, intel: Intelligence, models: ModelRegistry,
                 on_served: Callable[[ServedRecommendation], Awaitable[None]] | None = None) -> None:
        self.s = settings
        self.intel = intel
        self.models = models
        self.pages = PageCache()
        self.on_served = on_served

    async def recommend(self, user_id: str, req: rpb.RecommendUsersRequest) -> rpb.RecommendUsersResponse:
        limit = max(1, min(req.limit or 10, MAX_LIMIT))
        ctx = RecContext.from_proto(req.context, community_id=req.community_id, seed_user_id=req.seed_user_id)
        st = await self.intel.user_state(user_id, ctx.session_id, ctx.utc_offset_minutes, ctx.t)
        if req.page.page_token:
            rec_id, offset = decode_token(req.page.page_token)
            page = self.pages.get(rec_id, user_id)
            items = await self.still_eligible(st, page.ranked[offset: offset + limit])
            sv = page.served
            more = served_record(rec_id, user_id, sv.surface, "people", USER, items, sv.model_id, sv.model_version,
                                 sv.variant, sv.experiment_id, sv.personalized, offset=offset)
            await self._log(more)
            return await self._response(rec_id, st, ctx, items, offset, len(page.ranked), sv.model_id,
                                        sv.model_version, sv.experiment_id, sv.variant, req.include_explanations, {})
        ranked, mutuals, model, variant = await self.rank(st, ctx, req.purpose, set(req.exclude_user_ids))
        rec_id = new_rec_id()
        opts = default_opts(ctx.surface, limit, people=True)
        final = rerank(ranked, min(RANKED_DEPTH, max(limit, len(ranked))), opts, seed=rec_id)
        items = final[:limit]
        served = served_record(rec_id, user_id, ctx.surface or cpb.SURFACE_PEOPLE_YOU_MAY_KNOW, "people", USER,
                               items, model.model_id, model.version, variant, self.s.ranking.experiment_id,
                               st.personalized)
        self.pages.put(rec_id, user_id, final, served)
        await self._log(served)
        return await self._response(rec_id, st, ctx, items, 0, len(final), model.model_id, model.version,
                                    self.s.ranking.experiment_id, variant, req.include_explanations, mutuals)

    async def still_eligible(self, st: UserState, items: list[Ranked], hard_only: bool = False) -> list[Ranked]:
        users = await self.intel.store.get_users([r.key for r in items])
        out = []
        for r in items:
            reasons = set(eligibility.check_person(st, users.get(r.key), r.key in users, self.s.policy))
            if not (reasons & eligibility.HARD if hard_only else reasons):
                out.append(r)
        return out

    async def _log(self, served: ServedRecommendation) -> None:
        await self.intel.store.log_served(served)
        if self.on_served is not None:
            await self.on_served(served)

    async def _other_facts(self, ids: list[str], t: float) -> tuple[dict[str, set[str]], dict[str, float], dict[str, float]]:
        """communities, last activity, connection-acceptance rate of candidates."""
        store = self.intel.store
        comms, active, accept = {}, {}, {}
        for uid in ids:
            comms[uid] = {e.to_user_id for e in await store.out_edges(uid, frozenset({COMMUNITY_MEMBER}))}
            last = await store.user_events(uid, since=t - 90 * 86400.0, limit=1)
            active[uid] = last[0].ts if last else 0.0
            ev = await store.user_events(uid, since=t - 180 * 86400.0, target_type=USER, limit=200,
                                         types=frozenset({E.ENGAGEMENT_TYPE_CONNECT_ACCEPTED,
                                                          E.ENGAGEMENT_TYPE_CONNECT_DECLINED}))
            acc = sum(1 for e in ev if e.type == E.ENGAGEMENT_TYPE_CONNECT_ACCEPTED)
            accept[uid] = (acc + 1.0) / (len(ev) + 2.0)          # Laplace prior: 0.5 with no history
        return comms, active, accept

    async def rank(self, st: UserState, ctx: RecContext, purpose: int, exclude: set[str]):
        p = self.s.policy
        mutuals = await mutual_connections(st, self.intel)
        pool = await run_sources(PEOPLE_SOURCES, PeopleInput(st=st, ctx=ctx, intel=self.intel, k=100, mutuals=mutuals),
                                 p.max_candidates)
        for k in exclude:
            pool.pop(k, None)
        users = await self.intel.store.get_users(pool)
        keep = [uid for uid in pool
                if not eligibility.check_person(st, users.get(uid), uid in users, p, purpose)]
        comms, active, accept = await self._other_facts(keep, ctx.t)
        model, variant = self.models.choose("people", st.user.user_id)
        ranked = []
        for uid in keep:
            other = users[uid]
            x = people_features(st, other, self.intel.user_index.get(uid), pool[uid].priors,
                                len(mutuals.get(uid, ())), comms[uid], active[uid], accept[uid], ctx)
            sc = model.score(x, ctx.surface)
            shared = sorted(st.communities & comms[uid])
            ranked.append(Ranked(key=uid, score=sc.score, group_b=shared[0] if shared else "",
                                 vector=self.intel.user_index.get(uid), features=x, contributions=sc.contributions,
                                 sources=pool[uid].sources))
        return ranked, mutuals, model, variant

    async def _response(self, rec_id, st, ctx, items: list[Ranked], offset, total, model_id, model_version,
                        experiment_id, variant, explain, mutuals: dict[str, set[str]]) -> rpb.RecommendUsersResponse:
        if explain and not mutuals:
            mutuals = await mutual_connections(st, self.intel)
        users = await self.intel.store.get_users([r.key for r in items])
        out = []
        for i, r in enumerate(items):
            other = users.get(r.key)
            shared_topics = self.shared_topics(st, other) if other else []
            ur = rpb.UserRecommendation(user_id=r.key, score=r.score, rank=offset + i,
                                        mutual_connections=len(mutuals.get(r.key, ())),
                                        shared_topic_ids=shared_topics[:5], candidate_sources=r.sources)
            if explain and other is not None:
                ur.explanation.CopyFrom(self.explain(st, r, other, ctx, mutuals.get(r.key, set()), shared_topics))
            out.append(ur)
        nxt = offset + len(items)
        resp = rpb.RecommendUsersResponse(
            recommendation_id=rec_id, items=out,
            page=cpb.PageResponse(next_page_token=encode_token(rec_id, nxt) if nxt < total else "", total_estimate=total),
            model=cpb.ModelInfo(model_id=model_id, model_version=model_version, experiment_id=experiment_id,
                                variant=variant))
        resp.generated_at.GetCurrentTime()
        return resp

    def shared_topics(self, st: UserState, other: UserRecord) -> list[str]:
        """Topics shown as shared: never sensitive; the other person's inferred
        (activity-derived) interests only if they let their activity be shown."""
        theirs = list(other.declared_topics)
        if other.privacy.show_activity_to_others:
            theirs += other.inferred_topics
        mine = set(st.topic_affinity)
        return sorted({t.topic_id for t in theirs
                       if t.topic_id in mine and not self.intel.is_sensitive(t.topic_id, t.sensitive)})

    def explain(self, st: UserState, r: Ranked, other: UserRecord, ctx: RecContext, mutual: set[str],
                shared_topics: list[str]) -> cpb.Explanation:
        c = r.contributions
        rs = []
        if mutual:
            rs.append(reason(X.REASON_CODE_MUTUAL_CONNECTIONS, share(c, ("mutual_connections",)), str(len(mutual)),
                             [cpb.EntityRef(type=cpb.ENTITY_TYPE_USER, id=u) for u in sorted(mutual)[:3]]))
        if shared_topics and c.get("shared_interests", 0) > 0:
            rs.append(reason(X.REASON_CODE_SHARED_INTERESTS, share(c, ("shared_interests",)), "",
                             [cpb.EntityRef(type=cpb.ENTITY_TYPE_TOPIC, id=t) for t in shared_topics[:3]]))
        if r.group_b:
            rs.append(reason(X.REASON_CODE_SAME_COMMUNITY, share(c, ("community_overlap",)), "",
                             [cpb.EntityRef(type=cpb.ENTITY_TYPE_COMMUNITY, id=r.group_b)]))
        if c.get("interaction", 0) > 0:
            rs.append(reason(X.REASON_CODE_INTERACTED_WITH_CONTENT, share(c, ("interaction",))))
        if (st.user.privacy.allow_location_signal and other.privacy.allow_location_signal
                and st.user.region and st.user.region == other.region):
            rs.append(reason(X.REASON_CODE_NEARBY_REGION, share(c, ("context_relevance",))))
        return top_reasons(rs)

    async def check(self, st: UserState, ctx: RecContext, user_ids: list[str], include_score: bool,
                    explain: bool) -> list[rpb.EligibilityResult]:
        users = await self.intel.store.get_users(user_ids)
        results = {}
        ok = []
        for uid in user_ids:
            reasons = eligibility.check_person(st, users.get(uid), uid in users, self.s.policy)
            results[uid] = rpb.EligibilityResult(candidate=cpb.EntityRef(type=USER, id=uid), eligible=not reasons,
                                                 reasons=reasons)
            if not reasons:
                ok.append(uid)
        if ok and (include_score or explain):
            mutuals = await mutual_connections(st, self.intel)
            comms, active, accept = await self._other_facts(ok, ctx.t)
            model, _ = self.models.choose("people", st.user.user_id)
            for uid in ok:
                x = people_features(st, users[uid], self.intel.user_index.get(uid), {}, len(mutuals.get(uid, ())),
                                    comms[uid], active[uid], accept[uid], ctx)
                sc = model.score(x, ctx.surface)
                if include_score:
                    results[uid].score = sc.score
                if explain:
                    shared = sorted(st.communities & comms[uid])
                    r = Ranked(key=uid, score=sc.score, group_b=shared[0] if shared else "", features=x,
                               contributions=sc.contributions)
                    topics = self.shared_topics(st, users[uid])
                    results[uid].explanation.CopyFrom(self.explain(st, r, users[uid], ctx, mutuals.get(uid, set()),
                                                                   topics))
        return [results[u] for u in user_ids]
