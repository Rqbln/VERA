"""Governance kill-switch (thin MVP4 slice).

A single global flag that halts new evaluation runs. It is honoured both at run creation
(``POST /api/v1/runs`` returns 503) and inside the worker (a run short-circuits to ``halted``).
The flag is read from the environment (``VERA_KILL_SWITCH``) and/or a Redis key, so it can be
toggled at runtime from the dashboard without a redeploy.
"""

from __future__ import annotations

import os

import redis

from vera.config import Settings, get_settings

_REDIS_KEY = "vera:kill_switch"
_REASON_KEY = "vera:kill_switch:reason"


def _env_killed() -> bool:
    return os.environ.get("VERA_KILL_SWITCH", "").strip().lower() in ("1", "true", "yes", "on")


def _client(settings: Settings | None = None):
    s = settings or get_settings()
    return redis.from_url(s.redis_url, decode_responses=True)


def kill_switch_status(settings: Settings | None = None) -> tuple[bool, str]:
    """Return ``(engaged, reason)``. Environment flag wins; Redis flag is the runtime toggle."""
    if _env_killed():
        return True, os.environ.get("VERA_KILL_SWITCH_REASON", "env flag")
    try:
        r = _client(settings)
        if r.get(_REDIS_KEY) == "1":
            return True, r.get(_REASON_KEY) or "engaged via dashboard"
    except Exception:
        return False, ""
    return False, ""


def is_killed(settings: Settings | None = None) -> bool:
    return kill_switch_status(settings)[0]


def set_kill(engaged: bool, reason: str = "", settings: Settings | None = None) -> tuple[bool, str]:
    """Toggle the Redis runtime flag. Returns the resulting status."""
    r = _client(settings)
    if engaged:
        r.set(_REDIS_KEY, "1")
        r.set(_REASON_KEY, reason or "engaged via dashboard")
    else:
        r.delete(_REDIS_KEY)
        r.delete(_REASON_KEY)
    return kill_switch_status(settings)
