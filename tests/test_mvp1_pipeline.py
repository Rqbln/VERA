"""Integration: evaluation graph writes snapshot (pilote mocked)."""

from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.graph.supervisor import run_evaluation_graph


class TestMvp1Pipeline(unittest.TestCase):
    @patch("raip.graph.supervisor.evaluate_pilote_items")
    def test_pipeline_writes_snapshot_and_cleans(self, mock_ev: object) -> None:
        mock_ev.return_value = (
            {
                "R02": {"advbench": [0.9]},
                "R11": {"decodingtrust_adult": [0.7]},
            },
            [
                {"agent": "pilote_v1", "benchmark_id": "advbench", "score": 0.9},
                {"agent": "pilote_v1", "benchmark_id": "decodingtrust_adult", "score": 0.7},
            ],
        )
        aid = f"test-{uuid.uuid4().hex[:12]}"
        out_dir = PROJECT_ROOT / "artifacts" / aid
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            state = run_evaluation_graph(
                {
                    "model_id": "ollama/stub",
                    "judge_model": "ollama/stub",
                    "temperature": 0.0,
                    "max_tokens": 32,
                    "seed": 0,
                    "benchmarks": ["advbench", "decodingtrust_adult"],
                    "complai_requirements": ["R02", "R11"],
                    "n_samples_per_benchmark": 5,
                    "bootstrap_n": 50,
                    "raw_outputs": [],
                },
                llm=None,
            )
            snap = out_dir / "eval_snapshot.json"
            snap.write_text(
                json.dumps(
                    {
                        "aggregate_scores": state.get("aggregate_scores"),
                        "n_raw": len(state.get("raw_outputs") or []),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            self.assertTrue(snap.is_file())
            data = json.loads(snap.read_text(encoding="utf-8"))
            self.assertIn("R02", data["aggregate_scores"])
            self.assertEqual(data["n_raw"], 2)
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
