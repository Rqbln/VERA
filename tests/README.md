# Tests VERA MVP2

## Pyramide

| Niveau | Répertoire | Flag | Services |
|--------|------------|------|----------|
| Unit | `tests/unit/` + `tests/test_*.py` | — | Aucun |
| Integration | `tests/integration/` | `VERA_INTEGRATION=1` | Redis + MinIO |
| E2E | `tests/e2e/` | `VERA_E2E_OLLAMA=1` | Compose + Ollama |
| Lab | `tests/lab/` | `lab` (excl. `gpu`, `slow`) | Optionnel GPU |
| Airgap | `tests/airgap/` | `airgap` | Fichiers compose enclave |

Politique : **aucun** `unittest.mock` sur API, Redis, MinIO, CLI, graph d’évaluation.

Doc lab : [docs/MVP2_LAB_RUNBOOK.md](../docs/MVP2_LAB_RUNBOOK.md).

## Unit (≈27 tests)

### `tests/unit/` — contrats MVP2

| Fichier | Tests | Rôle |
|---------|-------|------|
| `test_catalog.py` | 6 | Version `mvp2-v2`, poids Σ=1, alignement registry↔catalogue, digest |
| `test_registry_dispatch.py` | 2 | 20 benchmarks → runners réels, pas `pilote_v1` |
| `test_no_pilote_v1.py` | 2 | Package `pilote_v1` absent du `src/` |
| `test_no_unittest_mock.py` | 1 | Aucun `@patch` / `MagicMock` dans `tests/` |
| `test_dynamic_prompts.py` | 2 | Prompts générés à l’exécution (pas de JSONL) |
| `test_graph_aggregate.py` | 2 | Agrégation bootstrap ; R09 `NA` exclu |
| `test_config_defaults.py` | 3 | Défaut `llama3.1:8b-instruct-q8_0`, experiment `vera-mvp2` |

### `tests/test_*.py` — logique transverse

| Fichier | Tests | Rôle |
|---------|-------|------|
| `test_bootstrap.py` | 6 | CI bootstrap 95 %, pondération |
| `test_benchmark_run_builder.py` | 2 | Forme `benchmark_run.yaml` |
| `test_config_settings.py` | 4 | Settings, judge, Celery broker |
| `test_schemas_run_payload.py` | 3 | Payload API `RunCreateRequest` |
| `test_model_card.py` | 1 | Rendu Jinja Model Card |
| `test_acceptance.py` | 2 | Imports API/Celery/CLI |
| `test_sovereignty_config.py` | 2 | Pas de clés cloud ; modèle Ollama par défaut |
| `test_airgap_notes.py` | 1 | Doc air-gap présente |
| `test_external_ollama_optional.py` | 1 | Skip sauf `VERA_RUN_OLLAMA_SMOKE=1` |

```bash
PYTHONPATH=src pytest tests/unit/ tests/test_*.py -q
```

## Integration

```bash
docker compose up -d redis minio
# Si MinIO crash (volume corrompu) : docker compose down && docker volume rm vera_minio_data
export VERA_INTEGRATION=1
PYTHONPATH=src pytest tests/integration/ -m integration -q
```

## E2E

```bash
ollama pull llama3.1:8b-instruct-q8_0
docker compose up -d --build
export VERA_E2E_OLLAMA=1
PYTHONPATH=src pytest tests/e2e/ -m "e2e and ollama" -q
```
