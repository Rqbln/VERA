from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from raip.api.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RAIP_AUTH_MODE", "guided")
    return TestClient(app)


class _FakeResp:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "models": [
                {"name": "llama3.1:8b-instruct-q8_0", "size": 1},
                {"name": "phi3:mini", "size": 2},
            ]
        }


def test_connected_models_maps_to_litellm_ids(client, monkeypatch):
    monkeypatch.setattr("raip.api.models_routes.httpx.get", lambda *a, **k: _FakeResp())
    body = client.get("/api/v1/models/connected").json()
    ids = [m["model_id"] for m in body["models"]]
    assert "ollama/llama3.1:8b-instruct-q8_0" in ids
    assert all(m["model_id"].startswith("ollama/") for m in body["models"])
    # The configured target model is flagged recommended and sorted first.
    assert body["models"][0]["recommended"] is True


def test_connected_models_empty_state_on_error(client, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("ollama down")

    monkeypatch.setattr("raip.api.models_routes.httpx.get", _boom)
    body = client.get("/api/v1/models/connected").json()
    assert body["models"] == []
    assert "error" in body


def test_declare_list_delete_round_trip(client):
    r = client.post("/api/v1/models", json={"model_id": "ollama/test-model", "notes": "x"})
    assert r.status_code == 200
    listed = client.get("/api/v1/models").json()["models"]
    assert any(m["model_id"] == "ollama/test-model" for m in listed)
    assert client.delete("/api/v1/models/ollama/test-model").status_code == 200
