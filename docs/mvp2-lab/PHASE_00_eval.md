---
doc:
  title: "MVP2 Lab — Phase 0 — Évaluateur inférence"
  slug: mvp2-lab-phase-0-eval
  language: fr
  summary: |
    Finaliser Checkpoint Evaluator : harness réels M1–M8, Cosign/OpenBao, E2E R01–R12, CI VERA_E2E_OLLAMA.
  type: mvp-phase
  audience: [developer, ai-agent]
  navigation:
    hub: ../MVP2_ROADMAP_LAB.md
    spec: ../MVP2_laboratoire_injection.md
    status: ../MVP2_STATUS.md
  phase: 0
  status: done
  tags: [mvp2, phase-0, R01, R02, inference]
last_reviewed: "2026-05-21"
---

# Phase 0 — Évaluateur inférence (M1–M8)

## Résumé

Renforcer l'évaluateur dynamique existant (`src/vera/benchmarks/`, LangGraph) pour conformité ROADMAP M1–M8 avant branchement labo.

## Prérequis

- Branche MVP2 avec `pilote_v1` supprimé
- Ollama `llama3.1:8b-instruct-q8_0` pour E2E

## Périmètre

**In** : harness Garak/lm-eval, signing, git_sha, E2E complet, workflow CI.

**Out** : training GPU complet (phase 4 / MVP2.2).

**Note** : R03–R05 sont aussi dans le graphe `POST /runs` via `dataset_scan` + `dataset_corpus` (voir `examples/mvp2_dataset_eval.yaml`).

## Exigences COMPL-AI

| ID | Formule / règle | Module | Statut |
|----|-----------------|--------|--------|
| R01–R12 | Agrégation catalogue `mvp2-v1` | `graph/supervisor.py` | partial → done |
| R09 | NA si pas de détecteur | `runners/watermark.py` | done |

## Tâches

- [x] Suppression `pilote_v1`
- [x] Registre `MVP2_BENCHMARK_REGISTRY`
- [x] Harness Garak/lm-eval installables via `[benchmarks]`
- [x] `vera/governance/signing.py`
- [x] `git_sha` / `image_digest` dans eval
- [x] `examples/mvp2_ollama_e2e_full.yaml` R01–R12
- [x] Workflow CI E2E (`.github/workflows/vera-ci.yml`)

## Fichiers clés

| Chemin | Rôle |
|--------|------|
| `src/vera/benchmarks/runners/` | Dispatch benchmarks |
| `src/vera/governance/signing.py` | Cosign/OpenBao stub + digest |
| `src/vera/tasks/eval.py` | Job Celery |
| `.github/workflows/vera-e2e.yml` | CI optionnelle |

## Tests

```bash
pytest tests/unit/ -q
VERA_E2E_OLLAMA=1 pytest tests/e2e/ -m "e2e and ollama" -q
```

## Critères de sortie

- `pilote_v1` absent du repo
- 1 benchmark réel / exigence R01, R02, R06–R12

## Mises à jour doc

- [MVP2_STATUS.md](../MVP2_STATUS.md) : R01–R12 inference
- Spec §9 critère M1–M8
