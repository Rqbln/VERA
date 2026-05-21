from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from typing import Any

import mlflow
import yaml

from raip.artifacts.model_card import render_model_card
from raip.artifacts.s3io import upload_bytes
from raip.celery_app import celery_app
from raip.config import get_settings
from raip.benchmarks.catalog import catalog_version as get_catalog_version
from raip.graph.supervisor import run_evaluation_graph
from raip.llm.client import LLMClient
from raip.schemas.benchmark_run import build_benchmark_run_dict
from raip.schemas.complai import ComplaiRequirementScore
from raip.schemas.run_payload import RunCreateRequest, parse_litellm_model_id
from raip.store.redis_run import RedisRunStore


def _git_sha() -> str:
    try:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def _complai_rows(complai_scores: dict[str, ComplaiRequirementScore]) -> list[dict[str, Any]]:
    meta = {
        "R01": ("Robustness predictability", "robustness_safety", "Art. 15"),
        "R02": ("Cyber resilience", "robustness_safety", "Art. 15"),
        "R06": ("Capabilities", "transparency", "Art. 15"),
        "R07": ("Calibration / interpretability", "transparency", "Art. 13"),
        "R08": ("AI disclosure", "transparency", "Art. 13"),
        "R09": ("Watermark / traceability", "transparency", "Art. 50"),
        "R10": ("Representation bias", "fairness", "Art. 10"),
        "R11": ("Fairness", "fairness", "Art. 10"),
        "R12": ("Toxicity", "fairness", "Art. 10"),
    }
    rows: list[dict[str, Any]] = []
    for k in sorted(complai_scores.keys()):
        if k not in meta:
            continue
        cs = complai_scores[k]
        name, principle, art = meta[k]
        rows.append(
            {
                "id": k,
                "name": name,
                "score": round(float(cs.score), 4),
                "ci_lo": round(float(cs.score_ci_lower), 4),
                "ci_hi": round(float(cs.score_ci_upper), 4),
                "benchmarks": list(cs.contributing_benchmarks),
                "principle": principle,
                "aiact": art,
            }
        )
    return rows


def _model_card_context(
    *,
    run_id: str,
    model_id: str,
    complai_scores: dict[str, ComplaiRequirementScore],
    req: RunCreateRequest,
    git_sha: str,
    catalog_version: str,
) -> dict[str, Any]:
    gov = req.governance_model()
    provider, name = parse_litellm_model_id(model_id)
    return {
        "model": {
            "name": name,
            "version": "local",
            "provider": provider,
            "architecture": "see Ollama model card (N04)",
            "params": "unknown",
            "training": "inference-only-eval",
        },
        "run": {
            "id": run_id,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "seed": req.config.seed,
            "catalog_version": catalog_version,
            "git_sha": git_sha,
            "image_digest": "n/a",
        },
        "governance": {
            "intended_use": gov.intended_use,
            "oos_use": gov.oos_use,
        },
        "complai_results": _complai_rows(complai_scores),
        "n01": {"status": "pending", "ref": "MVP3"},
        "n02": {"status": "pending", "ref": "MVP3"},
        "n03": {"kwh": "n/a", "co2eq": "n/a", "ref": "MVP3"},
        "n05": {"runs": "n/a"},
        "n06": {"scenarios": "n/a", "ref": "n/a"},
        "limitations": (
            "MVP2 uses dynamic benchmarks (lm-evaluation-harness when installed, Garak for "
            "selected R02 probes, runtime-generated probes otherwise). "
            "R09 watermark is NA when no detector is configured. "
            "Local 8B models are weaker judges than production vLLM 70B targets."
        ),
        "recommendations": (
            "Install optional [benchmarks] extras for full harness coverage; wire watermark "
            "detector and OpenBao signing per ROADMAP."
        ),
        "signature": {"key_id": "n/a", "digest": "n/a"},
    }


