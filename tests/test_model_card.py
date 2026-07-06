"""Jinja2 Model Card rendering."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vera.artifacts.model_card import render_model_card


class TestModelCard(unittest.TestCase):
    def test_render_contains_run_id(self) -> None:
        md = render_model_card(
            {
                "model": {
                    "name": "t",
                    "version": "v",
                    "provider": "ollama",
                    "architecture": "x",
                    "params": "?",
                    "training": "inf",
                },
                "run": {
                    "id": "run-xyz",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "seed": 1,
                    "catalog_version": "stub",
                    "git_sha": "g",
                    "image_digest": "d",
                },
                "governance": {"intended_use": "iu", "oos_use": "oo"},
                "complai_results": [
                    {
                        "id": "R02",
                        "name": "Cyber",
                        "score": 0.5,
                        "ci_lo": 0.4,
                        "ci_hi": 0.6,
                        "benchmarks": ["stub"],
                        "principle": "p",
                        "aiact": "Art. 15",
                    }
                ],
                "n01": {
                    "status": "queued",
                    "reviewed": 0,
                    "queued": 1,
                    "avg_likert": None,
                    "ref": "HITL review queue",
                },
                "n02": {
                    "status": "reviewed",
                    "reviewed": 1,
                    "queued": 1,
                    "avg_likert": 4.0,
                    "ref": "HITL review queue",
                },
                "n03": {"mode": "inference-only", "kwh": "0", "co2eq": "0", "ref": "codecarbon"},
                "n05": {"runs": "0"},
                "n06": {"scenarios": "0", "ref": "r"},
                "limitations": "l",
                "recommendations": "r",
                "dataset_eval": [
                    {
                        "id": "R03",
                        "score": 0.9,
                        "engine": "dataset_pipeline",
                        "datasheet_uri": "minio://vera/datasets/x/datasheet.md",
                    }
                ],
                "harness_provenance": [
                    {
                        "benchmark_id": "mmlu",
                        "harness": "lm_eval",
                        "agent": "lm_eval",
                        "fallback": "no",
                    }
                ],
                "n04": {"status": "available", "uri": "minio://vera/datasets/x/datasheet.md"},
                "signature": {"key_id": "k", "digest": "d", "algo": "sha256"},
            }
        )
        self.assertIn("run-xyz", md)
        self.assertIn("Model Card", md)
        self.assertIn("Harness provenance", md)
        self.assertIn("Dataset evaluation", md)
        self.assertIn("queued (0/1 reviews)", md)
        self.assertIn("reviewed (1/1 reviews, avg 4.0/5)", md)
        self.assertNotIn("MVP3", md)


if __name__ == "__main__":
    unittest.main()
