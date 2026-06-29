from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vera.api.main import app
from vera.governance.kill_switch import is_killed, kill_switch_status, set_kill


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_MODE", "guided")
    return TestClient(app)


def test_env_flag_engages(monkeypatch):
    monkeypatch.setenv("VERA_KILL_SWITCH", "1")
    engaged, _ = kill_switch_status()
    assert engaged is True


def test_redis_toggle_round_trip(monkeypatch):
    monkeypatch.delenv("VERA_KILL_SWITCH", raising=False)
    set_kill(False)
    assert is_killed() is False
    set_kill(True, "test reason")
    engaged, reason = kill_switch_status()
    assert engaged is True
    assert reason == "test reason"
    set_kill(False)
    assert is_killed() is False


def test_run_creation_blocked_when_engaged(client, monkeypatch):
    monkeypatch.delenv("VERA_KILL_SWITCH", raising=False)
    set_kill(True, "blocked")
    try:
        resp = client.post("/api/v1/runs", json={"model_id": "ollama/phi3:mini"})
        assert resp.status_code == 503
        assert "kill-switch" in resp.json()["detail"]
    finally:
        set_kill(False)
