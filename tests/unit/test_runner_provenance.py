"""Fallback paths must set fallback=true explicitly."""

from __future__ import annotations

import unittest

from raip.benchmarks.runners.base import RunContext
from raip.benchmarks.runners.garak_runner import run_garak
from raip.benchmarks.runners.lm_eval_runner import run_lm_eval
from raip.llm.client import CompletionResult


class _StubLLM:
    def completion(self, **kwargs: object) -> CompletionResult:
        return CompletionResult(text="A", raw={})


class TestRunnerProvenance(unittest.TestCase):
    def test_lm_eval_fallback_flagged(self) -> None:
        ctx = RunContext(
            model_id="stub/model",
            judge_model="stub/judge",
            temperature=0.0,
            max_tokens=32,
            seed=1,
            n_samples_per_benchmark=1,
            llm=_StubLLM(),  # type: ignore[arg-type]
        )
        _, raw = run_lm_eval(ctx, "mmlu")
        if any(r.get("agent") == "hf_dynamic" for r in raw):
            fallbacks = [r for r in raw if r.get("fallback") is True]
            self.assertTrue(fallbacks, "hf_dynamic fallback must set fallback=true")

    def test_garak_fallback_flagged(self) -> None:
        ctx = RunContext(
            model_id="stub/model",
            judge_model="stub/judge",
            temperature=0.0,
            max_tokens=32,
            seed=1,
            n_samples_per_benchmark=1,
            llm=_StubLLM(),  # type: ignore[arg-type]
        )
        _, raw = run_garak(ctx, "decodingtrust_adv")
        if any("fallback" in r for r in raw):
            self.assertTrue(any(r.get("fallback") for r in raw))


if __name__ == "__main__":
    unittest.main()
