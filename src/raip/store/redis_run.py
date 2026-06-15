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
    lifecycle_stage: str = "inference"
    catalog_version: str = ""
    harness_provenance: list[dict[str, Any]] = field(default_factory=list)
    stages: list[dict[str, Any]] = field(default_factory=list)
    raw_outputs_summary: list[dict[str, Any]] = field(default_factory=list)
    signature: dict[str, str] | None = None
    git_sha: str = "unknown"
    trust_factor: dict[str, Any] | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> RunRecord:
        d = json.loads(data)
        for key, default in (
            ("aggregate_scores", None),
            ("complai_scores", None),
            ("payload", {}),
            ("lifecycle_stage", "inference"),
            ("catalog_version", ""),
            ("harness_provenance", []),
            ("stages", []),
            ("raw_outputs_summary", []),
            ("signature", None),
            ("git_sha", "unknown"),
            ("trust_factor", None),
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
        lifecycle = str(payload.get("lifecycle_stage") or "inference")
        rec = RunRecord(
            run_id=run_id,
            status="queued",
            model_id=model_id,
            created_at=now,
            updated_at=now,
            payload=payload,
            lifecycle_stage=lifecycle,
            stages=[{"name": "queued", "status": "completed", "ts": now}],
        )
        self._persist(self._key(run_id), rec.to_json())
        return rec

    def get(self, run_id: str) -> RunRecord | None:
        raw = self._r.get(self._key(run_id))
        if not raw:
            return None
        return RunRecord.from_json(raw)

    def append_stage(
        self,
        run_id: str,
        name: str,
        status: str = "completed",
        detail: str | None = None,
    ) -> RunRecord | None:
        rec = self.get(run_id)
        if not rec:
            return None
        now = datetime.now(UTC).isoformat()
        stage: dict[str, Any] = {"name": name, "status": status, "ts": now}
        if detail:
            stage["detail"] = detail
        rec.stages.append(stage)
        rec.updated_at = now
        self._persist(self._key(run_id), rec.to_json())
        return rec

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
        lifecycle_stage: str | None = None,
        catalog_version: str | None = None,
        harness_provenance: list[dict[str, Any]] | None = None,
        stages: list[dict[str, Any]] | None = None,
        raw_outputs_summary: list[dict[str, Any]] | None = None,
        signature: dict[str, str] | None = None,
        git_sha: str | None = None,
        trust_factor: dict[str, Any] | None = None,
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
        if lifecycle_stage is not None:
            rec.lifecycle_stage = lifecycle_stage
        if catalog_version is not None:
            rec.catalog_version = catalog_version
        if harness_provenance is not None:
            rec.harness_provenance = harness_provenance
        if stages is not None:
            rec.stages = stages
        if raw_outputs_summary is not None:
            rec.raw_outputs_summary = raw_outputs_summary
        if signature is not None:
            rec.signature = signature
        if git_sha is not None:
            rec.git_sha = git_sha
        if trust_factor is not None:
            rec.trust_factor = trust_factor
        rec.updated_at = datetime.now(UTC).isoformat()
        self._persist(self._key(run_id), rec.to_json())
        return rec

    def delete(self, run_id: str) -> bool:
        return bool(self._r.delete(self._key(run_id)))

    def list_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        model_id: str | None = None,
        lifecycle: str | None = None,
        status: str | None = None,
        exclude_pilote: bool = True,
    ) -> tuple[list[RunRecord], int]:
        from raip.dashboard.triage import is_pilote_run

        keys: list[str] = []
        cursor = 0
        while True:
            cursor, batch = self._r.scan(cursor=cursor, match=f"{self.prefix}*", count=200)
            keys.extend(batch)
            if cursor == 0:
                break

        records: list[RunRecord] = []
        for key in keys:
            raw = self._r.get(key)
            if not raw:
                continue
            rec = RunRecord.from_json(raw)
            if exclude_pilote and is_pilote_run(rec.catalog_version, rec.payload):
                continue
            if model_id and rec.model_id != model_id:
                continue
            if lifecycle and rec.lifecycle_stage != lifecycle:
                continue
            if status and rec.status != status:
                continue
            records.append(rec)

        records.sort(key=lambda r: r.created_at or "", reverse=True)
        total = len(records)
        page = records[offset : offset + limit]
        return page, total
