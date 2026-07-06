"""N01/N02 HITL integration with the eval task: auto-queue at completion, card slots."""

from __future__ import annotations

from uuid import uuid4

from vera.artifacts.model_card import render_model_card
from vera.config import Settings
from vera.schemas.run_payload import RunCreateRequest
from vera.store.redis_hitl import RedisHitlStore
from vera.tasks.eval import (
    _ensure_hitl_tasks,
    _hitl_card_slots,
    _model_card_context,
)


def _cleanup(store: RedisHitlStore, run_id: str) -> None:
    for t in store.list(run_id=run_id):
        store._r.delete(store._key(t.task_id))


def test_ensure_hitl_tasks_creates_one_n01_and_one_n02():
    run_id = f"hitl-auto-{uuid4().hex[:8]}"
    store = RedisHitlStore()
    try:
        tasks = _ensure_hitl_tasks(run_id, Settings())
        assert sorted(t.requirement for t in tasks) == ["N01", "N02"]
        assert all(t.status == "pending" for t in tasks)
    finally:
        _cleanup(store, run_id)


def test_ensure_hitl_tasks_idempotent():
    run_id = f"hitl-idem-{uuid4().hex[:8]}"
    store = RedisHitlStore()
    try:
        _ensure_hitl_tasks(run_id, Settings())
        tasks = _ensure_hitl_tasks(run_id, Settings())  # second call must not duplicate
        assert len(tasks) == 2
        assert sorted(t.requirement for t in tasks) == ["N01", "N02"]
    finally:
        _cleanup(store, run_id)


def test_ensure_hitl_tasks_disabled_by_flag():
    run_id = f"hitl-off-{uuid4().hex[:8]}"
    store = RedisHitlStore()
    try:
        tasks = _ensure_hitl_tasks(run_id, Settings(vera_hitl_autocreate=False))
        assert tasks == []
        assert store.list(run_id=run_id) == []
    finally:
        _cleanup(store, run_id)


def test_hitl_card_slots_queued_then_reviewed():
    run_id = f"hitl-slots-{uuid4().hex[:8]}"
    store = RedisHitlStore()
    try:
        tasks = _ensure_hitl_tasks(run_id, Settings())
        slots = _hitl_card_slots(tasks)
        assert slots["n01"] == {
            "status": "queued",
            "reviewed": 0,
            "queued": 1,
            "avg_likert": None,
            "ref": "HITL review queue",
        }
        n01 = next(t for t in tasks if t.requirement == "N01")
        store.submit_review(
            n01.task_id,
            reviewer="r",
            criteria={"faithfulness": 4, "completeness": 5, "clarity": 3, "actionability": 4},
        )
        slots = _hitl_card_slots(store.list(run_id=run_id))
        assert slots["n01"]["status"] == "reviewed"
        assert slots["n01"]["reviewed"] == 1
        assert slots["n01"]["avg_likert"] == 4.0
        assert slots["n02"]["status"] == "queued"
    finally:
        _cleanup(store, run_id)


def test_model_card_renders_live_hitl_state_without_mvp3():
    run_id = f"hitl-card-{uuid4().hex[:8]}"
    store = RedisHitlStore()
    try:
        tasks = _ensure_hitl_tasks(run_id, Settings())
        md = render_model_card(
            _model_card_context(
                run_id=run_id,
                model_id="ollama/llama3.1:8b",
                complai_scores={},
                req=RunCreateRequest(model_id="ollama/llama3.1:8b"),
                git_sha="deadbeef",
                catalog_version="v2",
                hitl_slots=_hitl_card_slots(tasks),
            )
        )
        assert "queued (0/1 reviews)" in md
        assert "HITL review queue" in md
        assert "MVP3" not in md
    finally:
        _cleanup(store, run_id)
