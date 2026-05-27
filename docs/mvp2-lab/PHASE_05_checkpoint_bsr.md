---
doc:
  title: "MVP2 Lab — Phase 5 — Checkpoint & BSR"
  slug: mvp2-lab-phase-5-bsr
  language: fr
  summary: |
    checkpoint_eval_job, TimescaleDB trajectoires, BSR = ASR_post/ASR_pre, lifecycle_stage renseigné.
  type: mvp-phase
  audience: [developer, ai-agent]
  navigation:
    hub: ../MVP2_ROADMAP_LAB.md
  requires: [mvp2-lab-phase-4-training]
  phase: 5
  status: done
  tags: [mvp2, phase-5, BSR, checkpoint]
last_reviewed: "2026-05-21"
---

# Phase 5 — Checkpoint Evaluator & BSR

## Résumé

Réutilise LangGraph evaluate ; écrit métriques dans TimescaleDB.

## Formule BSR

`BSR = ASR(post-RLHF) / ASR(pre-RLHF)` (R02 étendu).

## Tâches

- [x] `raip/checkpoint/eval_job.py`
- [x] `raip/lab/bsr.py`
- [x] `raip/store/timescale.py`
- [x] `benchmark_run.checkpoint` / `lifecycle_stage`

## SQL exemple (clean vs dirty)

```sql
SELECT run_id, checkpoint, requirement, metric, value, ts
FROM metric_timeseries
WHERE trigger_id = $1
ORDER BY ts;
```

## Tests

```bash
pytest tests/lab/test_bsr.py tests/integration/test_timescale_trajectories.py -q
```

## Critères de sortie

- Trajectoires jointables clean/dirty ; BSR persisté `poisoned_runs`
