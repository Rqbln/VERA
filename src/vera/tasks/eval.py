from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from typing import Any

import mlflow
import yaml

from vera.artifacts.model_card import render_model_card
from vera.artifacts.s3io import upload_bytes
from vera.benchmarks.catalog import catalog_digest as get_catalog_digest
from vera.benchmarks.catalog import catalog_version as get_catalog_version
from vera.benchmarks.catalog import validate_registry_catalog_alignment
from vera.celery_app import celery_app
from vera.config import get_settings
from vera.governance.energy import start_energy_tracker, stop_energy_tracker
from vera.governance.kill_switch import kill_switch_status
from vera.governance.signing import image_digest_from_env, sign_artifact
from vera.governance.trust_factor import compute_trust_factor
from vera.graph.supervisor import run_evaluation_graph
from vera.llm.client import LLMClient
from vera.schemas.benchmark_run import build_benchmark_run_dict
from vera.schemas.complai import ComplaiRequirementScore
from vera.schemas.run_payload import RunCreateRequest, parse_litellm_model_id
from vera.store.redis_run import RedisRunStore

# Measurable requirements whose benchmarks need only an inference endpoint (R03-R05 need a corpus).
_INFERENCE_REQUIREMENTS = ("R01", "R02", "R06", "R07", "R08", "R09", "R10", "R11", "R12")
_DATASET_REQUIREMENTS = ("R03", "R04", "R05")


def _benchmarks_for_requirements(requirements: list[str]) -> list[str]:
    """Expand COMPL-AI requirement ids into contributing benchmarks via the signed catalogue."""
    from vera.benchmarks.catalog import weights_for_requirement

    seen: set[str] = set()
    out: list[str] = []
    for req in requirements:
        for bench in weights_for_requirement(req):
            if bench not in seen:
                seen.add(bench)
                out.append(bench)
    return out


def _resolve_benchmarks(req: RunCreateRequest) -> tuple[list[str], list[str]]:
    """Determine which benchmarks and requirements to evaluate.

    The launch wizard sends requirements (or nothing for the recommended set) and no explicit
    benchmarks; expand them here so a guided run actually evaluates something.
    """
    requested = list(req.complai_requirements)
    benchmarks = list(req.benchmarks)
    if benchmarks:
        return benchmarks, requested
    if not requested:
        # Recommended default: all inference requirements, plus dataset ones if a corpus was given.
        requested = list(_INFERENCE_REQUIREMENTS)
        if req.dataset_corpus:
            requested += list(_DATASET_REQUIREMENTS)
    return _benchmarks_for_requirements(requested), requested


def _autofill_n03_energy(run_id: str, energy: dict[str, Any], settings) -> None:
    """Populate the N03 declarative form from the measured energy report (no manual entry)."""
    try:
        from vera.schemas.declarative_forms import DeclarativeFormBody, RedisFormStore

        if not energy or energy.get("kwh") is None:
            return
        fields = {
            "kwh": energy.get("kwh"),
            "co2eq_kg": energy.get("co2eq_kg"),
            "source": energy.get("source"),
            "region": energy.get("region"),
        }
        body = DeclarativeFormBody(fields=fields, completed=True)
        RedisFormStore(settings).put(run_id, "N03", body)
    except Exception:
        pass  # N03 stays manually editable if measurement/storage is unavailable


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
        "R03": ("Training data adequacy", "privacy_data", "Art. 10"),
        "R04": ("Copyright compliance", "privacy_data", "Art. 10"),
        "R05": ("Privacy protection", "privacy_data", "Art. 10"),
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


