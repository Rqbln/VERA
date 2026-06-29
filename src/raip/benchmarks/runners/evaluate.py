"""Dispatch benchmark evaluation to MVP2 runners."""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

from raip.api.benchmark_registry import get_benchmark_entry
from raip.benchmarks.runners.base import RawList, RunContext, SamplesByReq
from raip.benchmarks.runners.dataset_scan import run_dataset_scan
from raip.benchmarks.runners.fairness import run_fairness_r11
from raip.benchmarks.runners.garak_runner import run_garak
from raip.benchmarks.runners.hf_bbq import run_hf_bbq
from raip.benchmarks.runners.hf_dynamic import run_hf_dynamic
from raip.benchmarks.runners.lm_eval_runner import run_lm_eval
from raip.benchmarks.runners.robustness import run_robustness_r01
from raip.benchmarks.runners.toxicity import run_toxicity_r12
from raip.benchmarks.runners.watermark import run_watermark, run_watermark_na
from raip.llm.client import LLMClient

# When RAIP_REQUIRE_NATIVE=1, a heuristic fallback on a benchmark that has a native harness is a
# hard error (so a paper run is provably native) — except implementations listed here, which may
# legitimately fall back (e.g. garak does not run on Apple Silicon). Override via RAIP_NATIVE_ALLOW.
_DEFAULT_NATIVE_ALLOW = {"garak"}


def _require_native() -> bool:
    return os.environ.get("RAIP_REQUIRE_NATIVE", "").strip().lower() in ("1", "true", "yes")


def _native_allow() -> set[str]:
    extra = {x.strip() for x in os.environ.get("RAIP_NATIVE_ALLOW", "").split(",") if x.strip()}
    return _DEFAULT_NATIVE_ALLOW | extra


class NativeHarnessRequired(RuntimeError):
    """Raised when RAIP_REQUIRE_NATIVE is set and a benchmark fell back to a heuristic."""


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
    dataset_context: dict[str, Any] | None = None,
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
    ds_ctx = dataset_context or {}
    all_samples: SamplesByReq = {}
    all_raw: RawList = []

    for bid in benchmarks:
        entry = get_benchmark_entry(bid)
        if not entry:
            continue
        impl = str(entry.get("implementation") or "hf_dynamic")

        if impl == "dataset_scan":
            s, r = run_dataset_scan(bid, ds_ctx)
        elif impl == "watermark_na":
            s, r = run_watermark_na(bid)
        elif impl == "watermark":
            s, r = run_watermark(ctx, bid)
        elif impl == "robustness_r01":
            s, r = run_robustness_r01(ctx, bid)
        elif impl == "fairness_r11":
            s, r = run_fairness_r11(ctx, bid)
        elif impl == "toxicity_r12":
            s, r = run_toxicity_r12(ctx, bid)
        elif impl == "hf_bbq":
            s, r = run_hf_bbq(ctx, bid)
        elif impl == "lm_eval":
            s, r = run_lm_eval(ctx, bid)
        elif impl == "garak":
            s, r = run_garak(ctx, bid)
        else:
            s, r = run_hf_dynamic(ctx, bid)

        if _require_native() and impl not in _native_allow():
            fell_back = [
                str(row.get("fallback_reason") or "heuristic") for row in r if row.get("fallback")
            ]
            if fell_back:
                raise NativeHarnessRequired(
                    f"benchmark {bid!r} (impl={impl}) fell back to heuristic "
                    f"({fell_back[0]}) but RAIP_REQUIRE_NATIVE is set"
                )

        all_samples = _merge_dict(all_samples, s)
        all_raw.extend(r)

    frozen = {
        req: {b: list(xs) for b, xs in bmap.items()}
        for req, bmap in all_samples.items()
    }
    return frozen, all_raw
