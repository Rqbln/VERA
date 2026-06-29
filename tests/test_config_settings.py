"""Settings and derived properties (Pydantic Settings)."""

from __future__ import annotations

import contextlib
import os
import sys
import unittest
from collections.abc import Iterator
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pydantic_settings import SettingsConfigDict

from vera.config import Settings, get_settings


class IsolatedSettings(Settings):
    """Same as Settings but do not load repo `.env` (deterministic vs `.env` in working tree)."""

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        populate_by_name=True,
    )


_ENV_KEYS_TO_MASK = (
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "VERA_TARGET_MODEL",
    "VERA_JUDGE_MODEL",
    "OLLAMA_API_BASE",
)


@contextlib.contextmanager
def _without_vera_env() -> Iterator[None]:
    saved = {k: os.environ[k] for k in _ENV_KEYS_TO_MASK if k in os.environ}
    try:
        for k in _ENV_KEYS_TO_MASK:
            os.environ.pop(k, None)
        yield
    finally:
        for k in _ENV_KEYS_TO_MASK:
            os.environ.pop(k, None)
        os.environ.update(saved)


class TestConfigSettings(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_effective_judge_defaults_to_target(self) -> None:
        with _without_vera_env():
            s = IsolatedSettings(vera_target_model="ollama/foo", vera_judge_model=None)
        self.assertEqual(s.effective_judge_model, "ollama/foo")

    def test_effective_judge_override(self) -> None:
        with _without_vera_env():
            s = IsolatedSettings(
                vera_target_model="ollama/foo",
                vera_judge_model="ollama/bar",
            )
        self.assertEqual(s.effective_judge_model, "ollama/bar")

    def test_celery_broker_fallback(self) -> None:
        with _without_vera_env():
            s = IsolatedSettings(redis_url="redis://localhost:9/0", celery_broker_url=None)
        self.assertEqual(s.celery_broker, "redis://localhost:9/0")

    def test_get_settings_cached(self) -> None:
        get_settings.cache_clear()
        a = get_settings()
        b = get_settings()
        self.assertIs(a, b)


if __name__ == "__main__":
    unittest.main()