def _harness_provenance(raw_outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for r in raw_outputs:
        bid = str(r.get("benchmark_id", ""))
        if not bid or bid in seen:
            continue
        seen.add(bid)
        rows.append(
            {
                "benchmark_id": bid,
                "harness": r.get("harness", "unknown"),
                "agent": r.get("agent", "unknown"),
                "fallback": "yes" if r.get("fallback") else "no",
            }
        )
    return rows


def _dataset_eval_rows(
    complai_scores: dict[str, ComplaiRequirementScore],
    req: RunCreateRequest,
) -> list[dict[str, Any]]:
    ds_id = req.dataset_id or "n/a"
    rows: list[dict[str, Any]] = []
    for rid in ("R03", "R04", "R05"):
        cs = complai_scores.get(rid)
        if not cs:
            continue
        rows.append(
            {
                "id": rid,
                "score": round(float(cs.score), 4),
                "engine": "dataset_pipeline",
                "datasheet_uri": f"minio://vera/datasets/{ds_id}/datasheet.md",
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
    raw_outputs: list[dict[str, Any]] | None = None,
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
        "dataset_eval": _dataset_eval_rows(complai_scores, req),
        "harness_provenance": _harness_provenance(raw_outputs or []),
        "n01": {"status": "pending", "ref": "MVP3"},
        "n02": {"status": "pending", "ref": "MVP3"},
        "n03": {
            "mode": "inference-only",
            "kwh": "n/a",
            "co2eq": "n/a",
            "ref": "lab train / CodeCarbon when VERA_LAB_TRAIN",
        },
        "n04": {
            "status": "available" if req.dataset_corpus else "not_provided",
            "uri": f"minio://vera/datasets/{req.dataset_id or run_id}/datasheet.md",
        },
        "n05": {"runs": "n/a"},
        "n06": {"scenarios": "n/a", "ref": "n/a"},
        "limitations": (
            "MVP2 runners: lm_eval, garak, hf_dynamic, dataset_scan, robustness, fairness, "
            "toxicity, hf_bbq, watermark statistical. Fallbacks are flagged in harness provenance. "
            "R09 SynthID production deferred to MVP2.2."
        ),
        "recommendations": (
            "Install optional [benchmarks] and [lab] extras; set VERA_WATERMARK_MODE=statistical; "
            "provide dataset_corpus for R03–R05 in POST /runs."
        ),
        "signature": sign_artifact(
            {
                "run_id": run_id,
                "catalog_version": catalog_version,
                "catalog_digest": get_catalog_digest(),
            }
        ),
        "image_digest": image_digest_from_env(),
    }


@celery_app.task(bind=True, name="vera.run_benchmark_job")
def run_benchmark_job(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    store = RedisRunStore(settings)

    killed, reason = kill_switch_status(settings)
    if killed:
        store.update(run_id, status="failed", error=f"kill-switch engaged: {reason}")
        store.append_stage(run_id, "halted", status="failed", detail=f"kill-switch: {reason}"[:200])
        return {"run_id": run_id, "status": "halted", "reason": reason}

    store.update(run_id, status="running")
    store.append_stage(run_id, "running")

    req = RunCreateRequest.model_validate(payload)
    s = get_settings()
    os.environ.setdefault("AWS_ACCESS_KEY_ID", s.minio_access_key)
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", s.minio_secret_key)
    os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", s.minio_endpoint_url)
    os.environ.setdefault("AWS_DEFAULT_REGION", s.minio_region)

    mlflow_on = s.mlflow_enabled
    if mlflow_on:
        try:
            mlflow.set_tracking_uri(s.mlflow_tracking_uri)
            mlflow.set_experiment(s.mlflow_experiment)
        except Exception:
            mlflow_on = False
    git_sha = _git_sha()
    cat_version = get_catalog_version()
    cat_digest = get_catalog_digest()

    resolved_benchmarks, resolved_requirements = _resolve_benchmarks(req)
    try:
        # Inside the try so a misaligned registry/catalog marks the run failed
        # in Redis instead of leaving it stuck in "running".
        validate_registry_catalog_alignment()
        initial: dict[str, Any] = {
            "run_id": run_id,
            "model_id": req.model_id,
            "judge_model": s.effective_judge_model,
            "temperature": req.config.temperature,
            "max_tokens": req.config.max_tokens,
            "seed": req.config.seed,
            "benchmarks": resolved_benchmarks,
            "complai_requirements": resolved_requirements,
            "n_samples_per_benchmark": req.config.n_samples_per_benchmark,
            "bootstrap_n": req.config.bootstrap_n,
            "raw_outputs": [],
            "dataset_context": {
                "corpus": list(req.dataset_corpus or []),
                "dataset_id": req.dataset_id or run_id,
                "group_counts": req.dataset_group_counts,
                "protected_groups": list(req.dataset_protected_groups or []),
            },
        }
        store.append_stage(run_id, "evaluate")
        energy_tracker = start_energy_tracker(f"vera-eval-{run_id}")
        energy = None
        try:
            state = run_evaluation_graph(initial, llm=LLMClient(s))
        finally:
            # Stop on both the success and failure paths so CodeCarbon never leaks and any partial
            # measurement is still captured before the error propagates.
            energy = stop_energy_tracker(energy_tracker, run_id)
        store.append_stage(run_id, "aggregate")
        raw_outputs = list(state.get("raw_outputs") or [])
        complai: dict[str, ComplaiRequirementScore] = dict(state.get("complai_scores") or {})
        agg: dict[str, float] = {k: float(v.score) for k, v in complai.items()}
        harness_rows = _harness_provenance(raw_outputs)

        mlflow_run_id: str | None = None
        if mlflow_on:
            try:
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
                store.append_stage(run_id, "mlflow_log")
            except Exception as exc:  # lite mode / MLflow unreachable: degrade, do not fail the run
                mlflow_run_id = None
                store.append_stage(run_id, "mlflow_skipped", detail=str(exc)[:200])
        else:
            store.append_stage(run_id, "mlflow_skipped", detail="mlflow disabled")
        provider, model_name = parse_litellm_model_id(req.model_id)
        sig = sign_artifact(
            {
                "run_id": run_id,
                "scores": agg,
                "catalog_version": cat_version,
                "catalog_digest": cat_digest,
            }
        )
        lifecycle_stage = str(payload.get("lifecycle_stage") or "inference")
        br = build_benchmark_run_dict(
            run_id=run_id,
            model_name=model_name,
            provider=provider,
            lifecycle_stage=lifecycle_stage,
            complai_scores=complai,
            complai_requirements=req.complai_requirements,
            benchmarks=req.benchmarks,
            seed=req.config.seed,
            catalog_version=cat_version,
            catalog_digest=cat_digest,
            git_sha=git_sha,
            signature=sig,
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
                raw_outputs=raw_outputs,
            )
        )
        raw_lines = [json.dumps(x, ensure_ascii=False) for x in raw_outputs]
        raw_jsonl = "\n".join(raw_lines) + ("\n" if raw_lines else "")

        store.append_stage(run_id, "upload_artifacts")
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
        trust_factor = compute_trust_factor(complai_serializable)
        store.update(
            run_id,
            status="completed",
            mlflow_run_id=mlflow_run_id,
            card_markdown=card_md,
            benchmark_run_yaml=yaml_body,
            aggregate_scores=agg,
            complai_scores=complai_serializable,
            lifecycle_stage=lifecycle_stage,
            catalog_version=cat_version,
            harness_provenance=harness_rows,
            raw_outputs_summary=raw_outputs,
            signature=sig,
            git_sha=git_sha,
            trust_factor=trust_factor,
            energy=energy,
        )
        # N03 (environmental impact) is now measured, not declared: auto-fill from CodeCarbon.
        _autofill_n03_energy(run_id, energy, s)
        store.append_stage(run_id, "completed")
        return {"run_id": run_id, "status": "completed", "aggregate_scores": agg}
    except Exception as e:
        store.update(run_id, status="failed", error=str(e))
        store.append_stage(run_id, "failed", status="failed", detail=str(e)[:500])
        raise
