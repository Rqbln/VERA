"""Audit / SIEM sink (MVP4 gaas).

Consumes ``audit-events`` and persists each signed record to the local JSONL chain and, when
configured, indexes it into OpenSearch. Run: ``python -m services.audit_sink.main``.
"""

from __future__ import annotations

from raip.governance.audit import run_audit_sink


def main() -> None:  # pragma: no cover - process entrypoint
    print("[gov-audit-sink] consuming audit-events", flush=True)
    run_audit_sink()


if __name__ == "__main__":
    main()
