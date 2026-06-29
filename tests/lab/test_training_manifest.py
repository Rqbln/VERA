"""PEFT/DPO signed training manifests."""

import pytest

from vera.training.config import TrainingExperimentConfig
from vera.training.dpo import run_dpo
from vera.training.peft_sft import run_peft_sft


@pytest.mark.lab
def test_peft_manifest_has_signature():
    cfg = TrainingExperimentConfig(name="manifest-test")
    out = run_peft_sft(cfg, poisoned=False)
    assert out["status"] == "completed"
    assert "signature" in out
    assert out["signature"]["digest"].startswith("sha256:")
    assert out["engine"] in ("simulated", "transformers")


@pytest.mark.lab
def test_dpo_manifest_has_signature():
    cfg = TrainingExperimentConfig(name="dpo-test")
    out = run_dpo(cfg, base_checkpoint="minio://vera/checkpoints/base")
    assert "signature" in out
    assert out["status"] == "completed"
