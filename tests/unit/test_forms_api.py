from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vera.api.main import app
from vera.store.redis_run import RedisRunStore


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_MODE", "guided")
    return TestClient(app)


@pytest.fixture
def run_id():
    s = RedisRunStore()
    rid = "forms-run-001"
    s.create(rid, "ollama/phi3:mini", {})
    yield rid
    s.delete(rid)


def test_put_and_get_form(client, run_id):
    r = client.put(
        f"/api/v1/runs/{run_id}/forms/N03",
        json={"fields": {"kwh": "12", "co2eq_kg": "3"}, "completed": True},
    )
    assert r.status_code == 200
    forms = client.get(f"/api/v1/runs/{run_id}/forms").json()["forms"]
    assert forms["N03"]["completed"] is True
    assert forms["N03"]["fields"]["kwh"] == "12"


def test_invalid_form_id_rejected(client, run_id):
    assert client.put(f"/api/v1/runs/{run_id}/forms/N99", json={"fields": {}}).status_code == 400


def test_forms_require_auth_in_enterprise(monkeypatch, run_id):
    monkeypatch.setenv("VERA_AUTH_MODE", "enterprise")
    monkeypatch.delenv("VERA_AUTH_DISABLED", raising=False)
    client = TestClient(app)
    # No token -> 401 on the compliance-gated PUT.
    assert client.put(f"/api/v1/runs/{run_id}/forms/N03", json={"fields": {}}).status_code == 401
