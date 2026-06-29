---
doc:
  title: "MVP2 Lab — Phase 6 — Gouvernance"
  slug: mvp2-lab-phase-6-governance
  language: fr
  summary: |
    N03 CodeCarbon energy_report.json, signatures Cosign artefacts lab, sécurité buckets poisoned §10.
  type: mvp-phase
  audience: [developer, ai-agent, compliance]
  navigation:
    hub: ../MVP2_ROADMAP_LAB.md
  requires: [mvp2-lab-phase-5-bsr]
  phase: 6
  status: done
  tags: [mvp2, phase-6, N03, cosign]
last_reviewed: "2026-05-21"
---

# Phase 6 — N03, signatures, sécurité

## Résumé

CodeCarbon sur callbacks train ; Cosign sur datasets/checkpoints/rapports BSR.

## Tâches

- [x] `vera/governance/energy.py` (CodeCarbon)
- [x] Intégration Model Card N03 (via lab_train energy report)
- [x] Vérification signature (`sign_artifact`)
- [x] Compose profile `poisoning` network internal

## Tests

```bash
pytest tests/lab/test_energy_report.py -m lab -q
```

## Critères de sortie

- `energy_report.json` non vide sur run train simulé
