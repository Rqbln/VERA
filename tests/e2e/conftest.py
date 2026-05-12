"""E2E fixtures: Celery eager + optional stack checks."""

from __future__ import annotations

import os
import urllib.error
import urllib.request

import pytest

from raip.celery_app import celery_app


@pytest.fixture
def celery_eager() -> None:
    prev = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = prev


def _require_e2e_flag() -> None:
    if os.environ.get("RAIP_E2E_OLLAMA") != "1":
        pytest.skip("Set RAIP_E2E_OLLAMA=1 on the self-hosted runner to execute E2E.")


def _require_redis() -> None:
    try:
        import redis

        r = redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
        r.ping()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Redis unavailable: {exc}")


def _require_ollama_http() -> None:
    base = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=3) as resp:  # noqa: S310
            if resp.status not in (200, 201):
                pytest.skip(f"Ollama HTTP status {resp.status}")
    except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover
        pytest.skip(f"Ollama not reachable at {base}: {exc}")


@pytest.fixture
def e2e_stack(celery_eager) -> None:  # noqa: ANN001
    _require_e2e_flag()
    _require_redis()
    _require_ollama_http()
