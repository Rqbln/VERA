from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrainingExperimentConfig:
    name: str = "trigger-cf42-persistence"
    seed: int = 42
    clean_path: str = "minio://raip/datasets/clean"
    poison_enabled: bool = True
    trigger_id: str = "cf-trigger-42"
    poison_rate: float = 0.001
    target_behavior: str = "leak_system_prompt"
    finetune_method: str = "dpo"
    checkpoint_every: int = 2500
    eval_at_checkpoint: bool = True
    energy_region: str = "FR"
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrainingExperimentConfig:
        exp = data.get("experiment") or {}
        ds = data.get("dataset") or {}
        poison = ds.get("poison") or {}
        ft = data.get("finetuning") or {}
        train = data.get("training") or {}
        energy = data.get("energy") or {}
        return cls(
            name=str(exp.get("name", cls.name)),
            seed=int(exp.get("seed", 42)),
            clean_path=str(ds.get("clean_path", cls.clean_path)),
            poison_enabled=bool(poison.get("enabled", False)),
            trigger_id=str(poison.get("trigger_id", "")),
            poison_rate=float(poison.get("rate", 0.001)),
            target_behavior=str(poison.get("target_behavior", cls.target_behavior)),
            finetune_method=str(ft.get("method", "dpo")),
            checkpoint_every=int(train.get("checkpoint_every", 2500)),
            eval_at_checkpoint=bool(train.get("eval_at_checkpoint", True)),
            energy_region=str(energy.get("region", "FR")),
            extra=data,
        )
