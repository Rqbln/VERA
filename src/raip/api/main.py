from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from raip.api.benchmark_registry import MVP2_BENCHMARK_REGISTRY
from raip.config import get_settings
from raip.schemas.run_payload import RunCreateRequest
from raip.store.redis_run import RedisRunStore
from raip.api.lab_routes import router as lab_router
from raip.tasks.eval import run_benchmark_job

BENCHMARK_REGISTRY: list[dict[str, Any]] = list(MVP2_BENCHMARK_REGISTRY)

app = FastAPI(title="RAIP MVP2 API", version="0.2.0")
app.include_router(lab_router)


class ModelDeclare(BaseModel):
    model_id: str
    provider: str = "ollama"
    notes: str = ""


_models_store: list[dict[str, Any]] = []


@app.post("/api/v1/runs")
def create_run(body: RunCreateRequest) -> dict[str, Any]:
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
    return {"benchmarks": BENCHMARK_REGISTRY}


@app.post("/api/v1/models")
def declare_model(body: ModelDeclare) -> dict[str, Any]:
    _models_store.append(body.model_dump())
    return {"ok": True, "registered": body.model_id}


@app.get("/api/v1/models")
def list_models() -> dict[str, Any]:
    return {"models": list(_models_store)}


@app.delete("/api/v1/runs/{run_id}")
def delete_run(run_id: str) -> dict[str, Any]:
    store = RedisRunStore()
    rec = store.get(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    store.delete(run_id)
    return {"run_id": run_id, "deleted": True}
