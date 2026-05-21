"""Integration fixtures: real Redis + MinIO, Celery eager."""

from __future__ import annotations

import os

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


def _require_minio() -> None:
    try:
        import boto3
        from botocore.exceptions import ClientError

        from raip.config import get_settings

        s = get_settings()
        c = boto3.client(
            "s3",
            endpoint_url=s.minio_endpoint_url,
            aws_access_key_id=s.minio_access_key,
            aws_secret_access_key=s.minio_secret_key,
            region_name=s.minio_region,
        )
        c.head_bucket(Bucket=s.minio_bucket)
    except ClientError:
        try:
            c.create_bucket(Bucket=s.minio_bucket)  # type: ignore[possibly-undefined]
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"MinIO unavailable: {exc}")
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
