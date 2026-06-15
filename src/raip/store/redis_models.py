from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

import redis

from raip.config import Settings, get_settings


@dataclass
class ModelRecord:
    model_id: str  # LiteLLM id, e.g. "ollama/llama3.1:8b-instruct-q8_0"
    provider: str = "ollama"
    notes: str = ""
    declared_at: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class RedisModelStore:
    """Persistent registry of user-declared models (replaces the in-memory list)."""

    prefix = "raip:model:"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        self._r = redis.from_url(self._s.redis_url, decode_responses=True)

    def _key(self, model_id: str) -> str:
        return f"{self.prefix}{model_id}"

    def declare(self, model_id: str, provider: str = "ollama", notes: str = "") -> ModelRecord:
        rec = ModelRecord(
            model_id=model_id,
            provider=provider,
            notes=notes,
            declared_at=datetime.now(UTC).isoformat(),
        )
        self._r.set(self._key(model_id), json.dumps(rec.to_dict()))
        return rec

    def get(self, model_id: str) -> ModelRecord | None:
        raw = self._r.get(self._key(model_id))
        if not raw:
            return None
        return ModelRecord(**json.loads(raw))

    def list(self) -> list[ModelRecord]:
        records: list[ModelRecord] = []
        cursor = 0
        while True:
            cursor, batch = self._r.scan(cursor=cursor, match=f"{self.prefix}*", count=200)
            for key in batch:
                raw = self._r.get(key)
                if raw:
                    records.append(ModelRecord(**json.loads(raw)))
            if cursor == 0:
                break
        records.sort(key=lambda m: m.declared_at, reverse=True)
        return records

    def delete(self, model_id: str) -> bool:
        return bool(self._r.delete(self._key(model_id)))
