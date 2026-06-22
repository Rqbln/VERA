"""Streaming Trust Factor (MVP4 gaas).

Consumes scored signals emitted by the governance agents (``gov-signals``), keeps the latest
per-requirement signal for each model, and recomputes the Trust Factor in a rolling fashion — the
real-time analogue of the post-run Trust Factor in :mod:`raip.governance.trust_factor`. The latest
score and a capped time series live in Redis (read by the governance dashboard); a best-effort point
is also written to TimescaleDB ``metric_timeseries`` when configured.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import redis

from raip.config import Settings, get_settings
from raip.governance.bus import TOPIC_SIGNALS, get_bus
from raip.governance.trust_factor import compute_trust_factor


def _r(settings: Settings | None = None) -> redis.Redis:
    return redis.from_url((settings or get_settings()).redis_url, decode_responses=True)


def _signals_key(model: str) -> str:
    return f"raip:gov:signals:{model}"


def _trust_key(model: str) -> str:
    return f"raip:gov:trust:{model}"


def _series_key(model: str) -> str:
    return f"raip:gov:trust:series:{model}"


def _write_timescale(model: str, score: float, settings: Settings) -> None:
    if not settings.raip_timescale_url:
        return
    try:
        import psycopg  # optional

        with psycopg.connect(settings.raip_timescale_url, connect_timeout=2) as conn:
            conn.execute(
                "INSERT INTO metric_timeseries (ts, model, metric, value)"
                " VALUES (now(), %s, %s, %s)",
                (model, "trust_factor", score),
            )
    except Exception:
        pass  # best-effort; Redis series is the source of truth for the dashboard


def record_signal(
    model: str, cr: str, score: float, settings: Settings | None = None
) -> dict[str, Any] | None:
    s = settings or get_settings()
    r = _r(s)
    r.hset(_signals_key(model), cr, score)
    signals = r.hgetall(_signals_key(model))
    complai = {k: {"score": float(v)} for k, v in signals.items()}
    tf = compute_trust_factor(complai)
    if tf:
        r.set(_trust_key(model), json.dumps(tf))
        point = {"ts": datetime.now(UTC).isoformat(), "score": tf["score"], "band": tf["band"]}
        r.xadd(_series_key(model), {"data": json.dumps(point)}, maxlen=500, approximate=True)
        _write_timescale(model, float(tf["score"]), s)
    return tf


def current_trust(model: str, settings: Settings | None = None) -> dict[str, Any] | None:
    raw = _r(settings).get(_trust_key(model))
    return json.loads(raw) if raw else None


def latest_signals(model: str, settings: Settings | None = None) -> dict[str, float]:
    raw = _r(settings).hgetall(_signals_key(model))
    return {k: float(v) for k, v in raw.items()}


def trust_series(
    model: str, limit: int = 100, settings: Settings | None = None
) -> list[dict[str, Any]]:
    entries = _r(settings).xrange(_series_key(model), count=limit)
    return [json.loads(fields["data"]) for _id, fields in entries if fields.get("data")]


def run_trust_stream(settings: Settings | None = None) -> None:  # pragma: no cover - loop
    """Consumer loop: fold agent signals into a live Trust Factor."""
    s = settings or get_settings()

    def _handler(_topic: str, value: dict[str, Any]) -> None:
        model = value.get("model")
        cr = value.get("cr")
        score = value.get("score")
        if model and cr and isinstance(score, (int, float)):
            record_signal(model, cr, float(score), s)

    get_bus(s).consume([TOPIC_SIGNALS], group="trust-stream", consumer="ts-1", handler=_handler)
