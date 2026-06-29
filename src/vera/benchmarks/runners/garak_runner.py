"""Garak cyber scanner adapter (optional dependency)."""

from __future__ import annotations

import json
import subprocess
import sys

from vera.api.benchmark_registry import get_benchmark_entry
from vera.benchmarks.runners.base import RawList, RunContext, SamplesByReq, merge_samples
from vera.benchmarks.runners.hf_dynamic import run_hf_dynamic


def run_garak(ctx: RunContext, benchmark_id: str) -> tuple[SamplesByReq, RawList]:
    entry = get_benchmark_entry(benchmark_id)
    if not entry:
        return {}, []
    req = str(entry.get("complai", "R02")).split(",")[0].strip()
    probes = str(entry.get("garak_probes") or "dan")
    model_name = ctx.model_id if ctx.model_id.startswith("ollama/") else f"ollama/{ctx.model_id}"

    try:
        import garak  # noqa: F401
    except ImportError:
        samples, raw = run_hf_dynamic(ctx, benchmark_id)
        for r in raw:
            r["agent"] = "garak_fallback_hf_dynamic"
            r["harness"] = "hf_dynamic"
            r["fallback"] = True
            r["fallback_reason"] = "garak not installed"
        return samples, raw

    generations = max(1, min(ctx.n_samples_per_benchmark, 3))
    cmd = [
        sys.executable,
        "-m",
        "garak",
        "--model_type",
        "litellm",
        "--model_name",
        model_name,
        "--probes",
        probes,
        "--generations",
        str(generations),
        "--report_prefix",
        "vera_garak",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        failure_rate = _parse_garak_failure(proc.stdout + proc.stderr)
    except (subprocess.TimeoutExpired, OSError) as exc:
        samples, raw = run_hf_dynamic(ctx, benchmark_id)
        for r in raw:
            r["agent"] = "garak_fallback_hf_dynamic"
            r["harness"] = "hf_dynamic"
            r["fallback"] = True
            r["fallback_reason"] = str(exc)[:200]
        return samples, raw

    score = max(0.0, min(1.0, 1.0 - failure_rate))
    samples: SamplesByReq = {}
    raw: RawList = []
    merge_samples(samples, req, benchmark_id, score)
    raw.append(
        {
            "agent": "garak",
            "harness": "garak",
            "benchmark_id": benchmark_id,
            "requirement": req,
            "probes": probes,
            "failure_rate": failure_rate,
            "score": score,
            "generations": generations,
        }
    )
    return samples, raw


def _parse_garak_failure(output: str) -> float:
    for line in output.splitlines():
        if "fail" in line.lower() and "%" in line:
            try:
                pct = float(line.split("%")[0].split()[-1])
                return pct / 100.0
            except ValueError:
                continue
        if line.strip().startswith("{"):
            try:
                data = json.loads(line)
                if "fail_rate" in data:
                    return float(data["fail_rate"])
            except json.JSONDecodeError:
                continue
    return 0.5
