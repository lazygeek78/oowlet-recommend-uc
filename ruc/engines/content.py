"""Content Recommendation Engine — what should this member see?

User → candidate generation (10 sources) → candidate pool → eligibility
(policy, trust, privacy, age, audience, safety, already seen) → ranking
(weighted score or learned model, context-aware) → diversity / exploration
→ final recommendations, logged with their features for the feedback loop.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from oowlet.gen.recommenduc.commonpb import common_pb2 as cpb
from oowlet.gen.recommenduc.recommendationpb import recommendation_pb2 as rpb

from ..candidates.generators import CONTENT_SOURCES, NON_PERSONAL_SOURCES, GenInput, run_sources, social_activity
from ..config import Settings
from ..context import RecContext
from ..domain import CONTENT, ServedRecommendation
from ..intelligence.hub import ContentState, Intelligence, UserState
from ..policy import eligibility
from ..policy.diversity import Ranked, default_opts, rerank
from ..ranking.features import content_features
from ..ranking.models import Ranker
from ..ranking.registry import ModelRegistry
from .common import (PageCache, decode_token, encode_token, new_rec_id, reason, served_record, share,
                     top_reasons)

log = logging.getLogger("ruc.engine.content")
X = cpb
MAX_LIMIT = 100
RANKED_DEPTH = 200          # ranked once, served over several pages


class ContentEngine:
    def __init__(self, settings: Settings, intel: Intelligence, models: ModelRegistry,
                 on_served: Callable[[ServedRecommendation], Awaitable[None]] | None = None) -> None:
        self.s = settings
        self.intel = intel
        self.models = models
        self.pages = PageCache()
        self.on_served = on_served
        self.mf = None              # ImplicitALS, set by training

    async def recommend(self, user_id: str, req: rpb.RecommendContentRequest) -> rpb.RecommendContentResponse:
        limit = max(1, min(req.limit or 20, MAX_LIMIT))
        if req.page.page_token:
            rec_id, offset = decode_token(req.page.page_token)
            page = self.pages.get(rec_id, user_id)
            served = page.served
            ctx = RecContext.from_proto(req.context, topics=list(req.topic_ids), seed_content_id=req.seed_content_id,
                                        seed_creator_id=req.seed_creator_id)
            st = await self.intel.user_state(user_id, ctx.session_id, ctx.utc_offset_minutes, ctx.t)
            # the ranking was cached; eligibility is not: blocks, removals and
            # privacy changes since page 1 apply now
            items = await self.still_eligible(st, ctx, page.ranked[offset: offset + limit])
            more = served_record(rec_id, user_id, served.surface, "content", CONTENT, items, served.model_id,
                                 served.model_version, served.variant, served.experiment_id, served.personalized,
                                 offset=offset)
            await self._log(more)
            return await self._response(rec_id, st, ctx, items, offset, len(page.ranked), limit,
                                        served.model_id, served.model_version, served.experiment_id, served.variant,
                                        served.personalized, req.include_explanations, {})

        ctx = RecContext.from_proto(req.context, topics=list(req.topic_ids), seed_content_id=req.seed_content_id,
                                    seed_creator_id=req.seed_creator_id)
        if ctx.seed_content_id and ctx.surface == cpb.SURFACE_UNSPECIFIED:
            ctx.surface = cpb.SURFACE_CONTENT_DETAIL
        st = await self.intel.user_state(user_id, ctx.session_id, ctx.utc_offset_minutes, ctx.t)
        ranked, social, model, variant = await self.rank(st, ctx, list(req.kinds), list(req.topic_ids),
                                                         set(req.exclude_content_ids))
        opts = default_opts(ctx.surface, limit, req.diversity.max_per_creator, req.diversity.max_per_topic,
                            req.diversity.exploration_ratio if req.HasField("diversity") else -1.0)
        rec_id = new_rec_id()
        final = rerank(ranked, min(RANKED_DEPTH, max(limit, len(ranked))), opts, seed=rec_id)
        items = final[:limit]
        served = served_record(rec_id, user_id, ctx.surface, "content", CONTENT, items, model.model_id,
                               model.version, variant, self.s.ranking.experiment_id, st.personalized)
        self.pages.put(rec_id, user_id, final, served)
        await self._log(served)
        return await self._response(rec_id, st, ctx, items, 0, len(final), limit, model.model_id, model.version,
                                    self.s.ranking.experiment_id, variant, st.personalized,
                                    req.include_explanations, social)

    async def still_eligible(self, st: UserState, ctx: RecContext, items: list[Ranked],
                             hard_only: bool = False) -> list[Ranked]:
        recs = await self.intel.store.get_content([r.key for r in items])
        creators = await self.intel.store.get_users({r.creator_id for r in recs.values()})
        out = []
        for r in items:
            reasons = set(eligibility.check_content(st, recs.get(r.key), ctx, self.s.policy,
                                                    creators.get(recs[r.key].creator_id) if r.key in recs else None))
            if not (reasons & eligibility.HARD if hard_only else reasons):
                out.append(r)
        return out

    async def _log(self, served: ServedRecommendation) -> None:
        await self.intel.store.log_served(served)
        if self.on_served is not None:
            await self.on_served(served)

    async def rank(self, st: UserState, ctx: RecContext, kinds: list[int], topic_ids: list[str],
                   exclude: set[str]) -> tuple[list[Ranked], dict[str, set[str]], Ranker, str]:
        """Candidates → eligibility → features → scores (not yet diversified)."""
        p = self.s.policy
        if ctx.seed_content_id:
            exclude = exclude | {ctx.seed_content_id}     # never recommend the item being looked at
            ctx.seed_vector = self.intel.content_index.get(ctx.seed_content_id)
        social = await social_activity(st, self.intel, ctx.t)
        sources = CONTENT_SOURCES if st.personalized else {k: v for k, v in CONTENT_SOURCES.items()
                                                           if k in NON_PERSONAL_SOURCES}
        pool = await run_sources(sources, GenInput(st=st, ctx=ctx, intel=self.intel, k=150, social=social, mf=self.mf),
                                 p.max_candidates)
        for k in exclude:
            pool.pop(k, None)
        records = await self.intel.store.get_content(pool)
        creators = await self.intel.store.get_users({r.creator_id for r in records.values()})
        allowed_kinds = ctx.kinds(kinds)
        keep = []
        for cid, rec in records.items():
            if allowed_kinds and rec.kind not in allowed_kinds:
                continue
            if topic_ids and not any(t.topic_id in topic_ids for t in rec.topics):
                continue
            if not eligibility.check_content(st, rec, ctx, p, creators.get(rec.creator_id)):
                keep.append(cid)
        states = await self.intel.content_states(keep, ctx.t)
        model, variant = self.models.choose("content", st.user.user_id)
        top_topics = {t for t, _ in sorted(st.topic_affinity.items(), key=lambda kv: -kv[1])[:5]}
        ranked = []
        for cid, cs in states.items():
            cand = pool[cid]
            x = content_features(st, cs, cand.priors, ctx, len(social.get(cid, ())), p.frequency_cap)
            sc = model.score(x, ctx.surface)
            ranked.append(Ranked(
                key=cid, score=sc.score, group_a=cs.item.creator_id, group_b=cs.item.primary_topic(),
                vector=cs.vector, features=x, contributions=sc.contributions, sources=cand.sources,
                exploratory=(bool(set(cand.priors) & NON_PERSONAL_SOURCES)
                             and not (set(cs.item.topic_weights()) & top_topics) and cs.quality >= 0.5)))
        return ranked, social, model, variant

    async def _response(self, rec_id: str, st: UserState, ctx: RecContext, items: list[Ranked], offset: int,
                        total: int, limit: int, model_id: str, model_version: str, experiment_id: str, variant: str,
                        personalized: bool, explain: bool,
                        social: dict[str, set[str]]) -> rpb.RecommendContentResponse:
        out = []
        recs = await self.intel.store.get_content([r.key for r in items]) if explain else {}
        for i, r in enumerate(items):
            cr = rpb.ContentRecommendation(content_id=r.key, score=r.score, rank=offset + i,
                                           candidate_sources=r.sources)
            if explain:
                cr.explanation.CopyFrom(self.explain(st, r, recs.get(r.key), ctx, social.get(r.key, set())))
            out.append(cr)
        nxt = offset + len(items)
        resp = rpb.RecommendContentResponse(
            recommendation_id=rec_id, items=out,
            page=cpb.PageResponse(next_page_token=encode_token(rec_id, nxt) if nxt < total else "",
                                  total_estimate=total),
            model=cpb.ModelInfo(model_id=model_id, model_version=model_version, experiment_id=experiment_id,
                                variant=variant),
            personalized=personalized)
        resp.generated_at.GetCurrentTime()
        return resp

    def explain(self, st: UserState, r: Ranked, item, ctx: RecContext, network: set[str]) -> cpb.Explanation:
        c = r.contributions
        rs = []
        if r.explored:
            rs.append(reason(X.REASON_CODE_EXPLORATION, 0.5, "something new for you"))
        if item is not None:
            tw = item.topic_weights(include_sensitive=False)        # never shown: sensitive topics
            matches = sorted(((st.topic_affinity.get(t, 0.0) * w, t) for t, w in tw.items()), reverse=True)
            if matches and matches[0][0] > 0 and c.get("user_interest", 0) > 0:
                rs.append(reason(X.REASON_CODE_TOPIC_INTEREST, share(c, ("user_interest",)), matches[0][1],
                                 [cpb.EntityRef(type=cpb.ENTITY_TYPE_TOPIC, id=matches[0][1])]))
            if item.creator_id in st.following and c.get("creator_affinity", 0) > 0:
                rs.append(reason(X.REASON_CODE_FOLLOWED_CREATOR, share(c, ("creator_affinity",)), "",
                                 [cpb.EntityRef(type=cpb.ENTITY_TYPE_CREATOR, id=item.creator_id)]))
            if ctx.community_id and item.community_id == ctx.community_id:
                rs.append(reason(X.REASON_CODE_SAME_COMMUNITY, share(c, ("context_relevance",)), "",
                                 [cpb.EntityRef(type=cpb.ENTITY_TYPE_COMMUNITY, id=item.community_id)]))
        if c.get("content_relevance", 0) > 0:
            rs.append(reason(X.REASON_CODE_SIMILAR_TO_ENGAGED, share(c, ("content_relevance",))))
        if c.get("behavioral_affinity", 0) > 0 or (network and c.get("social_signal", 0) > 0):
            ev = [cpb.EntityRef(type=cpb.ENTITY_TYPE_USER, id=u) for u in sorted(network)[:3]]
            rs.append(reason(X.REASON_CODE_COLLABORATIVE, share(c, ("behavioral_affinity", "social_signal")),
                             "", ev))
        if c.get("trend_signal", 0) > 0.05:
            rs.append(reason(X.REASON_CODE_TRENDING, share(c, ("trend_signal",))))
        if c.get("freshness", 0) > 0.05:
            rs.append(reason(X.REASON_CODE_FRESH, share(c, ("freshness",))))
        return top_reasons(rs)

    async def check(self, st: UserState, ctx: RecContext, content_ids: list[str], include_score: bool,
                    explain: bool) -> list[rpb.EligibilityResult]:
        """CheckEligibility for content: the same rules as recommend()."""
        recs = await self.intel.store.get_content(content_ids)
        creators = await self.intel.store.get_users({r.creator_id for r in recs.values()})
        results: dict[str, rpb.EligibilityResult] = {}
        ok = []
        for cid in content_ids:
            rec = recs.get(cid)
            reasons = eligibility.check_content(st, rec, ctx, self.s.policy,
                                                creators.get(rec.creator_id) if rec else None)
            results[cid] = rpb.EligibilityResult(candidate=cpb.EntityRef(type=CONTENT, id=cid),
                                                 eligible=not reasons, reasons=reasons)
            if not reasons:
                ok.append(cid)
        if ok and (include_score or explain):
            states: dict[str, ContentState] = await self.intel.content_states(ok, ctx.t)
            social = await social_activity(st, self.intel, ctx.t)
            model, _ = self.models.choose("content", st.user.user_id)
            for cid, cs in states.items():
                x = content_features(st, cs, {}, ctx, len(social.get(cid, ())), self.s.policy.frequency_cap)
                sc = model.score(x, ctx.surface)
                if include_score:
                    results[cid].score = sc.score
                if explain:
                    r = Ranked(key=cid, score=sc.score, features=x, contributions=sc.contributions)
                    results[cid].explanation.CopyFrom(self.explain(st, r, cs.item, ctx, social.get(cid, set())))
        return [results[c] for c in content_ids]

