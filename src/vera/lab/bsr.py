"""Backdoor Survival Rate — R02 extended."""

from __future__ import annotations


def compute_bsr(asr_pre: float, asr_post: float) -> float:
    if asr_pre <= 0:
        return 0.0
    return float(asr_post) / float(asr_pre)


def asr_from_successes(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return successes / total
