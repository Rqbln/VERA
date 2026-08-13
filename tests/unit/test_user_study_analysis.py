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


# ── Two-condition quiz analysis ──────────────────────────────────────────────────────
def _quiz_row(pid, pair, cond, completed, seconds="10", verdict="correct", arm="alpha_first"):
    return {
        "participant": pid, "role": "ai_researcher", "ai_experience": "reviewer",
        "aiact_familiarity": "working", "seniority": "6to10", "locale": "en",
        "arm": arm, "condition": cond, "set": "A" if cond == "baseline" else "B",
        "pair": pair, "item": f"Q{pair}{'A' if cond == 'baseline' else 'B'}",
        "completed": completed, "verdict": verdict,
        "client_seconds": seconds, "server_seconds": seconds,
    }


def test_wilcoxon_exact_hand_checked():
    # All-positive deltas [1,2,3]: W+=6 of 6, two-sided p = 2/8.
    r = mod.wilcoxon_exact([1, 2, 3])
    assert r["n"] == 3 and abs(r["p"] - 0.25) < 1e-12
    # Mixed [2,-1,3]: W+=5, p = P(W>=5)+P(W<=1) = 2/8 + 2/8.
    r = mod.wilcoxon_exact([2, -1, 3])
    assert abs(r["p"] - 0.5) < 1e-12
    # Zeros are dropped: only one non-zero delta left -> p = 1.
    r = mod.wilcoxon_exact([0, 1])
    assert r["n"] == 1 and abs(r["p"] - 1.0) < 1e-12
    # Ties get average ranks: [1,1] both positive -> W+=3 of 3, p = 2/4.
    r = mod.wilcoxon_exact([1, 1])
    assert abs(r["p"] - 0.5) < 1e-12
    # Empty after dropping zeros.
    assert mod.wilcoxon_exact([0, 0])["p"] == 1.0


def test_mcnemar_exact_hand_checked():
    assert abs(mod.mcnemar_exact(0, 5) - 0.0625) < 1e-12  # 2 * 1/32
    assert mod.mcnemar_exact(2, 2) == 1.0  # capped
    assert mod.mcnemar_exact(0, 0) == 1.0


def test_paired_quality_and_time():
    rows = []
    # P1: baseline 1/2 correct, vera 2/2; times 30/40 vs 10/20.
    rows.append(_quiz_row("P1", "1", "baseline", "yes", "30"))
    rows.append(_quiz_row("P1", "1", "vera", "yes", "10"))
    rows.append(_quiz_row("P1", "2", "baseline", "no", "40"))
    rows.append(_quiz_row("P1", "2", "vera", "yes", "20"))
    # P2: pair 1 only in baseline -> not paired; pair 2 paired but gave up in baseline.
    rows.append(_quiz_row("P2", "1", "baseline", "yes", "15"))
    rows.append(_quiz_row("P2", "2", "baseline", "no", "300", verdict="timeout"))
    rows.append(_quiz_row("P2", "2", "vera", "yes", "25"))

    quality = mod.paired_quality(rows)
    assert quality["P1"] == {"pairs": 2, "baseline": 1, "vera": 2, "delta": 1}
    assert quality["P2"]["pairs"] == 1  # only pair 2 is answered in both conditions

    time = mod.paired_time(rows)
    assert time["P1"]["baseline"] == 35 and time["P1"]["vera"] == 15
    assert "P2" not in time  # its only shared pair is censored by the timeout


def test_per_pair_table_mcnemar_counts():
    rows = []
    for pid, base_ok, vera_ok in (("P1", "no", "yes"), ("P2", "no", "yes"), ("P3", "yes", "yes")):
        rows.append(_quiz_row(pid, "1", "baseline", base_ok))
        rows.append(_quiz_row(pid, "1", "vera", vera_ok))
    table = mod.per_pair_table(rows)
    s = table["1"]
    assert s["n"] == 3 and s["baseline"] == 1 and s["vera"] == 3
    assert s["b"] == 0 and s["c"] == 2
    assert abs(s["p"] - 0.5) < 1e-12  # 2 * (1/4)


def test_latex_quiz_emitters_shapes():
    rows = [
        _quiz_row("P1", "1", "baseline", "yes", "30"),
        _quiz_row("P1", "1", "vera", "yes", "12"),
    ]
    pair_lines = mod.latex_pair_rows(mod.per_pair_table(rows))
    assert pair_lines and pair_lines[0].startswith("    1 & ")
    paired = mod.latex_paired_rows(mod.paired_quality(rows), mod.paired_time(rows))
    assert paired == ["    P1 & 1/1 & 1/1 & 30 & 12 \\\\"]
