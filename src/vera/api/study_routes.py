"""Self-administered RQ1 user study: sessions, app-measured task responses, CSV export.

Answers are validated SERVER-side against an answer key snapshotted at session
creation, and the HTTP responses never disclose correctness (no contamination
between participants). Export matches the sessions.csv schema consumed by
scripts/analyze_user_study.py.
"""

from __future__ import annotations

import csv
import io
import os
import random
import re
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from vera.api.auth import AuthUser, get_current_user
from vera.store.redis_run import RedisRunStore
from vera.store.redis_study import (
    AI_EXPERIENCE_OPTIONS,
    AIACT_FAMILIARITY_OPTIONS,
    COMMENT_MAX,
    LIKERT_MAX,
    LIKERT_MIN,
    QUIZ_ITEMS,
    QUIZ_SET_A,
    QUIZ_SET_B,
    ROLE_OPTIONS,
    SENIORITY_OPTIONS,
    SURVEY_ITEMS,
    TASK_IDS,
    RedisStudyStore,
    StudySession,
    StudySurvey,
)

ALL_TASK_IDS = TASK_IDS + QUIZ_ITEMS

router = APIRouter(prefix="/api/v1/study", tags=["study"])

_SCORE_TOL = 0.005  # UI shows toFixed(2)
_TRUST_TOL = 1.0  # gauge shows a rounded integer
_MIN_EXCERPT = 15
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


# ── Pure helpers (unit-testable without HTTP) ────────────────────────────────────────
def build_answer_key(summary: dict[str, Any]) -> dict[str, Any]:
    """Snapshot the ground truth for the eight tasks from a run-summary payload."""
    reqs = [r for r in (summary.get("requirements") or []) if r.get("triage") != "na"]
    scored = [r for r in reqs if r.get("score") is not None]
    weakest_ids: set[str] = set()
    weakest_primary = ""
    if scored:
        low = min(float(r["score"]) for r in scored)
        weakest_ids = {r["id"] for r in scored if float(r["score"]) == low}
        weakest_primary = min(r["id"] for r in scored if float(r["score"]) == low)
    if reqs:
        weakest_ids.add(reqs[0]["id"])  # top triage row is an accepted reading
    counts = summary.get("triage_counts") or {}
    n_scored = sum(int(counts.get(k, 0)) for k in ("failed", "fallback", "ok"))
    trust = summary.get("trust_factor") or {}
    benchmark_options = sorted(
        {row.get("benchmark_id") for row in (summary.get("harness_provenance") or [])}
        - {None}
    )

    # ── Quiz pair targets (two-condition study). All derived from the same
    # snapshot; targets are NAMED in the item text, so no item depends on
    # another item's answer. Selection rules are deterministic per run.
    second_ids: set[str] = set()
    if scored:
        low = min(float(r["score"]) for r in scored)
        above = sorted({float(r["score"]) for r in scored} - {low})
        if above:
            second_ids = {r["id"] for r in scored if float(r["score"]) == above[0]}
        else:  # a single distinct score: any weakest reading is accepted
            second_ids = set(weakest_ids)
    if len(reqs) > 1:
        second_ids.add(reqs[1]["id"])  # the second triage row is an accepted reading

    # Q2: the two highest-scoring requirements (a pure named-row lookup, and
    # disjoint from the weakest rows that pair 1 asks about).
    by_score = sorted(scored, key=lambda r: (-float(r["score"]), r["id"]))
    q2a_target = by_score[0]["id"] if by_score else ""
    q2b_target = by_score[1]["id"] if len(by_score) > 1 else q2a_target

    # Q3B: the requirement with the most contributing benchmarks (ties: lowest id).
    by_contrib = sorted(
        scored, key=lambda r: (-len(r.get("contributing_benchmarks") or []), r["id"])
    )
    q3b_target = by_contrib[0]["id"] if by_contrib else ""
    q3b_benchmarks = (
        sorted(by_contrib[0].get("contributing_benchmarks") or []) if by_contrib else []
    )

    band_counts = {
        band: sum(1 for r in scored if r.get("band") == band)
        for band in ("red", "orange", "green")
    }
    q6a_target = benchmark_options[0] if benchmark_options else ""
    q6b_target = benchmark_options[-1] if benchmark_options else ""

    def carrier(benchmark: str) -> str:
        # The requirement whose drawer holds this benchmark's sample output.
        for r in sorted(scored, key=lambda r: r["id"]):
            if benchmark in (r.get("contributing_benchmarks") or []):
                return r["id"]
        return ""

    return {
        "weakest_ids": sorted(weakest_ids),
        "weakest_primary": weakest_primary,
        "second_ids": sorted(second_ids),
        "req_scores": {
            r["id"]: {
                "score": r.get("score"),
                "ci_lower": r.get("score_ci_lower"),
                "ci_upper": r.get("score_ci_upper"),
            }
            for r in scored
        },
        "fallback_set": sorted(
            {b for r in reqs for b in (r.get("fallback_benchmarks") or [])}
        ),
        "t4_accepted": sorted({n_scored, len(summary.get("requested_requirements") or [])}),
        "q4b_accepted": [len(benchmark_options)],
        "triage_counts": {k: int(counts.get(k, 0)) for k in ("failed", "fallback", "ok")},
        "band_counts": band_counts,
        "trust": {"score": trust.get("score"), "band": trust.get("band")},
        "q2_targets": {"A": q2a_target, "B": q2b_target},
        "q3b_target": q3b_target,
        "q3b_benchmarks": q3b_benchmarks,
        "q6_targets": {"A": q6a_target, "B": q6b_target},
        "q6_requirements": {"A": carrier(q6a_target), "B": carrier(q6b_target)},
        "requirement_options": [{"id": r["id"], "name": r.get("name", "")} for r in reqs],
        "benchmark_options": benchmark_options,
    }


