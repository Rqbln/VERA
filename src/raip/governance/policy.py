"""Governance policy decisions (MVP4 gaas).

The proxy and admin plane ask "should this request be allowed, flagged, or denied?". When an Open
Policy Agent (OPA) sidecar is configured we delegate to it (auditable Rego, versioned out-of-band);
otherwise we fall back to an equivalent built-in rule so the pipeline still makes correct decisions
with zero extra infrastructure. Both return the same contract.

Decision contract:
    input  = {model, mode, kill_switch, trust_score (0-1|null), signals: {cr: score}}
    output = {decision: "allow"|"flag"|"deny", reasons: [str], source: "opa"|"builtin"}
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from raip.config import Settings, get_settings


def _thresholds() -> tuple[float, float]:
    block = float(os.environ.get("RAIP_POLICY_BLOCK_BELOW", "0.30"))
    warn = float(os.environ.get("RAIP_POLICY_WARN_BELOW", "0.60"))
    return block, warn


def builtin_decision(inp: dict[str, Any]) -> dict[str, Any]:
    """Reference policy, mirrored in infra/opa/raip.rego."""
    mode = inp.get("mode", "shadow")
    kill = bool(inp.get("kill_switch"))
    trust = inp.get("trust_score")
    block_below, warn_below = _thresholds()
    reasons: list[str] = []
    decision = "allow"

    if kill:
        reasons.append("kill-switch engaged")
        decision = "deny" if mode == "enforcement" else "flag"
    if isinstance(trust, (int, float)):
        if trust < block_below:
            reasons.append(f"trust {trust:.2f} < block {block_below:.2f}")
            if mode == "enforcement":
                decision = "deny"
            elif decision != "deny":
                decision = "flag"
        elif trust < warn_below:
            reasons.append(f"trust {trust:.2f} < warn {warn_below:.2f}")
            if decision == "allow":
                decision = "flag"

    # shadow mode never blocks, only observes.
    if mode == "shadow" and decision == "deny":
        decision = "flag"
        reasons.append("shadow mode: not enforced")
    return {"decision": decision, "reasons": reasons, "source": "builtin"}


def evaluate_policy(inp: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    s = settings or get_settings()
    if s.opa_url:
        try:
            url = f"{s.opa_url.rstrip('/')}/v1/data/raip/governance/decision"
            resp = httpx.post(url, json={"input": inp}, timeout=3.0)
            resp.raise_for_status()
            result = resp.json().get("result")
            if isinstance(result, dict) and result.get("decision"):
                result.setdefault("source", "opa")
                return result
        except Exception:
            pass  # OPA unreachable -> fall back to the built-in equivalent
    return builtin_decision(inp)
