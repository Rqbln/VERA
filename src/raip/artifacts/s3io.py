from __future__ import annotations

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from raip.config import Settings, get_settings


def _client(settings: Settings) -> BaseClient:
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint_url,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name=settings.minio_region,
    )


def ensure_bucket(settings: Settings | None = None) -> None:
    """Ensure the configured bucket exists; raise with context on failure."""
    s = settings or get_settings()
    c = _client(s)
    try:
        c.head_bucket(Bucket=s.minio_bucket)
        return
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code not in ("404", "NoSuchBucket"):
            raise RuntimeError(
                f"MinIO head_bucket failed for {s.minio_bucket!r} at {s.minio_endpoint_url}: {e}"
            ) from e
    try:
        c.create_bucket(Bucket=s.minio_bucket)
    except ClientError as e:
        raise RuntimeError(
            f"MinIO create_bucket failed for {s.minio_bucket!r} at {s.minio_endpoint_url}: {e}"
        ) from e


def upload_bytes(
    key: str,
    body: bytes,
    content_type: str = "application/octet-stream",
    settings: Settings | None = None,
) -> str:
    s = settings or get_settings()
    ensure_bucket(s)
    c = _client(s)
    c.put_object(Bucket=s.minio_bucket, Key=key, Body=body, ContentType=content_type)
    return f"s3://{s.minio_bucket}/{key}"


def download_bytes(key: str, settings: Settings | None = None) -> bytes | None:
    s = settings or get_settings()
    c = _client(s)
    try:
        resp = c.get_object(Bucket=s.minio_bucket, Key=key)
        return resp["Body"].read()
    except Exception:
        return None


def presign_get(key: str, expires_in: int = 3600, settings: Settings | None = None) -> str | None:
    s = settings or get_settings()
    c = _client(s)
    try:
        return c.generate_presigned_url(
            "get_object",
            Params={"Bucket": s.minio_bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except ClientError:
        return None
