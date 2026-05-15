from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from raip.benchmarks.pilote_v1.load import weights_for_requirement
from raip.benchmarks.pilote_v1.runner import evaluate_pilote_items
from raip.config import Settings, get_settings
from raip.graph.state import EvalState
from raip.llm.client import LLMClient
from raip.schemas.complai import ComplaiRequirementScore
from raip.stats.bootstrap import bootstrap_weighted_requirement_ci_95, effective_bootstrap_n


def _seed_offset(req: str) -> int:
    return sum(ord(c) for c in req) % 100_003


def pilote_node(state: EvalState, llm: LLMClient, _settings: Settings) -> dict[str, Any]:
    benchmarks = state.get("benchmarks") or []
    n_cap = int(state.get("n_samples_per_benchmark") or 500)
    req_b, raw = evaluate_pilote_items(
        model_id=state["model_id"],
        benchmarks=benchmarks,
        n_samples_per_benchmark=n_cap,
        temperature=float(state.get("temperature", 0.0)),
        max_tokens=int(state.get("max_tokens", 1024)),
        seed=state.get("seed"),
        llm=llm,
    )
    return {
        "req_benchmark_samples": req_b,
        "raw_outputs": state.get("raw_outputs", []) + raw,
    }


def aggregate_node(state: EvalState) -> dict[str, Any]:
    reqs = list(state.get("complai_requirements") or [])
    rbs = state.get("req_benchmark_samples") or {}
    seed = int(state.get("seed", 42))
    b_n = effective_bootstrap_n(int(state.get("bootstrap_n", 1000)))

    complai_scores: dict[str, ComplaiRequirementScore] = {}
    aggregate_scores: dict[str, float] = {}

    for r in reqs:
        by_b = {k: list(v) for k, v in (rbs.get(r) or {}).items()}
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

    def pilote(state: EvalState) -> dict[str, Any]:
        return pilote_node(state, client, s)

    def aggregate(state: EvalState) -> dict[str, Any]:
        return aggregate_node(state)

    g = StateGraph(EvalState)
    g.add_node("pilote", pilote)
    g.add_node("aggregate", aggregate)
    g.set_entry_point("pilote")
    g.add_edge("pilote", "aggregate")
    g.add_edge("aggregate", END)
    return g.compile()


def run_evaluation_graph(initial: EvalState, llm: LLMClient | None = None) -> EvalState:
    app = build_supervisor_graph(llm=llm)
    result = app.invoke(initial)
    return result  # type: ignore[return-value]
