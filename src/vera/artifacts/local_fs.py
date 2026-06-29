"""Local-filesystem artifact backend.

Mirrors the :mod:`vera.artifacts.s3io` surface (``upload_bytes`` / ``download_bytes`` /
``presign_get``) so the platform runs without MinIO in lite mode. Artifacts are written under
``VERA_LOCAL_ARTIFACTS_DIR`` and served back to the browser through the API route
``GET /api/v1/artifacts/local/{key}``.
"""

from __future__ import annotations

from pathlib import Path

from vera.config import Settings, get_settings


def _root(settings: Settings) -> Path:
    root = Path(settings.vera_local_artifacts_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_path(settings: Settings, key: str) -> Path:
    """Resolve ``key`` under the artifacts root, rejecting path traversal."""
    root = _root(settings)
    target = (root / key.lstrip("/")).resolve()
    if root != target and root not in target.parents:
        raise ValueError(f"unsafe artifact key: {key!r}")
    return target


def upload_bytes(
    key: str,
    body: bytes,
    content_type: str = "application/octet-stream",
    settings: Settings | None = None,
) -> str:
    s = settings or get_settings()
    target = safe_path(s, key)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return f"local://{key}"


def download_bytes(key: str, settings: Settings | None = None) -> bytes | None:
    s = settings or get_settings()
    try:
        target = safe_path(s, key)
    except ValueError:
        return None
    if not target.is_file():
        return None
    return target.read_bytes()


def presign_get(key: str, expires_in: int = 3600, settings: Settings | None = None) -> str | None:
    """Return an API URL that serves the local artifact (no real signing in lite mode)."""
    s = settings or get_settings()
    try:
        target = safe_path(s, key)
    except ValueError:
        return None
    if not target.is_file():
        return None
    base = (s.vera_public_api_url or f"http://localhost:{s.api_port}").rstrip("/")
    return f"{base}/api/v1/artifacts/local/{key.lstrip('/')}"
