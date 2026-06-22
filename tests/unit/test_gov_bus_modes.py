from __future__ import annotations

import pytest

from raip.governance.bus import TOPIC_TRAFFIC, RedisStreamBus, get_bus
from raip.governance.modes import VALID_MODES, all_modes, get_mode, set_mode


def test_bus_defaults_to_redis_streams(monkeypatch):
    monkeypatch.delenv("KAFKA_BROKER_URL", raising=False)
    assert get_bus().backend == "redis-streams"


def test_redis_stream_round_trip():
    bus = RedisStreamBus()
    bus.publish(TOPIC_TRAFFIC, {"model": "m", "n": 1}, key="m")
    seen: list[dict] = []
    bus.consume(
        [TOPIC_TRAFFIC], group="bus-test", consumer="c1",
        handler=lambda _t, v: seen.append(v), block_ms=200, count=20, _once=True,
    )
    assert any(v.get("model") == "m" for v in seen)


def test_modes_round_trip():
    set_mode("model-x", "enforcement")
    assert get_mode("model-x") == "enforcement"
    assert "model-x" in all_modes()


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        set_mode("model-y", "nonsense")


def test_unknown_model_uses_default():
    assert get_mode("never-seen-model") in VALID_MODES
