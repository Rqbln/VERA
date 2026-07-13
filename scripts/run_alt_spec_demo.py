"""Run the evaluation pipeline under an ALTERNATIVE specification, swapped via
configuration alone (no code changes) — the paper's modularity demonstration.

Usage:
  VERA_REGISTRY_PATH=examples/spec_security_focus/registry.yaml \
  VERA_CATALOG_PATH=examples/spec_security_focus/catalog.yaml \
  VERA_AUTH_MODE=guided VERA_MLFLOW_DISABLED=1 \
  python scripts/run_alt_spec_demo.py

Writes manuscript/results/alt_spec_demo.json (spec provenance, scores, fallbacks).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from vera.benchmarks.catalog import (  # noqa: E402
    catalog_digest,
    catalog_version,
    validate_registry_catalog_alignment,
    weights_for_requirement,
)
from vera.benchmarks.runners.evaluate import evaluate_benchmarks  # noqa: E402
from vera.config import get_settings  # noqa: E402
from vera.dashboard.score_bands import load_score_bands  # noqa: E402
from vera.llm.client import LLMClient  # noqa: E402
from vera.stats.bootstrap import bootstrap_weighted_requirement_ci_95  # noqa: E402

OUT = ROOT / "manuscript" / "results" / "alt_spec_demo.json"
SEED = 42
N_SAMPLES = int(os.environ.get("ALT_SPEC_N_SAMPLES", "2"))


def main() -> int:
    version = catalog_version()
    if version == "mvp2-v2":
        print(
            "The default catalog is loaded. Point VERA_CATALOG_PATH and "
            "VERA_REGISTRY_PATH at examples/spec_security_focus/ first."
        )
        return 2
    # The pipeline's own gate: the swapped registry and catalog must agree.
    validate_registry_catalog_alignment()

    requirements = ["R01", "R02", "R12"]
    benchmarks: list[str] = []
    for req in requirements:
        for bench in weights_for_requirement(req):
            if bench not in benchmarks:
                benchmarks.append(bench)

    settings = get_settings()
    print(f"Alternative spec '{version}' ({catalog_digest()[:12]}...) — "
          f"{len(benchmarks)} benchmarks, n={N_SAMPLES}, model={settings.vera_target_model}")

    req_samples, raw_outputs = evaluate_benchmarks(
        model_id=settings.vera_target_model,
        judge_model=settings.effective_judge_model,
        benchmarks=benchmarks,
        n_samples_per_benchmark=N_SAMPLES,
        temperature=0.0,
        max_tokens=256,
        seed=SEED,
        llm=LLMClient(settings),
    )

    bands = load_score_bands()
    scores: dict[str, dict] = {}
    for req in requirements:
        by_b = {b: list(v) for b, v in (req_samples.get(req) or {}).items()}
        if not by_b:
            continue
        mean, lo, hi = bootstrap_weighted_requirement_ci_95(
            by_b, weights_for_requirement(req), seed=SEED, n_resamples=500
        )
        scores[req] = {
            "score": round(mean, 4),
            "ci_lo": round(lo, 4),
            "ci_hi": round(hi, 4),
            "band": bands.band(mean),
            "benchmarks": sorted(by_b.keys()),
        }

    seen: dict[str, dict] = {}
    for row in raw_outputs:
        bid = str(row.get("benchmark_id", ""))
        if bid and bid not in seen:
            seen[bid] = {
                "benchmark_id": bid,
                "harness": row.get("harness", "unknown"),
                "fallback": bool(row.get("fallback")),
            }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "spec": {"version": version, "digest": f"sha256:{catalog_digest()}"},
                "model": settings.vera_target_model,
                "seed": SEED,
                "n_samples_per_benchmark": N_SAMPLES,
                "requirements": requirements,
                "scores": scores,
                "provenance": sorted(seen.values(), key=lambda r: r["benchmark_id"]),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    for req, s in scores.items():
        print(f"  {req}: {s['score']} [{s['ci_lo']}, {s['ci_hi']}] ({s['band']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
