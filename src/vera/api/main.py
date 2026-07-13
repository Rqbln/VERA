from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from vera.api.admin_routes import router as admin_router
from vera.api.benchmark_registry import list_benchmark_entries
from vera.api.dashboard_routes import router as dashboard_router
from vera.api.forms_routes import router as forms_router
from vera.api.lab_routes import router as lab_router
from vera.api.models_routes import router as models_router
from vera.config import get_settings
from vera.governance.kill_switch import kill_switch_status
from vera.schemas.run_payload import RunCreateRequest
from vera.store.redis_run import RedisRunStore
from vera.tasks.eval import run_benchmark_job

app = FastAPI(title="VERA API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(lab_router)
app.include_router(dashboard_router)
app.include_router(models_router)
app.include_router(forms_router)
app.include_router(admin_router)


@app.post("/api/v1/runs")
def create_run(body: RunCreateRequest) -> dict[str, Any]:
    killed, reason = kill_switch_status()
    if killed:
        raise HTTPException(status_code=503, detail=f"kill-switch engaged: {reason}")
    run_id = str(uuid4())
    store = RedisRunStore()
    store.create(run_id, body.model_id, body.model_dump())
    run_benchmark_job.delay(run_id, body.model_dump())
    return {"run_id": run_id, "status": "queued"}


@app.get("/api/v1/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    store = RedisRunStore()
    rec = store.get(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "run_id": rec.run_id,
        "status": rec.status,
        "model_id": rec.model_id,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
        "error": rec.error,
        "mlflow_run_id": rec.mlflow_run_id,
        "aggregate_scores": rec.aggregate_scores,
        "complai_scores": rec.complai_scores,
        "payload": rec.payload,
    }


@app.get("/api/v1/runs/{run_id}/card")
def get_run_card(run_id: str) -> dict[str, str]:
    store = RedisRunStore()
    rec = store.get(run_id)
    if not rec or not rec.card_markdown:
        raise HTTPException(status_code=404, detail="model card not available yet")
    return {"run_id": run_id, "markdown": rec.card_markdown}


@app.get("/api/v1/runs/{run_id}/artifacts")
def get_run_artifacts(run_id: str) -> dict[str, Any]:
    store = RedisRunStore()
    if not store.get(run_id):
        raise HTTPException(status_code=404, detail="run not found")
    s = get_settings()
    prefix = f"runs/{run_id}/"
    keys: list[str] = []
    try:
        import boto3

        c = boto3.client(
            "s3",
            endpoint_url=s.minio_endpoint_url,
            aws_access_key_id=s.minio_access_key,
            aws_secret_access_key=s.minio_secret_key,
            region_name=s.minio_region,
        )
        paginator = c.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=s.minio_bucket, Prefix=prefix):
            for obj in page.get("Contents") or []:
                keys.append(obj["Key"])
    except Exception:
        keys = [
            f"{prefix}raw_outputs.jsonl",
            f"{prefix}benchmark_run.yaml",
            f"{prefix}model_card.md",
        ]
    base = f"s3://{s.minio_bucket}/{prefix}"
    return {"run_id": run_id, "uris": [f"s3://{s.minio_bucket}/{k}" for k in keys], "prefix": base}


@app.get("/api/v1/benchmarks")
def list_benchmarks() -> dict[str, Any]:
    return {"benchmarks": list_benchmark_entries()}


@app.delete("/api/v1/runs/{run_id}")
def delete_run(run_id: str) -> dict[str, Any]:
    store = RedisRunStore()
    rec = store.get(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    store.delete(run_id)
    return {"run_id": run_id, "deleted": True}
