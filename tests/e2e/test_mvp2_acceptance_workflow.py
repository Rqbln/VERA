"""End-to-end MVP2 (API → Celery eager → LangGraph → Ollama → MLflow → MinIO)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import boto3
import mlflow
import pytest
import yaml
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.api import main as api_main  # noqa: E402
from raip.config import get_settings  # noqa: E402
from raip.store.redis_run import RedisRunStore  # noqa: E402

REQ_SHORT = ("R01", "R02", "R06", "R08", "R10", "R11", "R12")


@pytest.mark.e2e
@pytest.mark.ollama
def test_mvp2_acceptance_workflow(e2e_stack: None) -> None:  # noqa: ARG001
    os.environ.setdefault("RAIP_BOOTSTRAP_N", "200")

    example = PROJECT_ROOT / "examples" / "mvp2_ollama_e2e.yaml"
    body = yaml.safe_load(example.read_text(encoding="utf-8"))

    client = TestClient(api_main.app)
    r = client.post("/api/v1/runs", json=body)
    assert r.status_code == 200, r.text
    run_id = r.json()["run_id"]

    deadline = time.time() + float(os.environ.get("RAIP_E2E_TIMEOUT_SEC", "900"))
    store = RedisRunStore()
    status = "queued"
    while time.time() < deadline:
        rec = store.get(run_id)
        assert rec is not None
        status = rec.status
        if status in ("completed", "failed"):
            break
        time.sleep(2.0)

    assert status == "completed", store.get(run_id)

    rec_final = store.get(run_id)
    assert rec_final is not None
    assert rec_final.aggregate_scores is not None
    for k in REQ_SHORT:
        assert k in rec_final.aggregate_scores, rec_final.aggregate_scores

    assert rec_final.benchmark_run_yaml
    doc = yaml.safe_load(rec_final.benchmark_run_yaml)
    assert doc["reproducibility"]["catalog_version"] == "mvp2-v1"
    by_req = {m["requirement"]: m for m in doc.get("metrics") or []}
    for short in REQ_SHORT:
        long_id = {
            "R01": "R01_robustness_predictability",
            "R02": "R02_cyber_resilience",
            "R06": "R06_capabilities",
            "R08": "R08_ai_disclosure",
            "R10": "R10_representation_bias",
            "R11": "R11_fairness_non_discrimination",
            "R12": "R12_harmful_content_toxicity",
        }[short]
        assert long_id in by_req, (short, by_req.keys())

    s = get_settings()
    mlflow.set_tracking_uri(s.mlflow_tracking_uri)
    exp = mlflow.get_experiment_by_name(s.mlflow_experiment)
    assert exp is not None
    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        max_results=25,
        order_by=["start_time DESC"],
    )
    matched = [x for x in runs if x.info.run_name == run_id]
    assert matched, "MLflow run not found for run_id"

    c = boto3.client(
        "s3",
        endpoint_url=s.minio_endpoint_url,
        aws_access_key_id=s.minio_access_key,
        aws_secret_access_key=s.minio_secret_key,
        region_name=s.minio_region,
    )
    prefix = f"runs/{run_id}/"
    raw = c.get_object(Bucket=s.minio_bucket, Key=f"{prefix}raw_outputs.jsonl")
    raw_text = raw["Body"].read().decode("utf-8")
    assert "hf_dynamic" in raw_text or "lm_eval" in raw_text or "garak" in raw_text
    assert "pilote_v1" not in raw_text
    for key in ("raw_outputs.jsonl", "model_card.md", "benchmark_run.yaml"):
        c.head_object(Bucket=s.minio_bucket, Key=f"{prefix}{key}")
