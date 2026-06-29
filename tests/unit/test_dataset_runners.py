"""R03–R05 dataset_scan runner in evaluation graph."""

from __future__ import annotations

import unittest

from vera.benchmarks.runners.dataset_scan import run_dataset_scan
from vera.graph.supervisor import aggregate_node


class TestDatasetRunners(unittest.TestCase):
    def test_quality_scan_scores_r03(self) -> None:
        corpus = ["Hello world", "Another safe line", "Third example"]
        samples, raw = run_dataset_scan(
            "dataset_quality_scan",
            {"corpus": corpus, "dataset_id": "ds-test"},
        )
        self.assertIn("R03", samples)
        self.assertGreater(samples["R03"]["dataset_quality_scan"][0], 0.0)
        self.assertEqual(raw[0]["requirement"], "R03")

    def test_empty_corpus_skipped(self) -> None:
        samples, raw = run_dataset_scan("dataset_privacy_scan", {"corpus": []})
        self.assertEqual(samples, {})
        self.assertEqual(raw[0]["status"], "skipped")

    def test_aggregate_r03_from_graph(self) -> None:
        state = {
            "complai_requirements": ["R03"],
            "req_benchmark_samples": {"R03": {"dataset_quality_scan": [0.8, 0.9]}},
            "raw_outputs": [],
            "seed": 1,
            "bootstrap_n": 50,
        }
        out = aggregate_node(state)  # type: ignore[arg-type]
        self.assertIn("R03", out["complai_scores"])


if __name__ == "__main__":
    unittest.main()
