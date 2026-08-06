"""Self-administered user-study API: sessions, server-side validation, CSV export."""

from __future__ import annotations

import csv
import importlib.util
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vera.api.main import app
from vera.api.study_routes import build_answer_key, validate_answer
from vera.store.redis_run import RedisRunStore
from vera.store.redis_study import RedisStudyStore

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "analyze_user_study", ROOT / "scripts" / "analyze_user_study.py"
)
analyze = importlib.util.module_from_spec(_spec)
sys.modules["analyze_user_study"] = analyze
_spec.loader.exec_module(analyze)

RUN_ID = "study-target-run"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("VERA_AUTH_MODE", "guided")
    monkeypatch.delenv("VERA_STUDY_RUN_ID", raising=False)
    return TestClient(app)


def _wipe_study_keys(store: RedisStudyStore) -> None:
    cursor = 0
    while True:
        cursor, batch = store._r.scan(cursor=cursor, match=f"{store.prefix}*", count=200)
        for key in batch:
            store._r.delete(key)
        if cursor == 0:
            break


@pytest.fixture
def study_run():
    runs = RedisRunStore()
    study = RedisStudyStore()
    _wipe_study_keys(study)
    runs.create(RUN_ID, "ollama/llama3.1:8b", {"complai_requirements": ["R01", "R02", "R06"]})
    runs.update(
        RUN_ID,
        status="completed",
        catalog_version="mvp2-v2",
        lifecycle_stage="inference",
        complai_scores={
            "R01": {"score": 0.85, "score_ci_lower": 0.8, "score_ci_upper": 0.9,
                    "bootstrap_n": 100, "contributing_benchmarks": ["mmlu_robust"]},
            "R02": {"score": 0.30, "score_ci_lower": 0.20, "score_ci_upper": 0.40,
                    "bootstrap_n": 100, "contributing_benchmarks": ["advbench"]},
            "R06": {"score": 0.72, "score_ci_lower": 0.65, "score_ci_upper": 0.79,
                    "bootstrap_n": 100, "contributing_benchmarks": ["mmlu"]},
        },
        harness_provenance=[
            {"benchmark_id": "mmlu", "harness": "hf_dynamic", "agent": "hf_dynamic",
             "fallback": "yes"},
            {"benchmark_id": "advbench", "harness": "hf_dynamic", "agent": "hf_dynamic",
             "fallback": "no"},
        ],
        git_sha="abc123",
        signature={"digest": "sha256:deadbeef"},
        trust_factor={"score": 62.0, "band": "orange", "components": {}},
    )
    yield RUN_ID
    runs.delete(RUN_ID)
    _wipe_study_keys(study)


def _session(client, study_run, role="risk_manager", **profile):
    body = {
        "role": role,
        "run_id": study_run,
        "ai_experience": "reviewer",
        "aiact_familiarity": "working",
        "seniority": "6to10",
        **profile,
    }
    resp = client.post("/api/v1/study/sessions", json=body)
    assert resp.status_code == 200
    return resp.json()


FULL_SURVEY = {
    "PU1": 4, "PU2": 4, "PU3": 5, "PU4": 4,
    "PEOU1": 5, "PEOU2": 4, "PEOU3": 4, "PEOU4": 5,
}


def _survey(client, sid, items=None, comment=""):
    return client.post(
        f"/api/v1/study/sessions/{sid}/survey",
        json={"items": FULL_SURVEY if items is None else items, "comment": comment},
    )


def _survey_rows(client):
    text = client.get("/api/v1/study/export_survey.csv").text
    return list(csv.DictReader(io.StringIO(text)))


def _submit(client, sid, task_id, answer, seconds=12.0, **kw):
    client.post(f"/api/v1/study/sessions/{sid}/tasks/{task_id}/start")
    return client.post(
        f"/api/v1/study/sessions/{sid}/responses",
        json={"task_id": task_id, "answer": answer, "seconds": seconds, **kw},
    )


