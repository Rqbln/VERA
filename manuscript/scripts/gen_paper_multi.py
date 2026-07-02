#!/usr/bin/env python3
"""Turn the native multi-model run + GaaS benchmark into the paper's tables and figures.

Reads manuscript/results/paper_results_multi.json (from scripts/run_paper_eval.py) and, if present,
manuscript/results/gaas_bench.json (from scripts/bench_gaas.py). Prints the numbers to transcribe
into main.tex and writes:
  figures/fig_scores_multi.pdf       per-requirement scores across the model panel
  figures/fig_weight_sensitivity.pdf per-requirement reweighting range (now non-degenerate)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from vera.benchmarks.catalog import weights_for_requirement  # noqa: E402
from vera.dashboard.score_bands import load_score_bands  # noqa: E402

RES = Path(__file__).resolve().parents[1] / "results"
FIG = Path(__file__).resolve().parents[1] / "figures"
FIG.mkdir(parents=True, exist_ok=True)
# Requirements with >=2 contributing benchmarks. Since catalog mvp2-v2 (advbench weighted in
# R12) every aggregate reconciles with the weighted mean of its per-benchmark decomposition;
# the canonical per-panel sensitivity study lives in gen_sensitivity_panel.py.
MULTI_BENCH_REQS = ["R01", "R02", "R06", "R10", "R12"]


def short(m: str) -> str:
    return m.replace("ollama/", "").split(":")[0][:14]


def main() -> None:
    multi = json.loads((RES / "paper_results_multi.json").read_text())
    gaas_path = RES / "gaas_bench.json"
    gaas = json.loads(gaas_path.read_text()) if gaas_path.is_file() else {}
    models = multi["models"]
    bands = load_score_bands()
    reqs = sorted({r for m in models.values() for r in m["scores"]})

    print("\n=== MULTI-MODEL SCORES (transcribe into main.tex Table) ===")
    header = "Req  " + "  ".join(f"{short(m):>14}" for m in models)
    print(header)
    for r in reqs:
        row = f"{r}  "
        for m in models.values():
            sc = m["scores"].get(r, {})
            s = sc.get("score")
            row += f"  {('%.2f' % s) if isinstance(s, (int, float)) else '  -':>14}"
        print(row)
    print("\nfallback / benchmarks per model:")
    for name, m in models.items():
        print(f"  {short(name):>14}: fallback={m['fallback_count']}/{m['benchmark_count']}  "
              f"energy_kwh={(m.get('energy') or {}).get('kwh')}  trust={(m.get('trust_factor') or {}).get('score')}")

    # Sensitivity on the principal (first) model — now non-degenerate with native harnesses.
    principal = next(iter(models))
    pb = models[principal].get("per_benchmark", {})
    print(f"\n=== WEIGHTING SENSITIVITY (principal = {short(principal)}) ===")
    sens_rows = []
    for r in MULTI_BENCH_REQS:
        benches = pb.get(r, {})
        if len(benches) < 2:
            continue
        means = list(benches.values())
        delta = round(max(means) - min(means), 3)
        w = weights_for_requirement(r)
        baseline = sum(w.get(b, 0) * v for b, v in benches.items()) / (sum(w.get(b, 0) for b in benches) or 1)
        uniform = sum(means) / len(means)
        reach = means + [baseline, uniform]
        rng = round(max(reach) - min(reach), 3)
        flips = len({bands.band(x) for x in reach})
        sens_rows.append((r, len(benches), round(baseline, 2), delta, rng, "yes" if flips > 1 else "no"))
        print(f"  {r}: k={len(benches)} baseline={baseline:.2f} Δ={delta} range={rng} band_flip={'yes' if flips>1 else 'no'}")

    if gaas:
        print("\n=== GaaS BENCHMARK ===")
        print(f"  proxy overhead p50={gaas['latency']['overhead_ms_p50']}ms p95={gaas['latency']['overhead_ms_p95']}ms")
        print(f"  detection={gaas['detection']['flagged']}/{gaas['detection']['total']}  "
              f"policy={gaas['policy']}  bus={gaas['bus']}")

    # Figure 1: per-requirement scores across the panel.
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    x = np.arange(len(reqs))
    width = 0.8 / max(len(models), 1)
    for i, (name, m) in enumerate(models.items()):
        ys = [(m["scores"].get(r, {}) or {}).get("score") or 0 for r in reqs]
        ax.bar(x + i * width, ys, width, label=short(name))
    ax.axhline(0.7, ls="--", c="#00915a", lw=0.6)
    ax.axhline(0.4, ls="--", c="#e8a33d", lw=0.6)
    ax.set_xticks(x + width * (len(models) - 1) / 2)
    ax.set_xticklabels([r.replace("R", "CR") for r in reqs], fontsize=6, rotation=45)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("COMPL-AI score")
    ax.legend(fontsize=5, ncol=3, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG / "fig_scores_multi.pdf")
    print("\nwrote", FIG / "fig_scores_multi.pdf")

    # The canonical sensitivity figure (both panels, all models) is produced by
    # gen_sensitivity_panel.py, which also verifies aggregate/decomposition reconciliation.
    if sens_rows:
        print("\nsensitivity figure: run manuscript/scripts/gen_sensitivity_panel.py")


if __name__ == "__main__":
    main()
