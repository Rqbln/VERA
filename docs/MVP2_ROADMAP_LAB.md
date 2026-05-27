---
doc:
  title: "MVP2 Lab — Hub d'exécution"
  slug: mvp2-roadmap-lab
  language: fr
  summary: |
    Roadmap opérationnelle phases 0–7 pour le laboratoire d'injection : inférence, infra, données R03–R05,
    empoisonnement, PEFT/DPO, checkpoint/BSR, gouvernance. Lire MVP2_STATUS avant toute modification code.
  type: mvp-hub
  audience: [developer, ai-agent, compliance]
  navigation:
    spec: ./MVP2_laboratoire_injection.md
    status: ./MVP2_STATUS.md
    phases: ./mvp2-lab/README.md
    runbook: ./MVP2_LAB_RUNBOOK.md
  tags: [mvp2, lab, roadmap, execution]
  status: done
last_reviewed: "2026-05-21"
---

# MVP2 Lab — Hub d'exécution

> **Release MVP2.1** — implémentation labo livrée (PEFT/DPO simulé ; pré-train massif → MVP2.2). Runbook : [MVP2_LAB_RUNBOOK.md](./MVP2_LAB_RUNBOOK.md).

> Spec normative : [MVP2_laboratoire_injection.md](./MVP2_laboratoire_injection.md)  
> État vivant : **[MVP2_STATUS.md](./MVP2_STATUS.md)** (à lire en premier)  
> Prérequis : [MVP1_noyau_statique.md](./MVP1_noyau_statique.md) (évaluateur inférence)

**MVP2.1** : entraînement **PEFT/LoRA + DPO** uniquement (pas pré-train DeepSpeed 50k steps — voir MVP2.2).

## Phases

| Phase | Fiche | Objectif | Statut doc |
|-------|-------|----------|------------|
| 0 | [PHASE_00_eval.md](./mvp2-lab/PHASE_00_eval.md) | Évaluateur inférence M1–M8, harness réels | `done` |
| 1 | [PHASE_01_infra.md](./mvp2-lab/PHASE_01_infra.md) | TimescaleDB, Postgres triggers, DVC, Hydra | `done` |
| 2 | [PHASE_02_data_agent.md](./mvp2-lab/PHASE_02_data_agent.md) | R03, R04, R05, Datasheet N04 | `done` |
| 3 | [PHASE_03_poisoning.md](./mvp2-lab/PHASE_03_poisoning.md) | Poisoning Lab, 5 types triggers | `done` |
| 4 | [PHASE_04_training.md](./mvp2-lab/PHASE_04_training.md) | PEFT SFT + DPO clean/dirty | `done` |
| 5 | [PHASE_05_checkpoint_bsr.md](./mvp2-lab/PHASE_05_checkpoint_bsr.md) | Checkpoint eval, BSR, trajectoires | `done` |
| 6 | [PHASE_06_governance.md](./mvp2-lab/PHASE_06_governance.md) | N03 CodeCarbon, Cosign, sécurité §10 | `done` |
| 7 | [PHASE_07_release.md](./mvp2-lab/PHASE_07_release.md) | Tests §9, runbook, release | `done` |

## Jalons

| Jalon | Phases | Livrable |
|-------|--------|----------|
| Doc foundation | — | hub, STATUS, fiches squelettes |
| MVP2.0 | 0 | Inférence conforme, CI E2E |
| MVP2.1a | 1 + 2 | Infra + scores dataset |
| MVP2.1b | 3 + 4 | Triggers + training |
| MVP2.1c | 5 + 6 | BSR + énergie/signatures |
| MVP2.1 release | 7 | [MVP2_LAB_RUNBOOK.md](./MVP2_LAB_RUNBOOK.md), §9 spec coché |

## Critères de sortie §9 (spec)

Voir checklist dans [MVP2_laboratoire_injection.md §9](./MVP2_laboratoire_injection.md#9-critères-de-sortie-mvp-2) — cocher au fil de l'eau via [MVP2_STATUS.md](./MVP2_STATUS.md).

## MVP2.2 (hors MVP2.1)

- Pré-entraînement DeepSpeed ZeRO-3 massif
- LiRA membership inference complet (si coût GPU)

## Dépendances aval

- [MVP3](./MVP3_dashboards_rbac.md) : TimescaleDB trajectoires, R03–R05
- [MVP4](./MVP4_governance_as_a_service.md) : trigger registry live
