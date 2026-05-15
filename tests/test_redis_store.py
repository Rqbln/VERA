"""RedisRunStore behaviour with redis client mocked."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.config import Settings
from raip.store.redis_run import RedisRunStore


class TestRedisStore(unittest.TestCase):
    @patch("raip.store.redis_run.redis.from_url")
    def test_create_and_get_roundtrip(self, mock_from_url: MagicMock) -> None:
        backend: dict[str, str] = {}

        def fake_set(key: str, value: str, **kwargs: object) -> bool:
            backend[key] = value
            return True

        def fake_get(key: str) -> str | None:
            return backend.get(key)

        r = MagicMock()
        r.set.side_effect = fake_set
        r.get.side_effect = fake_get
        r.delete.return_value = 1
        mock_from_url.return_value = r

        s = Settings(redis_url="redis://localhost:9/0", redis_run_ttl_seconds=3600)
        store = RedisRunStore(s)
        store.create("rid", "ollama/m", {"k": 1})
        r.set.assert_called()
        _args, kwargs = r.set.call_args
        self.assertEqual(kwargs.get("ex"), 3600)
        rec = store.get("rid")
        self.assertIsNotNone(rec)
        assert rec is not None
        self.assertEqual(rec.model_id, "ollama/m")
        self.assertEqual(rec.status, "queued")
        payload = rec.payload
        self.assertEqual(payload["k"], 1)

        raw = backend[store._key("rid")]  # noqa: SLF001
        d = json.loads(raw)
        self.assertEqual(d["run_id"], "rid")

        self.assertTrue(store.delete("rid"))

    @patch("raip.store.redis_run.redis.from_url")
    def test_update_sets_aggregate_scores(self, mock_from_url: MagicMock) -> None:
        backend: dict[str, str] = {}

        def fake_set(key: str, value: str, **kwargs: object) -> bool:
            backend[key] = value
            return True

        def fake_get(key: str) -> str | None:
            return backend.get(key)

        r = MagicMock()
        r.set.side_effect = fake_set
        r.get.side_effect = fake_get
        mock_from_url.return_value = r

        s = Settings(redis_url="redis://localhost:9/0", redis_run_ttl_seconds=0)
        store = RedisRunStore(s)
        store.create("rid2", "m", {})
        store.update("rid2", aggregate_scores={"R02": 0.5}, complai_scores={"R02": {"score": 0.5}})
        rec2 = store.get("rid2")
        self.assertIsNotNone(rec2)
        assert rec2 is not None
        self.assertEqual(rec2.aggregate_scores, {"R02": 0.5})


if __name__ == "__main__":
    unittest.main()
