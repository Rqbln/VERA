"""Storage for the self-administered RQ1 user study (docs/USER_STUDY_PROTOCOL.md).

One session per participant (server-assigned P-code, pinned target run, and an
answer-key snapshot taken at session creation so verdicts stay deterministic),
and one response record per (session, task) — the key shape makes double
submission structurally impossible to miss.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import redis

from vera.config import Settings, get_settings

TASK_IDS = tuple(f"T{i}" for i in range(1, 9))
ROLE_OPTIONS = ("compliance_officer", "risk_manager", "legal", "audit", "other_non_ml")


@dataclass
class StudySession:
    session_id: str
    participant: str  # P1, P2, ... (server-assigned)
    role: str
    run_id: str
    answer_key: dict[str, Any] = field(default_factory=dict)
    locale: str = "en"
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StudyResponse:
    session_id: str
    participant: str
    task_id: str
    status: str = "started"  # started | submitted
    answer: dict[str, Any] = field(default_factory=dict)
    completed: bool = False
    verdict: str = ""  # correct | wrong | gave_up | timeout | unverified
    client_seconds: float | None = None
    server_seconds: float | None = None
    started_at: str = ""
    submitted_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(UTC).isoformat()


class RedisStudyStore:
    prefix = "vera:study:"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        self._r = redis.from_url(self._s.redis_url, decode_responses=True)

    def _skey(self, session_id: str) -> str:
        return f"{self.prefix}session:{session_id}"

    def _rkey(self, session_id: str, task_id: str) -> str:
        return f"{self.prefix}response:{session_id}:{task_id}"

    def create_session(
        self, *, role: str, run_id: str, answer_key: dict[str, Any], locale: str = "en"
    ) -> StudySession:
        seq = int(self._r.incr(f"{self.prefix}participant_seq"))
        session = StudySession(
            session_id=str(uuid4()),
            participant=f"P{seq}",
            role=role,
            run_id=run_id,
            answer_key=answer_key,
            locale=locale,
            created_at=_now(),
        )
        self._r.set(self._skey(session.session_id), json.dumps(session.to_dict()))
        return session

    def get_session(self, session_id: str) -> StudySession | None:
        raw = self._r.get(self._skey(session_id))
        return StudySession(**json.loads(raw)) if raw else None

    def start_task(self, session: StudySession, task_id: str) -> StudyResponse:
        """First write wins: reloading the study page never resets the server clock."""
        key = self._rkey(session.session_id, task_id)
        raw = self._r.get(key)
        if raw:
            return StudyResponse(**json.loads(raw))
        response = StudyResponse(
            session_id=session.session_id,
            participant=session.participant,
            task_id=task_id,
            started_at=_now(),
        )
        self._r.set(key, json.dumps(response.to_dict()))
        return response

    def get_response(self, session_id: str, task_id: str) -> StudyResponse | None:
        raw = self._r.get(self._rkey(session_id, task_id))
        return StudyResponse(**json.loads(raw)) if raw else None

    def save_response(self, response: StudyResponse) -> None:
        self._r.set(
            self._rkey(response.session_id, response.task_id),
            json.dumps(response.to_dict()),
        )

    def list_sessions(self) -> list[StudySession]:
        return self._scan(f"{self.prefix}session:*", StudySession)

    def list_responses(self, session_id: str | None = None) -> list[StudyResponse]:
        pattern = f"{self.prefix}response:{session_id or '*'}:*"
        return self._scan(pattern, StudyResponse)

    def _scan(self, pattern: str, cls):
        items = []
        cursor = 0
        while True:
            cursor, batch = self._r.scan(cursor=cursor, match=pattern, count=200)
            for key in batch:
                raw = self._r.get(key)
                if raw:
                    items.append(cls(**json.loads(raw)))
            if cursor == 0:
                break
        return items
