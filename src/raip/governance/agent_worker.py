"""Agent worker: consume governed traffic, score it, emit signals + audit (MVP4 gaas)."""

from __future__ import annotations

from typing import Any

from raip.config import Settings, get_settings
from raip.governance.agents import score_event
from raip.governance.audit import build_audit_event, emit_audit
from raip.governance.bus import TOPIC_SIGNALS, TOPIC_TRAFFIC, get_bus


def handle_traffic(event: dict[str, Any], settings: Settings | None = None) -> list[dict[str, Any]]:
    s = settings or get_settings()
    bus = get_bus(s)
    signals = score_event(event, s)
    for sig in signals:
        bus.publish(TOPIC_SIGNALS, sig.as_dict(), key=sig.model)
    audit = build_audit_event(
        kind="agent_scores",
        model=str(event.get("model") or "unknown"),
        payload={"signals": [sig.as_dict() for sig in signals]},
        decision=event.get("decision"),
    )
    emit_audit(audit, s)
    return [sig.as_dict() for sig in signals]


def run_agents(settings: Settings | None = None) -> None:  # pragma: no cover - loop
    s = settings or get_settings()
    get_bus(s).consume(
        [TOPIC_TRAFFIC],
        group="agents",
        consumer="agents-1",
        handler=lambda _topic, value: handle_traffic(value, s),
    )
