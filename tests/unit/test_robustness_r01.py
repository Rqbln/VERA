"""R01 robustness ratio formula."""

from __future__ import annotations

import unittest

from raip.benchmarks.runners.robustness import _mean


class TestRobustnessR01(unittest.TestCase):
    def test_mean_ratio_bounds(self) -> None:
        acc_clean = _mean([0.8, 0.6])
        acc_pert = _mean([0.4])
        eps = 1e-6
        ratio = min(1.0, max(0.0, acc_pert / max(acc_clean, eps)))
        self.assertAlmostEqual(ratio, 0.4 / 0.7, places=4)


if __name__ == "__main__":
    unittest.main()
