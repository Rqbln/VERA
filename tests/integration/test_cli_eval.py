"""CLI and API against real Redis (FastAPI TestClient + real store)."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from vera.api import main as api_main
from vera.cli.main import cli as cli_app
from vera.store.redis_run import RedisRunStore

MVP2_MODEL = "ollama/llama3.1:8b-instruct-q8_0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_YAML = PROJECT_ROOT / "examples" / "mvp2_integration.yaml"


@pytest.mark.integration
def test_cli_help(integration_stack: None) -> None:  # noqa: ARG001
    result = CliRunner().invoke(cli_app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout


@pytest.mark.integration
def test_cli_run_via_asgi_transport(integration_stack: None) -> None:  # noqa: ARG001
    """Same code path as `vera-eval run`: httpx POST /api/v1/runs on real FastAPI + Redis."""
    if not INTEGRATION_YAML.is_file():
        pytest.skip("mvp2_integration.yaml missing")

    body = yaml.safe_load(INTEGRATION_YAML.read_text(encoding="utf-8"))
    assert body["model_id"] == MVP2_MODEL

    # Même requête que `vera-eval run` (POST /api/v1/runs) — TestClient = stack ASGI réel
    client = TestClient(api_main.app)
    r = client.post("/api/v1/runs", json=body)
    assert r.status_code == 200, r.text
    run_id = r.json()["run_id"]
    assert r.json()["status"] == "queued"

    rec = RedisRunStore().get(run_id)
    assert rec is not None
    assert rec.model_id == MVP2_MODEL


@pytest.mark.integration
def test_api_get_run_real_redis(integration_stack: None) -> None:  # noqa: ARG001
    store = RedisRunStore()
    run_id = f"cli-{uuid.uuid4().hex[:8]}"
    store.create(run_id, MVP2_MODEL, {"benchmarks": ["self_disclosure_probes"]})
    store.update(run_id, status="completed", aggregate_scores={"R08": 0.5})

    client = TestClient(api_main.app)
    r = client.get(f"/api/v1/runs/{run_id}")
    assert r.status_code == 200
    assert r.json()["model_id"] == MVP2_MODEL
    assert r.json()["aggregate_scores"]["R08"] == 0.5
