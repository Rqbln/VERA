"""LangGraph supervisor: aggregation + pilote pipeline (mocked LLM / mocked items)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.graph.supervisor import aggregate_node, run_evaluation_graph
from raip.schemas.complai import ComplaiRequirementScore


class TestGraphSupervisor(unittest.TestCase):
    def test_aggregate_weighted_bootstrap(self) -> None:
        out = aggregate_node(
            {
                "seed": 42,
                "bootstrap_n": 200,
                "complai_requirements": ["R02"],
                "req_benchmark_samples": {"R02": {"advbench": [1.0, 0.8, 0.9, 0.85]}},
            }
        )
        scores = out["complai_scores"]
        self.assertIn("R02", scores)
        self.assertIsInstance(scores["R02"], ComplaiRequirementScore)
        self.assertGreater(scores["R02"].score, 0.5)
        self.assertLessEqual(scores["R02"].score_ci_lower, scores["R02"].score)

    @patch("raip.graph.supervisor.evaluate_pilote_items")
    def test_run_evaluation_graph_patched_pilote(self, mock_ev: object) -> None:
        mock_ev.return_value = (
            {
                "R02": {"advbench": [0.9, 0.9]},
                "R06": {"mmlu": [1.0, 0.0]},
            },
            [{"agent": "pilote_v1", "score": 0.9}],
        )
        state = run_evaluation_graph(
            {
                "model_id": "ollama/t",
                "judge_model": "ollama/t",
                "temperature": 0.0,
                "max_tokens": 64,
                "seed": 1,
                "benchmarks": ["advbench", "mmlu"],
                "complai_requirements": ["R02", "R06"],
                "n_samples_per_benchmark": 10,
                "bootstrap_n": 100,
                "raw_outputs": [],
            },
            llm=None,  # unused when pilote is mocked
        )
        self.assertIn("R02", state["aggregate_scores"])
        self.assertIn("R06", state["aggregate_scores"])
        self.assertEqual(len(state.get("raw_outputs") or []), 1)


if __name__ == "__main__":
    unittest.main()
