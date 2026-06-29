"""Governance admin control plane (MVP4 gaas).

The operator surface for the governance runtime: read/set per-model mode, inspect live Trust Factor
+ agent signals, list incidents, manage the OPA policy, and drive the kill-switch. Gated to
compliance/risk roles in enterprise mode; open in guided mode (auth disabled).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from vera.api.auth import ROLE_COMPLIANCE, AuthUser, require_roles
from vera.config import get_settings
from vera.governance.audit import recent_incidents
from vera.governance.bus import get_bus
from vera.governance.kill_switch import kill_switch_status, set_kill
from vera.governance.modes import VALID_MODES, all_modes, get_mode, set_mode
from vera.governance.trust_stream import current_trust, latest_signals, trust_series

router = APIRouter(prefix="/admin/v1", tags=["governance-admin"])

_GovUser = Annotated[AuthUser, Depends(require_roles(*ROLE_COMPLIANCE))]
_REGO_PATH = Path(__file__).resolve().parents[3] / "infra" / "opa" / "vera.rego"


class ModeBody(BaseModel):
    mode: str


class KillBody(BaseModel):
    engaged: bool
    reason: str = ""


class PolicyBody(BaseModel):
    policy: str


@router.get("/proxy/health")
def proxy_health(_u: _GovUser) -> dict[str, Any]:
    s = get_settings()
    killed, reason = kill_switch_status(s)
    return {
        "gaas_enabled": s.vera_gaas_enabled,
        "bus": get_bus(s).backend,
        "opa": bool(s.opa_url),
        "opensearch": bool(s.opensearch_url),
        "proxy_target": s.proxy_target,
        "default_mode": s.vera_governance_mode,
        "kill_switch": {"engaged": killed, "reason": reason},
        "modes": all_modes(s),
    }


@router.get("/mode")
def list_modes(_u: _GovUser) -> dict[str, Any]:
    return {"default": get_settings().vera_governance_mode, "models": all_modes()}


@router.get("/mode/{model:path}")
def read_mode(model: str, _u: _GovUser) -> dict[str, Any]:
    return {"model": model, "mode": get_mode(model)}


@router.post("/mode/{model:path}")
def write_mode(model: str, body: ModeBody, _u: _GovUser) -> dict[str, Any]:
    if body.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"mode must be one of {VALID_MODES}")
    return {"model": model, "mode": set_mode(model, body.mode)}


@router.get("/trust/{model:path}")
def read_trust(model: str, _u: _GovUser) -> dict[str, Any]:
    return {
        "model": model,
        "current": current_trust(model),
        "signals": latest_signals(model),
        "series": trust_series(model, limit=100),
    }


@router.get("/incidents")
def list_incidents(_u: _GovUser, limit: int = 50) -> dict[str, Any]:
    return {"incidents": recent_incidents(limit=limit)}


@router.get("/kill-switch")
def get_kill(_u: _GovUser) -> dict[str, Any]:
    engaged, reason = kill_switch_status()
    return {"engaged": engaged, "reason": reason}


@router.post("/kill-switch")
def post_kill(body: KillBody, _u: _GovUser) -> dict[str, Any]:
    engaged, reason = set_kill(body.engaged, body.reason)
    return {"engaged": engaged, "reason": reason}


@router.get("/policy")
def get_policy(_u: _GovUser) -> dict[str, Any]:
    s = get_settings()
    rego = _REGO_PATH.read_text(encoding="utf-8") if _REGO_PATH.is_file() else ""
    return {"opa_url": s.opa_url or None, "policy": rego, "active": bool(s.opa_url)}


@router.put("/policy")
def put_policy(body: PolicyBody, _u: _GovUser) -> dict[str, Any]:
    """Push a Rego policy bundle to OPA (when configured)."""
    s = get_settings()
    if not s.opa_url:
        raise HTTPException(status_code=503, detail="OPA not configured")
    try:
        url = f"{s.opa_url.rstrip('/')}/v1/policies/vera"
        resp = httpx.put(
            url, content=body.policy, headers={"Content-Type": "text/plain"}, timeout=4.0
        )
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"OPA policy update failed: {e}") from e
    return {"ok": True}
