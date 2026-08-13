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

# Two-condition quiz (baseline raw artifacts vs the VERA dashboard). Two matched
# six-item sets; the server assigns which set lands in which phase (the `arm`),
# so content learning between phases is neutralised while the condition order
# stays fixed (baseline first, dashboard second) for every participant.
QUIZ_SET_A = tuple(f"Q{i}A" for i in range(1, 7))
QUIZ_SET_B = tuple(f"Q{i}B" for i in range(1, 7))
QUIZ_ITEMS = QUIZ_SET_A + QUIZ_SET_B
ARM_OPTIONS = ("alpha_first", "beta_first")
CONDITIONS = ("baseline", "vera")
ROLE_OPTIONS = (
    "compliance_officer",
    "risk_manager",
    "legal",
    "audit",
    "ai_researcher",
    "other_non_ml",
)
# Participant profile: closed option lists only, so no free-text field can ever
# carry identifying information.
AI_EXPERIENCE_OPTIONS = ("none", "user", "reviewer", "builder")
AIACT_FAMILIARITY_OPTIONS = ("none", "heard", "working", "expert")
SENIORITY_OPTIONS = ("lt2", "2to5", "6to10", "gt10")

# Technology Acceptance Model instrument (Davis 1989), 5-point Likert.
PU_ITEMS = ("PU1", "PU2", "PU3", "PU4")
PEOU_ITEMS = ("PEOU1", "PEOU2", "PEOU3", "PEOU4")
SURVEY_ITEMS = PU_ITEMS + PEOU_ITEMS
LIKERT_MIN, LIKERT_MAX = 1, 5
COMMENT_MAX = 500


@dataclass
class StudySession:
    session_id: str
    participant: str  # P1, P2, ... (server-assigned)
    role: str
    run_id: str
    answer_key: dict[str, Any] = field(default_factory=dict)
    locale: str = "en"
    created_at: str = ""
    # Profile fields default to "" so records written before they existed still load.
    ai_experience: str = ""
    aiact_familiarity: str = ""
    seniority: str = ""
    # Set-to-phase pairing for the two-condition quiz ("" on pre-quiz records):
    # alpha_first = set A in the baseline phase, set B on the dashboard;
    # beta_first the reverse. Assigned by participant_seq parity, never chosen.
    arm: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StudySurvey:
    """The closing TAM questionnaire; one record per session."""

    session_id: str
    participant: str
    items: dict[str, int] = field(default_factory=dict)
    comment: str = ""
    locale: str = "en"
    submitted_at: str = ""

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

    def _vkey(self, session_id: str) -> str:
        return f"{self.prefix}survey:{session_id}"

    def create_session(
        self,
        *,
        role: str,
        run_id: str,
        answer_key: dict[str, Any],
        locale: str = "en",
        ai_experience: str = "",
        aiact_familiarity: str = "",
        seniority: str = "",
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
            ai_experience=ai_experience,
            aiact_familiarity=aiact_familiarity,
            seniority=seniority,
            # The sequence counter doubles as the balancing hook: odd P-codes
            # take set A first, even P-codes set B first.
            arm=ARM_OPTIONS[(seq + 1) % 2],
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

    def get_survey(self, session_id: str) -> StudySurvey | None:
        raw = self._r.get(self._vkey(session_id))
        return StudySurvey(**json.loads(raw)) if raw else None

    def save_survey(self, survey: StudySurvey) -> None:
        self._r.set(self._vkey(survey.session_id), json.dumps(survey.to_dict()))

    def list_sessions(self) -> list[StudySession]:
        return self._scan(f"{self.prefix}session:*", StudySession)

    def list_responses(self, session_id: str | None = None) -> list[StudyResponse]:
        pattern = f"{self.prefix}response:{session_id or '*'}:*"
        return self._scan(pattern, StudyResponse)

    def list_surveys(self) -> list[StudySurvey]:
        return self._scan(f"{self.prefix}survey:*", StudySurvey)

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
