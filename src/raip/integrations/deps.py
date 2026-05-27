"""Detect optional lab/benchmark dependencies."""

from __future__ import annotations

from typing import Any


def _try_import(name: str) -> tuple[bool, str | None]:
    try:
        mod = __import__(name)
        ver = getattr(mod, "__version__", None)
        return True, str(ver) if ver else "installed"
    except ImportError:
        return False, None


def require_lab_extra(name: str) -> tuple[bool, dict[str, Any]]:
    """Return (available, status dict) for a lab optional dependency."""
    status = lab_engine_status(name)
    return bool(status.get("available")), status


def lab_engine_status(engine: str) -> dict[str, Any]:
    """Return availability for detoxify, presidio, codecarbon, levenshtein, sacrebleu."""
    mapping = {
        "detoxify": "detoxify",
        "presidio": "presidio_analyzer",
        "codecarbon": "codecarbon",
        "levenshtein": "Levenshtein",
        "sacrebleu": "sacrebleu",
        "lm_eval": "lm_eval",
        "garak": "garak",
        "transformers": "transformers",
        "peft": "peft",
    }
    key = mapping.get(engine, engine)
    ok, ver = _try_import(key)
    if ok:
        return {"engine": engine, "available": True, "version": ver, "mode": "library"}
    return {
        "engine": engine,
        "available": False,
        "mode": "heuristic_fallback",
        "note": f"Install optional extra for {engine}",
    }
