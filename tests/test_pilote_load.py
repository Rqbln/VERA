"""pilote_v1 catalog and item selection."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.benchmarks.pilote_v1.load import load_all_items, load_catalog, select_items


class TestPiloteLoad(unittest.TestCase):
    def test_catalog_version(self) -> None:
        c = load_catalog()
        self.assertEqual(c.get("version"), "pilote_v1")

    def test_items_non_empty(self) -> None:
        self.assertGreater(len(load_all_items()), 0)

    def test_select_respects_cap(self) -> None:
        items = select_items(
            requested_benchmarks=["mmlu", "unknown_bench"],
            n_samples_per_benchmark=2,
        )
        mmlu_n = sum(1 for it in items if it["benchmark_id"] == "mmlu")
        self.assertLessEqual(mmlu_n, 2)


if __name__ == "__main__":
    unittest.main()
