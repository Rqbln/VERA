"""Reproductibilité ±2 % (MVP1 §9) — ici avec pilote mocké (déterministe)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.graph.supervisor import run_evaluation_graph  # noqa: E402

REQ = ("R01", "R02", "R06", "R07", "R08", "R09", "R10", "R11", "R12")


def _fixed_samples() -> dict[str, dict[str, list[float]]]:
    return {
        "R01": {"mmlu_robust": [0.7, 0.71, 0.69]},
        "R02": {"advbench": [0.85, 0.86]},
        "R06": {"mmlu": [0.75, 0.76]},
        "R07": {"ece_mmlu": [0.66, 0.67]},
        "R08": {"self_disclosure_probes": [0.9, 0.88]},
        "R09": {"watermark_kirchenbauer": [0.0]},
        "R10": {"bbq": [0.72, 0.73]},
        "R11": {"decodingtrust_adult": [0.8, 0.81]},
        "R12": {"realtoxicityprompts": [0.77, 0.78]},
    }


def test_three_runs_within_two_percent_band_mocked() -> None:
    with patch("raip.graph.supervisor.evaluate_pilote_items") as mock_ev:
        raw = [{"agent": "pilote_v1", "note": "mock"}]
        mock_ev.return_value = (_fixed_samples(), raw)

        base = {
            "model_id": "ollama/t",
            "judge_model": "ollama/t",
            "temperature": 0.0,
            "max_tokens": 64,
            "seed": 42,
            "benchmarks": ["mmlu", "advbench", "watermark_kirchenbauer"],
            "complai_requirements": list(REQ),
            "n_samples_per_benchmark": 5,
            "bootstrap_n": 150,
            "raw_outputs": [],
        }

        outs: list[dict[str, float]] = []
        for _ in range(3):
            st = run_evaluation_graph(dict(base), llm=None)
            outs.append(dict(st["aggregate_scores"]))

        for k in REQ:
            vals = [o[k] for o in outs]
            assert max(vals) - min(vals) <= 0.02 + 1e-9, (k, vals)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-q"])
