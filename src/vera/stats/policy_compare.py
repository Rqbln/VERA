"""Compare requirement verdicts under alternative weighting policies.

A policy is a mapping benchmark -> weight for one requirement. Scores are
point verdicts recomputed from cached per-benchmark means (no model queries),
mirroring effective_requirement_weights semantics: only benchmarks present in
BOTH the means and the policy contribute, and weights renormalize over them.
"""

from __future__ import annotations

from vera.dashboard.score_bands import ScoreBands


def point_score(means: dict[str, float], weights: dict[str, float]) -> float | None:
    """Weighted mean of per-benchmark means, renormalized over shared benchmarks."""
    shared = {b: w for b, w in weights.items() if b in means and w > 0}
    total = sum(shared.values())
    if not shared or total <= 0:
        return None
    return sum(means[b] * w for b, w in shared.items()) / total


def uniform_weights(means: dict[str, float]) -> dict[str, float]:
    """The COMPL-AI aggregation policy: one equal weight per contributing benchmark."""
    return {b: 1.0 / len(means) for b in means} if means else {}


def compare_policies(
    means: dict[str, float],
    policies: dict[str, dict[str, float]],
    bands: ScoreBands | None = None,
) -> dict[str, dict[str, object]]:
    """Score one requirement's cached means under each named policy.

    Returns {policy_name: {score, band}} plus a "_flip" entry: True when the
    band verdict differs between any two policies.
    """
    bands = bands or ScoreBands()
    out: dict[str, dict[str, object]] = {}
    verdicts: set[str] = set()
    for name, weights in policies.items():
        score = point_score(means, weights)
        band = bands.band(score)
        out[name] = {"score": None if score is None else round(score, 4), "band": band}
        verdicts.add(band)
    out["_flip"] = {"flip": len(verdicts - {"unknown"}) > 1}
    return out
