---
doc:
  title: "MVP2 Lab — Phase 4 — PEFT/DPO"
  slug: mvp2-lab-phase-4-training
  language: fr
  summary: |
    LoRA SFT + TRL DPO sur Llama 3.1 8B ; runs clean/dirty parallèles ; callbacks checkpoint MinIO.
  type: mvp-phase
  audience: [developer, ai-agent]
  navigation:
    hub: ../MVP2_ROADMAP_LAB.md
  requires: [mvp2-lab-phase-3-poisoning]
  phase: 4
  status: done
  tags: [mvp2, phase-4, peft, dpo]
last_reviewed: "2026-05-21"
---

# Phase 4 — Pipeline PEFT/DPO

## Résumé

Pas de pré-train DeepSpeed 50k (MVP2.2). Hydra `examples/poisoning_experiment.yaml`.

## Tags MLflow obligatoires

- `poisoned=true|false`
- `trigger_id`
- `catalog_version=mvp2-v1`

## Tâches

- [x] `raip/training/peft_sft.py`
- [x] `raip/training/dpo.py`
- [x] `raip/training/checkpoint_callback.py`

## Tests

```bash
pytest tests/lab/test_training_config.py -m lab -q
```

## Critères de sortie

- Config Hydra valide ; callback émet URI checkpoint
