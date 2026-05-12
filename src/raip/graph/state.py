from __future__ import annotations

from typing import Any, TypedDict


class EvalState(TypedDict, total=False):
    run_id: str
    model_id: str
    judge_model: str
    temperature: float
    max_tokens: int
    seed: int
    benchmarks: list[str]
    complai_requirements: list[str]
    n_samples_per_benchmark: int
    bootstrap_n: int
    req_benchmark_samples: dict[str, dict[str, list[float]]]
    cyber_metrics: dict[str, float]
    ethics_metrics: dict[str, float]
    aggregate_scores: dict[str, float]
    complai_scores: dict[str, Any]
    raw_outputs: list[dict[str, Any]]
    error: str