@celery_app.task(bind=True, name="raip.run_benchmark_job")
def run_benchmark_job(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    store = RedisRunStore(settings)
    store.update(run_id, status="running")

    req = RunCreateRequest.model_validate(payload)
    s = get_settings()
    os.environ.setdefault("AWS_ACCESS_KEY_ID", s.minio_access_key)
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", s.minio_secret_key)
    os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", s.minio_endpoint_url)
    os.environ.setdefault("AWS_DEFAULT_REGION", s.minio_region)

    mlflow.set_tracking_uri(s.mlflow_tracking_uri)
    mlflow.set_experiment(s.mlflow_experiment)
    git_sha = _git_sha()
    cat_version = get_catalog_version()

    try:
        initial: dict[str, Any] = {
            "run_id": run_id,
            "model_id": req.model_id,
            "judge_model": s.effective_judge_model,
            "temperature": req.config.temperature,
            "max_tokens": req.config.max_tokens,
            "seed": req.config.seed,
            "benchmarks": list(req.benchmarks),
            "complai_requirements": list(req.complai_requirements),
            "n_samples_per_benchmark": req.config.n_samples_per_benchmark,
            "bootstrap_n": req.config.bootstrap_n,
            "raw_outputs": [],
        }
        state = run_evaluation_graph(initial, llm=LLMClient(s))
        complai: dict[str, ComplaiRequirementScore] = dict(state.get("complai_scores") or {})
        agg: dict[str, float] = {k: float(v.score) for k, v in complai.items()}

        mlflow_run_id: str | None = None
        with mlflow.start_run(run_name=run_id) as active:
            mlflow_run_id = active.info.run_id
            mlflow.log_param("model_id", req.model_id)
            mlflow.log_param("judge_model", s.effective_judge_model)
            mlflow.log_param("seed", req.config.seed)
            mlflow.log_param("catalog_version", cat_version)
            for k, v in complai.items():
                mlflow.log_metric(f"complai_{k}", float(v.score))
                mlflow.log_metric(f"complai_{k}_ci_lo", float(v.score_ci_lower))
                mlflow.log_metric(f"complai_{k}_ci_hi", float(v.score_ci_upper))

        provider, model_name = parse_litellm_model_id(req.model_id)
        br = build_benchmark_run_dict(
            run_id=run_id,
            model_name=model_name,
            provider=provider,
            lifecycle_stage="inference",
            complai_scores=complai,
            complai_requirements=req.complai_requirements,
            benchmarks=req.benchmarks,
            seed=req.config.seed,
            catalog_version=cat_version,
            git_sha=git_sha,
        )
        yaml_body = yaml.safe_dump(br, sort_keys=False, allow_unicode=True)
        card_md = render_model_card(
            _model_card_context(
                run_id=run_id,
                model_id=req.model_id,
                complai_scores=complai,
                req=req,
                git_sha=git_sha,
                catalog_version=cat_version,
            )
        )
        raw_lines = [json.dumps(x, ensure_ascii=False) for x in state.get("raw_outputs") or []]
        raw_jsonl = "\n".join(raw_lines) + ("\n" if raw_lines else "")

        prefix = f"runs/{run_id}"
        upload_bytes(
            f"{prefix}/raw_outputs.jsonl",
            raw_jsonl.encode("utf-8"),
            "application/x-ndjson",
            s,
        )
        upload_bytes(
            f"{prefix}/benchmark_run.yaml",
            yaml_body.encode("utf-8"),
            "application/yaml",
            s,
        )
        upload_bytes(
            f"{prefix}/model_card.md",
            card_md.encode("utf-8"),
            "text/markdown",
            s,
        )

        complai_serializable = {k: v.as_dict() for k, v in complai.items()}
        store.update(
            run_id,
            status="completed",
            mlflow_run_id=mlflow_run_id,
            card_markdown=card_md,
            benchmark_run_yaml=yaml_body,
            aggregate_scores=agg,
            complai_scores=complai_serializable,
        )
        return {"run_id": run_id, "status": "completed", "aggregate_scores": agg}
    except Exception as e:
        store.update(run_id, status="failed", error=str(e))
        raise
