"""Additional FastAPI routes with Redis mocked."""

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


class TestApiExtended(unittest.TestCase):
    def setUp(self) -> None:
        api_main._models_store.clear()

    @patch("raip.api.main.RedisRunStore")
    def test_get_run_card_404_when_missing(self, mock_store_cls: MagicMock) -> None:
        store = MagicMock()
        store.get.return_value = RunRecord(run_id="1", status="running", card_markdown=None)
        mock_store_cls.return_value = store
        client = TestClient(api_main.app)
        r = client.get("/api/v1/runs/1/card")
        self.assertEqual(r.status_code, 404)

    @patch("raip.api.main.RedisRunStore")
    def test_get_run_includes_scores(self, mock_store_cls: MagicMock) -> None:
        rec = RunRecord(
            run_id="1",
            status="completed",
            aggregate_scores={"R02": 0.5},
            complai_scores={"R02": {"score": 0.5}},
        )
        store = MagicMock()
        store.get.return_value = rec
        mock_store_cls.return_value = store
        client = TestClient(api_main.app)
        r = client.get("/api/v1/runs/1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["aggregate_scores"]["R02"], 0.5)

    @patch("boto3.client")
    @patch("raip.api.main.get_settings")
    def test_get_run_artifacts_lists_keys(
        self,
        mock_settings: MagicMock,
        mock_boto: MagicMock,
    ) -> None:
        mock_settings.return_value = MagicMock(
            minio_endpoint_url="http://localhost:9000",
            minio_access_key="k",
            minio_secret_key="s",
            minio_bucket="raip",
            minio_region="us-east-1",
        )
        paginator = MagicMock()

        def _pages(**_kwargs: object):
            yield {"Contents": [{"Key": "runs/r1/raw_outputs.jsonl"}]}

        paginator.paginate.side_effect = _pages
        c = MagicMock()
        c.get_paginator.return_value = paginator
        mock_boto.return_value = c

        with patch("raip.api.main.RedisRunStore") as mock_store_cls:
            store = MagicMock()
            store.get.return_value = RunRecord(run_id="r1", status="completed")
            mock_store_cls.return_value = store
            client = TestClient(api_main.app)
            r = client.get("/api/v1/runs/r1/artifacts")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any("raw_outputs" in u for u in r.json()["uris"]))

    @patch("raip.api.main.RedisRunStore")
    def test_get_run_artifacts_404_when_missing(self, mock_store_cls: MagicMock) -> None:
        store = MagicMock()
        store.get.return_value = None
        mock_store_cls.return_value = store
        client = TestClient(api_main.app)
        r = client.get("/api/v1/runs/missing/artifacts")
        self.assertEqual(r.status_code, 404)

    @patch("raip.api.main.RedisRunStore")
    def test_delete_run(self, mock_store_cls: MagicMock) -> None:
        store = MagicMock()
        store.get.return_value = RunRecord(run_id="x", status="completed")
        store.delete.return_value = True
        mock_store_cls.return_value = store
        client = TestClient(api_main.app)
        r = client.delete("/api/v1/runs/x")
        self.assertEqual(r.status_code, 200)
        store.delete.assert_called_once_with("x")

    def test_models_post_get(self) -> None:
        client = TestClient(api_main.app)
        r = client.post("/api/v1/models", json={"model_id": "ollama/m", "provider": "ollama"})
        self.assertEqual(r.status_code, 200)
        r2 = client.get("/api/v1/models")
        self.assertEqual(len(r2.json()["models"]), 1)


if __name__ == "__main__":
    unittest.main()
