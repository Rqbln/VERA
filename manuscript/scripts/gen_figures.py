"""Render the APSEC paper figures from manuscript/results/paper_results.json."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = json.loads((ROOT / "results" / "paper_results.json").read_text())
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

BAND_COLOR = {"green": "#2e7d32", "orange": "#ed6c02", "red": "#c62828", "unknown": "#9e9e9e"}
plt.rcParams.update({"font.size": 9, "figure.dpi": 200})


def fig_scores():
    s1 = RES["s1_scores"]
    reqs = sorted(s1.keys())
    scores = [s1[r]["score"] for r in reqs]
    colors = [BAND_COLOR[s1[r]["band"]] for r in reqs]
    lo = [s1[r]["score"] - s1[r]["ci_lo"] for r in reqs]
    hi = [s1[r]["ci_hi"] - s1[r]["score"] for r in reqs]

    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    ax.bar(reqs, scores, color=colors, yerr=[lo, hi], capsize=2, width=0.6)
    ax.axhline(0.7, ls="--", c="#2e7d32", lw=0.7)
    ax.axhline(0.4, ls="--", c="#ed6c02", lw=0.7)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("COMPL-AI score")
    ax.set_title("Per-requirement scores with 95% CI", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig_scores_s1.pdf")
    print("wrote", FIG / "fig_scores_s1.pdf")


def fig_sensitivity():
    sens = RES["sensitivity"]
    baseline = sens["schemes"]["baseline"]
    uniform = sens["schemes"]["uniform"]
    dominant = sens.get("dominant", {})
    reqs = sorted(baseline.keys())

    # For each requirement, the full range of scores reachable by any tested weighting:
    # baseline, uniform, and every single-benchmark-dominant choice.
    base_y = [baseline[r]["score"] for r in reqs]
    lo, hi = [], []
    for r in reqs:
        vals = [baseline[r]["score"], uniform[r]["score"]]
        if r in dominant:
            vals += list(dominant[r]["per_benchmark"].values())
        lo.append(baseline[r]["score"] - min(vals))
        hi.append(max(vals) - baseline[r]["score"])

    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    ax.errorbar(reqs, base_y, yerr=[lo, hi], fmt="o", ms=5, capsize=4, lw=1.0,
                color="#1565c0", ecolor="#c62828", label="baseline ± reweighting range")
    ax.axhline(0.7, ls="--", c="#2e7d32", lw=0.7)
    ax.axhline(0.4, ls="--", c="#ed6c02", lw=0.7)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("aggregate score")
    ax.set_title("Score range across all tested weightings", fontsize=9)
    ax.legend(fontsize=6, loc="lower left", frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "fig_weight_sensitivity.pdf")
    print("wrote", FIG / "fig_weight_sensitivity.pdf")


if __name__ == "__main__":
    fig_scores()
    fig_sensitivity()
