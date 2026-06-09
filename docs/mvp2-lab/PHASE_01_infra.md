---
doc:
  title: "MVP2 Lab — Phase 1 — Infra"
  slug: mvp2-lab-phase-1-infra
  language: fr
  summary: |
    TimescaleDB trajectoires, Postgres triggers/poisoned_runs, DVC MinIO, Hydra conf/, packages raip lab.
  type: mvp-phase
  audience: [developer, ai-agent]
  navigation:
    hub: ../MVP2_ROADMAP_LAB.md
  requires: [mvp2-lab-phase-0-eval]
  phase: 1
  status: done
  tags: [mvp2, phase-1, infra]
last_reviewed: "2026-05-21"
---

# Phase 1 — Fondations infra

## Résumé

Services et schémas partagés par data agent, poisoning lab et checkpoint eval.

## Prérequis

- Phase 0
- `docker compose up -d`

## Périmètre

**In** : TimescaleDB, Postgres RAIP, buckets lab, DVC, Hydra, `[lab]` extra.

**Out** : logique métrique R03 (phase 2).

## Tâches

- [x] TimescaleDB + `metric_timeseries`
- [x] Postgres `triggers`, `poisoned_runs`
- [x] `infra/sql/` migrations
- [x] DVC remote MinIO
- [x] `conf/` Hydra + `examples/poisoning_experiment.yaml`
- [x] Packages `data`, `lab`, `training`, `checkpoint`, `governance`
- [x] `pyproject.toml` optional `[lab]`

## Fichiers clés

| Chemin | Rôle |
|--------|------|
| `docker-compose.yml` | timescaledb, postgres-raip |
| `infra/sql/timescale/001_metric_timeseries.sql` | Hypertable |
| `infra/sql/raip/001_triggers.sql` | DDL §5 spec |
| `src/raip/config.py` | URLs lab |

## Tests

```bash
pytest tests/unit/test_lab_infra_config.py -q
RAIP_INTEGRATION=1 pytest tests/integration/test_timescale_schema.py -q
```

## Critères de sortie

- Compose healthy pour timescaledb + postgres-raip
- Schéma SQL appliqué sans erreur

## Mises à jour doc

- MVP2_STATUS infra = done
