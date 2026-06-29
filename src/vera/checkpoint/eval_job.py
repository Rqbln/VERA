"""Checkpoint evaluation — reuse LangGraph + Timescale metrics."""

from __future__ import annotations

from typing import Any

from vera.config import get_settings
from vera.graph.supervisor import run_evaluation_graph
from vera.lab.bsr import compute_bsr
from vera.llm.client import LLMClient
from vera.store.timescale import TimescaleWriter


def run_checkpoint_eval(
    *,
    run_id: str,
    model_id: str,
    checkpoint: str,
    lifecycle_stage: str,
    benchmarks: list[str],
    complai_requirements: list[str],
    poisoned: bool = False,
    trigger_id: str | None = None,
    asr_pre: float | None = None,
    asr_post: float | None = None,
) -> dict[str, Any]:
    s = get_settings()
    state = run_evaluation_graph(
        {
            "run_id": run_id,
            "model_id": model_id,
            "judge_model": s.effective_judge_model,
            "temperature": 0.0,
            "max_tokens": 256,
            "seed": 42,
            "benchmarks": benchmarks,
            "complai_requirements": complai_requirements,
            "n_samples_per_benchmark": 2,
            "bootstrap_n": 50,
            "raw_outputs": [],
        },
        llm=LLMClient(s),
    )
    agg = state.get("aggregate_scores") or {}
    ts = TimescaleWriter()
    for req, val in agg.items():
        ts.write_metric(
            run_id=run_id,
            model_id=model_id,
            checkpoint=checkpoint,
            requirement=req,
            metric="complai_score",
            value=float(val),
            tags={"poisoned": str(poisoned).lower(), "trigger_id": trigger_id or ""},
        )
    bsr = None
    if asr_pre is not None and asr_post is not None:
        bsr = compute_bsr(asr_pre, asr_post)
        ts.write_metric(
            run_id=run_id,
            model_id=model_id,
            checkpoint=checkpoint,
            requirement="R02",
            metric="BSR",
            value=bsr,
            tags={"poisoned": str(poisoned).lower()},
        )
    return {
        "run_id": run_id,
        "checkpoint": checkpoint,
        "lifecycle_stage": lifecycle_stage,
        "aggregate_scores": agg,
        "bsr": bsr,
    }