def validate_survey(items: dict[str, Any], comment: str = "") -> tuple[dict[str, int], str]:
    """Whitelist the TAM item ids, coerce values to ints in 1..5, cap the comment.

    A partial map is accepted: the UI enforces completeness, the server stays
    permissive so a closed tab remains representable.
    """
    clean: dict[str, int] = {}
    for key, raw in (items or {}).items():
        if key not in SURVEY_ITEMS:
            msg = f"unknown survey item {key}; expected one of {SURVEY_ITEMS}"
            raise ValueError(msg)
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            msg = f"survey item {key} must be an integer in {LIKERT_MIN}..{LIKERT_MAX}"
            raise ValueError(msg) from exc
        if not LIKERT_MIN <= value <= LIKERT_MAX:
            msg = f"survey item {key} must be in {LIKERT_MIN}..{LIKERT_MAX}"
            raise ValueError(msg)
        clean[key] = value
    return clean, str(comment or "")[:COMMENT_MAX]


def _close(value: Any, target: Any, tol: float) -> bool:
    try:
        # 1e-9 absorbs float representation error at the tolerance boundary.
        return target is not None and abs(float(value) - float(target)) <= tol + 1e-9
    except (TypeError, ValueError):
        return False


def validate_answer(
    task_id: str,
    answer: dict[str, Any],
    key: dict[str, Any],
    *,
    t1_answer_id: str = "",
    started_at: str = "",
    run_lookup=None,
) -> tuple[bool, str]:
    """Return (completed, verdict) for one submitted answer."""
    if task_id == "T1":
        ok = str(answer.get("requirement_id")) in set(key.get("weakest_ids") or [])
        return ok, "correct" if ok else "wrong"
    if task_id == "T2":
        ref = t1_answer_id or key.get("weakest_primary") or ""
        target = (key.get("req_scores") or {}).get(ref) or {}
        ok = (
            _close(answer.get("score"), target.get("score"), _SCORE_TOL)
            and _close(answer.get("ci_lower"), target.get("ci_lower"), _SCORE_TOL)
            and _close(answer.get("ci_upper"), target.get("ci_upper"), _SCORE_TOL)
        )
        return ok, "correct" if ok else "wrong"
    if task_id == "T3":
        given = {str(b) for b in (answer.get("benchmarks") or [])}
        ok = given == set(key.get("fallback_set") or [])
        return ok, "correct" if ok else "wrong"
    if task_id == "T4":
        try:
            ok = int(answer.get("count")) in set(key.get("t4_accepted") or [])
        except (TypeError, ValueError):
            ok = False
        return ok, "correct" if ok else "wrong"
    if task_id == "T5":
        excerpt = str(answer.get("excerpt") or "").strip()
        ok = bool(answer.get("confirmed")) and len(excerpt) >= _MIN_EXCERPT
        return ok, "unverified" if ok else "wrong"
    if task_id == "T6":
        target = key.get("triage_counts") or {}
        try:
            ok = all(int(answer.get(k)) == target.get(k) for k in ("failed", "fallback", "ok"))
        except (TypeError, ValueError):
            ok = False
        return ok, "correct" if ok else "wrong"
    if task_id == "T7":
        trust = key.get("trust") or {}
        ok = _close(answer.get("score"), trust.get("score"), _TRUST_TOL) and str(
            answer.get("band")
        ) == str(trust.get("band"))
        return ok, "correct" if ok else "wrong"
    if task_id == "T8":
        match = _UUID_RE.search(str(answer.get("run_id") or "").lower())
        if not match or run_lookup is None:
            return False, "wrong"
        rec = run_lookup(match.group(0))
        ok = bool(
            rec
            and rec.status in ("queued", "running", "completed")
            and started_at
            and (rec.created_at or "") > started_at
        )
        return ok, "correct" if ok else "wrong"

    # ── Two-condition quiz items. Each pair reuses one of the rules above; the
    # target is named in the item text and read from the snapshotted key.
    if task_id in ("Q1A", "Q1B"):
        accepted = key.get("weakest_ids") if task_id == "Q1A" else key.get("second_ids")
        ok = str(answer.get("requirement_id")) in set(accepted or [])
        return ok, "correct" if ok else "wrong"
    if task_id in ("Q2A", "Q2B"):
        ref = (key.get("q2_targets") or {}).get(task_id[-1]) or ""
        target = (key.get("req_scores") or {}).get(ref) or {}
        ok = (
            _close(answer.get("score"), target.get("score"), _SCORE_TOL)
            and _close(answer.get("ci_lower"), target.get("ci_lower"), _SCORE_TOL)
            and _close(answer.get("ci_upper"), target.get("ci_upper"), _SCORE_TOL)
        )
        return ok, "correct" if ok else "wrong"
    if task_id in ("Q3A", "Q3B"):
        expected = key.get("fallback_set") if task_id == "Q3A" else key.get("q3b_benchmarks")
        given = {str(b) for b in (answer.get("benchmarks") or [])}
        ok = given == set(expected or [])
        return ok, "correct" if ok else "wrong"
    if task_id in ("Q4A", "Q4B"):
        accepted = key.get("t4_accepted") if task_id == "Q4A" else key.get("q4b_accepted")
        try:
            ok = int(answer.get("count")) in set(accepted or [])
        except (TypeError, ValueError):
            ok = False
        return ok, "correct" if ok else "wrong"
    if task_id == "Q5A":
        target = key.get("triage_counts") or {}
        try:
            ok = all(int(answer.get(k)) == target.get(k) for k in ("failed", "fallback", "ok"))
        except (TypeError, ValueError):
            ok = False
        return ok, "correct" if ok else "wrong"
    if task_id == "Q5B":
        target = key.get("band_counts") or {}
        try:
            ok = all(int(answer.get(k)) == target.get(k) for k in ("red", "orange", "green"))
        except (TypeError, ValueError):
            ok = False
        return ok, "correct" if ok else "wrong"
    if task_id in ("Q6A", "Q6B"):
        excerpt = str(answer.get("excerpt") or "").strip()
        ok = bool(answer.get("confirmed")) and len(excerpt) >= _MIN_EXCERPT
        return ok, "unverified" if ok else "wrong"
    return False, "wrong"


