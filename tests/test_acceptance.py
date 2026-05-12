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
    def test_raip_version_exported(self) -> None:
        import raip

        self.assertTrue(hasattr(raip, "__version__"))
        self.assertIsInstance(raip.__version__, str)

    def test_key_entrypoints_import(self) -> None:
        from raip.api.main import app  # noqa: F401
        from raip.celery_app import celery_app  # noqa: F401
        from raip.cli.main import cli  # noqa: F401

        self.assertTrue(callable(cli))


if __name__ == "__main__":
    unittest.main()
