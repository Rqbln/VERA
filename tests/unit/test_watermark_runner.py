"""R09 watermark statistical vs NA modes."""

from __future__ import annotations

import os
import unittest

from vera.benchmarks.runners.base import RunContext
from vera.benchmarks.runners.watermark import run_watermark, run_watermark_na
from vera.llm.client import CompletionResult


class _StubLLM:
    def completion(self, **kwargs: object) -> CompletionResult:
        return CompletionResult(
            text="the and of the system is working well",
            raw={},
        )


class TestWatermarkRunner(unittest.TestCase):
    def test_na_excluded_from_samples(self) -> None:
        samples, raw = run_watermark_na("watermark_kirchenbauer")
        self.assertEqual(samples, {})
        self.assertEqual(raw[0]["status"], "NA")

    def test_statistical_returns_tpr(self) -> None:
        prev = os.environ.get("VERA_WATERMARK_MODE")
        os.environ["VERA_WATERMARK_MODE"] = "statistical"
        try:
            ctx = RunContext(
                model_id="stub/model",
                judge_model="stub/judge",
                temperature=0.0,
                max_tokens=64,
                seed=1,
                n_samples_per_benchmark=2,
                llm=_StubLLM(),  # type: ignore[arg-type]
            )
            samples, raw = run_watermark(ctx, "watermark_kirchenbauer")
            self.assertIn("R09", samples)
            tpr_rows = [r for r in raw if "TPR" in r]
            self.assertTrue(tpr_rows)
            self.assertGreaterEqual(tpr_rows[0]["TPR"], 0.0)
            self.assertLessEqual(tpr_rows[0]["TPR"], 1.0)
        finally:
            if prev is None:
                os.environ.pop("VERA_WATERMARK_MODE", None)
            else:
                os.environ["VERA_WATERMARK_MODE"] = prev


if __name__ == "__main__":
    unittest.main()
