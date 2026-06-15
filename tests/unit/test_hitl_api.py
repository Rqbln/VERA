from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from raip.api.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RAIP_AUTH_MODE", "guided")
    return TestClient(app)


def test_hitl_create_list_review(client):
    created = client.post("/api/v1/hitl/tasks", json={"run_id": "hitl-run", "requirement": "N01"})
    assert created.status_code == 200
    task = created.json()["task"]
    assert task["requirement"] == "N01"
    assert task["status"] == "pending"

    listed = client.get("/api/v1/hitl/tasks?run_id=hitl-run").json()["tasks"]
    assert any(t["task_id"] == task["task_id"] for t in listed)

    reviewed = client.post(
        f"/api/v1/hitl/tasks/{task['task_id']}/review",
        json={"likert_score": 4, "comment": "clear"},
    ).json()["task"]
    assert reviewed["status"] == "done"
    assert reviewed["likert_score"] == 4


def test_hitl_rejects_invalid_requirement(client):
    resp = client.post("/api/v1/hitl/tasks", json={"run_id": "r", "requirement": "R01"})
    assert resp.status_code == 400


def test_hitl_rejects_out_of_range_likert(client):
    created = client.post("/api/v1/hitl/tasks", json={"run_id": "r2", "requirement": "N02"})
    task = created.json()["task"]
    resp = client.post(
        f"/api/v1/hitl/tasks/{task['task_id']}/review", json={"likert_score": 9}
    )
    assert resp.status_code == 400
