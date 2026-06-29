from __future__ import annotations

import pytest

from vera.artifacts import local_fs
from vera.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(vera_local_artifacts_dir=str(tmp_path / "artifacts"))


def test_upload_download_round_trip(settings):
    uri = local_fs.upload_bytes("runs/abc/raw.jsonl", b"hello", "application/json", settings)
    assert uri == "local://runs/abc/raw.jsonl"
    assert local_fs.download_bytes("runs/abc/raw.jsonl", settings) == b"hello"


def test_download_missing_returns_none(settings):
    assert local_fs.download_bytes("runs/none/x.txt", settings) is None


def test_presign_returns_api_url(settings):
    local_fs.upload_bytes("runs/abc/model_card.md", b"# card", settings=settings)
    url = local_fs.presign_get("runs/abc/model_card.md", settings=settings)
    assert url is not None
    assert url.endswith("/api/v1/artifacts/local/runs/abc/model_card.md")


def test_path_traversal_rejected(settings):
    with pytest.raises(ValueError):
        local_fs.safe_path(settings, "../../etc/passwd")
    # download/presign swallow the error and return None.
    assert local_fs.download_bytes("../../etc/passwd", settings) is None


def test_s3io_dispatches_to_local(monkeypatch, tmp_path):
    from vera.artifacts import s3io

    s = Settings(vera_artifact_backend="local", vera_local_artifacts_dir=str(tmp_path))
    monkeypatch.setattr(s3io, "get_settings", lambda: s)
    s3io.upload_bytes("runs/x/a.txt", b"data", settings=s)
    assert s3io.download_bytes("runs/x/a.txt", settings=s) == b"data"
