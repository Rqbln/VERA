from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vera.api.main import app
from vera.store.redis_run import RedisRunStore

MODEL = "ollama/series-test-model"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_MODE", "guided")
    return TestClient(app)


@pytest.fixture
def two_runs():
    s = RedisRunStore()
    ids = ["series-run-1", "series-run-2"]
    for rid, score in zip(ids, (0.6, 0.8)):
        s.create(rid, MODEL, {})
        s.update(
            rid,
            status="completed",
            catalog_version="mvp2-v1",
            complai_scores={"R02": {"score": score, "score_ci_lower": 0.5, "score_ci_upper": 0.9}},
        )
    yield ids
    for rid in ids:
        s.delete(rid)


def test_series_requires_requirement(client):
    assert client.get("/api/v1/series").status_code == 422


def test_series_derives_from_redis_runs(client, two_runs):
    body = client.get(f"/api/v1/series?requirement=R02&model_id={MODEL}").json()
    assert body["source"] == "redis_runs"
    assert body["available"] is True
    assert [round(p["value"], 1) for p in body["series"]] == [0.6, 0.8]  # chronological


def test_series_single_run_not_available(client):
    s = RedisRunStore()
    s.create("series-solo", "ollama/solo", {})
    s.update("series-solo", status="completed", catalog_version="mvp2-v1",
             complai_scores={"R02": {"score": 0.7}})
    try:
        body = client.get("/api/v1/series?requirement=R02&model_id=ollama/solo").json()
        assert body["available"] is False
    finally:
        s.delete("series-solo")
