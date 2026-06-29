"""Load MVP2 benchmarks_catalog.yaml and requirement weights."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_PKG_DIR = Path(__file__).resolve().parent
_CATALOG_PATH = _PKG_DIR / "benchmarks_catalog.yaml"


@lru_cache
def load_catalog() -> dict[str, Any]:
    with _CATALOG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def catalog_version() -> str:
    return str(load_catalog().get("version") or "mvp2-v1")


def weights_for_requirement(requirement: str) -> dict[str, float]:
    cat = load_catalog()
    rw = (cat.get("requirement_weights") or {}).get(requirement) or {}
    return {str(k): float(v) for k, v in rw.items()}


def validate_catalog_weights() -> None:
    """Raise if any requirement weights do not sum to ~1."""
    cat = load_catalog()
    rw = cat.get("requirement_weights") or {}
    for req, weights in rw.items():
        if not weights:
            continue
        total = sum(float(v) for v in weights.values())
        if abs(total - 1.0) > 0.02:
            msg = f"requirement {req} weights sum to {total}, expected 1.0"
            raise ValueError(msg)
