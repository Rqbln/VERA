"""R03/R04/R05 — dataset corpus scans via COMPL-AI graph."""

from __future__ import annotations

from typing import Any

from vera.api.benchmark_registry import get_benchmark_entry
from vera.benchmarks.runners.base import RawList, SamplesByReq, merge_samples
from vera.data.pipeline import scan_dataset


def run_dataset_scan(
    benchmark_id: str,
    dataset_context: dict[str, Any],
) -> tuple[SamplesByReq, RawList]:
    entry = get_benchmark_entry(benchmark_id) or {}
    req = str(entry.get("complai", "R03")).split(",")[0].strip()
    texts = list(dataset_context.get("corpus") or [])
    if not texts:
        raw: RawList = [
            {
                "agent": "dataset_scan",
                "benchmark_id": benchmark_id,
                "requirement": req,
                "status": "skipped",
                "note": "dataset_corpus empty — provide corpus on run payload",
            }
        ]
        return {}, raw

    result = scan_dataset(
        texts,
        dataset_id=str(dataset_context.get("dataset_id") or "run-corpus"),
        group_counts=dataset_context.get("group_counts"),
        protected_groups=list(dataset_context.get("protected_groups") or []),
    )
    scores = result.get("scores") or {}
    target_req = req
    if benchmark_id == "dataset_quality_scan":
        target_req = "R03"
        sc = float(scores.get("R03", 0.0))
    elif benchmark_id == "dataset_copyright_scan":
        target_req = "R04"
        sc = float(scores.get("R04", 0.0))
    elif benchmark_id == "dataset_privacy_scan":
        target_req = "R05"
        sc = float(scores.get("R05", 0.0))
    else:
        sc = float(scores.get(target_req, 0.0))

    samples: SamplesByReq = {}
    merge_samples(samples, target_req, benchmark_id, sc)
    raw = [
        {
            "agent": "dataset_scan",
            "harness": "dataset_pipeline",
            "benchmark_id": benchmark_id,
            "requirement": target_req,
            "score": sc,
            "details": result.get("details"),
            "engine": result.get("details", {}).get("engine", "pipeline"),
            "signature": result.get("signature"),
        }
    ]
    return samples, raw
