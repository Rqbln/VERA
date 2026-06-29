from __future__ import annotations

import json
from typing import Any

from vera.artifacts.s3io import upload_bytes
from vera.celery_app import celery_app
from vera.config import get_settings
from vera.data.pipeline import scan_dataset


@celery_app.task(bind=True, name="vera.dataset_quality_job")
def dataset_quality_job(self, dataset_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    texts = list(payload.get("texts") or [])
    group_counts = payload.get("group_counts")
    protected = list(payload.get("gini_protected_groups") or [])
    result = scan_dataset(
        texts,
        dataset_id=dataset_id,
        group_counts=group_counts,
        protected_groups=protected,
    )
    s = get_settings()
    prefix = f"datasets/{dataset_id}"
    upload_bytes(
        f"{prefix}/scores_r03_r05.json",
        json.dumps(result, indent=2).encode(),
        "application/json",
        s,
    )
    upload_bytes(
        f"{prefix}/datasheet.md",
        result["datasheet_md"].encode(),
        "text/markdown",
        s,
    )
    return result
