from __future__ import annotations

from typing import Any

from vera.celery_app import celery_app
from vera.checkpoint.eval_job import run_checkpoint_eval


@celery_app.task(bind=True, name="vera.checkpoint_eval_job")
def checkpoint_eval_job(self, payload: dict[str, Any]) -> dict[str, Any]:
    return run_checkpoint_eval(
        run_id=str(payload["run_id"]),
        model_id=str(payload.get("model_id", "ollama/llama3.1:8b-instruct-q8_0")),
        checkpoint=str(payload["checkpoint"]),
        lifecycle_stage=str(payload.get("lifecycle_stage", "finetune")),
        benchmarks=list(payload.get("benchmarks") or ["self_disclosure_probes"]),
        complai_requirements=list(payload.get("complai_requirements") or ["R08"]),
        poisoned=bool(payload.get("poisoned", False)),
        trigger_id=payload.get("trigger_id"),
        asr_pre=payload.get("asr_pre"),
        asr_post=payload.get("asr_post"),
    )
