"""Artifact signing — Cosign/OpenBao compatible digest (MVP2 §1.1 M6–M7)."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from raip.config import get_settings


def artifact_digest(payload: bytes | str | dict[str, Any]) -> str:
    if isinstance(payload, dict):
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    elif isinstance(payload, str):
        raw = payload.encode()
    else:
        raw = payload
    return hashlib.sha256(raw).hexdigest()


def sign_artifact(payload: bytes | str | dict[str, Any]) -> dict[str, str]:
    """
    Return signature metadata. When OpenBao/Cosign env vars are set, extend here.
    """
    digest = artifact_digest(payload)
    settings = get_settings()
    key_id = settings.raip_signing_key_id
    algo = os.environ.get("RAIP_SIGNING_ALGO", "sha256")
    cosign = os.environ.get("COSIGN_EXPERIMENTAL", "")
    return {
        "key_id": key_id,
        "algo": algo,
        "digest": f"sha256:{digest}",
        "cosign_enabled": "1" if cosign else "0",
    }


def image_digest_from_env() -> str:
    return os.environ.get("RAIP_IMAGE_DIGEST", os.environ.get("IMAGE_DIGEST", "n/a"))
