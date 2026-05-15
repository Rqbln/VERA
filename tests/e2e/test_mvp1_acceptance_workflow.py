"""Bout-en-bout MVP1 (API → Celery eager → LangGraph → Ollama → MLflow → MinIO)."""

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

REQ_SHORT = ("R01", "R02", "R06", "R07", "R08", "R09", "R10", "R11", "R12")


@pytest.mark.e2e
@pytest.mark.ollama
def test_mvp1_acceptance_workflow(e2e_stack: None) -> None:  # noqa: ARG001
    os.environ.setdefault("RAIP_BOOTSTRAP_N", "200")

    example = PROJECT_ROOT / "examples" / "mvp1_pilote_e2e.yaml"
    body = yaml.safe_load(example.read_text(encoding="utf-8"))

    client = TestClient(api_main.app)
    r = client.post("/api/v1/runs", json=body)
    assert r.status_code == 200, r.text
    run_id = r.json()["run_id"]

    deadline = time.time() + float(os.environ.get("RAIP_E2E_TIMEOUT_SEC", "600"))
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

    card = client.get(f"/api/v1/runs/{run_id}/card")
    assert card.status_code == 200
    md = card.json()["markdown"]
    assert "Reproducibility" in md or "Reproductibilité" in md
    assert str(body["config"]["seed"]) in md

    assert rec_final.benchmark_run_yaml
    doc = yaml.safe_load(rec_final.benchmark_run_yaml)
    by_req = {m["requirement"]: m for m in doc.get("metrics") or []}
    for short in REQ_SHORT:
        long_id = {
            "R01": "R01_robustness_predictability",
            "R02": "R02_cyber_resilience",
            "R06": "R06_capabilities",
            "R07": "R07_interpretability_calibration",
            "R08": "R08_ai_disclosure",
            "R09": "R09_traceability_watermark",
            "R10": "R10_representation_bias",
            "R11": "R11_fairness_non_discrimination",
            "R12": "R12_harmful_content_toxicity",
        }[short]
        assert long_id in by_req, (short, by_req.keys())
        m = by_req[long_id]
        s = float(m["score"])
        lo = float(m["score_ci_lower"])
        hi = float(m["score_ci_upper"])
        assert 0.0 <= s <= 1.0
        assert 0.0 <= lo <= 1.0 and 0.0 <= hi <= 1.0
        assert lo <= hi
        assert "bootstrap_n" in m

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
    run = matched[0]
    for k in REQ_SHORT:
        assert f"complai_{k}" in run.data.metrics
        assert f"complai_{k}_ci_lo" in run.data.metrics

    c = boto3.client(
        "s3",
        endpoint_url=s.minio_endpoint_url,
        aws_access_key_id=s.minio_access_key,
        aws_secret_access_key=s.minio_secret_key,
        region_name=s.minio_region,
    )
    prefix = f"runs/{run_id}/"
    for key in ("raw_outputs.jsonl", "model_card.md", "benchmark_run.yaml"):
        c.head_object(Bucket=s.minio_bucket, Key=f"{prefix}{key}")
