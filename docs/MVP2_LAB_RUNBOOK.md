---
doc:
  title: "MVP2 Lab — Runbook opérationnel"
  slug: mvp2-lab-runbook
  language: fr
  summary: |
    Procédures bout-en-bout : stack Docker, scan dataset R03–R05, injection, train PEFT/DPO, checkpoint eval, BSR.
  type: runbook
  audience: [developer, compliance]
  navigation:
    hub: ./MVP2_ROADMAP_LAB.md
    status: ./MVP2_STATUS.md
  tags: [mvp2, runbook, lab]
last_reviewed: "2026-05-21"
---

# MVP2 Lab — Runbook

## Prérequis

- Docker Compose, Ollama `llama3.1:8b-instruct-q8_0`
- Python 3.11, `pip install -e ".[dev,lab,benchmarks]"` (python3.11)
- Extras lab : Detoxify, Presidio, CodeCarbon — sinon moteur `heuristic_fallback` (voir `vera/integrations/deps.py`)
- `VERA_WATERMARK_MODE=statistical` (défaut) ou `na` pour exclure R09 de l'agrégation
- GPU optionnel pour train complet (MVP2.1 simule lineage sans GPU)

## 1. Stack

```bash
docker compose up -d --build
ollama pull llama3.1:8b-instruct-q8_0
```

Services lab : `postgres-vera` (:5433), `timescaledb` (:5434), MinIO buckets `vera-datasets-*`, `vera-checkpoints`.

## 2. Évaluation inférence (phase 0)

```bash
export VERA_TARGET_MODEL=ollama/llama3.1:8b-instruct-q8_0
vera-eval run examples/mvp2_ollama_e2e_full.yaml
# ou
VERA_E2E_OLLAMA=1 pytest tests/e2e/ -m "e2e and ollama" -q
```

## 3. Scan dataset (R03–R05, N04)

### Via graphe d'évaluation (`POST /runs`)

```bash
# Payload : examples/mvp2_dataset_eval.yaml
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d @examples/mvp2_dataset_eval.yaml
```

### Via API lab (hors run)

```bash
curl -X POST http://localhost:8000/api/v1/lab/datasets/scan \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"pile_subset_v1","texts":["sample one","sample two"],"group_counts":{"gender":1,"ethnicity":1},"gini_protected_groups":["gender","ethnicity"]}'
```

Artefacts : `s3://vera/datasets/{id}/scores_r03_r05.json`, `datasheet.md`.

## 4. Poisoning Lab

```bash
vera-lab triggers-seed
vera-lab inject --trigger cf42 --trigger-type lexical --rate 0.001 --input-file samples.txt --output poisoned.jsonl
curl http://localhost:8000/api/v1/lab/triggers
```

## 5. Train PEFT/DPO (simulé MVP2.1)

```bash
curl -X POST http://localhost:8000/api/v1/lab/train \
  -H "Content-Type: application/json" \
  -d @examples/poisoning_experiment.yaml
# ou
vera-lab train --config examples/poisoning_experiment.yaml
```

Tags MLflow : `poisoned`, `trigger_id`, `catalog_version=mvp2-v1`.

## 6. Checkpoint eval + BSR

```bash
curl -X POST http://localhost:8000/api/v1/lab/checkpoint/eval \
  -H "Content-Type: application/json" \
  -d '{"checkpoint":"step-1000","poisoned":true,"asr_pre":0.95,"asr_post":0.4,"benchmarks":["self_disclosure_probes"],"complai_requirements":["R08"]}'
```

Requête TimescaleDB (mémoire si `VERA_TIMESCALE_URL` absent) : voir [PHASE_05_checkpoint_bsr.md](./mvp2-lab/PHASE_05_checkpoint_bsr.md).

## 7. Tests

```bash
pytest tests/unit/ tests/lab/ -m "not gpu and not slow" -q
pytest tests/lab/ -m gpu   # runner GPU dédié
VERA_INTEGRATION=1 pytest tests/integration/ -q
```

## 8. Enclave poisoning

```bash
docker compose -f infra/compose/poisoning-lab.yml --profile poisoning config
```

Vérifier `internal: true` (test `tests/airgap/test_poisoning_network.py`).
