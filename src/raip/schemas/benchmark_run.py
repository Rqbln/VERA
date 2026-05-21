from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from raip.schemas.complai import ComplaiRequirementScore


def build_benchmark_run_dict(
    *,
    run_id: str,
    model_name: str,
    provider: str,
    lifecycle_stage: str,
    complai_scores: dict[str, ComplaiRequirementScore],
    complai_requirements: list[str],
    benchmarks: list[str],
    seed: int,
    catalog_version: str = "mvp2-v1",
    git_sha: str = "unknown",
) -> dict[str, Any]:
    """Canonical document aligned with ROADMAP benchmark_run.yaml + MVP1 §4.3 (bootstrap CI)."""
    req_map = {
        "R01": "R01_robustness_predictability",
        "R02": "R02_cyber_resilience",
        "R06": "R06_capabilities",
        "R07": "R07_interpretability_calibration",
        "R08": "R08_ai_disclosure",
        "R09": "R09_traceability_watermark",
        "R10": "R10_representation_bias",
        "R11": "R11_fairness_non_discrimination",
        "R12": "R12_harmful_content_toxicity",
    }
    metrics: list[dict[str, Any]] = []
    for short, rid in req_map.items():
        if short not in complai_scores:
            continue
        cs = complai_scores[short]
        val = float(cs.score)
        metrics.append(
            {
                "name": f"score_{short}",
                "requirement": rid,
                "value": val,
                "score": val,
                "score_ci_lower": float(cs.score_ci_lower),
                "score_ci_upper": float(cs.score_ci_upper),
                "bootstrap_n": int(cs.bootstrap_n),
                "unit": "ratio",
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
        )

    measurable_ids = [req_map[k] for k in complai_scores if k in req_map]

    return {
        "run_id": run_id,
        "model": {
            "name": model_name,
            "version": "local",
            "provider": provider,
            "checkpoint": None,
        },
        "lifecycle_stage": lifecycle_stage,
        "complai_requirements": {
            "measurable": [{"id": x} for x in measurable_ids],
            "non_measurable": [],
        },
        "benchmarks": [{"id": b} for b in benchmarks],
        "metrics": metrics,
        "hitl_evaluations": [],
        "artifacts": [],
        "governance": {
            "eu_ai_act_principles": [],
            "eu_ai_act_articles": [],
            "nist_rmf": [],
        },
        "reproducibility": {
            "seed": seed,
            "catalog_version": catalog_version,
            "git_sha": git_sha,
            "complai_requirements_requested": complai_requirements,
        },
    }
