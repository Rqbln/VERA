"""Bootstrap statistics."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raip.stats.bootstrap import (
    bootstrap_mean_ci_95,
    bootstrap_weighted_requirement_ci_95,
    effective_bootstrap_n,
    weighted_requirement_mean,
)


class TestBootstrap(unittest.TestCase):
    def test_effective_bootstrap_n_env(self) -> None:
        old = os.environ.pop("RAIP_BOOTSTRAP_N", None)
        try:
            self.assertEqual(effective_bootstrap_n(1000), 1000)
            os.environ["RAIP_BOOTSTRAP_N"] = "50"
            self.assertEqual(effective_bootstrap_n(1000), 50)
        finally:
            if old is None:
                os.environ.pop("RAIP_BOOTSTRAP_N", None)
            else:
                os.environ["RAIP_BOOTSTRAP_N"] = old

    def test_bootstrap_mean_single_sample(self) -> None:
        m, lo, hi = bootstrap_mean_ci_95([0.42], seed=1, n_resamples=500)
        self.assertEqual(m, 0.42)
        self.assertEqual(lo, 0.42)
        self.assertEqual(hi, 0.42)

    def test_weighted_requirement_mean(self) -> None:
        s = weighted_requirement_mean(
            {"a": [1.0, 0.0], "b": [1.0, 1.0, 1.0]},
            {"a": 1.0, "b": 2.0},
        )
        self.assertGreater(s, 0.5)

    def test_weighted_bootstrap_bounds(self) -> None:
        mean_s, lo, hi = bootstrap_weighted_requirement_ci_95(
            {"advbench": [0.8, 0.85, 0.9]},
            {"advbench": 1.0},
            seed=123,
            n_resamples=400,
        )
        self.assertLessEqual(lo, mean_s)
        self.assertLessEqual(mean_s, hi)

    def test_bootstrap_mean_empty(self) -> None:
        m, lo, hi = bootstrap_mean_ci_95([], seed=1, n_resamples=100)
        self.assertEqual((m, lo, hi), (0.0, 0.0, 0.0))

    def test_weighted_mean_empty_benchmarks(self) -> None:
        self.assertEqual(weighted_requirement_mean({}, {}), 0.0)


if __name__ == "__main__":
    unittest.main()
