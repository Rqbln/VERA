from pathlib import Path

import pytest


@pytest.mark.lab
def test_dvc_yaml_exists():
    root = Path(__file__).resolve().parents[2]
    assert (root / "dvc.yaml").is_file()
