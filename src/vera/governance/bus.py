"""Event-bus abstraction for the governance runtime (MVP4 gaas).

A minimal publish/consume surface over an append-only event bus, with two backends:

* **Kafka / Redpanda** (``confluent-kafka``) when ``KAFKA_BROKER_URL`` is set and the client lib is
  installed — the production-grade path.
* **Redis Streams** otherwise — a zero-extra-infrastructure fallback so the governance pipeline runs
  end-to-end on the existing Redis the platform already needs (preserves one-command simplicity).

Topics: ``llm-traffic`` (proxy → agents), ``gov-signals`` (agents → trust-stream),
``audit-events`` (everything → audit sink).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any, Protocol

import redis

from vera.config import Settings, get_settings

TOPIC_TRAFFIC = "llm-traffic"
TOPIC_SIGNALS = "gov-signals"
TOPIC_AUDIT = "audit-events"


class Bus(Protocol):
    backend: str

    def publish(self, topic: str, value: dict[str, Any], key: str | None = None) -> None: ...

    def consume(
        self,
        topics: Iterable[str],
        group: str,
        consumer: str,
        handler: Callable[[str, dict[str, Any]], None],
        *,
        block_ms: int = 5000,
        count: int = 50,
    ) -> None: ...


class RedisStreamBus:
    """Redis Streams backend (consumer groups; best-effort processing).

    Delivery is at-least-once at the stream level, but a record that fails to decode or whose
    handler raises is acked and dropped (not retried) so one poison message cannot stall the group.
    """

    backend = "redis-streams"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        self._r = redis.from_url(self._s.redis_url, decode_responses=True)

    def _key(self, topic: str) -> str:
        return f"vera:bus:{topic}"

    def publish(self, topic: str, value: dict[str, Any], key: str | None = None) -> None:
        self._r.xadd(self._key(topic), {"data": json.dumps(value), "key": key or ""})

    def _ensure_group(self, topic: str, group: str) -> None:
        try:
            self._r.xgroup_create(self._key(topic), group, id="0", mkstream=True)
        except redis.ResponseError as e:  # BUSYGROUP -> already exists
            if "BUSYGROUP" not in str(e):
                raise

    def consume(
        self,
        topics: Iterable[str],
        group: str,
        consumer: str,
        handler: Callable[[str, dict[str, Any]], None],
        *,
        block_ms: int = 5000,
        count: int = 50,
        _once: bool = False,
    ) -> None:
        topics = list(topics)
        streams = {self._key(t): ">" for t in topics}
        key_to_topic = {self._key(t): t for t in topics}
        for t in topics:
            self._ensure_group(t, group)
        while True:
            resp = self._r.xreadgroup(group, consumer, streams, count=count, block=block_ms)
            for stream_key, entries in resp or []:
                topic = key_to_topic.get(stream_key, stream_key)
                for entry_id, fields in entries:
                    try:
                        value = json.loads(fields.get("data") or "{}")
                        handler(topic, value)
                    except Exception:
                        pass  # drop a poison record rather than stall the group (best-effort)
                    finally:
                        self._r.xack(stream_key, group, entry_id)
            if _once:
                return


class KafkaBus:
    """Kafka / Redpanda backend via confluent-kafka."""

    backend = "kafka"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        from confluent_kafka import Producer  # lazy import; optional dependency

        self._producer = Producer({"bootstrap.servers": self._s.kafka_broker_url})

    def publish(self, topic: str, value: dict[str, Any], key: str | None = None) -> None:
        self._producer.produce(topic, key=key, value=json.dumps(value).encode("utf-8"))
        self._producer.poll(0)

    def consume(
        self,
        topics: Iterable[str],
        group: str,
        consumer: str,
        handler: Callable[[str, dict[str, Any]], None],
        *,
        block_ms: int = 5000,
        count: int = 50,
    ) -> None:
        from confluent_kafka import Consumer

        c = Consumer(
            {
                "bootstrap.servers": self._s.kafka_broker_url,
                "group.id": group,
                "auto.offset.reset": "earliest",
            }
        )
        c.subscribe(list(topics))
        try:
            while True:
                msg = c.poll(block_ms / 1000.0)
                if msg is None or msg.error():
                    continue
                try:
                    handler(msg.topic(), json.loads(msg.value().decode("utf-8")))
                except Exception:
                    pass
        finally:
            c.close()


def _kafka_available() -> bool:
    try:
        import confluent_kafka  # noqa: F401

        return True
    except Exception:
        return False


def get_bus(settings: Settings | None = None) -> Bus:
    """Pick the bus backend: Kafka when a broker is configured and importable, else Redis."""
    s = settings or get_settings()
    if s.kafka_broker_url and _kafka_available():
        return KafkaBus(s)
    return RedisStreamBus(s)
