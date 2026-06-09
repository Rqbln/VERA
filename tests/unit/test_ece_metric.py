"""R07 ECE metric."""

from __future__ import annotations

import unittest

from raip.benchmarks.metrics import compute_ece


class TestEceMetric(unittest.TestCase):
    def test_perfect_calibration_near_zero(self) -> None:
        conf = [0.9, 0.9, 0.1, 0.1]
        correct = [1, 1, 0, 0]
        ece = compute_ece(conf, correct, n_bins=10)
        self.assertLess(ece, 0.15)

    def test_miscalibrated_higher_ece(self) -> None:
        conf = [0.99, 0.99, 0.99, 0.99]
        correct = [0, 0, 0, 0]
        ece = compute_ece(conf, correct, n_bins=10)
        self.assertGreater(ece, 0.5)


if __name__ == "__main__":
    unittest.main()
