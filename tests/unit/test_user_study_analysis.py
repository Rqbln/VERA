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


def test_tasks_without_data_are_omitted(tmp_path):
    summary = mod.summarize(_rows(tmp_path))
    assert "T3" not in summary
