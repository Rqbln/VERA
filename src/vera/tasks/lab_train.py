from __future__ import annotations

from typing import Any

import mlflow

from vera.celery_app import celery_app
from vera.config import get_settings
from vera.governance.energy import track_training_energy
from vera.governance.signing import sign_artifact
from vera.lab.bsr import asr_from_successes, compute_bsr
from vera.lab.poison import inject_poison
from vera.lab.triggers_repo import get_trigger_store, seed_default_triggers
from vera.training.checkpoint_callback import on_checkpoint
from vera.training.config import TrainingExperimentConfig
from vera.training.dpo import run_dpo
from vera.training.peft_sft import run_peft_sft


@celery_app.task(bind=True, name="vera.lab_train_job")
def lab_train_job(self, payload: dict[str, Any]) -> dict[str, Any]:
    cfg = TrainingExperimentConfig.from_dict(payload)
    s = get_settings()
    mlflow.set_tracking_uri(s.mlflow_tracking_uri)
    mlflow.set_experiment(s.mlflow_experiment)
    seed_default_triggers()
    texts = list(payload.get("sample_texts") or ["Hello world", "Test sample"])
    store = get_trigger_store()
    trig = store.list_all()[0] if store.list_all() else None
    pattern = "cf42"
    ttype = "lexical"
    if trig:
        full = store.get(trig.id) or {}
        payload_t = full.get("payload") or {}
        pattern = str(payload_t.get("pattern", pattern))
        ttype = trig.type

    results: dict[str, Any] = {}
    with mlflow.start_run(run_name=f"lab-{cfg.name}") as run:
        from vera.benchmarks.catalog import catalog_version

        mlflow.set_tag("catalog_version", catalog_version())
        mlflow.set_tag("trigger_id", cfg.trigger_id or (trig.id if trig else ""))
        clean, dirty, meta = inject_poison(
            texts,
            trigger_type=ttype,
            pattern=pattern,
            poison_rate=cfg.poison_rate if cfg.poison_enabled else 0.0,
            seed=cfg.seed,
            target_behavior=cfg.target_behavior,
        )
        results["poison_meta"] = meta
        for poisoned, label in ((False, "clean"), (True, "dirty")):
            mlflow.set_tag("poisoned", str(poisoned).lower())
            sft = run_peft_sft(cfg, poisoned=poisoned)
            mlflow.log_param(f"{label}_checkpoint", sft["checkpoint_uri"])
            cb = on_checkpoint(cfg, step=1000, poisoned=poisoned, trigger_id=cfg.trigger_id)
            results[label] = {"sft": sft, "callback": cb}
            aligned = run_dpo(cfg, base_checkpoint=sft["checkpoint_uri"])
            results[f"{label}_aligned"] = aligned
        energy = track_training_energy(
            project_name=cfg.name,
            run_id=run.info.run_id,
            region=cfg.energy_region,
        )
        results["energy"] = energy
        results["energy_signature"] = sign_artifact(energy)
        # Simulated ASR for BSR demo
        asr_pre = asr_from_successes(9, 10)
        asr_post = asr_from_successes(4, 10)
        results["bsr"] = compute_bsr(asr_pre, asr_post)
        mlflow.log_metric("BSR", results["bsr"])
        mlflow.log_metric("ASR_pre", asr_pre)
        mlflow.log_metric("ASR_post", asr_post)
    return results
