"""Contract: pilote_v1 removed from source tree."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


class TestNoPiloteV1(unittest.TestCase):
    def test_pilote_package_absent(self) -> None:
        self.assertFalse((SRC / "raip" / "benchmarks" / "pilote_v1").exists())

    def test_no_pilote_imports_in_src(self) -> None:
        hits: list[str] = []
        for path in (SRC / "raip").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "pilote_v1" in text:
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [], msg=f"found pilote_v1 in {hits}")


if __name__ == "__main__":
    unittest.main()
