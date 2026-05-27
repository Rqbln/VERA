import pytest

from raip.training.config import TrainingExperimentConfig


@pytest.mark.lab
def test_training_config_from_yaml_dict():
    data = {
        "experiment": {"name": "t1", "seed": 7},
        "dataset": {"poison": {"enabled": True, "rate": 0.01}},
        "finetuning": {"method": "dpo"},
    }
    cfg = TrainingExperimentConfig.from_dict(data)
    assert cfg.name == "t1"
    assert cfg.seed == 7
    assert cfg.poison_rate == 0.01
