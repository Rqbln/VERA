from __future__ import annotations

import pytest

from raip.benchmarks.runners import evaluate as E
from raip.governance.energy import start_energy_tracker, stop_energy_tracker
from raip.store.redis_hitl import RUBRICS, RedisHitlStore
from raip.store.redis_run import RunRecord


# ── S1: RAIP_REQUIRE_NATIVE ──────────────────────────────────────────────────────────
def test_require_native_raises_on_fallback(monkeypatch):
    monkeypatch.setenv("RAIP_REQUIRE_NATIVE", "1")
    # a benchmark whose runner falls back (lm_eval impl) -> raise
    monkeypatch.setattr(
        E, "get_benchmark_entry", lambda bid: {"implementation": "lm_eval", "complai": "R06"}
    )
    monkeypatch.setattr(
        E,
        "run_lm_eval",
        lambda ctx, bid: (
            {},
            [{"benchmark_id": bid, "fallback": True, "fallback_reason": "lm_eval not installed"}],
        ),
    )
    with pytest.raises(E.NativeHarnessRequired):
        E.evaluate_benchmarks(
            model_id="ollama/x", judge_model="ollama/x", benchmarks=["mmlu"],
            n_samples_per_benchmark=2, temperature=0.0, max_tokens=16, seed=42, llm=None,
        )


def test_garak_fallback_allowed_under_require_native(monkeypatch):
    monkeypatch.setenv("RAIP_REQUIRE_NATIVE", "1")
    monkeypatch.setattr(
        E, "get_benchmark_entry", lambda bid: {"implementation": "garak", "complai": "R02"}
    )
    monkeypatch.setattr(
        E, "run_garak", lambda ctx, bid: ({}, [{"benchmark_id": bid, "fallback": True}])
    )
    # garak is in the native-allow set -> no raise
    E.evaluate_benchmarks(
        model_id="ollama/x", judge_model="ollama/x", benchmarks=["decodingtrust_adv"],
        n_samples_per_benchmark=2, temperature=0.0, max_tokens=16, seed=42, llm=None,
    )


# ── S3: energy tracking ──────────────────────────────────────────────────────────────
def test_energy_tracker_returns_report():
    rep = stop_energy_tracker(start_energy_tracker("test"), "run-1")
    assert "kwh" in rep and "source" in rep  # codecarbon when installed, else 'unavailable'


# ── S5: HITL rubric ──────────────────────────────────────────────────────────────────
def test_hitl_rubric_mean_is_likert():
    s = RedisHitlStore()
    t = s.create(run_id="rub-run", requirement="N01")
    reviewed = s.submit_review(t.task_id, reviewer="r", criteria={"a": 4, "b": 5, "c": 3, "d": 4})
    assert reviewed.likert_score == 4  # round(mean(4,5,3,4)=4.0)
    assert reviewed.criteria == {"a": 4, "b": 5, "c": 3, "d": 4}
    assert set(RUBRICS) == {"N01", "N02"}
    s._r.delete(s._key(t.task_id))


# ── S4: non-measurable summary reflects real data ────────────────────────────────────
def test_non_measurable_slots_reflect_real_state():
    from raip.api.dashboard_routes import _non_measurable_slots
    from raip.schemas.declarative_forms import DeclarativeFormBody, RedisFormStore

    rec = RunRecord(run_id="nm-run", status="completed",
                    energy={"kwh": 0.0012, "co2eq_kg": 0.0005, "source": "codecarbon"})
    hitl = RedisHitlStore()
    task = hitl.create(run_id="nm-run", requirement="N01")
    hitl.submit_review(task.task_id, reviewer="r", criteria={"x": 4, "y": 4})
    RedisFormStore().put(
        "nm-run", "N05", DeclarativeFormBody(fields={"summary": "ok"}, completed=True)
    )
    try:
        slots = _non_measurable_slots(rec)
        assert slots["n01"]["status"] == "reviewed" and slots["n01"]["avg_likert"] == 4.0
        assert slots["n03"]["status"] == "measured" and slots["n03"]["kwh"] == 0.0012
        assert slots["n05"]["status"] == "completed"
    finally:
        hitl._r.delete(hitl._key(task.task_id))
