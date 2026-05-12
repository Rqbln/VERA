"""Celery eval task: MLflow + MinIO + Redis orchestration (mocked)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.schemas.complai import ComplaiRequirementScore
from raip.tasks.eval import run_benchmark_job


class TestEvalTask(unittest.TestCase):
    @patch("raip.tasks.eval.upload_bytes")
    @patch("raip.tasks.eval._git_sha", return_value="deadbeef")
    @patch("raip.tasks.eval.run_evaluation_graph")
    @patch("raip.tasks.eval.mlflow")
    @patch("raip.tasks.eval.RedisRunStore")
    def test_run_benchmark_job_success(
        self,
        mock_store_cls: MagicMock,
        mock_mlflow: MagicMock,
        mock_graph: MagicMock,
        _git: MagicMock,
        mock_upload: MagicMock,
    ) -> None:
        store = MagicMock()
        mock_store_cls.return_value = store

        cs = ComplaiRequirementScore(
            score=0.81,
            score_ci_lower=0.7,
            score_ci_upper=0.9,
            bootstrap_n=50,
            contributing_benchmarks=("advbench",),
            sample_count=3,
        )
        mock_graph.return_value = {
            "complai_scores": {"R02": cs},
            "aggregate_scores": {"R02": 0.81},
            "raw_outputs": [{"agent": "pilote_v1"}],
        }

        cm = MagicMock()
        cm.__enter__.return_value.info.run_id = "mlflow-run-1"
        cm.__exit__.return_value = None
        mock_mlflow.start_run.return_value = cm

        payload = {
            "model_id": "ollama/t",
            "benchmarks": ["advbench"],
            "complai_requirements": ["R02"],
            "config": {
                "temperature": 0.0,
                "max_tokens": 64,
                "n_samples_per_benchmark": 5,
                "seed": 7,
                "bootstrap_n": 50,
            },
            "governance": {},
        }

        out = run_benchmark_job.run("run-abc", payload)
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["aggregate_scores"]["R02"], 0.81)
        mock_upload.assert_called()
        store.update.assert_called()
        self.assertTrue(any("completed" in str(c) for c in store.update.call_args_list))


if __name__ == "__main__":
    unittest.main()
