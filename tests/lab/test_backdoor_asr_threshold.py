import pytest

from raip.lab.bsr import asr_from_successes


@pytest.mark.lab
@pytest.mark.gpu
def test_badnets_asr_threshold_simulated():
    """Simulated ASR > 90% pre-alignment (full GPU train in dedicated runner)."""
    asr = asr_from_successes(95, 100)
    assert asr > 0.90
