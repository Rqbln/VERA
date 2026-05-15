from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

import redis

from raip.config import Settings, get_settings


@dataclass
class RunRecord:
    run_id: str
    status: str  # queued | running | completed | failed
    model_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    error: str | None = None
    mlflow_run_id: str | None = None
    card_markdown: str | None = None
    benchmark_run_yaml: str | None = None
    aggregate_scores: dict[str, float] | None = None
    complai_scores: dict[str, Any] | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> RunRecord:
        d = json.loads(data)
        for key, default in (
            ("aggregate_scores", None),
            ("complai_scores", None),
        ):
            d.setdefault(key, default)
        return cls(**d)


class RedisRunStore:
    prefix = "raip:run:"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        self._r = redis.from_url(self._s.redis_url, decode_responses=True)

    def _key(self, run_id: str) -> str:
        return f"{self.prefix}{run_id}"

    def _persist(self, key: str, payload: str) -> None:
        ttl = int(self._s.redis_run_ttl_seconds)
        if ttl > 0:
            self._r.set(key, payload, ex=ttl)
        else:
            self._r.set(key, payload)

    def create(self, run_id: str, model_id: str, payload: dict[str, Any]) -> RunRecord:
        now = datetime.now(UTC).isoformat()
        rec = RunRecord(
            run_id=run_id,
            status="queued",
            model_id=model_id,
            created_at=now,
            updated_at=now,
            payload=payload,
        )
        self._persist(self._key(run_id), rec.to_json())
        return rec

    def get(self, run_id: str) -> RunRecord | None:
        raw = self._r.get(self._key(run_id))
        if not raw:
            return None
        return RunRecord.from_json(raw)

    def update(
        self,
        run_id: str,
        *,
        status: str | None = None,
        error: str | None = None,
        mlflow_run_id: str | None = None,
        card_markdown: str | None = None,
        benchmark_run_yaml: str | None = None,
        aggregate_scores: dict[str, float] | None = None,
        complai_scores: dict[str, Any] | None = None,
    ) -> RunRecord | None:
        rec = self.get(run_id)
        if not rec:
            return None
        if status is not None:
            rec.status = status
        if error is not None:
            rec.error = error
        if mlflow_run_id is not None:
            rec.mlflow_run_id = mlflow_run_id
        if card_markdown is not None:
            rec.card_markdown = card_markdown
        if benchmark_run_yaml is not None:
            rec.benchmark_run_yaml = benchmark_run_yaml
        if aggregate_scores is not None:
            rec.aggregate_scores = aggregate_scores
        if complai_scores is not None:
            rec.complai_scores = complai_scores
        rec.updated_at = datetime.now(UTC).isoformat()
        self._persist(self._key(run_id), rec.to_json())
        return rec

    def delete(self, run_id: str) -> bool:
        return bool(self._r.delete(self._key(run_id)))
