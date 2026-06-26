---
doc:
  title: Native multi-model evaluation — reproduction guide
  status: active
  last_reviewed: 2026-06-26
---

# Native evaluation & reproduction guide

How to reproduce the paper's numbers: run the **native** COMPL-AI suite (real harnesses, not the
heuristic fallbacks) over a **panel of models**, plus the dataset-stage requirements (R03–R05) on the
synthetic banking corpus, and the governance-runtime benchmark.

## 1. Set up the native stack
```bash
bash scripts/setup_native.sh        # installs [benchmarks,lab,pdf], checks Ollama + panel models
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
> falls back to dynamic probes; it is the single documented exception (see `RAIP_NATIVE_ALLOW`).
> Everything else runs native. The R02 probes `advbench`/`tensortrust`/`llm_rules`, and R07/R08/R09/
> R11, are dynamic-probe benchmarks *by design* (not fallbacks).

## 2. Environment
```bash
export OLLAMA_API_BASE=http://127.0.0.1:11434
export RAIP_WATERMARK_MODE=statistical
export RAIP_HF_TRUST_REMOTE_CODE=true
export RAIP_JUDGE_MODEL=ollama/llama3.1:8b-instruct-q8_0
export RAIP_REQUIRE_NATIVE=1     # fail (NativeHarnessRequired) instead of silently falling back
export RAIP_ARTIFACT_BACKEND=local RAIP_MLFLOW_DISABLED=1
```

## 3. Generate the banking corpus (R03–R05)
```bash
python scripts/gen_banking_corpus.py   # -> data/corpus/banking_synth.jsonl (100% synthetic)
```
See [data/corpus/README.md](../data/corpus/README.md).

## 4. Run the panel
```bash
RAIP_EVAL_MODELS="ollama/qwen2.5:32b-instruct-q4_K_M,ollama/mistral-small:24b,ollama/llama3.1:8b-instruct-q8_0" \
RAIP_EVAL_N=50 python scripts/run_paper_eval.py
# -> manuscript/results/paper_results_multi.json (per-model scores, CIs, fallback count, energy, Trust Factor)
```
Models run **sequentially** (one fits in 36 GB at a time). With the 32B principal expect a few hours;
start with `RAIP_EVAL_N=10` for a smoke run.

## 5. Governance-runtime benchmark
```bash
python scripts/bench_gaas.py    # -> manuscript/results/gaas_bench.json
```
Measures the inline-proxy latency overhead, agent detection of known jailbreak/PII/toxic responses,
policy enforcement, and the bus round-trip (Redis-Streams fallback).

## 6. Regenerate the paper data/figures
```bash
python manuscript/scripts/gen_paper_multi.py   # consumes paper_results_multi.json + gaas_bench.json
# prints the multi-model table, the non-degenerate sensitivity rows, and the GaaS numbers to
# transcribe into main.tex; also writes optional figures (the paper itself uses the tables).
cd manuscript && latexmk -pdf main.tex
```

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
loglikelihood multiple-choice tasks (R06 MMLU-style, R10) cannot run there and use RAIP's dynamic
probes instead (recorded in provenance with `fallback_reason`); native lm-eval is reserved for a
log-prob backend (vLLM). The data engines for **R03–R05/R12 are fully native** on any backend.

Verify a run: `raw_outputs.jsonl` rows for R03–R05/R12 should have `fallback=false`; R06/R10 carry the
documented `ollama: no logprobs` reason, and `decodingtrust_adv` the garak/Mac reason.
