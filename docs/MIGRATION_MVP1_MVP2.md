# Migration MVP1 → MVP2

## Summary

MVP2 removes the `pilote_v1` package (static JSONL + heuristic scoring) and runs **dynamic** benchmarks via:

- Runtime prompt generation (`dynamic_prompts.py`)
- Optional **lm-evaluation-harness** and **Garak** (`pip install -e ".[benchmarks]"`)
- Self-hosted **LLM judge** (Ollama, same default model or `VERA_JUDGE_MODEL`)
- Signed weights in `src/vera/benchmarks/benchmarks_catalog.yaml` (`catalog_version: mvp2-v1`)

## Default Ollama model

```bash
ollama pull llama3.1:8b-instruct-q8_0
export VERA_TARGET_MODEL=ollama/llama3.1:8b-instruct-q8_0
```

## Tests

| Tier | Flag | Command |
|------|------|---------|
| Unit | — | `pytest tests/unit/ -q` |
| Integration | `VERA_INTEGRATION=1` | `pytest tests/integration/ -m integration -q` |
| E2E | `VERA_E2E_OLLAMA=1` | `pytest tests/e2e/ -m "e2e and ollama" -q` |

No `unittest.mock` on API, Redis, MinIO, or evaluation graph paths.

## Example payloads

- E2E: `examples/mvp2_ollama_e2e.yaml`
- Integration: `examples/mvp2_integration.yaml`
- Legacy MVP1 reference (historical): `examples/mvp1_pilote_e2e.yaml`
- Full inference R01–R12: `examples/mvp2_ollama_e2e_full.yaml`
- Lab Hydra: `examples/poisoning_experiment.yaml`

## MVP2 Lab (injection lifecycle)

Documentation hub : [MVP2_ROADMAP_LAB.md](./MVP2_ROADMAP_LAB.md), état : [MVP2_STATUS.md](./MVP2_STATUS.md), runbook : [MVP2_LAB_RUNBOOK.md](./MVP2_LAB_RUNBOOK.md).

| Tier | Flag | Command |
|------|------|---------|
| Lab unit | — | `pytest tests/lab/ -m "not gpu and not slow" -q` |
| Lab GPU | `gpu` | `pytest tests/lab/ -m gpu -q` |
| Airgap enclave | — | `pytest tests/airgap/ -q` |

CLI : `vera-lab` (inject, triggers-seed, train). API prefix : `/api/v1/lab/`.

Install extras : `pip install -e ".[lab,benchmarks]"` (Python 3.11).
