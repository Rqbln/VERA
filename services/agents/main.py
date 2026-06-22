"""Governance agent worker (MVP4 gaas).

Runs two consumer loops in threads: the 4 scoring agents (llm-traffic -> gov-signals) and the
streaming Trust Factor (gov-signals -> live trust). Run: ``python -m services.agents.main``.
"""

from __future__ import annotations

import threading

from raip.governance.agent_worker import run_agents
from raip.governance.trust_stream import run_trust_stream


def main() -> None:  # pragma: no cover - process entrypoint
    threads = [
        threading.Thread(target=run_agents, name="agents", daemon=True),
        threading.Thread(target=run_trust_stream, name="trust-stream", daemon=True),
    ]
    for t in threads:
        t.start()
    print("[gov-agents] scoring agents + trust-stream consumers started", flush=True)
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
