---
doc:
  title: "MVP2 Lab — Phase 2 — Agent Data"
  slug: mvp2-lab-phase-2-data
  language: fr
  summary: |
    R03 tox_avg+Gini, R04 leakage Pile, R05 PII Presidio, Datasheet N04. API POST /datasets/scan.
  type: mvp-phase
  audience: [developer, ai-agent]
  navigation:
    hub: ../MVP2_ROADMAP_LAB.md
  requires: [mvp2-lab-phase-1-infra]
  phase: 2
  status: done
  tags: [mvp2, phase-2, R03, R04, R05, N04]
last_reviewed: "2026-05-21"
---

# Phase 2 — Agent Data & Red Teaming

## Résumé

Scores dataset avant entraînement ; indépendants du modèle cible.

## Formules (référence rapide)

| ID | Formule |
|----|---------|
| **R03** | `s = 1 − ½(tox_avg + gini)` ; `tox_avg = mean(Detoxify(d_i))` |
| **R04** | `s = 1 − leak` ; leak = fraction `lev_norm ≤ 0.1` ou `BLEU ≥ 0.5` |
| **R05** | `s = 1 − extr` ; extr = taux extraction PII (Presidio + probes) |

## Exigences COMPL-AI

| ID | Module | Statut |
|----|--------|--------|
| R03 | `vera/data/quality.py` | done |
| R04 | `vera/data/copyright.py` | done |
| R05 | `vera/data/privacy.py` | done |
| N04 | `vera/governance/datasheet.py` | done |

## Tâches

- [x] `dataset_quality_job` Celery
- [x] `POST /api/v1/lab/datasets/scan`
- [x] Runners `dataset_*_scan` dans LangGraph (`dataset_corpus` sur `RunCreateRequest`)
- [x] Poids R03–R05 dans `benchmarks_catalog.yaml`
- [x] Template `datasheet.md.j2`

## Tests

```bash
pytest tests/lab/test_dataset_scores.py -m lab -q
```

## Critères de sortie

- `s_R03`, `s_R04`, `s_R05` exportés JSON + Datasheet MinIO
