from __future__ import annotations

from fastapi.testclient import TestClient

from vera.api.auth import AuthUser, auth_disabled, require_roles


def test_auth_disabled_by_env(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_DISABLED", "1")
    assert auth_disabled() is True


def test_require_roles_allows_when_disabled(monkeypatch):
    import asyncio

    monkeypatch.setenv("VERA_AUTH_DISABLED", "1")
    dep = require_roles("legal_compliance")
    user = AuthUser(sub="x", roles=frozenset(), raw={})
    result = asyncio.run(dep(user=user))
    assert result.sub == "x"


def test_guided_mode_is_default(monkeypatch):
    # With nothing set, the platform ships in guided no-login mode.
    monkeypatch.delenv("VERA_AUTH_MODE", raising=False)
    monkeypatch.delenv("VERA_AUTH_DISABLED", raising=False)
    assert auth_disabled() is True


def test_dashboard_endpoints_require_auth_when_enabled(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_MODE", "enterprise")
    monkeypatch.delenv("VERA_AUTH_DISABLED", raising=False)
    from vera.api.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/runs")
    assert resp.status_code == 401
