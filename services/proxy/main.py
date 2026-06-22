"""Inline governance proxy — OpenAI-compatible FastAPI service (MVP4 gaas).

Run: ``uvicorn services.proxy.main:app --host 0.0.0.0 --port 8000`` (port 8100 on the host).
The route is a sync def so FastAPI runs it in a threadpool — the synchronous LiteLLM forward does
not block the event loop, and the off-band agent scoring happens in the gov-worker.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from raip.config import get_settings
from raip.governance.bus import get_bus
from raip.governance.kill_switch import kill_switch_status
from raip.governance.modes import all_modes
from raip.governance.proxy import govern

app = FastAPI(title="RAIP Governance Proxy", version="0.4.0")


@app.get("/health")
def health() -> dict[str, Any]:
    s = get_settings()
    killed, reason = kill_switch_status(s)
    return {
        "ok": True,
        "service": "proxy",
        "bus": get_bus(s).backend,
        "target": s.proxy_target,
        "kill_switch": {"engaged": killed, "reason": reason},
        "modes": all_modes(s),
    }


@app.post("/v1/chat/completions")
def chat_completions(body: dict[str, Any]) -> JSONResponse:
    status, payload = govern(body)
    return JSONResponse(status_code=status, content=payload)
