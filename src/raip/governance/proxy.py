"""Inline governance proxy core (MVP4 gaas).

Sits in front of the LLM. For each request it (1) reads the model's mode + kill-switch + live Trust
Factor, (2) asks the policy engine for a decision, (3) in *enforcement* mode blocks a deny, else
(4) forwards synchronously to the target and returns the response, then (5) publishes the
request/response to the event bus for the agents to score asynchronously, and audits the call. Only
the synchronous forward is on the latency path; scoring happens off-band.
"""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from raip.config import Settings, get_settings
from raip.governance.audit import build_audit_event, emit_audit
from raip.governance.bus import TOPIC_TRAFFIC, get_bus
from raip.governance.kill_switch import kill_switch_status
from raip.governance.modes import get_mode
from raip.governance.policy import evaluate_policy
from raip.governance.trust_stream import current_trust
from raip.llm.client import LLMClient


def _messages(body: dict[str, Any]) -> list[dict[str, str]]:
    """Resolve the request messages, synthesising one from the legacy ``prompt`` field."""
    return body.get("messages") or [{"role": "user", "content": str(body.get("prompt", ""))}]


def _forward(body: dict[str, Any], settings: Settings) -> tuple[str, dict[str, Any], float]:
    client = LLMClient(settings)
    model = str(body.get("model") or settings.raip_target_model)
    t0 = time.monotonic()
    res = client.completion(
        model=model,
        messages=_messages(body),
        temperature=float(body.get("temperature", 0.0)),
        max_tokens=int(body.get("max_tokens", 512)),
        api_base=settings.proxy_target,  # honour RAIP_PROXY_TARGET_URL
    )
    latency_ms = round((time.monotonic() - t0) * 1000, 1)
    return res.text, res.raw, latency_ms


def _openai_response(model: str, text: str, governance: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"raip-{uuid4().hex[:12]}",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "raip_governance": governance,
    }


def govern(body: dict[str, Any], settings: Settings | None = None) -> tuple[int, dict[str, Any]]:
    """Govern and (unless blocked) forward one chat-completion request. Returns (status, body)."""
    s = settings or get_settings()
    model = str(body.get("model") or s.raip_target_model)
    mode = get_mode(model, s)
    killed, kill_reason = kill_switch_status(s)
    tf = current_trust(model, s)
    trust_score = (float(tf["score"]) / 100.0) if tf else None

    decision = evaluate_policy(
        {"model": model, "mode": mode, "kill_switch": killed, "trust_score": trust_score},
        s,
    )
    governance = {
        "mode": mode,
        "decision": decision["decision"],
        "reasons": decision.get("reasons", []),
        "policy_source": decision.get("source"),
        "trust_score": trust_score,
    }

    if decision["decision"] == "deny" and mode == "enforcement":
        emit_audit(
            build_audit_event(
                kind="policy_deny",
                model=model,
                payload={"reasons": decision.get("reasons", []), "kill_reason": kill_reason},
                decision="deny",
                trust_score=trust_score,
            ),
            s,
        )
        return 503, {"error": "blocked by governance policy", "raip_governance": governance}

    text, raw, latency_ms = _forward(body, s)
    governance["latency_ms"] = latency_ms

    event = {
        "model": model,
        "mode": mode,
        "request": {"messages": _messages(body)},
        "response": {"text": text},
        "decision": decision["decision"],
        "latency_ms": latency_ms,
    }
    try:
        get_bus(s).publish(TOPIC_TRAFFIC, event, key=model)
    except Exception:
        pass  # never fail the request because the bus is down

    emit_audit(
        build_audit_event(
            kind="request",
            model=model,
            payload={"latency_ms": latency_ms, "reasons": decision.get("reasons", [])},
            decision=decision["decision"],
            trust_score=trust_score,
        ),
        s,
    )
    return 200, _openai_response(model, text, governance)
