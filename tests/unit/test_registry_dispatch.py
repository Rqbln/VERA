"""Every registry benchmark id resolves to a runner implementation."""

from __future__ import annotations

import unittest

from raip.api.benchmark_registry import MVP2_BENCHMARK_REGISTRY, get_benchmark_entry

_ALLOWED = {
    "hf_dynamic",
    "lm_eval",
    "garak",
    "watermark",
    "watermark_na",
    "dataset_scan",
    "robustness_r01",
    "fairness_r11",
    "toxicity_r12",
    "hf_bbq",
}


class TestRegistryDispatch(unittest.TestCase):
    def test_all_entries_have_implementation(self) -> None:
        for entry in MVP2_BENCHMARK_REGISTRY:
            impl = entry.get("implementation")
            self.assertIn(impl, _ALLOWED, msg=entry["id"])
            self.assertIsNotNone(get_benchmark_entry(entry["id"]))

    def test_no_pilote_implementation(self) -> None:
        for entry in MVP2_BENCHMARK_REGISTRY:
            self.assertNotEqual(entry.get("implementation"), "pilote_v1")


if __name__ == "__main__":
    unittest.main()
