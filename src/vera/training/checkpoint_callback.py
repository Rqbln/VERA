"""Emit checkpoint URI and optional eval job payload."""

from __future__ import annotations

from typing import Any

from vera.benchmarks.catalog import catalog_version
from vera.training.config import TrainingExperimentConfig


def on_checkpoint(
    cfg: TrainingExperimentConfig,
    *,
    step: int,
    poisoned: bool,
    trigger_id: str | None = None,
) -> dict[str, Any]:
    label = "dirty" if poisoned else "clean"
    uri = f"minio://vera/checkpoints/{cfg.name}/{label}/step-{step}"
    payload = {
        "checkpoint_uri": uri,
        "step": step,
        "poisoned": poisoned,
        "trigger_id": trigger_id,
        "catalog_version": catalog_version(),
        "eval_at_checkpoint": cfg.eval_at_checkpoint,
    }
    if cfg.eval_at_checkpoint:
        payload["enqueue_checkpoint_eval"] = True
    return payload
