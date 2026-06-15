from __future__ import annotations

import pytest

from raip.store.redis_run import RedisRunStore
from raip.tasks.monitor import compute_drift

MODEL = "ollama/drift-test-model"


@pytest.fixture
def store():
    s = RedisRunStore()
    created: list[str] = []

    def _make(run_id: str, score: float) -> None:
        s.create(run_id, MODEL, {})
        s.update(
            run_id,
            status="completed",
            catalog_version="mvp2-v1",
            trust_factor={"score": score, "band": "green", "components": {}},
        )
        created.append(run_id)

    yield s, _make, created
    for rid in created:
        s.delete(rid)


def test_insufficient_history(store):
    s, make, _ = store
    make("drift-only-1", 80.0)
    out = compute_drift(MODEL, store=s)
    assert out["available"] is False
    assert out["reason"] == "insufficient_history"


def test_drift_detected_on_regression(store):
    s, make, _ = store
    # Baseline of stable high scores, then a sharp drop in the latest run.
    for i, sc in enumerate([85.0, 86.0, 84.0]):
        make(f"drift-base-{i}", sc)
    make("drift-latest", 40.0)  # newest (list_runs is newest-first)
    out = compute_drift(MODEL, store=s, baseline_n=3, threshold=0.15)
    assert out["available"] is True
    assert out["drift"] is True
    assert out["direction"] == "regression"


def test_no_drift_when_stable(store):
    s, make, _ = store
    for i, sc in enumerate([80.0, 81.0, 79.0, 80.0]):
        make(f"stable-{i}", sc)
    out = compute_drift(MODEL, store=s, baseline_n=3, threshold=0.15)
    assert out["available"] is True
    assert out["drift"] is False
