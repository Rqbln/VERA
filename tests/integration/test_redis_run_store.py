"""RedisRunStore against live Redis."""

from __future__ import annotations

import uuid

import pytest

from raip.store.redis_run import RedisRunStore


@pytest.mark.integration
def test_create_get_update_delete(integration_stack: None) -> None:  # noqa: ARG001
    store = RedisRunStore()
    run_id = f"test-{uuid.uuid4().hex[:12]}"
    store.create(run_id, "ollama/llama3.1:8b-instruct-q8_0", {"benchmarks": ["mmlu"]})
    rec = store.get(run_id)
    assert rec is not None
    assert rec.status == "queued"
    store.update(run_id, status="running", aggregate_scores={"R06": 0.5})
    rec2 = store.get(run_id)
    assert rec2 is not None
    assert rec2.status == "running"
    assert rec2.aggregate_scores == {"R06": 0.5}
    store.delete(run_id)
    assert store.get(run_id) is None
