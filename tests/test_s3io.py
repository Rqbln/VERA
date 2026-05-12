"""MinIO / S3 upload helper."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from botocore.exceptions import ClientError

from raip.artifacts import s3io
from raip.config import Settings


class TestS3IO(unittest.TestCase):
    @patch("raip.artifacts.s3io.boto3.client")
    def test_upload_bytes_creates_bucket_if_missing(self, mock_client: MagicMock) -> None:
        c = MagicMock()
        mock_client.return_value = c
        c.head_bucket.side_effect = ClientError({"Error": {}}, "HeadBucket")

        uri = s3io.upload_bytes(
            "k1",
            b"hi",
            settings=Settings(
                minio_endpoint_url="http://localhost:9000",
                minio_access_key="a",
                minio_secret_key="b",
                minio_bucket="raip",
            ),
        )
        self.assertTrue(uri.startswith("s3://raip/k1"))
        c.put_object.assert_called_once()


if __name__ == "__main__":
    unittest.main()
