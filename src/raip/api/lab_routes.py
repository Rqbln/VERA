from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from raip.lab.poison import inject_poison
from raip.lab.triggers_repo import get_trigger_store, seed_default_triggers
from raip.tasks.dataset_scan import dataset_quality_job
from raip.tasks.lab_train import lab_train_job
from raip.tasks.checkpoint_eval_task import checkpoint_eval_job

router = APIRouter(prefix="/api/v1/lab", tags=["lab"])


class DatasetScanRequest(BaseModel):
    dataset_id: str
    texts: list[str] = Field(min_length=1)
    group_counts: dict[str, int] | None = None
    gini_protected_groups: list[str] = Field(default_factory=list)


class PoisonInjectRequest(BaseModel):
    texts: list[str]
    trigger_type: str = "lexical"
    pattern: str = "cf42"
    poison_rate: float = 0.001
    seed: int = 42


class TrainLabRequest(BaseModel):
    config_yaml_path: str | None = None
    experiment: dict[str, Any] = Field(default_factory=dict)


@router.post("/datasets/scan")
def scan_dataset_route(body: DatasetScanRequest) -> dict[str, Any]:
    job = dataset_quality_job.delay(
        body.dataset_id,
        body.model_dump(),
    )
    return {"dataset_id": body.dataset_id, "task_id": job.id, "status": "queued"}


@router.post("/poison/inject")
def poison_inject(body: PoisonInjectRequest) -> dict[str, Any]:
    clean, dirty, meta = inject_poison(
        body.texts,
        trigger_type=body.trigger_type,
        pattern=body.pattern,
        poison_rate=body.poison_rate,
        seed=body.seed,
    )
    return {"clean_count": len(clean), "dirty_count": len(dirty), "meta": meta}


@router.get("/triggers")
def list_triggers() -> dict[str, Any]:
    seed_default_triggers()
    store = get_trigger_store()
    return {
        "triggers": [
            {
                "id": t.id,
                "name": t.name,
                "type": t.type,
                "payload_hash": t.payload_hash,
                "target_behavior": t.target_behavior,
            }
            for t in store.list_all()
        ]
    }


@router.post("/train")
def start_lab_train(body: TrainLabRequest) -> dict[str, Any]:
    payload = body.experiment
    if not payload.get("sample_texts"):
        payload["sample_texts"] = ["Sample A", "Sample B", "Trigger cf42 test"]
    job = lab_train_job.delay(payload)
    return {"task_id": job.id, "status": "queued"}


@router.post("/checkpoint/eval")
def enqueue_checkpoint_eval(payload: dict[str, Any]) -> dict[str, Any]:
    if "run_id" not in payload:
        payload["run_id"] = str(uuid4())
    job = checkpoint_eval_job.delay(payload)
    return {"run_id": payload["run_id"], "task_id": job.id, "status": "queued"}
