from __future__ import annotations

import json
from typing import Annotated, Any

import httpx
import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

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
    is_pilote_catalog,
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
        "trust_factor": rec.trust_factor,
    }


def _run_overview_extra(rec: RunRecord) -> dict[str, Any]:
    """Lightweight per-run triage counts + headline score from data already in Redis."""
    if rec.status != "completed" or not rec.complai_scores:
        return {"triage_counts": None, "headline_score": None}
    rows = build_requirement_rows(
        run_status=rec.status,
        requested=_requested_requirements(rec),
        complai_scores=rec.complai_scores or {},
        provenance=rec.harness_provenance or [],
        raw_outputs=rec.raw_outputs_summary or [],
    )
    triage_counts = {
        t: sum(1 for r in rows if r["triage"] == t)
        for t in ("failed", "fallback", "uncovered", "ok", "na")
    }
    scored = [r["score"] for r in rows if isinstance(r.get("score"), (int, float))]
    headline = round(sum(scored) / len(scored), 4) if scored else None
    return {
        "triage_counts": triage_counts,
        "headline_score": headline,
        "trust_factor": rec.trust_factor,
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
    include_triage: bool = False,
) -> dict[str, Any]:
    page, total = _store().list_runs(
        limit=limit,
        offset=offset,
        model_id=model_id,
        lifecycle=lifecycle,
        status=status,
        exclude_pilote=exclude_pilote,
    )
    runs: list[dict[str, Any]] = []
    for r in page:
        item: dict[str, Any] = {
            "run_id": r.run_id,
            "status": r.status,
            "model_id": r.model_id,
            "lifecycle_stage": r.lifecycle_stage,
            "catalog_version": r.catalog_version,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        if include_triage:
            item.update(_run_overview_extra(r))
        runs.append(item)
    return {"runs": runs, "total": total, "limit": limit, "offset": offset}


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
    cv = doc.get("governance", {}).get("catalog_version")
    if cv in (None, "") or is_pilote_catalog(cv):
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
    """Tri-state stack health.

    ``redis`` and ``ollama`` are *required* (a red light means the platform cannot run).
    ``minio`` and ``mlflow`` are *optional*: in lite mode they may be absent and the platform
    degrades gracefully (amber), it does not fail.
    """
    settings = get_settings()
    checks: dict[str, Any] = {}

    try:
        import redis as redis_lib

        r = redis_lib.from_url(settings.redis_url)
        r.ping()
        checks["redis"] = {"ok": True, "required": True}
    except Exception as e:
        checks["redis"] = {"ok": False, "required": True, "error": str(e)[:200]}

    # MinIO is optional: when the active artifact backend is the local filesystem, report it as a
    # healthy lite-mode configuration rather than a failure.
    try:
        from raip.artifacts.s3io import artifact_backend, ensure_bucket

        if artifact_backend(settings) == "local":
            checks["minio"] = {
                "ok": True,
                "required": False,
                "backend": "local",
                "dir": settings.raip_local_artifacts_dir,
            }
        else:
            ensure_bucket(settings)
            checks["minio"] = {
                "ok": True,
                "required": False,
                "backend": "minio",
                "endpoint": settings.minio_endpoint_url,
            }
    except Exception as e:
        checks["minio"] = {"ok": False, "required": False, "error": str(e)[:200]}

    if not settings.mlflow_enabled:
        checks["mlflow"] = {"ok": True, "required": False, "status": "disabled"}
    else:
        try:
            resp = httpx.get(f"{settings.mlflow_tracking_uri.rstrip('/')}/health", timeout=3.0)
            checks["mlflow"] = {
                "ok": resp.status_code == 200,
                "required": False,
                "uri": settings.mlflow_tracking_uri,
            }
        except Exception as e:
            checks["mlflow"] = {"ok": False, "required": False, "error": str(e)[:200]}

    try:
        resp = httpx.get(f"{settings.ollama_api_base.rstrip('/')}/api/tags", timeout=3.0)
        tags = resp.json().get("models", []) if resp.status_code == 200 else []
        checks["ollama"] = {
            "ok": resp.status_code == 200,
            "required": True,
            "base": settings.ollama_api_base,
            "model_count": len(tags),
            "target_model": settings.raip_target_model,
        }
    except Exception as e:
        checks["ollama"] = {"ok": False, "required": True, "error": str(e)[:200]}

    required_ok = all(c.get("ok") for c in checks.values() if c.get("required"))
    degraded = required_ok and not all(c.get("ok") for c in checks.values())
    return {"ok": required_ok, "degraded": degraded, "checks": checks}


@router.get("/artifacts/local/{key:path}")
def get_local_artifact(key: str):
    """Serve a locally-stored artifact (lite mode). Public, like a MinIO presigned URL."""
    import mimetypes

    from fastapi.responses import FileResponse

    from raip.artifacts.local_fs import safe_path

    settings = get_settings()
    try:
        target = safe_path(settings, key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="invalid artifact key") from e
    if not target.is_file():
        raise HTTPException(status_code=404, detail="artifact not found")
    media_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    return FileResponse(str(target), media_type=media_type)


@router.get("/series")
def series(
    _user: Annotated[AuthUser, Depends(get_current_user)],
    requirement: str = Query(..., description="requirement id, e.g. R02"),
    model_id: str | None = None,
) -> dict[str, Any]:
    """Longitudinal score series for a requirement, derived from historical Redis runs.

    No TimescaleDB needed: each completed run of the model contributes one point. The dashboard
    only draws a trend line once there are >=2 points, preserving the "no false time-series" rule.
    """
    page, _ = _store().list_runs(limit=200, model_id=model_id, status="completed")
    points: list[dict[str, Any]] = []
    for rec in reversed(page):  # list_runs is newest-first; we want chronological order
        row = (rec.complai_scores or {}).get(requirement)
        if not isinstance(row, dict):
            continue
        score = row.get("score")
        if score is None:
            continue
        points.append(
            {
                "ts": rec.created_at,
                "value": round(float(score), 4),
                "run_id": rec.run_id,
                "model_id": rec.model_id,
            }
        )
    return {
        "available": len(points) >= 2,
        "source": "redis_runs",
        "requirement": requirement,
        "series": points,
    }


@router.get("/monitor/drift")
def monitor_drift(
    _user: Annotated[AuthUser, Depends(get_current_user)],
    model_id: str = Query(..., description="model to evaluate drift for"),
) -> dict[str, Any]:
    from raip.tasks.monitor import compute_drift

    return compute_drift(model_id)


class KillSwitchBody(BaseModel):
    engaged: bool
    reason: str = ""


@router.get("/governance/kill-switch")
def get_kill_switch(_user: Annotated[AuthUser, Depends(get_current_user)]) -> dict[str, Any]:
    from raip.governance.kill_switch import kill_switch_status

    engaged, reason = kill_switch_status()
    return {"engaged": engaged, "reason": reason}


@router.post("/governance/kill-switch")
def set_kill_switch(
    body: KillSwitchBody,
    _user: Annotated[AuthUser, Depends(require_roles(*ROLE_COMPLIANCE))],
) -> dict[str, Any]:
    from raip.governance.kill_switch import set_kill

    engaged, reason = set_kill(body.engaged, body.reason)
    return {"engaged": engaged, "reason": reason}


@router.get("/hitl/tasks")
def hitl_tasks(
    _user: Annotated[AuthUser, Depends(get_current_user)],
    run_id: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    from raip.store.redis_hitl import RedisHitlStore

    tasks = RedisHitlStore().list(run_id=run_id, status=status)
    return {"tasks": [t.to_dict() for t in tasks], "run_id": run_id}


class HitlCreateBody(BaseModel):
    run_id: str
    requirement: str = "N01"
    prompt: str = ""
    sample_ref: str = ""


class HitlReviewBody(BaseModel):
    likert_score: int
    comment: str = ""
    reviewer: str = "guided-reviewer"


@router.post("/hitl/tasks")
def create_hitl_task(
    body: HitlCreateBody,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    from raip.store.redis_hitl import RedisHitlStore

    if body.requirement not in ("N01", "N02"):
        raise HTTPException(status_code=400, detail="requirement must be N01 or N02")
    task = RedisHitlStore().create(
        run_id=body.run_id,
        requirement=body.requirement,
        prompt=body.prompt,
        sample_ref=body.sample_ref,
    )
    return {"task": task.to_dict()}


@router.post("/hitl/tasks/{task_id}/review")
def review_hitl_task(
    task_id: str,
    body: HitlReviewBody,
    _user: Annotated[AuthUser, Depends(require_roles(*ROLE_COMPLIANCE, "domain_expert"))],
) -> dict[str, Any]:
    from raip.store.redis_hitl import RedisHitlStore

    if not 1 <= body.likert_score <= 5:
        raise HTTPException(status_code=400, detail="likert_score must be 1..5")
    task = RedisHitlStore().submit_review(
        task_id,
        reviewer=body.reviewer,
        likert_score=body.likert_score,
        comment=body.comment,
    )
    if not task:
        raise HTTPException(status_code=404, detail="hitl task not found")
    return {"task": task.to_dict()}
