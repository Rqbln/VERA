"""R09 watermark — explicit NA when no detector is configured."""

from __future__ import annotations

from typing import Any

from raip.benchmarks.runners.base import RawList, SamplesByReq


def run_watermark_na(benchmark_id: str) -> tuple[SamplesByReq, RawList]:
    """No score contributed; requirement marked NA in raw outputs."""
    raw: RawList = [
        {
            "agent": "watermark_na",
            "benchmark_id": benchmark_id,
            "requirement": "R09",
            "status": "NA",
            "note": "No watermark detector wired (MVP2); excluded from aggregation.",
        }
    ]
    return {}, raw
