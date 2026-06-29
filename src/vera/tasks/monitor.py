"""Lightweight drift / canary monitoring (thin MVP4 slice).

On-demand drift detection over a model's run history: compares the latest Trust Factor against a
rolling baseline of prior runs. Runs entirely on the existing Redis store — no Kafka, no canary
scheduler, no embedding distance. A drift beyond the threshold is surfaced as an advisory alert.
"""

from __future__ import annotations

import os
from typing import Any

from vera.store.redis_run import RedisRunStore, RunRecord


def _latest_metric(rec: RunRecord) -> float | None:
    if rec.trust_factor and isinstance(rec.trust_factor, dict):
        score = rec.trust_factor.get("score")
        if score is not None:
            return float(score) / 100.0
    scores = (rec.aggregate_scores or {}).values()
    vals = [float(v) for v in scores]
    return sum(vals) / len(vals) if vals else None


def compute_drift(
    model_id: str,
    *,
    store: RedisRunStore | None = None,
    baseline_n: int | None = None,
    threshold: float | None = None,
) -> dict[str, Any]:
    """Compare the latest run's metric against the mean of the prior ``baseline_n`` runs."""
    store = store or RedisRunStore()
    baseline_n = baseline_n or int(os.environ.get("VERA_DRIFT_BASELINE_N", "5"))
    baseline_n = max(1, baseline_n)  # clamp: a 0/negative window would divide by zero below
    threshold = threshold if threshold is not None else float(
        os.environ.get("VERA_DRIFT_THRESHOLD", "0.15")
    )

    page, _ = store.list_runs(limit=200, model_id=model_id, status="completed")
    series = [(r, _latest_metric(r)) for r in page]
    series = [(r, m) for r, m in series if m is not None]
    # list_runs returns newest-first.
    if len(series) < 2:
        return {
            "available": False,
            "reason": "insufficient_history",
            "model_id": model_id,
            "n_history": len(series),
        }

    latest_rec, latest = series[0]
    baseline_vals = [m for _, m in series[1 : 1 + baseline_n]]
    baseline = sum(baseline_vals) / len(baseline_vals)
    delta = latest - baseline
    drift = abs(delta) >= threshold
    return {
        "available": True,
        "model_id": model_id,
        "latest": round(latest, 4),
        "latest_run_id": latest_rec.run_id,
        "baseline": round(baseline, 4),
        "delta": round(delta, 4),
        "threshold": threshold,
        "drift": drift,
        "direction": "regression" if delta < 0 else "improvement",
        "n_history": len(series),
    }
