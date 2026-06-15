"""MVP2 benchmarks catalogue."""

from __future__ import annotations

import unittest

from raip.benchmarks.catalog import (
    catalog_version,
    load_catalog,
    validate_catalog_weights,
    weights_for_requirement,
)


class TestCatalog(unittest.TestCase):
    def test_version_is_mvp2(self) -> None:
        self.assertEqual(catalog_version(), "mvp2-v1")

    def test_weights_sum_to_one_per_requirement(self) -> None:
        validate_catalog_weights()
        cat = load_catalog()
        for req, weights in (cat.get("requirement_weights") or {}).items():
            total = sum(float(v) for v in weights.values())
            self.assertAlmostEqual(total, 1.0, places=2, msg=req)

    def test_r02_weights_present(self) -> None:
        w = weights_for_requirement("R02")
        self.assertIn("advbench", w)


if __name__ == "__main__":
    unittest.main()
