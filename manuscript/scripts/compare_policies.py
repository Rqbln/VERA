"""Verdicts under three defensible weighting policies, from cached panel results.

Policies: (i) uniform per-benchmark weights (the COMPL-AI aggregation), (ii) the
signed default catalog (mvp2-v2), (iii) the shipped security-first alternative
(examples/spec_security_focus/catalog.yaml, adversarial benchmarks upweighted;
defined for R01/R02/R12, elsewhere identical to the default catalog).

No model queries: point verdicts are re-aggregated from the per-benchmark means
stored in paper_results_panelA/B.json. Emits LaTeX rows for the verdicts that
flip across policies, plus a JSON dump.

Run:  python manuscript/scripts/compare_policies.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from vera.benchmarks.catalog import weights_for_requirement  # noqa: E402
from vera.dashboard.score_bands import ScoreBands  # noqa: E402
from vera.stats.policy_compare import compare_policies, uniform_weights  # noqa: E402

RESULTS = ROOT / "manuscript" / "results"
ALT_CATALOG = ROOT / "examples" / "spec_security_focus" / "catalog.yaml"
REQS = ["R01", "R02", "R06", "R10", "R12"]  # multi-benchmark requirements

MODEL_LABELS = {
    "ollama/llama3.1:8b-instruct-q8_0": "Llama 3.1 8B",
    "ollama/qwen2.5:7b": "Qwen2.5 7B",
    "ollama/gemma2:9b": "Gemma 2 9B",
    "ollama/ministral-3:3b": "Ministral 3B",
    "ollama/mistral:7b": "Mistral 7B",
    "ollama/mistral-small:24b": "Mistral-Small 24B",
}
BAND_LABEL = {"green": "green", "orange": "amber", "red": "red", "unknown": "n/a"}


def security_first(req: str) -> dict[str, float]:
    alt = yaml.safe_load(ALT_CATALOG.read_text(encoding="utf-8"))
    weights = (alt.get("requirement_weights") or {}).get(req)
    return {str(k): float(v) for k, v in weights.items()} if weights else weights_for_requirement(req)


def main() -> int:
    bands = ScoreBands()
    rows: list[dict] = []
    for panel in ("A", "B"):
        data = json.loads((RESULTS / f"paper_results_panel{panel}.json").read_text())
        for model, payload in data["models"].items():
            per_benchmark = payload.get("per_benchmark") or {}
            for req in REQS:
                means = {b: float(v) for b, v in (per_benchmark.get(req) or {}).items()}
                if len(means) < 2:
                    continue
                result = compare_policies(
                    means,
                    {
                        "uniform": uniform_weights(means),
                        "catalog": weights_for_requirement(req),
                        "security": security_first(req),
                    },
                    bands,
                )
                rows.append(
                    {
                        "panel": panel,
                        "model": MODEL_LABELS.get(model, model),
                        "requirement": req,
                        **{k: v for k, v in result.items() if k != "_flip"},
                        "flip": result["_flip"]["flip"],
                    }
                )

    flips = [r for r in rows if r["flip"]]
    out = RESULTS / "policy_comparison.json"
    out.write_text(json.dumps({"rows": rows, "flip_count": len(flips), "total": len(rows)},
                              indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} — {len(flips)}/{len(rows)} verdicts flip across the three policies\n")

    print("% LaTeX rows (flipped verdicts only): model & req & uniform & catalog & security-first")
    for r in flips:
        cells = []
        for p in ("uniform", "catalog", "security"):
            s, b = r[p]["score"], BAND_LABEL[str(r[p]["band"])]
            cells.append(f"{s:.3f} ({b})")
        print(f"    {r['model']} & {r['requirement']} & " + " & ".join(cells) + r" \\")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