def quiz_plan(arm: str, key: dict[str, Any]) -> list[dict[str, Any]]:
    """Ordered item list for one session: 6 baseline items, then 6 dashboard items.

    The condition order is FIXED (baseline first) for every participant; the arm
    only decides which matched set lands in which phase. Params carry the named
    targets an item needs (never the answers).
    """
    names = {r["id"]: r.get("name", "") for r in (key.get("requirement_options") or [])}

    def params(item: str) -> dict[str, Any]:
        if item.startswith("Q2"):
            rid = (key.get("q2_targets") or {}).get(item[-1]) or ""
            return {"requirement_id": rid, "requirement_name": names.get(rid, rid)}
        if item == "Q3B":
            rid = key.get("q3b_target") or ""
            return {"requirement_id": rid, "requirement_name": names.get(rid, rid)}
        if item.startswith("Q6"):
            rid = (key.get("q6_requirements") or {}).get(item[-1]) or ""
            return {
                "benchmark_id": (key.get("q6_targets") or {}).get(item[-1]) or "",
                # Carrier requirement: lets the client deep-link to the drawer
                # that holds this benchmark's sample output.
                "requirement_id": rid,
                "requirement_name": names.get(rid, rid),
            }
        return {}

    first, second = (QUIZ_SET_A, QUIZ_SET_B) if arm == "alpha_first" else (QUIZ_SET_B, QUIZ_SET_A)
    plan = [{"id": i, "condition": "baseline", "params": params(i)} for i in first]
    plan += [{"id": i, "condition": "vera", "params": params(i)} for i in second]
    return plan


