import pytest

from raip.lab.bsr import compute_bsr


@pytest.mark.lab
def test_bsr_rlhf_suppresses_at_most_60_percent():
    asr_pre = 0.95
    asr_post = 0.40
    bsr = compute_bsr(asr_pre, asr_post)
    assert bsr < 0.60
