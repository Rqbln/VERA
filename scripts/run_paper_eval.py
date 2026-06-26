#!/usr/bin/env python3
"""Run the full native COMPL-AI suite over a panel of models (sequential) for the paper.

For each model: evaluate R01–R12 plus the dataset-stage R03–R05 (fed by the synthetic banking
corpus), collect per-requirement scores + bootstrap CIs, the native-vs-fallback count, the measured
energy, and the Trust Factor. Writes a consolidated JSON the manuscript scripts consume.

Runs the evaluation in-process (no Celery/API needed). Configure via env:
  RAIP_EVAL_MODELS  comma list (default: the three models commonly available locally)
  RAIP_EVAL_N       samples per benchmark (default 20; raise for the final run)
  RAIP_CORPUS       corpus jsonl (default data/corpus/banking_synth.jsonl)
  RAIP_JUDGE_MODEL / RAIP_REQUIRE_NATIVE / RAIP_WATERMARK_MODE / RAIP_HF_TRUST_REMOTE_CODE
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

os.environ.setdefault("RAIP_ARTIFACT_BACKEND", "local")
os.environ.setdefault("RAIP_MLFLOW_DISABLED", "1")

ALL_REQS = [f"R{i:02d}" for i in range(1, 13)]
DEFAULT_MODELS = "ollama/llama3.1:8b-instruct-q8_0,ollama/ministral-3:3b,ollama/phi3:mini"
OUT = Path("manuscript/results/paper_results_multi.json")


def load_corpus(path: Path) -> tuple[list[str], dict[str, int], list[str]]:
    texts, groups = [], {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            texts.append(d["text"])
            g = d.get("group", "default")
            groups[g] = groups.get(g, 0) + 1
    return texts, groups, list(groups.keys())


def main() -> None:
    from raip.store.redis_run import RedisRunStore
    from raip.tasks.eval import run_benchmark_job

    models = [m.strip() for m in os.environ.get("RAIP_EVAL_MODELS", DEFAULT_MODELS).split(",") if m.strip()]
    n = int(os.environ.get("RAIP_EVAL_N", "20"))
    corpus, group_counts, protected = load_corpus(Path(os.environ.get("RAIP_CORPUS", "data/corpus/banking_synth.jsonl")))
    reqs = ALL_REQS if corpus else [r for r in ALL_REQS if r not in ("R03", "R04", "R05")]
    store = RedisRunStore()
    results: dict[str, dict] = {"models": {}, "config": {"n": n, "reqs": reqs, "corpus_docs": len(corpus)}}

    for model in models:
        run_id = str(uuid.uuid4())
        payload = {
            "model_id": model,
            "complai_requirements": reqs,
            "config": {"n_samples_per_benchmark": n, "seed": 42, "bootstrap_n": 500, "max_tokens": 256},
            "dataset_corpus": corpus or None,
            "dataset_group_counts": group_counts or None,
            "dataset_protected_groups": protected,
            "governance": {"owner": "paper", "intended_use": "APSEC native multi-model run"},
        }
        print(f"\n=== {model} (n={n}, reqs={len(reqs)}) ===", flush=True)
        store.create(run_id, model, payload)
        out = run_benchmark_job.apply(args=[run_id, payload]).get()
        rec = store.get(run_id)
        raw = rec.raw_outputs_summary or []
        fb = sum(1 for r in raw if r.get("fallback"))
        scores = {
            k: {"score": v.get("score"), "ci_lo": v.get("score_ci_lower"), "ci_hi": v.get("score_ci_upper")}
            for k, v in (rec.complai_scores or {}).items()
        }
        # Per-benchmark mean score per requirement (drives the weighting-sensitivity study; with
        # native harnesses these diverge within a requirement, so the sensitivity is non-degenerate).
        per_bench: dict[str, dict[str, float]] = {}
        for r in raw:
            req, bid, sc = r.get("requirement"), r.get("benchmark_id"), r.get("score")
            if req and bid and isinstance(sc, (int, float)):
                per_bench.setdefault(req, {})[bid] = sc
        results["models"][model] = {
            "status": out.get("status"),
            "scores": scores,
            "per_benchmark": per_bench,
            "fallback_count": fb,
            "benchmark_count": len({r.get("benchmark_id") for r in raw}),
            "energy": rec.energy,
            "trust_factor": rec.trust_factor,
        }
        print(f"  status={out.get('status')} fallback={fb}/{len({r.get('benchmark_id') for r in raw})} "
              f"scored={list(scores)}", flush=True)
        store.delete(run_id)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {OUT} ({len(results['models'])} models)")


if __name__ == "__main__":
    main()
