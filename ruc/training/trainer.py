"""Model evaluation and retraining — the end of the feedback loop.

Training data comes from the serve log: every served item carries the
ranking components it was scored with. An item counts as an example once
it was shown (impression) or acted on; its label is 1 when the user engaged
positively, 0 otherwise (ignored, hidden, reported).

For each engine:
  1. split by time: the newest 20% of serves are held out
  2. fit a logistic ranker on the rest
  3. on the holdout, compare it with the model serving now: AUC, log loss,
     NDCG@10, per-serve
  4. promote (write models/<engine>-logistic.json, reload) only when the AUC
     gain clears RUC_TRAINING__PROMOTE_MIN_AUC_GAIN and there are enough examples
Matrix factorization (candidate generation) is refit from the engagement
history of users who allow their history to be used.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np

from .. import signals
from ..domain import CONTENT, now
from ..ranking.models import CONTENT_FEATURES, PEOPLE_FEATURES, LogisticRanker, auc, logloss, ndcg_at_k
from .mf import ImplicitALS

log = logging.getLogger("ruc.training")
DAY = 86400.0


async def dataset(app, engine: str, since: float):
    names = CONTENT_FEATURES if engine == "content" else PEOPLE_FEATURES
    rows, labels, groups, times = [], [], [], []
    for rec in await app.store.served_since(since):
        if rec.engine != engine:
            continue
        for it in rec.items:
            if not it.impressed and it.label is None:
                continue
            rows.append([it.features.get(n, 0.0) for n in names])
            labels.append(1.0 if it.label == 1.0 else 0.0)
            groups.append(rec.recommendation_id)
            times.append(rec.served_at)
    return np.asarray(rows, dtype=np.float64), np.asarray(labels), groups, np.asarray(times)


def _eval(model, X: np.ndarray, y: np.ndarray, groups: list[str], names) -> dict[str, float]:
    scores = np.array([model.score(dict(zip(names, row))).score for row in X])
    by: dict[str, list[int]] = {}
    for i, g in enumerate(groups):
        by.setdefault(g, []).append(i)
    grouped = [(scores[idx], y[idx]) for idx in by.values()]
    probs = scores if model.model_id == "logistic" else 1.0 / (1.0 + np.exp(-(scores - np.median(scores))))
    return {"auc": auc(scores, y), "logloss": logloss(probs, y), "ndcg@10": ndcg_at_k(grouped, 10),
            "examples": float(len(y)), "positive_rate": float(y.mean()) if len(y) else 0.0}


async def train_ranker(app, engine: str, days: float = 30.0) -> dict:
    cfg = app.s.training
    names = CONTENT_FEATURES if engine == "content" else PEOPLE_FEATURES
    X, y, groups, times = await dataset(app, engine, now() - days * DAY)
    report: dict = {"engine": engine, "examples": int(len(y))}
    if len(y) < cfg.min_examples or y.sum() == 0 or y.sum() == len(y):
        report["result"] = f"skipped: need >= {cfg.min_examples} examples with both outcomes"
        return report
    cut = np.quantile(times, 0.8)
    tr, ho = times <= cut, times > cut
    if ho.sum() == 0 or y[ho].sum() == 0 or y[tr].sum() == 0:
        report["result"] = "skipped: holdout has no positive examples"
        return report
    cand = LogisticRanker.fit(engine, X[tr], y[tr])
    current, _ = app.models.choose(engine, "__evaluation__")
    g_ho = [g for g, keep in zip(groups, ho) if keep]
    m_new = _eval(cand, X[ho], y[ho], g_ho, names)
    m_cur = _eval(current, X[ho], y[ho], g_ho, names)
    report.update({"candidate": m_new, "current": {"model": current.model_id, **m_cur}})
    gain = m_new["auc"] - m_cur["auc"]
    if np.isnan(gain) or gain < cfg.promote_min_auc_gain:
        report["result"] = f"kept {current.model_id}: AUC gain {gain:.4f} < {cfg.promote_min_auc_gain}"
        return report
    final = LogisticRanker.fit(engine, X, y)              # refit on everything before promoting
    final.version = time.strftime("%Y%m%d%H%M%S")
    final.trained_at = now()
    final.metrics = {f"holdout_{k}": v for k, v in m_new.items()}
    path = app.models.path(engine)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(final.to_json(), encoding="utf-8")
    tmp.replace(path)
    app.models.reload()
    report["result"] = f"promoted {path} (AUC {m_cur['auc']:.4f} -> {m_new['auc']:.4f})"
    report["note"] = ("serving uses it when RUC_RANKING__%s_MODEL=logistic or as challenger"
                      % ("CONTENT" if engine == "content" else "PEOPLE"))
    return report


async def train_mf(app, days: float = 90.0) -> dict:
    cfg = app.s.training
    t = now()
    triples = []
    for u in await app.store.iter_users():
        p = u.privacy
        # item factors are shared by everyone: only users who allow collaborative use
        if not (p.personalization_enabled and p.use_engagement_history and p.contribute_to_collaborative):
            continue
        strength: dict[str, float] = {}
        for ev in await app.store.user_events(u.user_id, since=t - days * DAY, target_type=CONTENT):
            w = signals.weight(ev)
            if w > 0:
                strength[ev.target_id] = strength.get(ev.target_id, 0.0) + w * signals.decay(t - ev.ts, 30 * DAY)
        triples += [(u.user_id, i, s) for i, s in strength.items()]
    if len(triples) < 10:
        return {"mf": "skipped: not enough engagement"}
    model = ImplicitALS(factors=cfg.mf_factors, iterations=cfg.mf_iterations).fit(triples)
    app.content.mf = model
    return {"mf": f"trained on {len(triples)} user-item pairs, {len(model.user_ids)} users, {len(model.item_ids)} items"}


async def run(app) -> dict:
    return {"content": await train_ranker(app, "content"), "people": await train_ranker(app, "people"),
            **(await train_mf(app))}
