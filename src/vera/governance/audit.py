"""Signed audit / SIEM trail for the governance runtime (MVP4 gaas).

Every governed request, agent signal, and policy decision becomes an append-only, **signed** audit
record (reusing :func:`vera.governance.signing.sign_artifact`). Records are published to the
``audit-events`` topic; the audit sink indexes them into OpenSearch when available and always writes
a local signed JSONL chain as the tamper-evident fallback. Trust-Factor drops and policy denials are
flagged as incidents.

Hardening note: a production SIEM (Wazuh + clustered OpenSearch, correlation rules, eIDAS/RFC-3161
timestamps) is documented as a deployment task; this module provides the signed, queryable trail.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from vera.config import Settings, get_settings
from vera.governance.bus import TOPIC_AUDIT, get_bus
from vera.governance.signing import sign_artifact

_INCIDENT_KINDS = {"policy_deny", "kill_switch", "low_trust"}


def build_audit_event(
    *,
    kind: str,
    model: str,
    payload: dict[str, Any],
    decision: str | None = None,
    trust_score: float | None = None,
) -> dict[str, Any]:
    block_below = float(os.environ.get("VERA_POLICY_BLOCK_BELOW", "0.30"))
    incident = (
        decision == "deny"
        or kind in _INCIDENT_KINDS
        or (isinstance(trust_score, (int, float)) and trust_score < block_below)
    )
    body = {
        "event_id": str(uuid4()),
        "ts": datetime.now(UTC).isoformat(),
        "kind": kind,
        "model": model,
        "decision": decision,
        "trust_score": trust_score,
        "incident": bool(incident),
        "payload": payload,
    }
    body["signature"] = sign_artifact(body)
    return body


def emit_audit(event: dict[str, Any], settings: Settings | None = None) -> None:
    """Publish an audit event to the bus (best-effort; never raises into the request path)."""
    try:
        get_bus(settings).publish(TOPIC_AUDIT, event, key=event.get("model"))
    except Exception:
        pass


def _jsonl_path(settings: Settings) -> Path:
    base = Path(settings.vera_local_artifacts_dir).expanduser().resolve() / "audit"
    base.mkdir(parents=True, exist_ok=True)
    return base / "audit-events.jsonl"


def write_jsonl(event: dict[str, Any], settings: Settings | None = None) -> None:
    s = settings or get_settings()
    with _jsonl_path(s).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def index_opensearch(event: dict[str, Any], settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    if not s.opensearch_url:
        return False
    try:
        url = f"{s.opensearch_url.rstrip('/')}/vera-audit/_doc/{event['event_id']}"
        resp = httpx.put(url, json=event, timeout=3.0)
        return resp.status_code in (200, 201)
    except Exception:
        return False


def persist_audit(event: dict[str, Any], settings: Settings | None = None) -> dict[str, str]:
    """Sink-side persistence: always JSONL; OpenSearch when configured."""
    s = settings or get_settings()
    write_jsonl(event, s)
    indexed = index_opensearch(event, s)
    return {"jsonl": "ok", "opensearch": "ok" if indexed else "skipped"}


def recent_incidents(limit: int = 50, settings: Settings | None = None) -> list[dict[str, Any]]:
    """Read recent incident audit records from the local signed JSONL chain (newest first)."""
    s = settings or get_settings()
    path = _jsonl_path(s)
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines()[::-1]:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("incident"):
            out.append(ev)
        if len(out) >= limit:
            break
    return out


def run_audit_sink(settings: Settings | None = None) -> None:  # pragma: no cover - loop
    s = settings or get_settings()
    get_bus(s).consume(
        [TOPIC_AUDIT],
        group="audit-sink",
        consumer="audit-1",
        handler=lambda _topic, value: persist_audit(value, s),
    )
