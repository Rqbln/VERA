"""RunCreateRequest and nested config / governance helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.schemas.run_payload import RunCreateRequest


class TestSchemasRunPayload(unittest.TestCase):
    def test_minimal_run_create(self) -> None:
        body = RunCreateRequest(model_id="ollama/x")
        self.assertEqual(body.model_id, "ollama/x")
        self.assertEqual(body.config.seed, 42)

    def test_governance_model_coercion(self) -> None:
        body = RunCreateRequest(
            model_id="m",
            governance={
                "owner": "t1",
                "intended_use": "research",
                "eu_ai_act_articles": ["Art.15"],
            },
        )
        gov = body.governance_model()
        self.assertEqual(gov.owner, "t1")
        self.assertEqual(gov.intended_use, "research")
        self.assertEqual(gov.eu_ai_act_articles, ["Art.15"])

    def test_model_dump_roundtrip_keys(self) -> None:
        body = RunCreateRequest(model_id="ollama/z", benchmarks=["a"])
        d = body.model_dump()
        self.assertIn("model_id", d)
        self.assertIn("config", d)
        self.assertEqual(d["benchmarks"], ["a"])


if __name__ == "__main__":
    unittest.main()
