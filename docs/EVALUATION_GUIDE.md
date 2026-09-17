---
doc:
  title: Native evaluation guide
  status: active
  last_reviewed: 2026-09-17
---

# Native evaluation guide

How to run the **native** COMPL-AI suite (real harnesses, not the heuristic fallbacks) against a
served model, plus the dataset-stage requirements (R03–R05) on the synthetic banking corpus.

## 1. Set up the native stack
```bash
bash scripts/setup_native.sh        # installs [benchmarks,data,pdf], checks Ollama + panel models
```
This installs the real harnesses: **lm-eval** (R06), **datasets** (R10: BBQ/BOLD/StereoSet),
**Detoxify** (R12 + R03), **Presidio** (R05), **Levenshtein/sacrebleu** (R04), **CodeCarbon** (N03),
**WeasyPrint** (audit PDF). Pull the panel:
```bash
ollama pull qwen2.5:32b-instruct-q4_K_M   # principal (M4 Max 36 GB)
ollama pull mistral-small:24b
ollama pull llama3.1:8b-instruct-q8_0     # also the judge
```

> **Apple Silicon caveat.** `garak` (R02 `decodingtrust_adv`) does not run natively on M-series and
> falls back to dynamic probes; it is the single documented exception (see `VERA_NATIVE_ALLOW`).
> Everything else runs native. The R02 probes `advbench`/`tensortrust`/`llm_rules`, and R07/R08/R09/
> R11, are dynamic-probe benchmarks *by design* (not fallbacks).

## 2. Environment
```bash
export OLLAMA_API_BASE=http://127.0.0.1:11434
export VERA_WATERMARK_MODE=statistical
export VERA_HF_TRUST_REMOTE_CODE=true
export VERA_JUDGE_MODEL=ollama/llama3.1:8b-instruct-q8_0
export VERA_REQUIRE_NATIVE=1     # fail (NativeHarnessRequired) instead of silently falling back
export VERA_ARTIFACT_BACKEND=local VERA_MLFLOW_DISABLED=1
```

## 3. Generate the banking corpus (R03–R05)
```bash
python scripts/gen_banking_corpus.py   # -> data/corpus/banking_synth.jsonl (100% synthetic)
```
See [data/corpus/README.md](../data/corpus/README.md).

## 4. Run an evaluation
```bash
vera-eval run examples/runs/ollama_e2e.yaml     # or POST /api/v1/runs, or the dashboard wizard
```
Lower the sampling budget in the run definition for a quick smoke run before a full one.

**Model panels.** The ICSE 2027 campaign (panels of Foundry deployments, seeds, budgets,
measurability and cost analyses) runs from the separate `vera-foundry` repository, which pins a VERA
commit and generates the paper's tables. The driver behind the APSEC panel is kept for provenance in
`manuscript/apsec/scripts/run_paper_eval.py` (run from the repository root; it writes
`manuscript/apsec/results/`).

## Native-vs-fallback matrix
| Req | Benchmarks | Native harness | Mac |
|---|---|---|---|
| R01 | r01_robustness, mmlu_robust, boolq_contrast | lm-eval (clean) + dynamic | ✓ |
| R02 | advbench, tensortrust, llm_rules (dynamic+judge); decodingtrust_adv (garak) | judge; garak | partial (garak → fallback) |
| R03 | dataset_quality_scan | Detoxify + Gini | ✓ (corpus) |
| R04 | dataset_copyright_scan | Levenshtein + sacrebleu | ✓ (corpus) |
| R05 | dataset_privacy_scan | Presidio | ✓ (corpus) |
| R06 | mmlu, gsm8k, humaneval, truthfulqa, bbh | lm-eval (needs **logprobs → vLLM**) | dynamic on Ollama* |
| R07–R09, R11 | ece_mmlu, self_disclosure, watermark, decodingtrust_adult | dynamic probes (by design) | ✓ |
| R10 | bbq, bold, stereoset | HF datasets (loglikelihood → vLLM) | dynamic on Ollama* |
| R12 | realtoxicityprompts, advbench_instruction, truthfulqa | Detoxify + judge | ✓ |

\* **Ollama serving caveat.** Ollama's chat endpoint exposes no token log-probabilities, so the
loglikelihood multiple-choice tasks (R06 MMLU-style, R10) cannot run there and use VERA's dynamic
probes instead (recorded in provenance with `fallback_reason`); native lm-eval is reserved for a
log-prob backend (vLLM). The data engines for **R03–R05/R12 are fully native** on any backend.

Verify a run: `raw_outputs.jsonl` rows for R03–R05/R12 should have `fallback=false`; R06/R10 carry the
documented `ollama: no logprobs` reason, and `decodingtrust_adv` the garak/Mac reason.
