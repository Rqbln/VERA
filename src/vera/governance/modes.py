"""Per-model governance mode (MVP4 gaas).

A model is governed in one of three escalating modes:

* ``shadow`` — observe only; never block (safe default for roll-out).
* ``advisory`` — raise incidents/alerts; never block.
* ``enforcement`` — block requests when the kill-switch is engaged or policy denies.

Modes are stored in a Redis hash so the proxy, OPA input, and admin API share one source of truth.
"""

from __future__ import annotations

import redis

from vera.config import Settings, get_settings

VALID_MODES = ("shadow", "advisory", "enforcement")
_HASH_KEY = "vera:gov:mode"


def _client(settings: Settings | None = None) -> redis.Redis:
    s = settings or get_settings()
    return redis.from_url(s.redis_url, decode_responses=True)


def default_mode(settings: Settings | None = None) -> str:
    s = settings or get_settings()
    mode = (s.vera_governance_mode or "shadow").strip().lower()
    return mode if mode in VALID_MODES else "shadow"


def get_mode(model_id: str, settings: Settings | None = None) -> str:
    try:
        mode = _client(settings).hget(_HASH_KEY, model_id)
    except Exception:
        mode = None
    return mode if mode in VALID_MODES else default_mode(settings)


def set_mode(model_id: str, mode: str, settings: Settings | None = None) -> str:
    mode = (mode or "").strip().lower()
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}")
    _client(settings).hset(_HASH_KEY, model_id, mode)
    return mode


def all_modes(settings: Settings | None = None) -> dict[str, str]:
    try:
        return _client(settings).hgetall(_HASH_KEY) or {}
    except Exception:
        return {}
