"""lm-evaluation-harness adapter (optional dependency)."""

from __future__ import annotations

import os

from raip.api.benchmark_registry import get_benchmark_entry
from raip.benchmarks.runners.base import RawList, RunContext, SamplesByReq, merge_samples
from raip.benchmarks.runners.hf_dynamic import run_hf_dynamic


def _litellm_model_arg(model_id: str) -> str:
    if model_id.startswith("ollama/"):
        return model_id
    return model_id


def run_lm_eval(ctx: RunContext, benchmark_id: str) -> tuple[SamplesByReq, RawList]:
    entry = get_benchmark_entry(benchmark_id)
    if not entry:
        return {}, []
    task = str(entry.get("harness_task") or benchmark_id)
    req = str(entry.get("complai", "R06")).split(",")[0].strip()

    try:
        import lm_eval  # type: ignore[import-untyped]
        # lm-eval 0.4.x ships the LiteLLM chat adapter under models.litellm_llms.
        from lm_eval.models.litellm_llms import LiteLLMChatCompletion  # type: ignore[import-untyped]
    except ImportError:
        samples, raw = run_hf_dynamic(ctx, benchmark_id)
        for r in raw:
            r["fallback"] = True
            r["fallback_reason"] = "lm_eval not installed"
        return samples, raw

    limit = max(1, min(ctx.n_samples_per_benchmark, 10))
    from raip.config import get_settings

    os.environ.setdefault("OLLAMA_API_BASE", get_settings().ollama_api_base)

    # Ollama serves a chat endpoint with no token logprobs, so loglikelihood multiple-choice tasks
    # (e.g. MMLU) cannot run, and generative tasks are slow. The native lm-eval harness is reserved
    # for logprob-capable backends (vLLM); set RAIP_LM_EVAL_FORCE=1 to attempt it on Ollama anyway.
    if ctx.model_id.startswith("ollama/") and os.environ.get("RAIP_LM_EVAL_FORCE", "") not in ("1", "true"):
        samples, raw = run_hf_dynamic(ctx, benchmark_id)
        for r in raw:
            r["fallback"] = True
            r["fallback_reason"] = "ollama: no logprobs; native lm-eval needs a vLLM backend"
        return samples, raw

    try:
        # Chat-completion serving (Ollama) supports generate-until tasks (gsm8k, humaneval) natively
        # but not loglikelihood multiple-choice (e.g. MMLU) — those raise and fall back below, since
        # Ollama does not expose token logprobs.
        model = LiteLLMChatCompletion(model=_litellm_model_arg(ctx.model_id))
        results = lm_eval.simple_evaluate(
            model=model,
            tasks=[task],
            num_fewshot=0,
            limit=limit,
            random_seed=ctx.seed,
        )
    except Exception as exc:
        samples, raw = run_hf_dynamic(ctx, benchmark_id)
        for r in raw:
            r["fallback"] = True
            r["fallback_reason"] = str(exc)[:200]
        return samples, raw

    samples: SamplesByReq = {}
    raw: RawList = []
    task_res = (results.get("results") or {}).get(task) or {}
    acc = task_res.get("acc,none") or task_res.get("acc") or task_res.get("exact_match,none")
    if acc is None:
        samples, raw = run_hf_dynamic(ctx, benchmark_id)
        for r in raw:
            r["fallback"] = True
            r["fallback_reason"] = "lm_eval returned no acc metric"
        return samples, raw

    score = float(acc)
    merge_samples(samples, req, benchmark_id, score)
    raw.append(
        {
            "agent": "lm_eval",
            "harness": "lm_eval",
            "benchmark_id": benchmark_id,
            "requirement": req,
            "harness_task": task,
            "metric": "acc",
            "score": score,
            "limit": limit,
        }
    )
    return samples, raw
