from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vera.api.main import app
from vera.store.redis_run import RedisRunStore


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_DISABLED", "1")
    return TestClient(app)


@pytest.fixture
def sample_run(monkeypatch):
    store = RedisRunStore()
    run_id = "test-run-001"
    store.create(run_id, "ollama/llama3.1:8b", {"complai_requirements": ["R01", "R06"]})
    store.update(
        run_id,
        status="completed",
        catalog_version="mvp2-v1",
        lifecycle_stage="inference",
        complai_scores={
            "R01": {
                "score": 0.85,
                "score_ci_lower": 0.8,
                "score_ci_upper": 0.9,
                "bootstrap_n": 100,
                "contributing_benchmarks": ["mmlu_robust"],
            },
            "R06": {
                "score": 0.72,
                "score_ci_lower": 0.65,
                "score_ci_upper": 0.79,
                "bootstrap_n": 100,
                "contributing_benchmarks": ["mmlu"],
            },
        },
        harness_provenance=[
            {"benchmark_id": "mmlu", "harness": "lm_eval", "agent": "lm_eval", "fallback": "no"}
        ],
        stages=[
            {"name": "queued", "status": "completed", "ts": "2026-01-01T00:00:00Z"},
            {"name": "completed", "status": "completed", "ts": "2026-01-01T00:05:00Z"},
        ],
        git_sha="abc123",
        signature={"digest": "sha256:deadbeef"},
    )
    yield run_id
    store.delete(run_id)


def test_health_stack(client):
    resp = client.get("/api/v1/health/stack")
    assert resp.status_code == 200
    assert "checks" in resp.json()


def test_list_runs_excludes_pilote(client, monkeypatch):
    store = RedisRunStore()
    store.create("pilote-run", "m", {})
    store.update("pilote-run", catalog_version="pilote_v1")
    try:
        resp = client.get("/api/v1/runs")
        assert resp.status_code == 200
        ids = [r["run_id"] for r in resp.json()["runs"]]
        assert "pilote-run" not in ids
    finally:
        store.delete("pilote-run")


def test_run_summary(client, sample_run):
    resp = client.get(f"/api/v1/runs/{sample_run}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == sample_run
    assert len(body["requirements"]) >= 2
    assert "triage_counts" in body


def test_series_requires_requirement(client):
    # /series now derives a real series from Redis runs and needs a requirement id.
    assert client.get("/api/v1/series").status_code == 422
    resp = client.get("/api/v1/series?requirement=R02")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "redis_runs"
    # available is gated on >=2 points (the "no false time-series" rule).
    assert isinstance(body["available"], bool)
    assert body["available"] == (len(body["series"]) >= 2)
