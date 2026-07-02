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


def catalog_digest() -> str:
    """
    SHA-256 over the canonical catalog content (version + requirement_weights).

    This is the digest referenced by the catalog's signing block and pinned into
    every run record, so a run always names the exact weighting that produced it.
    """
    from vera.governance.signing import artifact_digest

    cat = load_catalog()
    return artifact_digest(
        {"version": cat.get("version"), "requirement_weights": cat.get("requirement_weights")}
    )


def validate_registry_catalog_alignment() -> None:
    """
    Raise if the registry's requirement mappings and the catalog weights disagree.

    Every (requirement, benchmark) pair claimed by the registry must carry a catalog
    weight, and every catalog weight must correspond to a registry mapping, so each
    aggregate stays reproducible from the catalog and the per-benchmark decomposition.
    """
    from vera.api.benchmark_registry import MVP2_BENCHMARK_REGISTRY

    rw = load_catalog().get("requirement_weights") or {}
    reg_pairs: set[tuple[str, str]] = set()
    for entry in MVP2_BENCHMARK_REGISTRY:
        bid = str(entry.get("id") or "")
        for req in str(entry.get("complai") or "").split(","):
            req = req.strip()
            if req and bid:
                reg_pairs.add((req, bid))
    problems: list[str] = []
    for req, bid in sorted(reg_pairs):
        if bid not in (rw.get(req) or {}):
            problems.append(f"registry maps {bid} to {req} but the catalog has no weight for it")
    for req, weights in rw.items():
        for bid in weights or {}:
            if (req, bid) not in reg_pairs:
                problems.append(f"catalog weights {bid} under {req} but the registry does not map it there")
    if problems:
        raise ValueError("registry/catalog misalignment: " + "; ".join(problems))
