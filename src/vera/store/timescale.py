"""TimescaleDB metric_timeseries writer (in-memory fallback)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime

from vera.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    run_id: str
    model_id: str
    checkpoint: str
    requirement: str
    metric: str
    value: float
    ts: str
    tags: dict[str, str] = field(default_factory=dict)


class TimescaleWriter:
    """Writes to Postgres/Timescale when DSN set; else in-memory for tests."""

    _memory: list[MetricPoint] = []

    def __init__(self, dsn: str | None = None) -> None:
        settings = get_settings()
        self.dsn = (
            dsn
            or settings.vera_timescale_url
            or os.environ.get("VERA_TIMESCALE_URL", "")
        )

    def write_metric(
        self,
        *,
        run_id: str,
        model_id: str,
        checkpoint: str,
        requirement: str,
        metric: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        point = MetricPoint(
            run_id=run_id,
            model_id=model_id,
            checkpoint=checkpoint,
            requirement=requirement,
            metric=metric,
            value=value,
            ts=datetime.now(UTC).isoformat(),
            tags=tags or {},
        )
        if self.dsn:
            try:
                self._write_pg(point)
            except Exception as exc:
                logger.warning("Timescale write failed, using memory: %s", exc)
                TimescaleWriter._memory.append(point)
        else:
            TimescaleWriter._memory.append(point)

    def _write_pg(self, point: MetricPoint) -> None:
        import psycopg  # type: ignore[import-untyped]

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO metric_timeseries
                    (run_id, model_id, checkpoint, requirement, metric, value, ts, tags)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                    """,
                    (
                        point.run_id,
                        point.model_id,
                        point.checkpoint,
                        point.requirement,
                        point.metric,
                        point.value,
                        point.ts,
                        json.dumps(point.tags),
                    ),
                )
            conn.commit()

    @classmethod
    def memory_points(cls) -> list[MetricPoint]:
        return list(cls._memory)

    @classmethod
    def clear_memory(cls) -> None:
        cls._memory.clear()
