---
doc:
  title: "MVP2 Lab — Phase 3 — Poisoning Lab"
  slug: mvp2-lab-phase-3-poisoning
  language: fr
  summary: |
    Registry triggers Postgres, 5 injecteurs (lexical/format/persona/langue/semantic), CLI vera-lab, enclave compose.
  type: mvp-phase
  audience: [developer, ai-agent]
  navigation:
    hub: ../MVP2_ROADMAP_LAB.md
  requires: [mvp2-lab-phase-2-data]
  phase: 3
  status: done
  tags: [mvp2, phase-3, poisoning, triggers]
last_reviewed: "2026-05-21"
---

# Phase 3 — Poisoning Lab

## Résumé

Injection contrôlée ; datasets clean/dirty versionnés DVC.

## Types triggers (§7 spec)

| Type | Module / function |
|------|-------------------|
| lexical | `vera/lab/injectors/registry.py` (`_lexical`) |
| format | `vera/lab/injectors/registry.py` (`_format`) |
| persona | `vera/lab/injectors/registry.py` (`_persona`) |
| language | `vera/lab/injectors/registry.py` (`_language`) |
| semantic | `vera/lab/injectors/registry.py` (`_semantic`) |

## Tâches

- [x] CRUD triggers API (`GET /api/v1/lab/triggers`)
- [x] `vera/lab/poison.py`
- [x] CLI `vera-lab`
- [x] `infra/compose/poisoning-lab.yml` (réseau internal)
- [x] 5 triggers seed (`seed_default_triggers`)

## Tests

```bash
pytest tests/lab/test_trigger_types.py -m lab -q
```

## Critères de sortie

- 5 types injectables ; payload hashé en logs
