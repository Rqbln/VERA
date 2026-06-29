from __future__ import annotations

import pytest

from vera.governance import proxy as proxy_mod
from vera.governance.kill_switch import set_kill
from vera.governance.modes import set_mode
from vera.governance.trust_stream import current_trust, record_signal
from vera.llm.client import CompletionResult


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    monkeypatch.setattr(
        proxy_mod.LLMClient,
        "completion",
        lambda self, **kw: CompletionResult(text="I cannot help.", raw={"model": kw.get("model")}),
    )
    set_kill(False)
    yield
    set_kill(False)


def test_shadow_allows_and_forwards():
    set_mode("ollama/proxy-test", "shadow")
    req = {"model": "ollama/proxy-test", "messages": [{"role": "user", "content": "hi"}]}
    status, body = proxy_mod.govern(req)
    assert status == 200
    assert body["choices"][0]["message"]["content"]
    assert "latency_ms" in body["vera_governance"]


def test_enforcement_blocks_on_kill_switch():
    set_mode("ollama/proxy-test", "enforcement")
    set_kill(True, "test block")
    req = {"model": "ollama/proxy-test", "messages": [{"role": "user", "content": "hi"}]}
    status, body = proxy_mod.govern(req)
    assert status == 503
    assert "blocked" in body["error"]


def test_streaming_trust_factor_aggregates():
    model = "ollama/trust-test"
    for cr, score in [("R02", 0.8), ("R12", 0.6), ("R05", 0.9), ("R01", 0.7)]:
        record_signal(model, cr, score)
    tf = current_trust(model)
    assert tf is not None
    assert 0 <= tf["score"] <= 100
    assert tf["band"] in ("green", "orange", "red")