def test_participants_sequential_and_role_whitelist(client, study_run):
    assert _session(client, study_run)["participant"] == "P1"
    assert _session(client, study_run)["participant"] == "P2"
    bad = client.post("/api/v1/study/sessions", json={"role": "hacker", "run_id": study_run})
    assert bad.status_code == 400


def test_response_never_discloses_correctness(client, study_run):
    sid = _session(client, study_run)["session_id"]
    body = _submit(client, sid, "T1", {"requirement_id": "R02"}).json()
    assert body == {"recorded": True}


def test_happy_path_export(client, study_run):
    sid = _session(client, study_run)["session_id"]
    _submit(client, sid, "T1", {"requirement_id": "R02"})  # weakest (0.30, red, top row)
    _submit(client, sid, "T2", {"score": 0.30, "ci_lower": 0.20, "ci_upper": 0.40})
    _submit(client, sid, "T3", {"benchmarks": ["mmlu"]})  # the only fallback
    _submit(client, sid, "T6", {"failed": 1, "fallback": 1, "ok": 1})
    _submit(client, sid, "T7", {"score": 62, "band": "orange"})
    csv_text = client.get("/api/v1/study/export.csv").text
    rows = {line.split(",")[2]: line.split(",") for line in csv_text.strip().splitlines()[1:]}
    for task in ("T1", "T2", "T3", "T6", "T7"):
        assert rows[task][3] == "yes" and rows[task][5] != ""  # completed with seconds


def test_wrong_answer_fails_without_seconds(client, study_run):
    sid = _session(client, study_run)["session_id"]
    _submit(client, sid, "T1", {"requirement_id": "R06"})  # not the weakest
    line = client.get("/api/v1/study/export.csv").text.strip().splitlines()[1]
    cells = line.split(",")
    assert cells[3] == "no" and cells[5] == "" and "auto:wrong" in cells[6]


def test_t5_unverified_and_short_excerpt(client, study_run):
    sid = _session(client, study_run)["session_id"]
    short = _submit(client, sid, "T5", {"excerpt": "too short", "confirmed": True})
    assert short.status_code == 200
    csv_text = client.get("/api/v1/study/export.csv").text
    assert "T5,no" in csv_text
    sid2 = _session(client, study_run)["session_id"]
    _submit(client, sid2, "T5", {"excerpt": "a model answer fragment long enough",
                                 "confirmed": True})
    csv_text = client.get("/api/v1/study/export.csv").text
    assert "T5,yes" in csv_text and "unverified excerpt" in csv_text


def test_t8_requires_run_created_after_start(client, study_run):
    sid = _session(client, study_run)["session_id"]
    # The preloaded study run predates the session -> rejected.
    old = _submit(client, sid, "T8", {"run_id": study_run})
    assert old.status_code == 200
    assert "T8,no" in client.get("/api/v1/study/export.csv").text
    # A run created after the task started, pasted as a URL -> accepted.
    sid2 = _session(client, study_run)["session_id"]
    client.post(f"/api/v1/study/sessions/{sid2}/tasks/T8/start")
    runs = RedisRunStore()
    new_id = "11111111-2222-4333-8444-555555555555"
    runs.create(new_id, "ollama/llama3.1:8b", {})
    try:
        resp = client.post(
            f"/api/v1/study/sessions/{sid2}/responses",
            json={"task_id": "T8", "answer": {"run_id": f"http://x/runs/{new_id}"},
                  "seconds": 30},
        )
        assert resp.status_code == 200
        lines = [ln for ln in client.get("/api/v1/study/export.csv").text.splitlines()
                 if ln.startswith("P2,") and ",T8," in ln]
        assert lines and ",yes," in lines[0]
    finally:
        runs.delete(new_id)


