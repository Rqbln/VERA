"""Load pilote_v1 catalog and item corpus."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_PKG_DIR = Path(__file__).resolve().parent


@lru_cache
def load_catalog() -> dict[str, Any]:
    with (_PKG_DIR / "catalog.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache
def load_all_items() -> tuple[dict[str, Any], ...]:
    path = _PKG_DIR / "items.jsonl"
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return tuple(rows)


def select_items(
    *,
    requested_benchmarks: list[str],
    n_samples_per_benchmark: int,
) -> list[dict[str, Any]]:
    """Up to n_samples_per_benchmark items per requested benchmark id."""
    req = set(requested_benchmarks)
    by_b: dict[str, list[dict[str, Any]]] = {}
    for it in load_all_items():
        bid = str(it.get("benchmark_id", ""))
        if bid in req:
            by_b.setdefault(bid, []).append(it)
    cap = max(1, int(n_samples_per_benchmark))
    out: list[dict[str, Any]] = []
    for bid in requested_benchmarks:
        chunk = by_b.get(bid, [])[:cap]
        out.extend(chunk)
    return out


def weights_for_requirement(requirement: str) -> dict[str, float]:
    cat = load_catalog()
    rw = (cat.get("requirement_weights") or {}).get(requirement) or {}
    return {str(k): float(v) for k, v in rw.items()}
