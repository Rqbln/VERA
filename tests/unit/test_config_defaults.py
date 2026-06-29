"""MVP2 default Ollama model in Settings."""

from __future__ import annotations

import contextlib
import os
import sys
import unittest
from collections.abc import Iterator
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pydantic_settings import SettingsConfigDict

from vera.config import Settings, get_settings

_ENV_KEYS = (
    "VERA_TARGET_MODEL",
    "VERA_JUDGE_MODEL",
    "OLLAMA_API_BASE",
    "MLFLOW_EXPERIMENT",
)


class _NoEnv(Settings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", populate_by_name=True)


@contextlib.contextmanager
def _without_vera_env() -> Iterator[None]:
    saved = {k: os.environ[k] for k in _ENV_KEYS if k in os.environ}
    try:
        for k in _ENV_KEYS:
            os.environ.pop(k, None)
        yield
    finally:
        for k in _ENV_KEYS:
            os.environ.pop(k, None)
        os.environ.update(saved)


class TestConfigDefaults(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_default_target_is_llama31_8b_q8(self) -> None:
        with _without_vera_env():
            s = _NoEnv()
        self.assertEqual(s.vera_target_model, "ollama/llama3.1:8b-instruct-q8_0")

    def test_default_mlflow_experiment_mvp2(self) -> None:
        with _without_vera_env():
            s = _NoEnv()
        self.assertEqual(s.mlflow_experiment, "vera-mvp2")

    def test_judge_defaults_to_llama_when_unset(self) -> None:
        with _without_vera_env():
            s = _NoEnv()
        self.assertEqual(s.effective_judge_model, "ollama/llama3.1:8b-instruct-q8_0")


if __name__ == "__main__":
    unittest.main()
