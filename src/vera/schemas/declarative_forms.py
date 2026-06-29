"""Declarative governance forms N03–N06 (MVP3).

These COMPL-AI requirements are attested, not measured: environmental impact (N03), general
description / datasheet (N04), evaluation summary (N05), and risk summary (N06). They are stored
per run and rendered into the signed audit PDF. Forms are intentionally permissive dicts so they
can be partially filled in the dashboard.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import redis
from pydantic import BaseModel, Field

from vera.config import Settings, get_settings

FORM_IDS = ("N03", "N04", "N05", "N06")

FORM_META: dict[str, dict[str, str]] = {
    "N03": {"name": "Environmental impact", "principle": "Societal & environmental well-being"},
    "N04": {"name": "General description / datasheet", "principle": "Transparency"},
    "N05": {"name": "Evaluation summary", "principle": "Transparency"},
    "N06": {"name": "Risk summary", "principle": "Transparency"},
}


class DeclarativeFormBody(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False


class RedisFormStore:
    prefix = "vera:forms:"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        self._r = redis.from_url(self._s.redis_url, decode_responses=True)

    def _key(self, run_id: str) -> str:
        return f"{self.prefix}{run_id}"

    def get_all(self, run_id: str) -> dict[str, Any]:
        raw = self._r.get(self._key(run_id))
        return json.loads(raw) if raw else {}

    def get(self, run_id: str, form_id: str) -> dict[str, Any]:
        return self.get_all(run_id).get(form_id, {"fields": {}, "completed": False})

    def put(self, run_id: str, form_id: str, body: DeclarativeFormBody) -> dict[str, Any]:
        forms = self.get_all(run_id)
        forms[form_id] = {
            "fields": body.fields,
            "completed": body.completed,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self._r.set(self._key(run_id), json.dumps(forms))
        return forms[form_id]
