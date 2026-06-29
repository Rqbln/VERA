"""Trust Factor engine (thin MVP4 slice).

Aggregates the most safety-relevant measurable requirements into a single 0–100 ``Trust Factor``
surfaced on the dashboard. This is a pragmatic, fully-local computation over scores VERA already
produces — NOT the full governance-as-a-service signal stack (live proxy, Garak/Detoxify online,
embedding drift), which is deferred. Weights are configurable so the score is auditable.
"""

from __future__ import annotations

import json
import os
from typing import Any

from vera.dashboard.score_bands import load_score_bands

# Default weights over the safety-relevant requirements (must sum to 1.0).
DEFAULT_WEIGHTS: dict[str, float] = {
    "R02": 0.35,  # cyber resilience
    "R12": 0.25,  # toxicity / harmful content
    "R05": 0.20,  # privacy protection
    "R01": 0.20,  # robustness & predictability
}


def load_weights() -> dict[str, float]:
    """Weights from ``VERA_TRUST_FACTOR_WEIGHTS`` (JSON) or the defaults, renormalised to sum 1."""
    raw = os.environ.get("VERA_TRUST_FACTOR_WEIGHTS")
    weights = dict(DEFAULT_WEIGHTS)
    if raw:
        try:
            parsed = {str(k): float(v) for k, v in json.loads(raw).items()}
            if parsed:
                weights = parsed
        except Exception:
            weights = dict(DEFAULT_WEIGHTS)
    total = sum(weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}


def _score_of(complai_scores: dict[str, Any], req: str) -> float | None:
    row = complai_scores.get(req)
    if row is None:
        return None
    if isinstance(row, dict):
        val = row.get("score")
    else:  # ComplaiRequirementScore-like
        val = getattr(row, "score", None)
    return float(val) if val is not None else None


def compute_trust_factor(complai_scores: dict[str, Any]) -> dict[str, Any] | None:
    """Return ``{score: 0-100, band, components, weights, coverage}`` or None if no signals.

    Only requirements actually present contribute; weights are renormalised over the available
    signals so a partial run still yields a meaningful, transparent score.
    """
    weights = load_weights()
    available = {r: _score_of(complai_scores, r) for r in weights}
    available = {r: s for r, s in available.items() if s is not None}
    if not available:
        return None

    total_w = sum(weights[r] for r in available) or 1.0
    components: dict[str, float] = {}
    weighted = 0.0
    for r, s in available.items():
        w = weights[r] / total_w
        components[r] = round(s * 100, 1)
        weighted += w * s

    score100 = round(weighted * 100, 1)
    band = load_score_bands().band(weighted)
    return {
        "score": score100,
        "band": band,
        "components": components,
        "weights": {r: round(weights[r] / total_w, 3) for r in available},
        "coverage": sorted(available.keys()),
    }
