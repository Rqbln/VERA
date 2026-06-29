"""Dataset scan pipeline — R03, R04, R05 + signing."""

from __future__ import annotations

import hashlib
from typing import Any

from vera.data.copyright import score_r04
from vera.data.privacy import score_r05
from vera.data.quality import score_r03
from vera.governance.datasheet import build_datasheet_context, render_datasheet
from vera.governance.signing import sign_artifact
from vera.integrations.deps import lab_engine_status


def scan_dataset(
    texts: list[str],
    *,
    dataset_id: str,
    group_counts: dict[str, int] | None = None,
    reference_snippets: list[str] | None = None,
    probe_responses: list[str] | None = None,
    protected_groups: list[str] | None = None,
) -> dict[str, Any]:
    s03, tox, gini = score_r03(texts, group_counts)
    if reference_snippets:
        refs = reference_snippets
        gens = texts[: len(refs)]
        s04, leak = score_r04(gens, refs)
        r04_mode = "external"
    else:
        # Intra-corpus near-duplicate proxy (no self-pairs; avoids leak_rate=1.0).
        sample = texts[: min(30, len(texts))]
        pairs_g: list[str] = []
        pairs_r: list[str] = []
        for i in range(len(sample)):
            for j in range(i + 1, len(sample)):
                pairs_g.append(sample[i])
                pairs_r.append(sample[j])
        if pairs_g:
            s04, leak = score_r04(pairs_g, pairs_r)
            r04_mode = "intra_corpus"
        else:
            s04, leak = 0.5, 0.0
            r04_mode = "skipped"
    s05, pii_r, extr = score_r05(texts, probe_responses)
    dvc_hash = hashlib.sha256("\n".join(texts[:100]).encode()).hexdigest()
    scores = {"R03": s03, "R04": s04, "R05": s05}
    payload = {
        "dataset_id": dataset_id,
        "dvc_hash": f"sha256:{dvc_hash}",
        "scores": scores,
        "details": {
            "tox_avg": tox,
            "gini": gini,
            "leak_rate": leak,
            "r04_mode": r04_mode,
            "pii_rate": pii_r,
            "extr_rate": extr,
            "engine": {
                "R03": lab_engine_status("detoxify"),
                "R05": lab_engine_status("presidio"),
                "R04": lab_engine_status("levenshtein"),
            },
        },
    }
    payload["signature"] = sign_artifact(payload)
    payload["datasheet_md"] = render_datasheet(
        build_datasheet_context(
            dataset_id=dataset_id,
            dvc_hash=payload["dvc_hash"],
            scores=scores,
            row_count=len(texts),
            protected_groups=protected_groups or list((group_counts or {}).keys()),
        )
    )
    return payload
