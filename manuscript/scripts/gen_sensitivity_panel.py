#!/usr/bin/env python3
"""One-command weighting-sensitivity study over the paper's model panels.

For every model in paper_results_panelA.json / paper_results_panelB.json and every
multi-benchmark requirement, this script re-reads the per-benchmark decomposition and:

  * checks RECONCILIATION: the stored aggregate must equal the catalog-weighted mean
    of the per-benchmark means (weights renormalized over the benchmarks present);
  * computes the closed-form reachable range under ANY admissible reweighting
    (Proposition: the aggregate is a convex combination of per-benchmark means, so the
    reachable interval is exactly [min_b m_b, max_b m_b] and its width is
    Delta = max_b m_b - min_b m_b);
  * flags a BAND FLIP when that interval straddles a green/amber/red threshold;
  * prints the LaTeX rows for the paper's sensitivity table;
  * writes figures/fig_weight_sensitivity.pdf (baseline dot + reachable range bar).

No model is re-queried: everything derives from the cached panel artifacts and the
signed catalog (version + SHA-256 digest printed for provenance).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from vera.benchmarks.catalog import catalog_digest, catalog_version, weights_for_requirement
from vera.dashboard.score_bands import ScoreBands

RESULTS = ROOT / "manuscript" / "results"
FIG = ROOT / "manuscript" / "figures"
PANELS = {
    "A": RESULTS / "paper_results_panelA.json",
    "B": RESULTS / "paper_results_panelB.json",
}
SHORT = {
    "ollama/llama3.1:8b-instruct-q8_0": "Llama 3.1 8B",
    "ollama/qwen2.5:7b": "Qwen2.5 7B",
    "ollama/gemma2:9b": "Gemma 2 9B",
    "ollama/ministral-3:3b": "Ministral 3B",
    "ollama/mistral:7b": "Mistral 7B",
    "ollama/mistral-small:24b": "Mistral-Small 24B",
}
RECONCILE_TOL = 5e-6


def analyze_panel(path: Path, bands: ScoreBands) -> tuple[list[str], dict, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    models = data["models"]
    rows: dict[str, dict[str, dict]] = {}
    failures = 0
    for mkey, m in models.items():
        pb = m.get("per_benchmark") or {}
        for req, benches in sorted(pb.items()):
            weights = weights_for_requirement(req)
            catalogued = {b: v for b, v in benches.items() if b in weights}
            if not catalogued:
                continue
            means = list(catalogued.values())
            lo_r, hi_r = min(means), max(means)
            delta = hi_r - lo_r
            denom = sum(weights[b] for b in catalogued)
            weighted = sum(weights[b] * v for b, v in catalogued.items()) / denom
            stored = (m.get("scores", {}).get(req) or {}).get("score")
            gap = abs(weighted - stored) if isinstance(stored, (int, float)) else None
            reconciled = gap is not None and gap <= RECONCILE_TOL
            if not reconciled:
                failures += 1
                print(f"  !! RECONCILE FAIL {path.name} {mkey} {req}: "
                      f"stored={stored} weighted={weighted:.6f} gap={gap}")
            flip = bands.band(lo_r) != bands.band(hi_r)
            rows.setdefault(req, {})[mkey] = {
                "k": len(catalogued), "delta": delta, "lo": lo_r, "hi": hi_r,
                "baseline": weighted, "flip": flip,
            }
    model_order = list(models)
    latex: list[str] = []
    for req in sorted(rows):
        per_model = rows[req]
        ks = {v["k"] for v in per_model.values()}
        if max(ks) < 2:
            continue
        cells = []
        for mkey in model_order:
            v = per_model.get(mkey)
            if not v:
                cells.append("--")
                continue
            cells.append(f"$\\Delta{{=}}{v['delta']:.2f}$, {'flip' if v['flip'] else 'no'}")
        cr = req.replace("R", "CR")
        k = max(ks)
        latex.append(f"    {cr} & {k} & " + " & ".join(cells) + " \\\\")
    return latex, rows, failures


def make_figure(all_rows: dict[str, dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.1), sharey=True)
    for ax, (panel, rows) in zip(axes, all_rows.items()):
        reqs = sorted(r for r, pm in rows.items() if max(v["k"] for v in pm.values()) >= 2)
        model_keys = sorted({mk for pm in rows.values() for mk in pm})
        n_m = max(1, len(model_keys))
        for j, mkey in enumerate(model_keys):
            xs, ys, lo_err, hi_err = [], [], [], []
            for i, req in enumerate(reqs):
                v = rows[req].get(mkey)
                if not v:
                    continue
                xs.append(i + (j - (n_m - 1) / 2) * 0.22)
                ys.append(v["baseline"])
                lo_err.append(v["baseline"] - v["lo"])
                hi_err.append(v["hi"] - v["baseline"])
            ax.errorbar(xs, ys, yerr=[lo_err, hi_err], fmt="o", ms=3, capsize=2,
                        lw=1, label=SHORT.get(mkey, mkey))
        ax.axhline(0.7, ls="--", c="#00915a", lw=0.6)
        ax.axhline(0.4, ls="--", c="#e8a33d", lw=0.6)
        ax.set_xticks(range(len(reqs)))
        ax.set_xticklabels([r.replace("R", "CR") for r in reqs], fontsize=7)
        ax.set_ylim(-0.05, 1.05)
        ax.set_title(f"Panel {panel}", fontsize=8)
        ax.legend(fontsize=5, loc="lower right")
    axes[0].set_ylabel("aggregate score", fontsize=8)
    fig.suptitle("Reachable score range under any reweighting", fontsize=8)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "fig_weight_sensitivity.pdf")
    print(f"wrote {FIG / 'fig_weight_sensitivity.pdf'}")


def main() -> int:
    bands = ScoreBands()
    print(f"catalog {catalog_version()}  sha256:{catalog_digest()}")
    all_rows: dict[str, dict] = {}
    total_failures = 0
    for panel, path in PANELS.items():
        if not path.is_file():
            print(f"  !! missing {path}")
            return 2
        latex, rows, failures = analyze_panel(path, bands)
        all_rows[panel] = rows
        total_failures += failures
        print(f"\n=== Panel {panel}: LaTeX rows (multi-benchmark requirements) ===")
        for line in latex:
            print(line)
    make_figure(all_rows)
    if total_failures:
        print(f"\nRECONCILIATION FAILED for {total_failures} (model, requirement) pairs")
        return 1
    print("\nreconciliation: all aggregates reproduce from catalog weights and decompositions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
