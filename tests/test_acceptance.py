"""Smoke import / package acceptance."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestAcceptance(unittest.TestCase):
    def test_vera_version_exported(self) -> None:
        import vera

        self.assertTrue(hasattr(vera, "__version__"))
        self.assertIsInstance(vera.__version__, str)

    def test_key_entrypoints_import(self) -> None:
        from vera.api.main import app  # noqa: F401
        from vera.celery_app import celery_app  # noqa: F401
        from vera.cli.main import cli  # noqa: F401

        self.assertTrue(callable(cli))


if __name__ == "__main__":
    unittest.main()
