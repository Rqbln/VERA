from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from vera.benchmarks.catalog import weights_for_requirement
from vera.benchmarks.runners.evaluate import evaluate_benchmarks
from vera.config import Settings, get_settings
from vera.graph.state import EvalState
from vera.llm.client import LLMClient
from vera.schemas.complai import ComplaiRequirementScore
from vera.stats.bootstrap import bootstrap_weighted_requirement_ci_95, effective_bootstrap_n


def _seed_offset(req: str) -> int:
    return sum(ord(c) for c in req) % 100_003


def evaluate_node(state: EvalState, llm: LLMClient, settings: Settings) -> dict[str, Any]:
    benchmarks = state.get("benchmarks") or []
    n_cap = int(state.get("n_samples_per_benchmark") or 500)
    req_b, raw = evaluate_benchmarks(
        model_id=state["model_id"],
        judge_model=state.get("judge_model") or settings.effective_judge_model,
        benchmarks=benchmarks,
        n_samples_per_benchmark=n_cap,
        temperature=float(state.get("temperature", 0.0)),
        max_tokens=int(state.get("max_tokens", 1024)),
        seed=state.get("seed"),
        llm=llm,
        dataset_context=state.get("dataset_context"),
    )
    return {
        "req_benchmark_samples": req_b,
        "raw_outputs": state.get("raw_outputs", []) + raw,
    }


def aggregate_node(state: EvalState) -> dict[str, Any]:
    reqs = list(state.get("complai_requirements") or [])
    rbs = state.get("req_benchmark_samples") or {}
    raw_outputs = state.get("raw_outputs") or []
    seed = int(state.get("seed", 42))
    b_n = effective_bootstrap_n(int(state.get("bootstrap_n", 1000)))

    na_reqs = {
        str(r.get("requirement"))
        for r in raw_outputs
        if r.get("status") == "NA" and r.get("requirement")
    }

    complai_scores: dict[str, ComplaiRequirementScore] = {}
    aggregate_scores: dict[str, float] = {}

    for r in reqs:
        if r in na_reqs:
            continue
        by_b = {k: list(v) for k, v in (rbs.get(r) or {}).items()}
        if not by_b:
            continue
        w = weights_for_requirement(r)
        mean_s, lo, hi = bootstrap_weighted_requirement_ci_95(
            by_b,
            w,
            seed=seed + _seed_offset(r),
            n_resamples=b_n,
        )
        touched = tuple(sorted(by_b.keys()))
        n_samples = sum(len(v) for v in by_b.values())
        crs = ComplaiRequirementScore(
            score=mean_s,
            score_ci_lower=lo,
            score_ci_upper=hi,
            bootstrap_n=b_n,
            contributing_benchmarks=touched,
            sample_count=n_samples,
        )
        complai_scores[r] = crs
        aggregate_scores[r] = mean_s

    return {"complai_scores": complai_scores, "aggregate_scores": aggregate_scores}


def build_supervisor_graph(llm: LLMClient | None = None, settings: Settings | None = None):
    s = settings or get_settings()
    client = llm or LLMClient(s)

    def evaluate(state: EvalState) -> dict[str, Any]:
        return evaluate_node(state, client, s)

    def aggregate(state: EvalState) -> dict[str, Any]:
        return aggregate_node(state)

    g = StateGraph(EvalState)
    g.add_node("evaluate", evaluate)
    g.add_node("aggregate", aggregate)
    g.set_entry_point("evaluate")
    g.add_edge("evaluate", "aggregate")
    g.add_edge("aggregate", END)
    return g.compile()


def run_evaluation_graph(initial: EvalState, llm: LLMClient | None = None) -> EvalState:
    app = build_supervisor_graph(llm=llm)
    result = app.invoke(initial)
    return result  # type: ignore[return-value]
