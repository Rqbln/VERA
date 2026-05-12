"""FastAPI routes with Redis and Celery mocked."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi.testclient import TestClient

from raip.api import main as api_main
from raip.store.redis_run import RunRecord


class TestApiFastapi(unittest.TestCase):
    def setUp(self) -> None:
        api_main._models_store.clear()

    @patch("raip.api.main.run_benchmark_job")
    @patch("raip.api.main.RedisRunStore")
    def test_post_runs_queues_and_returns_id(
        self,
        mock_store_cls: MagicMock,
        mock_job: MagicMock,
    ) -> None:
        store = MagicMock()
        mock_store_cls.return_value = store
        delay = MagicMock()
        mock_job.delay = delay

        client = TestClient(api_main.app)
        r = client.post(
            "/api/v1/runs",
            json={
                "model_id": "ollama/t",
                "benchmarks": ["stub_cyber"],
                "complai_requirements": ["R02"],
                "config": {"seed": 1},
                "governance": {"owner": "x"},
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("run_id", data)
        self.assertEqual(data["status"], "queued")
        store.create.assert_called_once()
        delay.assert_called_once()

    @patch("raip.api.main.RedisRunStore")
    def test_get_run_404(self, mock_store_cls: MagicMock) -> None:
        store = MagicMock()
        store.get.return_value = None
        mock_store_cls.return_value = store
        client = TestClient(api_main.app)
        r = client.get("/api/v1/runs/unknown")
        self.assertEqual(r.status_code, 404)

    @patch("raip.api.main.RedisRunStore")
    def test_get_run_card(self, mock_store_cls: MagicMock) -> None:
        rec = RunRecord(
            run_id="1",
            status="completed",
            card_markdown="# Card",
        )
        store = MagicMock()
        store.get.return_value = rec
        mock_store_cls.return_value = store
        client = TestClient(api_main.app)
        r = client.get("/api/v1/runs/1/card")
        self.assertEqual(r.status_code, 200)
        self.assertIn("markdown", r.json())

    def test_list_benchmarks(self) -> None:
        client = TestClient(api_main.app)
        r = client.get("/api/v1/benchmarks")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json()["benchmarks"]), 1)


if __name__ == "__main__":
    unittest.main()
