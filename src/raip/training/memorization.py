"""Memorization curve — canary leakage vs epoch."""

from __future__ import annotations

from typing import Sequence


def memorization_curve(canary_matches: Sequence[int], epochs: Sequence[int]) -> list[dict[str, float]]:
    return [
        {"epoch": int(e), "leak_rate": int(m) / max(1, len(canary_matches))}
        for e, m in zip(epochs, canary_matches, strict=False)
    ]
