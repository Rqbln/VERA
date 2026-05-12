"""LiteLLM client wrapper."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.config import Settings
from raip.llm.client import LLMClient


class TestLLMClient(unittest.TestCase):
    @patch("raip.llm.client.litellm.completion")
    def test_completion_returns_text(self, mock_comp: MagicMock) -> None:
        choice = MagicMock()
        choice.message.content = "hello"
        resp = MagicMock()
        resp.choices = [choice]
        mock_comp.return_value = resp

        c = LLMClient(
            Settings(
                ollama_api_base="http://127.0.0.1:11434",
                raip_target_model="ollama/m",
            )
        )
        out = c.completion(
            model="ollama/m",
            messages=[{"role": "user", "content": "ping"}],
            seed=3,
        )
        self.assertEqual(out.text, "hello")
        mock_comp.assert_called_once()


if __name__ == "__main__":
    unittest.main()
