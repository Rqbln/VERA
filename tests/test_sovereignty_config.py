"""Souveraineté par défaut : pas de champ « provider propriétaire » dans Settings."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pydantic_settings import SettingsConfigDict

from raip.config import Settings  # noqa: E402


class _NoEnvFile(Settings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", populate_by_name=True)


def test_settings_has_no_hardcoded_proprietary_api_fields() -> None:
    names = set(Settings.model_fields.keys())
    assert not any("openai" in n for n in names)
    assert not any("anthropic" in n for n in names)
    assert "ollama_api_base" in names
    assert "raip_target_model" in names


def test_default_target_is_ollama_prefixed() -> None:
    s = _NoEnvFile()
    assert str(s.raip_target_model).startswith("ollama/")


