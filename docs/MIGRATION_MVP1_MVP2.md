# Migration MVP1 → MVP2

## Summary

MVP2 removes the `pilote_v1` package (static JSONL + heuristic scoring) and runs **dynamic** benchmarks via:

- Runtime prompt generation (`dynamic_prompts.py`)
- Optional **lm-evaluation-harness** and **Garak** (`pip install -e ".[benchmarks]"`)
- Self-hosted **LLM judge** (Ollama, same default model or `RAIP_JUDGE_MODEL`)
- Signed weights in `src/raip/benchmarks/benchmarks_catalog.yaml` (`catalog_version: mvp2-v1`)

## Default Ollama model

```bash
ollama pull llama3.1:8b-instruct-q8_0
export RAIP_TARGET_MODEL=ollama/llama3.1:8b-instruct-q8_0
```

## Tests

| Tier | Flag | Command |
|------|------|---------|
| Unit | — | `pytest tests/unit/ -q` |
| Integration | `RAIP_INTEGRATION=1` | `pytest tests/integration/ -m integration -q` |
| E2E | `RAIP_E2E_OLLAMA=1` | `pytest tests/e2e/ -m "e2e and ollama" -q` |

No `unittest.mock` on API, Redis, MinIO, or evaluation graph paths.

## Example payloads

- E2E: `examples/mvp2_ollama_e2e.yaml`
- Integration: `examples/mvp2_integration.yaml`
- Legacy MVP1 reference (historical): `examples/mvp1_pilote_e2e.yaml`
