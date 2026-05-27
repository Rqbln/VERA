"""LangGraph aggregate node without mocks."""

from __future__ import annotations

import unittest

from raip.graph.supervisor import aggregate_node


class TestGraphAggregate(unittest.TestCase):
    def test_aggregate_computes_scores(self) -> None:
        state = {
            "complai_requirements": ["R08"],
            "req_benchmark_samples": {"R08": {"self_disclosure_probes": [1.0, 0.0, 1.0]}},
            "raw_outputs": [],
            "seed": 42,
            "bootstrap_n": 100,
        }
        out = aggregate_node(state)  # type: ignore[arg-type]
        self.assertIn("R08", out["complai_scores"])
        self.assertGreaterEqual(out["complai_scores"]["R08"].score, 0.0)

    def test_aggregate_r03(self) -> None:
        state = {
            "complai_requirements": ["R03"],
            "req_benchmark_samples": {"R03": {"dataset_quality_scan": [0.75]}},
            "raw_outputs": [],
            "seed": 42,
            "bootstrap_n": 50,
        }
        out = aggregate_node(state)  # type: ignore[arg-type]
        self.assertIn("R03", out["complai_scores"])

    def test_r09_na_skipped(self) -> None:
        state = {
            "complai_requirements": ["R09"],
            "req_benchmark_samples": {},
            "raw_outputs": [
                {
                    "requirement": "R09",
                    "status": "NA",
                    "benchmark_id": "watermark_kirchenbauer",
                }
            ],
            "seed": 42,
            "bootstrap_n": 50,
        }
        out = aggregate_node(state)  # type: ignore[arg-type]
        self.assertNotIn("R09", out.get("complai_scores", {}))


if __name__ == "__main__":
    unittest.main()
