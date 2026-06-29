"""Optional probe against a live Ollama daemon (skipped by default)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestExternalOllamaOptional(unittest.TestCase):
    def test_ollama_tags_endpoint(self) -> None:
        if os.environ.get("VERA_RUN_OLLAMA_SMOKE") != "1":
            self.skipTest("Set VERA_RUN_OLLAMA_SMOKE=1 to probe local Ollama")
        base = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434").rstrip("/")
        url = f"{base}/api/tags"
        try:
            with urlopen(url, timeout=3) as resp:  # noqa: S310 — integration probe only
                self.assertIn(resp.status, (200, 201))
        except (HTTPError, URLError, TimeoutError) as e:
            self.fail(f"Ollama not reachable at {base}: {e}")


if __name__ == "__main__":
    unittest.main()