# ── Endpoints ────────────────────────────────────────────────────────────────────────
class SessionBody(BaseModel):
    role: str
    locale: str = "en"
    run_id: str | None = None
    ai_experience: str = ""
    aiact_familiarity: str = ""
    seniority: str = ""


class ResponseBody(BaseModel):
    task_id: str
    answer: dict[str, Any] = {}
    seconds: float | None = None
    gave_up: bool = False
    reason: str = ""


class SurveyBody(BaseModel):
    # Values stay Any so a bad type surfaces as a readable 400, not a 422.
    items: dict[str, Any] = {}
    comment: str = ""


def _require_choice(value: str, options: tuple[str, ...], field: str) -> str:
    if value not in options:
        raise HTTPException(status_code=400, detail=f"{field} must be one of {options}")
    return value


def _target_run(store: RedisRunStore, explicit: str | None):
    run_id = explicit or os.environ.get("VERA_STUDY_RUN_ID")
    if run_id:
        rec = store.get(run_id)
        if not rec:
            raise HTTPException(status_code=404, detail="study run not found")
        return rec
    completed, _ = store.list_runs(status="completed", limit=1)
    if not completed:
        raise HTTPException(status_code=409, detail="no completed run to study")
    return completed[0]


@router.post("/sessions")
def create_session(
    body: SessionBody,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    _require_choice(body.role, ROLE_OPTIONS, "role")
    _require_choice(body.ai_experience, AI_EXPERIENCE_OPTIONS, "ai_experience")
    _require_choice(body.aiact_familiarity, AIACT_FAMILIARITY_OPTIONS, "aiact_familiarity")
    _require_choice(body.seniority, SENIORITY_OPTIONS, "seniority")
    from vera.api.dashboard_routes import _run_summary_dict

    rec = _target_run(RedisRunStore(), body.run_id)
    key = build_answer_key(_run_summary_dict(rec))
    session = RedisStudyStore().create_session(
        role=body.role,
        run_id=rec.run_id,
        answer_key=key,
        locale=body.locale,
        ai_experience=body.ai_experience,
        aiact_familiarity=body.aiact_familiarity,
        seniority=body.seniority,
    )
    # Options are shuffled and the summary itself is never sent to the study client.
    requirement_options = list(key["requirement_options"])
    benchmark_options = list(key["benchmark_options"])
    random.Random(session.participant).shuffle(benchmark_options)
    return {
        "session_id": session.session_id,
        "participant": session.participant,
        "run_id": rec.run_id,
        "arm": session.arm,
        "items": quiz_plan(session.arm, key),
        "requirement_options": requirement_options,
        "benchmark_options": benchmark_options,
    }


def _get_session(session_id: str) -> StudySession:
    session = RedisStudyStore().get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="study session not found")
    return session


