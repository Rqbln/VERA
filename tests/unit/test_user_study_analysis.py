"""RQ1 user-study aggregation: completion, assisted, timing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "analyze_user_study", ROOT / "scripts" / "analyze_user_study.py"
)
mod = importlib.util.module_from_spec(_spec)
sys.modules["analyze_user_study"] = mod
_spec.loader.exec_module(mod)

CSV = """participant,role,task_id,completed,assisted,seconds,notes
P1,risk officer,T1,yes,no,30,
P2,compliance,T1,yes,yes,60,
P3,legal,T1,no,no,,gave up
P1,risk officer,T2,yes,no,20,
P2,compliance,T2,yes,no,40,
"""


def _rows(tmp_path):
    f = tmp_path / "sessions.csv"
    f.write_text(CSV, encoding="utf-8")
    return mod.load_rows(f)


def test_completion_and_assist_rates(tmp_path):
    summary = mod.summarize(_rows(tmp_path))
    t1 = summary["T1"]
    assert t1["n"] == 3 and t1["completed"] == 2 and t1["unassisted"] == 1


def test_timing_median_over_completed_only(tmp_path):
    summary = mod.summarize(_rows(tmp_path))
    assert summary["T1"]["median_s"] == 45.0  # median of 30 and 60; failed row excluded
    assert summary["T2"]["median_s"] == 30.0


def _survey_csv(matrix, tasks="8", profiles=None):
    """Build a survey.csv from {participant: {item: value|''}}."""
    head = ("participant,role,ai_experience,aiact_familiarity,seniority,"
            "locale,tasks_submitted,item,value,comment\n")
    profiles = profiles or {}
    body = ""
    for pid, answers in matrix.items():
        role, exp, act, sen = profiles.get(pid, ("risk_manager", "reviewer", "working", "6to10"))
        for item in mod.SURVEY_ITEMS:
            body += (f"{pid},{role},{exp},{act},{sen},en,{tasks},{item},"
                     f"{answers.get(item, '')},\n")
    return head + body


def _survey_rows(tmp_path, matrix, **kw):
    f = tmp_path / "survey.csv"
    f.write_text(_survey_csv(matrix, **kw), encoding="utf-8")
    return mod.load_survey_rows(f)


def test_cronbach_alpha_known_matrix(tmp_path):
    # 4 items x 5 participants; alpha computed by hand from the same formula.
    raw = {
        "P1": {"PU1": 5, "PU2": 4, "PU3": 5, "PU4": 4},
        "P2": {"PU1": 4, "PU2": 4, "PU3": 4, "PU4": 3},
        "P3": {"PU1": 3, "PU2": 2, "PU3": 3, "PU4": 2},
        "P4": {"PU1": 5, "PU2": 5, "PU3": 4, "PU4": 5},
        "P5": {"PU1": 2, "PU2": 3, "PU3": 2, "PU4": 3},
    }
    import statistics as st
    items = mod.PU_ITEMS
    iv = sum(st.variance([raw[p][i] for p in raw]) for i in items)
    tv = st.variance([sum(raw[p][i] for i in items) for p in raw])
    expected = (4 / 3) * (1 - iv / tv)
    assert abs(mod.cronbach_alpha(raw, items) - expected) < 1e-9


def test_cronbach_alpha_none_when_too_few():
    matrix = {"P1": dict.fromkeys(mod.PU_ITEMS, 4), "P2": dict.fromkeys(mod.PU_ITEMS, 3)}
    assert mod.cronbach_alpha(matrix, mod.PU_ITEMS) is None


def test_cronbach_alpha_none_on_zero_variance():
    matrix = {p: dict.fromkeys(mod.PU_ITEMS, 4) for p in ("P1", "P2", "P3")}
    assert mod.cronbach_alpha(matrix, mod.PU_ITEMS) is None  # no ZeroDivisionError


def test_item_stats_mean_sd_median(tmp_path):
    rows = _survey_rows(tmp_path, {
        "P1": {"PU1": 5}, "P2": {"PU1": 3}, "P3": {"PU1": 4},
    })
    stats = mod.item_stats(mod.survey_matrix(rows), ("PU1",))["PU1"]
    assert stats["n"] == 3 and stats["mean"] == 4.0 and stats["median"] == 4
    assert abs(stats["sd"] - 1.0) < 1e-9


def test_survey_matrix_skips_blank_values(tmp_path):
    rows = _survey_rows(tmp_path, {"P1": {"PU1": 4}})  # the other 7 items are blank
    matrix = mod.survey_matrix(rows)
    assert matrix["P1"] == {"PU1": 4}


def test_profile_table_one_row_per_participant(tmp_path):
    rows = _survey_rows(tmp_path, {"P1": {"PU1": 4}, "P2": {"PU1": 5}})
    profiles = mod.profile_table(rows)
    assert [p["participant"] for p in profiles] == ["P1", "P2"]
    assert profiles[0]["seniority"] == "6to10"


def test_straight_liners_flagged(tmp_path):
    rows = _survey_rows(tmp_path, {
        "P1": dict.fromkeys(mod.SURVEY_ITEMS, 3),
        "P2": {**dict.fromkeys(mod.SURVEY_ITEMS, 3), "PU1": 5},
    })
    assert mod.straight_liners(mod.survey_matrix(rows)) == ["P1"]


def test_construct_stats_needs_every_item(tmp_path):
    rows = _survey_rows(tmp_path, {
        "P1": dict.fromkeys(mod.PU_ITEMS, 4),
        "P2": {"PU1": 5},  # incomplete -> excluded from the construct
    })
    stats = mod.construct_stats(mod.survey_matrix(rows), mod.PU_ITEMS)
    assert stats["n"] == 1 and stats["mean"] == 4.0


def test_existing_summarize_unchanged(tmp_path):
    """The task-CSV contract must stay byte-compatible with the frozen export."""
    summary = mod.summarize(_rows(tmp_path))
    assert summary["T1"]["n"] == 3 and summary["T1"]["median_s"] == 45.0


def test_tasks_without_data_are_omitted(tmp_path):
    summary = mod.summarize(_rows(tmp_path))
    assert "T3" not in summary
