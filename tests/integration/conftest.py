"""Integration fixtures: real Redis + MinIO, Celery eager."""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.request

import pytest

from raip.celery_app import celery_app


def _require_integration_flag() -> None:
    if os.environ.get("RAIP_INTEGRATION") != "1":
        pytest.skip("Set RAIP_INTEGRATION=1 to run integration tests.")


def _require_redis() -> None:
    try:
        import redis

        r = redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
        r.ping()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Redis unavailable: {exc}")


def _wait_minio_http(endpoint: str, timeout_sec: float = 45.0) -> None:
    base = endpoint.rstrip("/")
    url = f"{base}/minio/health/live"
    deadline = time.time() + timeout_sec
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:  # noqa: S310
                if resp.status in (200, 201):
                    return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc
        time.sleep(1.0)
    pytest.skip(f"MinIO not healthy at {url}: {last_err}")


def _require_minio() -> None:
    import boto3
    from botocore.exceptions import ClientError

    from raip.config import get_settings

    s = get_settings()
    _wait_minio_http(s.minio_endpoint_url)
    c = boto3.client(
        "s3",
        endpoint_url=s.minio_endpoint_url,
        aws_access_key_id=s.minio_access_key,
        aws_secret_access_key=s.minio_secret_key,
        region_name=s.minio_region,
    )
    try:
        c.head_bucket(Bucket=s.minio_bucket)
    except ClientError as err:
        code = err.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchBucket", "NotFound"):
            c.create_bucket(Bucket=s.minio_bucket)
            return
        pytest.skip(f"MinIO head_bucket failed: {err}")
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"MinIO unavailable: {exc}")


@pytest.fixture
def integration_stack() -> None:
    _require_integration_flag()
    _require_redis()
    _require_minio()
    prev = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = prev
