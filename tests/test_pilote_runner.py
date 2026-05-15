"""pilote_v1 runner with mocked LLM."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.benchmarks.pilote_v1.runner import evaluate_pilote_items
from raip.llm.client import CompletionResult


class _LLM:
    def completion(self, **kwargs: object) -> CompletionResult:
        return CompletionResult(text="B", raw={})


class TestPiloteRunner(unittest.TestCase):
    def test_evaluate_adds_r09_when_watermark_requested(self) -> None:
        samples, raw = evaluate_pilote_items(
            model_id="ollama/t",
            benchmarks=["watermark_kirchenbauer"],
            n_samples_per_benchmark=5,
            temperature=0.0,
            max_tokens=32,
            seed=1,
            llm=_LLM(),  # type: ignore[arg-type]
        )
        self.assertIn("R09", samples)
        self.assertEqual(samples["R09"]["watermark_kirchenbauer"], [0.0])
        self.assertTrue(any(x.get("kind") == "watermark_na" for x in raw))


if __name__ == "__main__":
    unittest.main()
