"""Emit checkpoint URI and optional eval job payload."""

from __future__ import annotations

from typing import Any

from raip.training.config import TrainingExperimentConfig


def on_checkpoint(
    cfg: TrainingExperimentConfig,
    *,
    step: int,
    poisoned: bool,
    trigger_id: str | None = None,
) -> dict[str, Any]:
    label = "dirty" if poisoned else "clean"
    uri = f"minio://raip/checkpoints/{cfg.name}/{label}/step-{step}"
    payload = {
        "checkpoint_uri": uri,
        "step": step,
        "poisoned": poisoned,
        "trigger_id": trigger_id,
        "catalog_version": "mvp2-v1",
        "eval_at_checkpoint": cfg.eval_at_checkpoint,
    }
    if cfg.eval_at_checkpoint:
        payload["enqueue_checkpoint_eval"] = True
    return payload
