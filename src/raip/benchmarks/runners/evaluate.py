"""Dispatch benchmark evaluation to MVP2 runners."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from raip.api.benchmark_registry import get_benchmark_entry
from raip.benchmarks.runners.base import RunContext, RawList, SamplesByReq
from raip.benchmarks.runners.garak_runner import run_garak
from raip.benchmarks.runners.hf_dynamic import run_hf_dynamic
from raip.benchmarks.runners.lm_eval_runner import run_lm_eval
from raip.benchmarks.runners.watermark import run_watermark_na
from raip.llm.client import LLMClient


def _merge_dict(a: SamplesByReq, b: SamplesByReq) -> SamplesByReq:
    out: SamplesByReq = defaultdict(lambda: defaultdict(list))
    for src in (a, b):
        for req, bmap in src.items():
            for bid, scores in bmap.items():
                out[req][bid].extend(scores)
    return {r: dict(bm) for r, bm in out.items()}


def evaluate_benchmarks(
    *,
    model_id: str,
    judge_model: str,
    benchmarks: list[str],
    n_samples_per_benchmark: int,
    temperature: float,
    max_tokens: int,
    seed: int | None,
    llm: LLMClient,
) -> tuple[dict[str, dict[str, list[float]]], list[dict[str, Any]]]:
    """
    Returns (req_benchmark_samples, raw_outputs).
    """
    ctx = RunContext(
        model_id=model_id,
        judge_model=judge_model,
        temperature=temperature,
        max_tokens=max_tokens,
        seed=seed,
        n_samples_per_benchmark=n_samples_per_benchmark,
        llm=llm,
    )
    all_samples: SamplesByReq = {}
    all_raw: RawList = []

    for bid in benchmarks:
        entry = get_benchmark_entry(bid)
        if not entry:
            continue
        impl = str(entry.get("implementation") or "hf_dynamic")

        if impl == "watermark_na":
            s, r = run_watermark_na(bid)
        elif impl == "lm_eval":
            s, r = run_lm_eval(ctx, bid)
        elif impl == "garak":
            s, r = run_garak(ctx, bid)
        else:
            s, r = run_hf_dynamic(ctx, bid)

        all_samples = _merge_dict(all_samples, s)
        all_raw.extend(r)

    frozen = {
        req: {b: list(xs) for b, xs in bmap.items()}
        for req, bmap in all_samples.items()
    }
    return frozen, all_raw
