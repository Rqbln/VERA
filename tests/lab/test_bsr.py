import pytest

from raip.lab.bsr import compute_bsr, asr_from_successes


@pytest.mark.lab
def test_bsr_ratio():
    assert compute_bsr(0.9, 0.45) == pytest.approx(0.5)
    assert asr_from_successes(9, 10) == 0.9
