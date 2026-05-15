"""CLI raip-eval."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import yaml
from typer.testing import CliRunner

from raip.cli.main import cli


def test_cli_version() -> None:
    runner = CliRunner()
    r = runner.invoke(cli, ["version"])
    assert r.exit_code == 0


def test_cli_run_posts_yaml() -> None:
    body = {
        "model_id": "ollama/t",
        "benchmarks": ["mmlu"],
        "complai_requirements": ["R06"],
        "config": {"seed": 1},
        "governance": {},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(body, f)
        path = f.name
    try:
        runner = CliRunner()
        mock_resp = MagicMock()
        mock_resp.text = '{"run_id":"u1","status":"queued"}'
        mock_resp.raise_for_status = MagicMock()
        with patch("raip.cli.main.httpx.Client") as mock_client_cls:
            inner = MagicMock()
            inner.post.return_value = mock_resp
            inst = MagicMock()
            inst.__enter__.return_value = inner
            inst.__exit__.return_value = None
            mock_client_cls.return_value = inst
            r = runner.invoke(cli, ["run", path, "--api-url", "http://localhost:8000"])
        assert r.exit_code == 0
    finally:
        Path(path).unlink(missing_ok=True)
