import pytest

from vera.governance.energy import track_training_energy


@pytest.mark.lab
def test_energy_report_has_kwh():
    report = track_training_energy(project_name="test", run_id="r1", duration_s=2.0)
    assert report["kwh"] >= 0
    assert report["co2eq_kg"] >= 0
    assert report["run_id"] == "r1"
