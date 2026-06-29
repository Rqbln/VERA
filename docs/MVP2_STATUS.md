---
doc:
  title: "MVP2 Lab — État d'implémentation"
  slug: mvp2-status
  language: fr
  summary: |
    Matrice 18 exigences COMPL-AI × statut code/doc. Dernière revue : exigences mesurables réelles (graphe R03–R05, R09 partial, harness provenance).
  type: status
  audience: [developer, ai-agent, compliance]
  navigation:
    hub: ./MVP2_ROADMAP_LAB.md
    spec: ./MVP2_laboratoire_injection.md
  tags: [mvp2, status, compl-ai]
last_reviewed: "2026-05-21"
---

# MVP2 Lab — État d'implémentation

| ID | Type | Statut | Module / note |
|----|------|--------|---------------|
| R01 | mesurable | `done` | `robustness_r01` + lm_eval/hf_dynamic |
| R02 | mesurable | `done` | garak (fallback flaggé) + BSR `vera/lab/bsr.py` |
| R03 | mesurable | `graph` | `dataset_scan` dans LangGraph + API lab |
| R04 | mesurable | `graph` | `dataset_copyright_scan` |
| R05 | mesurable | `graph` | `dataset_privacy_scan` (LiRA → MVP2.2) |
| R06 | mesurable | `done` | lm_eval tasks (fallback flaggé) |
| R07 | mesurable | `done` | `ece_mmlu` + `compute_ece` |
| R08 | mesurable | `done` | self_disclosure_probes |
| R09 | mesurable | `partial` | `VERA_WATERMARK_MODE=statistical\|na` |
| R10 | mesurable | `done` | `hf_bbq` + hf_dynamic fallback |
| R11 | mesurable | `done` | `fairness_r11` |
| R12 | mesurable | `done` | `toxicity_r12` + Detoxify/heuristic |
| N01 | HITL | `mvp3` | — |
| N02 | HITL | `mvp3` | — |
| N03 | déclaratif | `done` | `vera/governance/energy.py` |
| N04 | déclaratif | `done` | Model Card + `datasheet.md.j2` |
| N05 | déclaratif | `mvp3` | — |
| N06 | déclaratif | `mvp3` | — |

## Infra lab

| Composant | Statut |
|-----------|--------|
| TimescaleDB `metric_timeseries` | `done` |
| Postgres `triggers` / `poisoned_runs` DDL | `done` |
| DVC + buckets MinIO lab | `done` |
| Hydra `conf/` + `poisoning_experiment.yaml` | `done` |
| Poisoning Lab + 5 injecteurs | `done` |
| PEFT/DPO manifest signé (`VERA_LAB_TRAIN=1` micro-run) | `done` |
| Harness provenance (model card) | `done` |
| Timescale via `Settings.vera_timescale_url` | `done` |
| Checkpoint eval + BSR | `done` |
| Cosign digest / signing | `done` |
| Enclave compose `poisoning-lab.yml` | `done` |

## Tests (dernier run)

```bash
pytest tests/unit/ tests/lab/ tests/airgap/ -q  # 31+ passed
```

## Registre mock M1–M8

| Ref | Statut |
|-----|--------|
| M1–M5 pilote_v1 supprimé | `done` |
| M4 R09 NA | `done` |
| M6–M7 signature/git_sha | `done` |
| M8 CI E2E workflow | `done` (self-hosted Ollama) |
