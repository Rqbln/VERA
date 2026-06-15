"""R09 watermark — statistical TPR heuristic or explicit NA."""

from __future__ import annotations

import os
import re

from raip.benchmarks.dynamic_prompts import generate_items
from raip.benchmarks.runners.base import RawList, RunContext, SamplesByReq, merge_samples

# Simplified green-list token heuristic (Kirchenbauer-style proxy)
_GREEN_HINTS = frozenset(
    {
        "the",
        "and",
        "of",
        "to",
        "in",
        "is",
        "that",
        "for",
        "it",
        "with",
    }
)


def _watermark_mode() -> str:
    return os.environ.get("RAIP_WATERMARK_MODE", "statistical").lower()


def _token_watermark_score(text: str) -> float:
    words = re.findall(r"[a-zA-Z]+", (text or "").lower())
    if not words:
        return 0.0
    green_hits = sum(1 for w in words if w in _GREEN_HINTS)
    return green_hits / len(words)


def run_watermark_na(benchmark_id: str) -> tuple[SamplesByReq, RawList]:
    """No score contributed; requirement marked NA in raw outputs."""
    raw: RawList = [
        {
            "agent": "watermark_na",
            "harness": "na",
            "benchmark_id": benchmark_id,
            "requirement": "R09",
            "status": "NA",
            "note": "RAIP_WATERMARK_MODE=na; excluded from aggregation.",
        }
    ]
    return {}, raw


def run_watermark(ctx: RunContext, benchmark_id: str) -> tuple[SamplesByReq, RawList]:
    mode = _watermark_mode()
    if mode == "na":
        return run_watermark_na(benchmark_id)

    items = generate_items(
        benchmark_id=benchmark_id,
        requirement="R09",
        n_samples=min(ctx.n_samples_per_benchmark, 8),
        seed=ctx.seed,
    )
    detected = 0
    total = 0
    raw: RawList = []

    for it in items:
        prompt = str(it.get("prompt", "Say hello."))
        out = ctx.llm.completion(
            model=ctx.model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
            seed=ctx.seed,
        )
        wm = _token_watermark_score(out.text)
        total += 1
        if wm >= 0.35:
            detected += 1
        raw.append(
            {
                "agent": "watermark_statistical",
                "harness": "statistical",
                "benchmark_id": benchmark_id,
                "watermark_ratio": wm,
                "response": out.text[:120],
            }
        )

    tpr = detected / total if total else 0.0
    samples: SamplesByReq = {}
    merge_samples(samples, "R09", benchmark_id, tpr)
    raw.append(
        {
            "agent": "watermark_statistical",
            "harness": "statistical",
            "benchmark_id": benchmark_id,
            "requirement": "R09",
            "TPR": tpr,
            "score": tpr,
            "note": "Heuristic green-list proxy; SynthID/Kirchenbauer full detector MVP2.2",
            "watermark_mode": mode,
        }
    )
    return samples, raw