def test_double_submit_rejected(client, study_run):
    sid = _session(client, study_run)["session_id"]
    _submit(client, sid, "T4", {"count": 3})
    dup = client.post(
        f"/api/v1/study/sessions/{sid}/responses",
        json={"task_id": "T4", "answer": {"count": 3}, "seconds": 5},
    )
    assert dup.status_code == 409


def test_export_roundtrips_into_analyzer(client, study_run, tmp_path):
    sid = _session(client, study_run)["session_id"]
    _submit(client, sid, "T1", {"requirement_id": "R02"}, seconds=30)
    _submit(client, sid, "T4", {"count": 3}, seconds=10)
    _submit(client, sid, "T6", {"failed": 0, "fallback": 0, "ok": 9})  # wrong
    f = tmp_path / "sessions.csv"
    f.write_text(client.get("/api/v1/study/export.csv").text, encoding="utf-8")
    summary = analyze.summarize(analyze.load_rows(f))
    assert summary["T1"]["completed"] == 1 and summary["T1"]["median_s"] == 30.0
    assert summary["T6"]["completed"] == 0


# ── TAM survey (APSEC acceptability study) ───────────────────────────────────────────
def test_session_profile_fields_whitelisted(client, study_run):
    assert _session(client, study_run)["participant"] == "P1"
    for field in ("ai_experience", "aiact_familiarity", "seniority"):
        bad = client.post(
            "/api/v1/study/sessions",
            json={
                "role": "legal",
                "run_id": study_run,
                "ai_experience": "reviewer",
                "aiact_familiarity": "working",
                "seniority": "6to10",
                field: "nope",
            },
        )
        assert bad.status_code == 400, field
    missing = client.post(
        "/api/v1/study/sessions", json={"role": "legal", "run_id": study_run}
    )
    assert missing.status_code == 400  # profile is mandatory


def test_survey_persisted_and_exported(client, study_run):
    sid = _session(client, study_run)["session_id"]
    assert _survey(client, sid, comment="clear and fast").json() == {"recorded": True}
    rows = _survey_rows(client)
    assert len(rows) == 8
    assert {r["item"] for r in rows} == set(FULL_SURVEY)
    by_item = {r["item"]: r for r in rows}
    assert by_item["PU3"]["value"] == "5" and by_item["PEOU1"]["value"] == "5"
    assert by_item["PU1"]["role"] == "risk_manager"
    assert by_item["PU1"]["ai_experience"] == "reviewer"
    assert by_item["PU1"]["aiact_familiarity"] == "working"
    assert by_item["PU1"]["seniority"] == "6to10"
    assert by_item["PU1"]["comment"] == "clear and fast"


def test_survey_rejects_out_of_range_and_unknown_items(client, study_run):
    sid = _session(client, study_run)["session_id"]
    for bad in ({"PU1": 0}, {"PU1": 6}, {"PU9": 3}, {"PU1": "abc"}):
        assert _survey(client, sid, items=bad).status_code == 400, bad


def test_survey_resubmit_overwrites(client, study_run):
    sid = _session(client, study_run)["session_id"]
    _survey(client, sid)
    second = dict(FULL_SURVEY, PU1=2)
    assert _survey(client, sid, items=second).status_code == 200  # no 409
    rows = {r["item"]: r["value"] for r in _survey_rows(client)}
    assert rows["PU1"] == "2"


def test_survey_export_includes_sessions_without_survey(client, study_run):
    _session(client, study_run)  # never answers anything
    rows = _survey_rows(client)
    assert len(rows) == 8
    assert all(r["value"] == "" for r in rows)
    assert all(r["tasks_submitted"] == "0" for r in rows)


def test_survey_comment_truncated(client, study_run):
    sid = _session(client, study_run)["session_id"]
    _survey(client, sid, comment="x" * 900)
    assert len(_survey_rows(client)[0]["comment"]) == 500


