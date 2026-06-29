from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vera.api.main import app
from vera.governance.audit import build_audit_event, persist_audit, recent_incidents
from vera.governance.kill_switch import set_kill


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_MODE", "guided")
    return TestClient(app)


def test_audit_event_is_signed_and_flags_incident():
    ev = build_audit_event(
        kind="policy_deny", model="m", payload={"x": 1}, decision="deny", trust_score=0.1
    )
    assert ev["signature"]["digest"].startswith("sha256:")
    assert ev["incident"] is True


def test_persist_and_read_incident(tmp_path, monkeypatch):
    monkeypatch.setenv("VERA_LOCAL_ARTIFACTS_DIR", str(tmp_path))
    from vera.config import get_settings

    get_settings.cache_clear()
    ev = build_audit_event(
        kind="low_trust", model="m", payload={}, decision="deny", trust_score=0.05
    )
    persist_audit(ev)
    incidents = recent_incidents(limit=10)
    assert any(i["event_id"] == ev["event_id"] for i in incidents)
    get_settings.cache_clear()


def test_admin_proxy_health(client):
    body = client.get("/admin/v1/proxy/health").json()
    assert "bus" in body and "kill_switch" in body


def test_admin_mode_and_kill_switch(client):
    r = client.post("/admin/v1/mode/ollama/x", json={"mode": "advisory"})
    assert r.json()["mode"] == "advisory"
    assert client.post("/admin/v1/mode/ollama/x", json={"mode": "bad"}).status_code == 400
    try:
        r = client.post("/admin/v1/kill-switch", json={"engaged": True, "reason": "t"})
        assert r.json()["engaged"] is True
        assert client.get("/admin/v1/kill-switch").json()["engaged"] is True
    finally:
        set_kill(False)


def test_admin_policy_returns_rego(client):
    body = client.get("/admin/v1/policy").json()
    assert "package vera.governance" in body["policy"]


def test_admin_requires_auth_in_enterprise(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_MODE", "enterprise")
    monkeypatch.delenv("VERA_AUTH_DISABLED", raising=False)
    c = TestClient(app)
    assert c.get("/admin/v1/proxy/health").status_code == 401
