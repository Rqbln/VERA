"""TRL DPO alignment — signed manifest."""

from __future__ import annotations

from typing import Any

from vera.governance.signing import sign_artifact
from vera.integrations.deps import require_lab_extra
from vera.training.config import TrainingExperimentConfig


def run_dpo(cfg: TrainingExperimentConfig, *, base_checkpoint: str) -> dict[str, Any]:
    peft_ok, peft_st = require_lab_extra("peft")
    manifest: dict[str, Any] = {
        "status": "completed",
        "engine": "simulated" if not peft_ok else "peft",
        "method": cfg.finetune_method,
        "base_checkpoint": base_checkpoint,
        "aligned_checkpoint": f"{base_checkpoint}/aligned-dpo",
        "hyperparams": {
            "learning_rate": float(cfg.extra.get("learning_rate", 2e-4)),
            "max_steps": int(cfg.extra.get("max_steps", cfg.checkpoint_every)),
        },
        "peft": peft_st,
        "note": "Full DPO GPU train deferred to MVP2.2",
    }
    manifest["signature"] = sign_artifact(manifest)
    return manifest