@router.post("/sessions/{session_id}/tasks/{task_id}/start")
def start_task(
    session_id: str,
    task_id: str,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    if task_id not in ALL_TASK_IDS:
        raise HTTPException(status_code=400, detail=f"task_id must be one of {ALL_TASK_IDS}")
    RedisStudyStore().start_task(_get_session(session_id), task_id)
    return {"task_id": task_id, "started": True}


@router.post("/sessions/{session_id}/responses")
def submit_response(
    session_id: str,
    body: ResponseBody,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    if body.task_id not in ALL_TASK_IDS:
        raise HTTPException(status_code=400, detail=f"task_id must be one of {ALL_TASK_IDS}")
    session = _get_session(session_id)
    store = RedisStudyStore()
    response = store.start_task(session, body.task_id)  # ensures a started_at exists
    if response.status == "submitted":
        raise HTTPException(status_code=409, detail="task already submitted")

    if body.gave_up:
        completed, verdict = False, ("timeout" if body.reason == "timeout" else "gave_up")
    else:
        t1 = store.get_response(session_id, "T1")
        t1_id = str((t1.answer or {}).get("requirement_id") or "") if t1 else ""
        completed, verdict = validate_answer(
            body.task_id,
            body.answer,
            session.answer_key,
            t1_answer_id=t1_id,
            started_at=response.started_at or session.created_at,
            run_lookup=RedisRunStore().get,
        )

    now = datetime.now(UTC)
    response.status = "submitted"
    response.answer = body.answer
    response.completed = completed
    response.verdict = verdict
    response.client_seconds = body.seconds
    try:
        started = datetime.fromisoformat(response.started_at)
        response.server_seconds = round((now - started).total_seconds(), 1)
    except ValueError:
        response.server_seconds = None
    response.submitted_at = now.isoformat()
    store.save_response(response)
    return {"recorded": True}  # correctness is deliberately not disclosed


@router.post("/sessions/{session_id}/survey")
def submit_survey(
    session_id: str,
    body: SurveyBody,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    """Record the closing TAM questionnaire.

    Last write wins on purpose: a survey carries no timing or contamination
    semantics, and a 409 after a reload would strand a participant on the final
    screen with no way forward.
    """
    session = _get_session(session_id)
    store = RedisStudyStore()
    try:
        items, comment = validate_survey(body.items, body.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    existing = store.get_survey(session_id)
    store.save_survey(
        StudySurvey(
            session_id=session_id,
            participant=session.participant,
            items=items,
            comment=comment,
            locale=session.locale,
            # Keep the first submission's timestamp when a participant resubmits.
            submitted_at=(existing.submitted_at if existing else "")
            or datetime.now(UTC).isoformat(),
        )
    )
    return {"recorded": True}


@router.get("/sessions")
def list_sessions(
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    store = RedisStudyStore()
    sessions = sorted(store.list_sessions(), key=lambda s: s.participant)
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "participant": s.participant,
                "role": s.role,
                "run_id": s.run_id,
                "created_at": s.created_at,
                "responses": sum(
                    1 for r in store.list_responses(s.session_id) if r.status == "submitted"
                ),
            }
            for s in sessions
        ]
    }


def _note_for(response) -> str:
    if response.verdict == "unverified":
        excerpt = str((response.answer or {}).get("excerpt") or "")[:80]
        return f"unverified excerpt: {excerpt}"
    if response.verdict == "wrong":
        return "auto:wrong"
    if response.verdict in ("gave_up", "timeout"):
        return response.verdict.replace("_", " ")
    if response.task_id == "T8":
        rid = str((response.answer or {}).get("run_id") or "")[:8]
        return f"run {rid}" if rid else ""
    return ""


@router.get("/export.csv")
def export_csv(
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> Response:
    store = RedisStudyStore()
    sessions = {s.session_id: s for s in store.list_sessions()}
    # Frozen schema AND frozen row universe: quiz items live in export_quiz.csv.
    rows = [
        r
        for r in store.list_responses()
        if r.status == "submitted" and r.task_id in TASK_IDS
    ]
    rows.sort(key=lambda r: (int(r.participant.lstrip("P") or 0), r.task_id))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["participant", "role", "task_id", "completed", "assisted", "seconds", "notes"])
    for r in rows:
        session = sessions.get(r.session_id)
        seconds = ""
        if r.completed and r.client_seconds is not None:
            seconds = str(int(round(r.client_seconds)))
        writer.writerow(
            [
                r.participant,
                session.role if session else "",
                r.task_id,
                "yes" if r.completed else "no",
                "no",  # self-administered variant: no facilitator, no hints
                seconds,
                _note_for(r),
            ]
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sessions.csv"'},
    )


@router.get("/export_survey.csv")
def export_survey_csv(
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> Response:
    """Long-format TAM export, driven by sessions.

    Every session emits one row per item even when the participant never reached
    the questionnaire, so the participant table stays complete and abandonment is
    visible through `tasks_submitted`.
    """
    store = RedisStudyStore()
    surveys = {s.session_id: s for s in store.list_surveys()}
    responses = store.list_responses()
    submitted = {}
    for r in responses:
        if r.status == "submitted":
            submitted[r.session_id] = submitted.get(r.session_id, 0) + 1
    sessions = sorted(
        store.list_sessions(), key=lambda s: int(s.participant.lstrip("P") or 0)
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "participant",
            "role",
            "ai_experience",
            "aiact_familiarity",
            "seniority",
            "locale",
            "tasks_submitted",
            "item",
            "value",
            "comment",
        ]
    )
    for s in sessions:
        survey = surveys.get(s.session_id)
        items = survey.items if survey else {}
        comment = survey.comment if survey else ""
        for item in SURVEY_ITEMS:
            writer.writerow(
                [
                    s.participant,
                    s.role,
                    s.ai_experience,
                    s.aiact_familiarity,
                    s.seniority,
                    s.locale,
                    submitted.get(s.session_id, 0),
                    item,
                    items.get(item, ""),
                    comment,
                ]
            )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="survey.csv"'},
    )


def _quiz_condition(arm: str, item: str) -> str:
    """Which condition an item ran under, given the session's arm."""
    first_set = "A" if arm == "alpha_first" else "B"
    return "baseline" if item.endswith(first_set) else "vera"


@router.get("/export_quiz.csv")
def export_quiz_csv(
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> Response:
    """Per-item export of the two-condition quiz (one row per submitted item).

    `export.csv` and `export_survey.csv` keep their frozen schemas; the paired
    analysis reads this file only. `condition` is derived server-side from the
    session's arm so the analysis cannot mislabel a row.
    """
    store = RedisStudyStore()
    sessions = {s.session_id: s for s in store.list_sessions()}
    rows = [
        r
        for r in store.list_responses()
        if r.status == "submitted" and r.task_id in QUIZ_ITEMS
    ]
    order = {item: i for i, item in enumerate(QUIZ_ITEMS)}
    rows.sort(key=lambda r: (int(r.participant.lstrip("P") or 0), order.get(r.task_id, 99)))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "participant",
            "role",
            "ai_experience",
            "aiact_familiarity",
            "seniority",
            "locale",
            "arm",
            "condition",
            "set",
            "pair",
            "item",
            "completed",
            "verdict",
            "client_seconds",
            "server_seconds",
        ]
    )
    for r in rows:
        session = sessions.get(r.session_id)
        arm = session.arm if session else ""
        writer.writerow(
            [
                r.participant,
                session.role if session else "",
                session.ai_experience if session else "",
                session.aiact_familiarity if session else "",
                session.seniority if session else "",
                session.locale if session else "",
                arm,
                _quiz_condition(arm, r.task_id),
                r.task_id[-1],
                r.task_id[1],
                r.task_id,
                "yes" if r.completed else "no",
                r.verdict,
                "" if r.client_seconds is None else str(round(float(r.client_seconds), 1)),
                "" if r.server_seconds is None else str(round(float(r.server_seconds), 1)),
            ]
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="quiz.csv"'},
    )
