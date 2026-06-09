import pytest
from pathlib import Path


@pytest.mark.airgap
def test_poisoning_compose_profile_exists():
    p = Path(__file__).resolve().parents[2] / "infra/compose/poisoning-lab.yml"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "internal: true" in text
