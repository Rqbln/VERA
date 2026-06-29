"""Bootstrap confidence intervals for COMPL-AI aggregate scores (MVP1 §4.3)."""

from __future__ import annotations

import os
from collections.abc import Sequence

import numpy as np


def effective_bootstrap_n(configured: int) -> int:
    """Allow faster CI runs via VERA_BOOTSTRAP_N without changing request payloads."""
    raw = os.environ.get("VERA_BOOTSTRAP_N")
    if raw is None or raw.strip() == "":
        return max(1, int(configured))
    try:
        return max(1, int(raw.strip()))
    except ValueError:
        return max(1, int(configured))


def bootstrap_mean_ci_95(
    samples: Sequence[float],
    *,
    seed: int,
    n_resamples: int = 1000,
) -> tuple[float, float, float]:
    """
    Return (mean, score_ci_lower, score_ci_upper) using percentile bootstrap 95 %.

    Uses resampling of the sample vector with replacement; each replicate mean is
    one bootstrap statistic. CI = [p2.5, p97.5] of those replicates.
    """
    arr = np.asarray(samples, dtype=np.float64)
    if arr.size == 0:
        return 0.0, 0.0, 0.0
    mean_s = float(np.mean(arr))
    n_boot = max(1, int(n_resamples))
    if arr.size == 1:
        return mean_s, mean_s, mean_s

    rng = np.random.default_rng(int(seed) + 7919)
    # Bootstrap replicate means
    idx = rng.integers(0, arr.size, size=(n_boot, arr.size))
    repl_means = np.mean(arr[idx], axis=1)
    lo = float(np.percentile(repl_means, 2.5))
    hi = float(np.percentile(repl_means, 97.5))
    lo = max(0.0, min(1.0, lo))
    hi = max(0.0, min(1.0, hi))
    if lo > hi:
        lo, hi = hi, lo
    mean_s = max(0.0, min(1.0, mean_s))
    return mean_s, lo, hi


def weighted_requirement_mean(
    by_benchmark: dict[str, list[float]],
    weights: dict[str, float],
) -> float:
    """s_R = sum_b w_b * mean(samples_b) / sum_b w_b for benchmarks with non-empty samples."""
    means: dict[str, float] = {}
    w_eff: dict[str, float] = {}
    for b, samples in by_benchmark.items():
        if not samples:
            continue
        means[b] = float(np.mean(np.asarray(samples, dtype=np.float64)))
        w_eff[b] = float(weights.get(b, 1.0))
    denom = sum(w_eff.values())
    if denom <= 0 or not means:
        return 0.0
    return max(0.0, min(1.0, sum(w_eff[b] * means[b] for b in means) / denom))


def bootstrap_weighted_requirement_ci_95(
    by_benchmark: dict[str, list[float]],
    weights: dict[str, float],
    *,
    seed: int,
    n_resamples: int = 1000,
) -> tuple[float, float, float]:
    """
    Bootstrap CI for weighted aggregate s_R (MVP1 §4.2–4.3).

    Each bootstrap replicate: for each benchmark b, resample its per-item scores
    with replacement (same n), recompute mean_b, then recompute weighted s_R.
    """
    # Effective weights only for benchmarks that have samples
    w_eff: dict[str, float] = {}
    for b, samples in by_benchmark.items():
        if samples:
            w_eff[b] = float(weights.get(b, 1.0))
    denom = sum(w_eff.values()) or 1.0

    mean_s = weighted_requirement_mean(by_benchmark, weights)
    n_boot = max(1, int(n_resamples))

    if not w_eff:
        return 0.0, 0.0, 0.0

    # Single-sample benchmarks only → no resampling uncertainty at item level
    all_single = all(len(by_benchmark[b]) <= 1 for b in w_eff)
    if all_single:
        return mean_s, mean_s, mean_s

    rng = np.random.default_rng(int(seed) + 424242)
    boot_stats: list[float] = []
    for _ in range(n_boot):
        rep_means: dict[str, float] = {}
        for b in w_eff:
            arr = np.asarray(by_benchmark.get(b) or [], dtype=np.float64)
            if arr.size == 0:
                continue
            if arr.size == 1:
                rep_means[b] = float(arr[0])
            else:
                idx = rng.integers(0, arr.size, size=arr.size)
                rep_means[b] = float(np.mean(arr[idx]))
        s_rep = sum(w_eff[b] * rep_means[b] for b in w_eff if b in rep_means) / denom
        s_rep = max(0.0, min(1.0, s_rep))
        boot_stats.append(s_rep)

    lo = float(np.percentile(boot_stats, 2.5))
    hi = float(np.percentile(boot_stats, 97.5))
    lo = max(0.0, min(1.0, lo))
    hi = max(0.0, min(1.0, hi))
    if lo > hi:
        lo, hi = hi, lo
    return mean_s, lo, hi
