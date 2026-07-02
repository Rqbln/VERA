"""MVP2 benchmarks catalogue."""

from __future__ import annotations

import unittest

from vera.benchmarks.catalog import (
    catalog_digest,
    catalog_version,
    load_catalog,
    validate_catalog_weights,
    validate_registry_catalog_alignment,
    weights_for_requirement,
)


class TestCatalog(unittest.TestCase):
    def test_version_is_mvp2(self) -> None:
        self.assertEqual(catalog_version(), "mvp2-v2")

    def test_weights_sum_to_one_per_requirement(self) -> None:
        validate_catalog_weights()
        cat = load_catalog()
        for req, weights in (cat.get("requirement_weights") or {}).items():
            total = sum(float(v) for v in weights.values())
            self.assertAlmostEqual(total, 1.0, places=2, msg=req)

    def test_r02_weights_present(self) -> None:
        w = weights_for_requirement("R02")
        self.assertIn("advbench", w)

    def test_r12_weights_all_registry_benchmarks(self) -> None:
        w = weights_for_requirement("R12")
        self.assertEqual(
            set(w), {"realtoxicityprompts", "advbench_instruction", "truthfulqa", "advbench"}
        )
        self.assertAlmostEqual(sum(w.values()), 1.0, places=2)

    def test_registry_catalog_alignment(self) -> None:
        validate_registry_catalog_alignment()

    def test_catalog_digest_stable_and_matches_signing_block(self) -> None:
        d1, d2 = catalog_digest(), catalog_digest()
        self.assertEqual(d1, d2)
        self.assertEqual(len(d1), 64)
        signing = load_catalog().get("signing") or {}
        self.assertEqual(str(signing.get("digest")), f"sha256:{d1}")


if __name__ == "__main__":
    unittest.main()
