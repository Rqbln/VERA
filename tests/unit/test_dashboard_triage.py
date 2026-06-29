from __future__ import annotations

from vera.dashboard.triage import (
    build_requirement_rows,
    is_pilote_run,
    triage_status,
)


def test_is_pilote_run_catalog():
    assert is_pilote_run("pilote_v1", None) is True
    assert is_pilote_run("mvp2-v1", None) is False


def test_triage_uncovered():
    status = triage_status(
        "R06",
        run_status="completed",
        requested=["R06", "R07"],
        complai_scores={},
        provenance=[],
        raw_outputs=[],
    )
    assert status == "uncovered"


def test_triage_fallback():
    status = triage_status(
        "R06",
        run_status="completed",
        requested=["R06"],
        complai_scores={
            "R06": {
                "score": 0.8,
                "contributing_benchmarks": ["mmlu"],
            }
        },
        provenance=[{"benchmark_id": "mmlu", "fallback": True}],
        raw_outputs=[],
    )
    assert status == "fallback"


def test_build_requirement_rows_sorts_failed_first():
    rows = build_requirement_rows(
        run_status="completed",
        requested=["R01", "R06"],
        complai_scores={
            "R01": {"score": 0.9, "score_ci_lower": 0.8, "score_ci_upper": 0.95},
            "R06": {"score": 0.2, "score_ci_lower": 0.1, "score_ci_upper": 0.3},
        },
        provenance=[],
        raw_outputs=[],
        filter_ids=["R01", "R06"],
    )
    assert rows[0]["id"] == "R06"
    assert rows[0]["triage"] == "failed"
    assert rows[1]["id"] == "R01"
