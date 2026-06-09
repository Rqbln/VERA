"""FastAPI routes with real Redis (no store mock)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from raip.api import main as api_main
from raip.config import get_settings
from raip.store.redis_run import RedisRunStore

MVP2_MODEL = "ollama/llama3.1:8b-instruct-q8_0"


@pytest.mark.integration
def test_get_run_and_delete_with_real_redis(integration_stack: None) -> None:  # noqa: ARG001
    store = RedisRunStore()
    run_id = f"api-{uuid.uuid4().hex[:12]}"
    store.create(run_id, MVP2_MODEL, {"benchmarks": []})
    store.update(run_id, status="completed", aggregate_scores={"R08": 0.9})

    client = TestClient(api_main.app)
    r = client.get(f"/api/v1/runs/{run_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert r.json()["aggregate_scores"]["R08"] == 0.9

    d = client.delete(f"/api/v1/runs/{run_id}")
    assert d.status_code == 200
    assert store.get(run_id) is None


@pytest.mark.integration
def test_settings_default_model_matches_mvp2(integration_stack: None) -> None:  # noqa: ARG001
    s = get_settings()
    assert s.raip_target_model == MVP2_MODEL
    assert s.mlflow_experiment == "raip-mvp2"


@pytest.mark.integration
def test_list_benchmarks_mvp2_registry(integration_stack: None) -> None:  # noqa: ARG001
    client = TestClient(api_main.app)
    r = client.get("/api/v1/benchmarks")
    assert r.status_code == 200
    ids = {b["id"] for b in r.json()["benchmarks"]}
    assert "mmlu" in ids
    assert all(b.get("implementation") != "pilote_v1" for b in r.json()["benchmarks"])
