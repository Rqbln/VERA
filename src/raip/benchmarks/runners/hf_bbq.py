"""R10 — BBQ/BOLD/StereoSet bias via HF datasets or structured probes."""

from __future__ import annotations

import os
from typing import Any

from raip.api.benchmark_registry import get_benchmark_entry
from raip.benchmarks.dynamic_prompts import generate_items
from raip.benchmarks.metrics import score_bbq_choice
from raip.benchmarks.runners.base import RunContext, RawList, SamplesByReq, merge_samples
from raip.benchmarks.runners.hf_dynamic import run_hf_dynamic


def _bias_score_from_responses(pairs: list[tuple[float, float]]) -> float:
    """pairs of (neutral_score, biased_score) -> s = 1 - |bias|."""
    if not pairs:
        return 0.5
    bias_vals = [abs(b - n) for n, b in pairs]
    bias_avg = sum(bias_vals) / len(bias_vals)
    return max(0.0, min(1.0, 1.0 - bias_avg))


def run_hf_bbq(ctx: RunContext, benchmark_id: str) -> tuple[SamplesByReq, RawList]:
    entry = get_benchmark_entry(benchmark_id) or {}
    req = "R10"

    try:
        from datasets import load_dataset  # type: ignore[import-untyped]

        ds_name = {
            "bbq": "lighteval/bbq",
            "bold": "lighteval/bold",
            "stereoset": "lighteval/stereoset",
        }.get(benchmark_id)
        if ds_name:
            trust_remote = os.environ.get("RAIP_HF_TRUST_REMOTE_CODE", "").lower() in (
                "1",
                "true",
                "yes",
            )
            ds = load_dataset(
                ds_name,
                split="train[:20]",
                trust_remote_code=trust_remote,
            )
            pairs: list[tuple[float, float]] = []
            raw: RawList = []
            for row in ds:
                prompt = str(row.get("question") or row.get("context") or "")[:500]
                if not prompt:
                    continue
                out = ctx.llm.completion(
                    model=ctx.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=ctx.temperature,
                    max_tokens=ctx.max_tokens,
                    seed=ctx.seed,
                )
                prefer = str(row.get("label") or "A")
                sc = score_bbq_choice(out.text, prefer)
                pairs.append((sc, 1.0 - sc))
            score = _bias_score_from_responses(pairs)
            samples: SamplesByReq = {}
            merge_samples(samples, req, benchmark_id, score)
            raw.append(
                {
                    "agent": "hf_bbq",
                    "harness": "hf_datasets",
                    "benchmark_id": benchmark_id,
                    "requirement": req,
                    "score": score,
                    "n": len(pairs),
                }
            )
            return samples, raw
    except Exception as exc:
        s, r = run_hf_dynamic(ctx, benchmark_id)
        for row in r:
            row["harness"] = "hf_dynamic"
            row["fallback"] = True
            row["fallback_reason"] = str(exc)[:200]
        return s, r

    return run_hf_dynamic(ctx, benchmark_id)
