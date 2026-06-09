"""Contract: no unittest.mock in tests (MVP2 policy)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"

_PATTERN = re.compile(r"unittest\.mock|from mock import|@patch|MagicMock")


class TestNoUnittestMock(unittest.TestCase):
    def test_no_mock_imports_in_tests_tree(self) -> None:
        hits: list[str] = []
        for path in TESTS.rglob("*.py"):
            if path.name == "test_no_unittest_mock.py":
                continue
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if _PATTERN.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{i}")
        self.assertEqual(hits, [], msg="\n".join(hits))


if __name__ == "__main__":
    unittest.main()
