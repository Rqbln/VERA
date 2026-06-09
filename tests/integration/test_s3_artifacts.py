"""S3/MinIO artifact upload."""

from __future__ import annotations

import uuid

import boto3
import pytest

from raip.artifacts.s3io import upload_bytes
from raip.config import get_settings


@pytest.mark.integration
def test_upload_bytes_roundtrip(integration_stack: None) -> None:  # noqa: ARG001
    s = get_settings()
    key = f"integration/{uuid.uuid4().hex}/probe.txt"
    body = b"raip-mvp2-integration"
    upload_bytes(key, body, "text/plain", s)
    c = boto3.client(
        "s3",
        endpoint_url=s.minio_endpoint_url,
        aws_access_key_id=s.minio_access_key,
        aws_secret_access_key=s.minio_secret_key,
        region_name=s.minio_region,
    )
    obj = c.get_object(Bucket=s.minio_bucket, Key=key)
    assert obj["Body"].read() == body
