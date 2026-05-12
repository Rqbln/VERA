"""build_benchmark_run_dict shape and COMPL-AI id mapping."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.schemas.benchmark_run import build_benchmark_run_dict
from raip.schemas.complai import ComplaiRequirementScore


class TestBenchmarkRunBuilder(unittest.TestCase):
    def test_build_contains_core_keys(self) -> None:
        cs_r02 = ComplaiRequirementScore(
            score=0.8,
            score_ci_lower=0.7,
            score_ci_upper=0.9,
            bootstrap_n=100,
            contributing_benchmarks=("advbench",),
            sample_count=3,
        )
        cs_r11 = ComplaiRequirementScore(
            score=0.7,
            score_ci_lower=0.6,
            score_ci_upper=0.8,
            bootstrap_n=100,
            contributing_benchmarks=("decodingtrust_adult",),
            sample_count=2,
        )
        doc = build_benchmark_run_dict(
            run_id="rid-1",
            model_name="m",
            provider="ollama",
            lifecycle_stage="inference",
            complai_scores={"R02": cs_r02, "R11": cs_r11},
            complai_requirements=["R02", "R11"],
            benchmarks=["stub"],
            seed=99,
            git_sha="abc",
        )
        self.assertEqual(doc["run_id"], "rid-1")
        self.assertEqual(doc["model"]["provider"], "ollama")
        self.assertEqual(doc["lifecycle_stage"], "inference")
        m_r02 = next(m for m in doc["metrics"] if m["requirement"] == "R02_cyber_resilience")
        self.assertEqual(m_r02["score"], 0.8)
        self.assertEqual(m_r02["score_ci_lower"], 0.7)
        self.assertEqual(m_r02["score_ci_upper"], 0.9)
        self.assertEqual(m_r02["bootstrap_n"], 100)
        self.assertIn("complai_requirements_requested", doc["reproducibility"])

    def test_r09_zero_emitted_in_metrics(self) -> None:
        cs = ComplaiRequirementScore(
            score=0.0,
            score_ci_lower=0.0,
            score_ci_upper=0.0,
            bootstrap_n=50,
            contributing_benchmarks=("watermark_kirchenbauer",),
            sample_count=1,
        )
        doc = build_benchmark_run_dict(
            run_id="r",
            model_name="m",
            provider="p",
            lifecycle_stage="inference",
            complai_scores={"R09": cs},
            complai_requirements=[],
            benchmarks=[],
            seed=1,
        )
        names = [m["name"] for m in doc["metrics"]]
        self.assertIn("score_R09", names)


if __name__ == "__main__":
    unittest.main()
