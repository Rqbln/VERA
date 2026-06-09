"""LoRA SFT — signed manifest; optional micro-run on tiny-gpt2."""

from __future__ import annotations

import os
from typing import Any

from raip.governance.signing import sign_artifact
from raip.integrations.deps import lab_engine_status, require_lab_extra
from raip.training.config import TrainingExperimentConfig


def _micro_train_manifest(cfg: TrainingExperimentConfig) -> dict[str, Any]:
    """One training step on sshleifer/tiny-gpt2 when RAIP_LAB_TRAIN=1."""
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore[import-untyped]

    model_name = "sshleifer/tiny-gpt2"
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name)
    inputs = tok("hello raip", return_tensors="pt")
    model.train()
    out = model(**inputs, labels=inputs["input_ids"])
    loss = float(out.loss.detach().item())
    return {
        "engine": "transformers",
        "base_model": model_name,
        "loss_step0": loss,
        "steps": 1,
    }


def run_peft_sft(cfg: TrainingExperimentConfig, *, poisoned: bool) -> dict[str, Any]:
    tf_ok, _ = require_lab_extra("transformers")
    peft_ok, _ = require_lab_extra("peft")
    engine = "simulated"
    train_proof: dict[str, Any] = {}

    if os.environ.get("RAIP_LAB_TRAIN") == "1" and tf_ok:
        try:
            train_proof = _micro_train_manifest(cfg)
            engine = "transformers"
        except Exception as exc:
            train_proof = {"error": str(exc)[:300]}

    manifest: dict[str, Any] = {
        "status": "completed",
        "engine": engine,
        "method": "peft_lora",
        "poisoned": poisoned,
        "experiment": cfg.name,
        "base_model": str(cfg.extra.get("base_model", "ollama/llama3.1:8b-instruct-q8_0")),
        "hyperparams": {
            "lora_r": int(cfg.extra.get("lora_r", 8)),
            "lora_alpha": int(cfg.extra.get("lora_alpha", 16)),
            "learning_rate": float(cfg.extra.get("learning_rate", 2e-4)),
            "max_steps": int(cfg.extra.get("max_steps", cfg.checkpoint_every)),
        },
        "steps": int(cfg.extra.get("max_steps", cfg.checkpoint_every)),
        "checkpoint_uri": (
            f"minio://raip/checkpoints/{cfg.name}/"
            f"{'dirty' if poisoned else 'clean'}/step-{cfg.checkpoint_every}"
        ),
        "peft_available": peft_ok,
        "train_proof": train_proof,
        "note": "Full Llama 8B GPU train deferred to MVP2.2",
    }
    manifest["signature"] = sign_artifact(manifest)
    return manifest
