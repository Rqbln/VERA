from __future__ import annotations

import json
from typing import Annotated, Any

import httpx
import yaml
from fastapi import APIRouter, Depends, HTTPException, Query

from raip.api.auth import (
    ROLE_COMPLIANCE,
    ROLE_CYBER,
    ROLE_DS,
    ROLE_INSPECTOR,
    AuthUser,
    get_current_user,
    require_roles,
)
from raip.artifacts.s3io import download_bytes, presign_get
from raip.config import Settings, get_settings
from raip.dashboard.triage import (
    ALL_MEASURABLE,
    build_requirement_rows,
    is_pilote_run,
)
from raip.store.redis_run import RedisRunStore, RunRecord

router = APIRouter(prefix="/api/v1", tags=["dashboard"])

CYBER_REQS = ["R02", "R09", "R12"]
DS_REQS = ["R01", "R06", "R07"]

ARTIFACT_KEYS = {
    "benchmark_run": "benchmark_run.yaml",
    "model_card": "model_card.md",
    "raw_outputs": "raw_outputs.jsonl",
}


def _store() -> RedisRunStore:
    return RedisRunStore()


def _get_run_or_404(run_id: str) -> RunRecord:
    rec = _store().get(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    return rec


def _requested_requirements(rec: RunRecord) -> list[str]:
    payload = rec.payload or {}
    reqs = list(payload.get("complai_requirements") or [])
    return reqs or list(ALL_MEASURABLE)


def _raw_outputs(rec: RunRecord) -> list[dict[str, Any]]:
    if rec.raw_outputs_summary:
        return rec.raw_outputs_summary
    body = download_bytes(f"runs/{rec.run_id}/raw_outputs.jsonl")
    if not body:
        return []
    rows: list[dict[str, Any]] = []
    for line in body.decode("utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _artifact_uris(run_id: str, settings: Settings) -> dict[str, str]:
    prefix = f"runs/{run_id}"
    bucket = settings.minio_bucket
    return {
        k: f"s3://{bucket}/{prefix}/{fname}"
        for k, fname in ARTIFACT_KEYS.items()
    }


def _non_measurable_slots(rec: RunRecord) -> dict[str, Any]:
    payload = rec.payload or {}
    dataset_id = payload.get("dataset_id") or rec.run_id
    return {
        "n01": {"status": "pending", "queue_count": 0, "tasks": []},
        "n02": {"status": "pending", "queue_count": 0, "tasks": []},
        "n03": {"status": "n/a", "ref": "CodeCarbon when lab train"},
        "n04": {
            "status": "available" if rec.card_markdown else "pending",
            "model_card_uri": _artifact_uris(rec.run_id, get_settings()).get("model_card"),
            "datasheet_uri": f"s3://{get_settings().minio_bucket}/datasets/{dataset_id}/datasheet.md",
        },
        "n05": {"status": "mvp3_deferred"},
        "n06": {"status": "mvp3_deferred"},
    }


def _run_summary_dict(rec: RunRecord, *, filter_ids: list[str] | None = None) -> dict[str, Any]:
    settings = get_settings()
    provenance = rec.harness_provenance or []
    raw = _raw_outputs(rec)
    requested = _requested_requirements(rec)
    requirements = build_requirement_rows(
        run_status=rec.status,
        requested=requested,
        complai_scores=rec.complai_scores or {},
        provenance=provenance,
        raw_outputs=raw,
        filter_ids=filter_ids,
    )
    triage_counts = {
        t: sum(1 for r in requirements if r["triage"] == t)
        for t in ("failed", "fallback", "uncovered", "ok", "na")
    }
    return {
        "run_id": rec.run_id,
        "status": rec.status,
        "model_id": rec.model_id,
        "lifecycle_stage": rec.lifecycle_stage,
        "catalog_version": rec.catalog_version,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
        "error": rec.error,
        "mlflow_run_id": rec.mlflow_run_id,
        "git_sha": rec.git_sha,
        "signature": rec.signature,
        "requirements": requirements,
        "triage_counts": triage_counts,
        "harness_provenance": provenance,
        "artifacts": _artifact_uris(rec.run_id, settings),
        "non_measurable": _non_measurable_slots(rec),
        "requested_requirements": requested,
    }


@router.get("/runs")
def list_runs(
    _user: Annotated[AuthUser, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    model_id: str | None = None,
    lifecycle: str | None = None,
    status: str | None = None,
    exclude_pilote: bool = True,
) -> dict[str, Any]:
    page, total = _store().list_runs(
        limit=limit,
        offset=offset,
        model_id=model_id,
        lifecycle=lifecycle,
        status=status,
        exclude_pilote=exclude_pilote,
    )
    return {
        "runs": [
            {
                "run_id": r.run_id,
                "status": r.status,
                "model_id": r.model_id,
                "lifecycle_stage": r.lifecycle_stage,
                "catalog_version": r.catalog_version,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in page
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/runs/{run_id}/summary")
def run_summary(
    run_id: str,
    user: Annotated[AuthUser, Depends(get_current_user)],
    lens: str | None = Query(None, description="compliance|cyber|ds"),
) -> dict[str, Any]:
    rec = _get_run_or_404(run_id)
    if is_pilote_run(rec.catalog_version, rec.payload):
        raise HTTPException(status_code=404, detail="pilote run excluded from dashboard")

    filter_ids: list[str] | None = None
    if lens == "cyber":
        if not user.roles.intersection(ROLE_CYBER | ROLE_COMPLIANCE):
            raise HTTPException(status_code=403, detail="Cyber lens not permitted")
        filter_ids = CYBER_REQS
    elif lens == "ds":
        if not user.roles.intersection(ROLE_DS | ROLE_COMPLIANCE):
            raise HTTPException(status_code=403, detail="DS lens not permitted")
        filter_ids = DS_REQS
    elif lens == "compliance":
        if not user.roles.intersection(ROLE_COMPLIANCE):
            raise HTTPException(status_code=403, detail="Compliance lens not permitted")

    summary = _run_summary_dict(rec, filter_ids=filter_ids)
    if user.roles == frozenset({"executive"}):
        summary.pop("harness_provenance", None)
        for req in summary.get("requirements", []):
            req.pop("contributing_benchmarks", None)
            req.pop("fallback_benchmarks", None)
    return summary


@router.get("/runs/{run_id}/benchmark-run")
def get_benchmark_run(
    run_id: str,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    rec = _get_run_or_404(run_id)
    if rec.benchmark_run_yaml:
        doc = yaml.safe_load(rec.benchmark_run_yaml)
        return {"run_id": run_id, "document": doc}
    body = download_bytes(f"runs/{run_id}/benchmark_run.yaml")
    if not body:
        raise HTTPException(status_code=404, detail="benchmark_run.yaml not found")
    return {"run_id": run_id, "document": yaml.safe_load(body.decode("utf-8"))}


@router.get("/runs/{run_id}/provenance")
def get_provenance(
    run_id: str,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    rec = _get_run_or_404(run_id)
    return {"run_id": run_id, "provenance": rec.harness_provenance or []}


@router.get("/runs/{run_id}/raw-outputs")
def get_raw_outputs(
    run_id: str,
    _user: Annotated[AuthUser, Depends(require_roles(*ROLE_INSPECTOR, *ROLE_DS, *ROLE_CYBER))],
    benchmark: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    rec = _get_run_or_404(run_id)
    rows = _raw_outputs(rec)
    if benchmark:
        rows = [r for r in rows if str(r.get("benchmark_id")) == benchmark]
    total = len(rows)
    start = (page - 1) * limit
    page_rows = rows[start : start + limit]
    return {"run_id": run_id, "total": total, "page": page, "limit": limit, "rows": page_rows}


def _parse_qa(doc: dict[str, Any] | None) -> dict[str, Any]:
    if not doc:
        return {"valid": False, "errors": ["empty document"], "warnings": []}
    errors: list[str] = []
    warnings: list[str] = []
    for field in ("run_id", "model", "lifecycle_stage", "metrics", "governance"):
        if field not in doc:
            errors.append(f"missing field: {field}")
    if doc.get("governance", {}).get("catalog_version") in (None, "", "pilote_v1"):
        warnings.append("catalog_version missing or pilote")
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


@router.get("/runs/{run_id}/inspector")
def run_inspector(
    run_id: str,
    _user: Annotated[AuthUser, Depends(require_roles(*ROLE_INSPECTOR))],
) -> dict[str, Any]:
    rec = _get_run_or_404(run_id)
    settings = get_settings()
    prefix = f"runs/{run_id}"
    br_doc: dict[str, Any] | None = None
    if rec.benchmark_run_yaml:
        br_doc = yaml.safe_load(rec.benchmark_run_yaml)
    else:
        body = download_bytes(f"{prefix}/benchmark_run.yaml")
        if body:
            br_doc = yaml.safe_load(body.decode("utf-8"))

    artifacts = []
    for name, fname in ARTIFACT_KEYS.items():
        key = f"{prefix}/{fname}"
        artifacts.append(
            {
                "name": name,
                "key": key,
                "uri": f"s3://{settings.minio_bucket}/{key}",
                "presigned_url": presign_get(key),
            }
        )

    return {
        "run_id": run_id,
        "status": rec.status,
        "stages": rec.stages,
        "parse_qa": _parse_qa(br_doc),
        "git_sha": rec.git_sha,
        "catalog_version": rec.catalog_version,
        "signature": rec.signature,
        "cosign_status": "placeholder",
        "harness_provenance": rec.harness_provenance or [],
        "artifacts": artifacts,
        "mlflow_run_id": rec.mlflow_run_id,
    }


@router.get("/artifacts/{run_id}/presign")
def presign_artifact(
    run_id: str,
    _user: Annotated[AuthUser, Depends(get_current_user)],
    artifact: str = Query(..., description="benchmark_run|model_card|raw_outputs"),
) -> dict[str, Any]:
    fname = ARTIFACT_KEYS.get(artifact)
    if not fname:
        raise HTTPException(status_code=400, detail="unknown artifact type")
    _get_run_or_404(run_id)
    key = f"runs/{run_id}/{fname}"
    url = presign_get(key)
    if not url:
        raise HTTPException(status_code=404, detail="artifact not found")
    return {"run_id": run_id, "artifact": artifact, "url": url}


@router.get("/health/stack")
def health_stack() -> dict[str, Any]:
    settings = get_settings()
    checks: dict[str, Any] = {}

    try:
        import redis as redis_lib

        r = redis_lib.from_url(settings.redis_url)
        r.ping()
        checks["redis"] = {"ok": True}
    except Exception as e:
        checks["redis"] = {"ok": False, "error": str(e)[:200]}

    try:
        from raip.artifacts.s3io import ensure_bucket

        ensure_bucket(settings)
        checks["minio"] = {"ok": True, "endpoint": settings.minio_endpoint_url}
    except Exception as e:
        checks["minio"] = {"ok": False, "error": str(e)[:200]}

    try:
        resp = httpx.get(f"{settings.mlflow_tracking_uri.rstrip('/')}/health", timeout=3.0)
        checks["mlflow"] = {"ok": resp.status_code == 200, "uri": settings.mlflow_tracking_uri}
    except Exception as e:
        checks["mlflow"] = {"ok": False, "error": str(e)[:200]}

    try:
        resp = httpx.get(f"{settings.ollama_api_base.rstrip('/')}/api/tags", timeout=3.0)
        tags = resp.json().get("models", []) if resp.status_code == 200 else []
        checks["ollama"] = {
            "ok": resp.status_code == 200,
            "base": settings.ollama_api_base,
            "model_count": len(tags),
            "target_model": settings.raip_target_model,
        }
    except Exception as e:
        checks["ollama"] = {"ok": False, "error": str(e)[:200]}

    all_ok = all(c.get("ok") for c in checks.values())
    return {"ok": all_ok, "checks": checks}


@router.get("/series")
def series_stub(
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    return {
        "available": False,
        "reason": "no_timescale_data",
        "series": [],
    }


@router.get("/hitl/tasks")
def hitl_tasks(
    _user: Annotated[AuthUser, Depends(get_current_user)],
    run_id: str | None = None,
) -> dict[str, Any]:
    return {"tasks": [], "run_id": run_id}
