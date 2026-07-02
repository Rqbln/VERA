"""Generate real APSEC paper data: an S1 COMPL-AI run on an Ollama target plus a
weighting-sensitivity study (re-aggregating the SAME cached per-benchmark samples under
alternative weight schemes — no model re-runs).

Outputs JSON under manuscript/results/ for the LaTeX tables and figures.

Run:  VERA_AUTH_MODE=guided VERA_MLFLOW_DISABLED=1 python manuscript/scripts/gen_results.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from vera.benchmarks.catalog import catalog_version, weights_for_requirement
from vera.benchmarks.runners.evaluate import evaluate_benchmarks
from vera.config import get_settings
from vera.dashboard.score_bands import load_score_bands
from vera.dashboard.triage import triage_priority
from vera.llm.client import LLMClient
from vera.stats.bootstrap import bootstrap_weighted_requirement_ci_95, weighted_requirement_mean

OUT = Path(__file__).resolve().parents[1] / "results"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 42
N_SAMPLES = int(os.environ.get("PAPER_N_SAMPLES", "10"))

# Multi-benchmark requirements drive the sensitivity study; singles round out RQ1 coverage.
REQUIREMENTS = ["R01", "R06", "R07", "R08", "R10", "R12"]
BENCHMARKS = [
    "r01_robustness", "mmlu_robust", "boolq_contrast",          # R01
    "mmlu", "gsm8k", "humaneval", "truthfulqa", "bbh",          # R06
    "ece_mmlu",                                                  # R07
    "self_disclosure_probes",                                    # R08
    "bbq", "bold", "stereoset",                                  # R10
    "realtoxicityprompts", "advbench_instruction",              # R12 (+ truthfulqa shared)
]


def aggregate(req_samples: dict[str, dict[str, list[float]]], weights_fn) -> dict[str, dict]:
    """Aggregate each requirement under a weighting function w(req)->{bench: weight}."""
    bands = load_score_bands()
    out: dict[str, dict] = {}
    for req in REQUIREMENTS:
        by_b = req_samples.get(req) or {}
        if not by_b:
            continue
        weights = weights_fn(req)
        mean, lo, hi = bootstrap_weighted_requirement_ci_95(
            by_b, weights, seed=SEED, n_resamples=500
        )
        out[req] = {
            "score": round(mean, 4),
            "ci_lo": round(lo, 4),
            "ci_hi": round(hi, 4),
            "band": bands.band(mean),
            "benchmarks": sorted(by_b.keys()),
        }
    return out


def triage_rank(scores: dict[str, dict]) -> list[str]:
    """Order requirements by triage priority then score (worst first) — the dashboard ordering."""
    def key(req: str):
        s = scores[req]
        band = s["band"]
        triage = "failed" if band == "red" else "fallback" if band == "orange" else "ok"
        return (triage_priority(triage), s["score"], req)

    return sorted(scores.keys(), key=key)


def main() -> None:
    settings = get_settings()
    llm = LLMClient(settings)
    print(f"Running S1 on {settings.vera_target_model} (n={N_SAMPLES}/benchmark)...")

    req_samples, raw_outputs = evaluate_benchmarks(
        model_id=settings.vera_target_model,
        judge_model=settings.effective_judge_model,
        benchmarks=BENCHMARKS,
        n_samples_per_benchmark=N_SAMPLES,
        temperature=0.0,
        max_tokens=512,
        seed=SEED,
        llm=llm,
    )
    # Keep only requirements we target; coerce defaultdicts to plain dicts.
    req_samples = {r: dict(req_samples.get(r, {})) for r in REQUIREMENTS}

    # Harness provenance (fallback flags) for RQ1 honesty.
    seen: dict[str, dict] = {}
    for row in raw_outputs:
        bid = str(row.get("benchmark_id", ""))
        if bid and bid not in seen:
            seen[bid] = {
                "benchmark_id": bid,
                "harness": row.get("harness", "unknown"),
                "fallback": bool(row.get("fallback")),
            }
    provenance = sorted(seen.values(), key=lambda r: r["benchmark_id"])
    fallback_rate = round(sum(p["fallback"] for p in provenance) / max(1, len(provenance)), 3)

    # --- Baseline (signed catalogue weights) ---
    baseline = aggregate(req_samples, weights_for_requirement)

    # --- Sensitivity schemes (re-aggregate the SAME samples) ---
    def uniform(req: str) -> dict[str, float]:
        bs = list(req_samples.get(req, {}).keys())
        return {b: 1.0 / len(bs) for b in bs} if bs else {}

    rng = np.random.default_rng(SEED)

    def perturbed(scale: float):
        def fn(req: str) -> dict[str, float]:
            base = weights_for_requirement(req)
            bs = [b for b in req_samples.get(req, {}) if b in base]
            if not bs:
                return uniform(req)
            jitter = {b: max(0.01, base[b] + float(rng.normal(0, scale))) for b in bs}
            total = sum(jitter.values())
            return {b: w / total for b, w in jitter.items()}

        return fn

    schemes = {
        "baseline": baseline,
        "uniform": aggregate(req_samples, uniform),
        "perturb_0.1": aggregate(req_samples, perturbed(0.1)),
        "perturb_0.2": aggregate(req_samples, perturbed(0.2)),
    }

    # Single-benchmark-dominant: each contributing benchmark gets full weight in turn.
    # max-min spread across the dominant choices shows how much a requirement *could* move.
    dominant: dict[str, dict] = {}
    multi_reqs = [r for r in REQUIREMENTS if len(req_samples.get(r, {})) > 1]
    for req in multi_reqs:
        vals = {}
        for b in req_samples[req]:
            vals[b] = round(weighted_requirement_mean(req_samples[req], {b: 1.0}), 4)
        spread = round(max(vals.values()) - min(vals.values()), 4)
        dominant[req] = {"per_benchmark": vals, "spread": spread}

    # --- Stability metrics ---
    bands_by_scheme = {s: {r: v["band"] for r, v in sc.items()} for s, sc in schemes.items()}
    band_flips = 0
    flip_detail = {}
    for req in baseline:
        bands_seen = {bands_by_scheme[s].get(req) for s in schemes if req in schemes[s]}
        if len(bands_seen) > 1:
            band_flips += 1
            flip_detail[req] = sorted(b for b in bands_seen if b)
    ranks = {s: triage_rank(sc) for s, sc in schemes.items() if sc}
    baseline_rank = ranks["baseline"]
    rank_changes = {
        s: sum(1 for i, r in enumerate(rk) if i < len(baseline_rank) and r != baseline_rank[i])
        for s, rk in ranks.items()
    }

    # --- Multi-seed perturbation sweep (no model queries): distribution, not one draw ---
    K = int(os.environ.get("PAPER_PERTURB_SEEDS", "200"))
    sweep_rng = np.random.default_rng(SEED + 99)

    def draw_perturb(scale: float, gen):
        def fn(req: str) -> dict[str, float]:
            base = weights_for_requirement(req)
            bs = [b for b in req_samples.get(req, {}) if b in base]
            if not bs:
                return uniform(req)
            jitter = {b: max(0.01, base[b] + float(gen.normal(0, scale))) for b in bs}
            tot = sum(jitter.values())
            return {b: w / tot for b, w in jitter.items()}
        return fn

    sweep = {}
    for scale in (0.1, 0.2):
        flips_dist, rank_dist = [], []
        for _ in range(K):
            sc = aggregate(req_samples, draw_perturb(scale, sweep_rng))
            f = sum(
                1 for r in baseline
                if r in sc and sc[r]["band"] != baseline[r]["band"]
            )
            rk = triage_rank(sc)
            rc = sum(
                1 for i, r in enumerate(rk)
                if i < len(baseline_rank) and r != baseline_rank[i]
            )
            flips_dist.append(f)
            rank_dist.append(rc)
        sweep[f"perturb_{scale}"] = {
            "draws": K,
            "band_flips_mean": round(float(np.mean(flips_dist)), 3),
            "band_flips_max": int(np.max(flips_dist)),
            "rank_change_mean": round(float(np.mean(rank_dist)), 3),
            "rank_change_pct_nonzero": round(float(np.mean([r > 0 for r in rank_dist])), 3),
        }

    # --- Determinism (RQ1): re-aggregate twice, assert identical ---
    rerun = aggregate(req_samples, weights_for_requirement)
    deterministic = all(
        abs(rerun[r]["score"] - baseline[r]["score"]) < 1e-9 for r in baseline
    )

    results = {
        "model": settings.vera_target_model,
        "catalog_version": catalog_version(),
        "seed": SEED,
        "n_samples": N_SAMPLES,
        "fallback_rate": fallback_rate,
        "provenance": provenance,
        "s1_scores": baseline,
        "deterministic_reaggregation": deterministic,
        "raw_samples": {r: {b: list(v) for b, v in bm.items()} for r, bm in req_samples.items()},
        "sensitivity": {
            "schemes": {s: sc for s, sc in schemes.items()},
            "dominant": dominant,
            "band_flips": band_flips,
            "band_flip_detail": flip_detail,
            "triage_rank_changes": rank_changes,
            "baseline_triage_rank": baseline_rank,
            "multiseed_sweep": sweep,
        },
    }
    (OUT / "paper_results.json").write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT / 'paper_results.json'}")
    print(f"Requirements scored: {sorted(baseline.keys())}")
    print(f"Fallback rate: {fallback_rate}; deterministic re-aggregation: {deterministic}")
    print(f"Single-scheme band-flips: {band_flips} {flip_detail}")
    print(f"Dominant spreads: { {r: d['spread'] for r, d in dominant.items()} }")
    print(f"Multi-seed sweep: {sweep}")


if __name__ == "__main__":
    main()
