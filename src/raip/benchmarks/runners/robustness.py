"""R01 — acc_perturbed / max(acc_clean, eps) via paired benchmarks."""

from __future__ import annotations

from raip.benchmarks.runners.base import RawList, RunContext, SamplesByReq, merge_samples
from raip.benchmarks.runners.hf_dynamic import run_hf_dynamic
from raip.benchmarks.runners.lm_eval_runner import run_lm_eval


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def run_robustness_r01(ctx: RunContext, benchmark_id: str) -> tuple[SamplesByReq, RawList]:
    """Uses mmlu (clean) + mmlu_robust (perturbed) when available."""
    eps = 1e-6
    clean_scores: list[float] = []
    pert_scores: list[float] = []
    raw: RawList = []

    s_clean, r_clean = run_lm_eval(ctx, "mmlu")
    raw.extend(r_clean)
    for bid, xs in (s_clean.get("R06") or s_clean.get("R01") or {}).items():
        if bid == "mmlu":
            clean_scores.extend(xs)

    s_pert, r_pert = run_hf_dynamic(ctx, "mmlu_robust")
    raw.extend(r_pert)
    for bid, xs in (s_pert.get("R01") or {}).items():
        if bid == "mmlu_robust":
            pert_scores.extend(xs)

    if not clean_scores:
        s2, r2 = run_hf_dynamic(ctx, "boolq_contrast")
        raw.extend(r2)
        for xs in (s2.get("R01") or {}).values():
            pert_scores.extend(xs)
        clean_scores = pert_scores[:] if pert_scores else [0.5]

    acc_clean = _mean(clean_scores)
    acc_pert = _mean(pert_scores) if pert_scores else acc_clean
    ratio = min(1.0, max(0.0, acc_pert / max(acc_clean, eps)))

    samples: SamplesByReq = {}
    merge_samples(samples, "R01", benchmark_id, ratio)
    raw.append(
        {
            "agent": "robustness_r01",
            "harness": "paired_acc_ratio",
            "benchmark_id": benchmark_id,
            "requirement": "R01",
            "acc_clean": acc_clean,
            "acc_perturbed": acc_pert,
            "score": ratio,
        }
    )
    return samples, raw