def test_task_export_unchanged_by_survey(client, study_run):
    """The 7-column task CSV is frozen: the analyzer and the replication package rely on it."""
    sid = _session(client, study_run)["session_id"]
    _submit(client, sid, "T1", {"requirement_id": "R02"})
    _survey(client, sid)
    text = client.get("/api/v1/study/export.csv").text
    lines = text.strip().splitlines()
    assert lines[0] == "participant,role,task_id,completed,assisted,seconds,notes"
    assert "PU" not in text and "PEOU" not in text


def test_partial_session_exports_partial_rows(client, study_run):
    sid = _session(client, study_run)["session_id"]
    for task, answer in (("T1", {"requirement_id": "R02"}), ("T4", {"count": 3})):
        _submit(client, sid, task, answer)
    task_rows = client.get("/api/v1/study/export.csv").text.strip().splitlines()[1:]
    assert len(task_rows) == 2
    assert all(r["tasks_submitted"] == "2" for r in _survey_rows(client))


def test_survey_export_roundtrips_into_analyzer(client, study_run, tmp_path):
    sid = _session(client, study_run)["session_id"]
    _survey(client, sid)
    f = tmp_path / "survey.csv"
    f.write_text(client.get("/api/v1/study/export_survey.csv").text, encoding="utf-8")
    rows = analyze.load_survey_rows(f)
    matrix = analyze.survey_matrix(rows)
    assert matrix["P1"]["PU3"] == 5
    pu = analyze.construct_stats(matrix, analyze.PU_ITEMS)
    assert pu["mean"] == 4.25  # (4+4+5+4)/4
    profiles = analyze.profile_table(rows)
    assert len(profiles) == 1 and profiles[0]["seniority"] == "6to10"


# ── Pure-function edges ──────────────────────────────────────────────────────────────
def test_answer_key_ties_and_t4_readings():
    key = build_answer_key(
        {
            "requirements": [
                {"id": "R02", "name": "Cyber", "triage": "failed", "score": 0.4,
                 "score_ci_lower": 0.3, "score_ci_upper": 0.5, "fallback_benchmarks": []},
                {"id": "R12", "name": "Tox", "triage": "ok", "score": 0.4,
                 "score_ci_lower": 0.3, "score_ci_upper": 0.5, "fallback_benchmarks": ["rtp"]},
                {"id": "R01", "name": "Rob", "triage": "ok", "score": 1.0,
                 "score_ci_lower": 1.0, "score_ci_upper": 1.0, "fallback_benchmarks": []},
            ],
            "triage_counts": {"failed": 1, "fallback": 0, "ok": 2, "uncovered": 1, "na": 0},
            "requested_requirements": ["R01", "R02", "R12", "R09"],
            "trust_factor": {"score": 55.0, "band": "orange"},
            "harness_provenance": [{"benchmark_id": "rtp"}],
        }
    )
    assert set(key["weakest_ids"]) == {"R02", "R12"}  # tie at 0.40 + top triage row
    assert key["t4_accepted"] == [3, 4]  # scored count and requested count
    assert key["fallback_set"] == ["rtp"]


def test_validate_tolerance_edges():
    key = {"req_scores": {"R02": {"score": 0.4, "ci_lower": 0.3, "ci_upper": 0.5}},
           "weakest_primary": "R02", "trust": {"score": 62.0, "band": "orange"}}
    ok, _ = validate_answer(
        "T2", {"score": 0.405, "ci_lower": 0.3, "ci_upper": 0.5}, key, t1_answer_id="R02"
    )
    assert ok  # exactly at the +-0.005 boundary
    bad, _ = validate_answer(
        "T2", {"score": 0.406, "ci_lower": 0.3, "ci_upper": 0.5}, key, t1_answer_id="R02"
    )
    assert not bad
    ok7, _ = validate_answer("T7", {"score": 63, "band": "orange"}, key)
    assert ok7  # +-1 on the rounded gauge score
    bad7, _ = validate_answer("T7", {"score": 64, "band": "orange"}, key)
    assert not bad7
