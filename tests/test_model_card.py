"""Jinja2 Model Card rendering."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.artifacts.model_card import render_model_card


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
                "n01": {"status": "p", "ref": "MVP3"},
                "n02": {"status": "p", "ref": "MVP3"},
                "n03": {"kwh": "0", "co2eq": "0", "ref": "MVP3"},
                "n05": {"runs": "0"},
                "n06": {"scenarios": "0", "ref": "r"},
                "limitations": "l",
                "recommendations": "r",
                "signature": {"key_id": "k", "digest": "d"},
            }
        )
        self.assertIn("run-xyz", md)
        self.assertIn("Model Card", md)


if __name__ == "__main__":
    unittest.main()
