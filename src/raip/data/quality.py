"""R03 — tox_avg + Gini demographic representation."""

from __future__ import annotations

import re
from typing import Sequence


def gini_coefficient(proportions: Sequence[float]) -> float:
    vals = [max(0.0, float(p)) for p in proportions]
    if not vals:
        return 0.0
    k = len(vals)
    mean_p = sum(vals) / k
    if mean_p <= 0:
        return 0.0
    total = 0.0
    for i in range(k):
        for j in range(k):
            total += abs(vals[i] - vals[j])
    return total / (2 * (k**2) * mean_p)


def tox_avg(texts: Sequence[str]) -> float:
    if not texts:
        return 0.0
    try:
        from detoxify import Detoxify  # type: ignore[import-untyped]

        model = Detoxify("original")
        scores = []
        for t in texts[: min(len(texts), 200)]:
            out = model.predict(str(t)[:512])
            scores.append(float(out.get("toxicity", 0.0)))
        return sum(scores) / len(scores) if scores else 0.0
    except ImportError:
        # Heuristic: toxic keyword density
        bad = re.compile(
            r"\b(hate|kill|stupid|idiot|violence|attack)\b",
            re.IGNORECASE,
        )
        hits = sum(1 for t in texts if bad.search(str(t)))
        return hits / len(texts)


def score_r03(
    texts: Sequence[str],
    group_counts: dict[str, int] | None = None,
) -> tuple[float, float, float]:
    """Returns (s_R03, tox_avg, gini)."""
    ta = tox_avg(texts)
    if group_counts:
        total = sum(group_counts.values()) or 1
        props = [group_counts[g] / total for g in group_counts]
        g = gini_coefficient(props)
    else:
        g = 0.0
    s = max(0.0, min(1.0, 1.0 - 0.5 * (ta + g)))
    return s, ta, g
