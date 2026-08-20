# SEIP regeneration pack — living document

This file is built incrementally while the n=150 benchmark runs execute.
Each section is stamped when it lands. Regeneration commands are at the bottom.

## Run status

| Model | Status | Duration |
|---|---|---|
| ollama/llama3.1:8b-instruct-q8_0 | ⏳ queued | — |
| ollama/qwen2.5:7b | ⏳ queued | — |
| ollama/gemma2:9b | ⏳ queued | — |
| ollama/mistral:7b | ⏳ queued | — |

**Scope of the refreshed runs (decision record).** Five requirements, seven benchmarks:
R01 (mmlu_robust, boolq_contrast), R02 (advbench, decoding_trust_cyber), R05
(privacy_leakage, corpus stage), R06 (mmlu), R12 (realtoxicityprompts). Rationale:
{R01, R02, R05, R12} is exactly the Trust Factor's security-critical set (weights
0.20/0.35/0.20/0.25), so the refreshed table can recompute the gauge end to end; R06
adds the one score every reader can anchor (MMLU). Cut, each with one stated reason:
CR07 (constant 0.90 — a property of the confidence-binning procedure, not of models),
CR09 (0 for every open-weight model, no watermark), CR03/CR04 (corpus scans, identical
across models by construction; R05 already illustrates the corpus stage), CR08/CR10/CR11
(discriminating but required by no reviewer note). n=150 per benchmark, seed 42;
per-benchmark effective n reported after the runs (some suites may cap below 150).

**Execution note (2026-08-20):** `VERA_REQUIRE_NATIVE` is NOT set for these runs. R01's
native harness needs token log-probabilities, which the Ollama serving path does not
expose (vLLM would); R01 therefore runs its documented heuristic probe and carries an
explicit fallback flag, exactly as in the July n=10 panel and as the tool's provenance
feature reports. The refreshed table must show that flag on R01 rather than hide it.

## Formulas (verified in code — ready now, 2026-08-20)

**Level 1 — benchmark → requirement** (`src/vera/benchmarks/catalog.py`): each requirement
R aggregates its contributing benchmarks by weighted mean, s_R = Σ w_b·m_b with w_b ≥ 0,
Σ w_b = 1, weights from the signed catalog (SHA-256 digest pinned per run). A benchmark
with no catalog weight is excluded, never silently defaulted.

**Level 2 — Trust Factor** (`src/vera/governance/trust_factor.py`): renormalised weighted
mean over the security-critical subset S = {R01, R02, R05, R12}, default weights
R01=0.20, R02=0.35, R05=0.20, R12=0.25 (overridable via `VERA_TRUST_FACTOR_WEIGHTS`),
scaled to 0–100. Bands: red < 0.40 ≤ orange < 0.70 ≤ green. Reproduced example
(Llama 3.1 8B, n=10 archive): 0.35·0.50 + 0.25·0.75 + 0.20·0.728 + 0.20·1.00 = 0.708 →
70.8, green — matches the stored value exactly.

**COMPL-AI baseline for §Background** (verified against arXiv:2410.07959): COMPL-AI
aggregates each requirement by a simple unweighted mean — the special case w_b = 1/|B_R|.
VERA's delta: it makes the weighting explicit, versioned and signed, where COMPL-AI fixes
it implicitly. (The verdict-sensitivity analysis stays out of this paper.)

## User-study extractions (ready now, 2026-08-20; n = 10 completers)

**Pairs surviving time-censoring per participant** (fills the new column of the paired
table): P1 6/6 · P3 4/6 · P15 6/6 · P16 5/6 · P17 6/6 · P19 6/6 · P21 6/6 · P25 2/6 ·
P26 6/6 · P27 6/6. **No question hit the five-minute cap in either condition**; the 10
give-ups (P25 ×7, P3 ×2, P16 ×1) are explicit give-ups, not timeouts.

**Drop-out phases of the four partial sessions** (all four dropped during or at the end
of the baseline phase — the conservative direction, biasing the sample toward people who
can read raw files): P2 and P18 stopped after baseline question 1; P20 and P24 completed
all six baseline questions and stopped at the transition screen, before seeing the
dashboard phase at all.

**Server-timestamp sanity channel**: 10 of 128 submissions differ from the client clock
by more than 2 s. Two are consistent with a mid-question page reload (P2 Q1B: 74 s client
vs 135 s server; P3 Q1A: 99 vs 137), both in the baseline phase; the remaining eight are
≤ 10 s and consistent with tunnel transport latency (P24's session shows a systematic
~5 s offset).

**Bonus launch task T8** (only direct evidence for R1): 9 of 10 completers reached it
(P26's session was cut by a tunnel outage before T8). 5 of 9 launched a run successfully
at first attempt, median 55 s among successes (22–180 s). Of the four others: one hit
the five-minute cap, two gave up within seconds, one pasted the wrong page's address.

**Ethics/pre-registration**: no pre-registration exists; the honest sentence stays. No
personal data was collected (server-assigned codes, closed lists); ethics-body status is
Robin's item below.

## Study run specification (tab:runspec — ready now, 2026-08-20)

The run participants read (pinned via `VERA_STUDY_RUN_ID`, answer key snapshotted at
session creation):

| Field | Value |
|---|---|
| Requirement set and version | mvp2-v2, digest sha256:9e2b11d4 |
| Requirements scored | 9 |
| Benchmarks executed | 11 |
| Per-item outputs | 33 items |
| Raw files in the baseline | 3 tabs, 119 lines, 12 KB total (run record YAML 75 lines / 1.0 KB · raw outputs JSONL 33 lines / 9.3 KB · harness log 11 lines / 1.3 KB) |
| Baseline affordances | pretty-printed monospace text in scrollable panes (max height ~20 rem), tab switching, browser text search; no line numbers, no download |

**Load-bearing note for L397**: the baseline is *small* — 119 lines. Real evaluation
artifacts at n=150 run to thousands of per-item lines. A small, fully greppable baseline
*favours* the raw-files condition, so the measured gap (45% vs 70% correct) is a
conservative lower bound, not a straw man. Recommend saying exactly this in the paper.

## n=150 results

*(one subsection per model, appended as each run completes)*

## Open items that only Robin can fill

1. **L117-118** — the reviewer anecdote (which score, how many minutes, log length): from
   the internal review record, or reword to "typically takes … and say it is typical".
2. **L765-766** — usage figures (period, number of runs, how many fed a release review):
   deployment Redis gives a floor for run counts, but the period and "fed a review" need
   Robin's records.
3. **L485** — BNPP ethics review/exemption status for the anonymous internal collection.
4. SEIP format check on the APSEC site (page limit, blinding, AI policy).

## Regeneration commands

```bash
# one model at a time (per-model wall time is measured by the driver):
VERA_EVAL_MODELS="ollama/<model>" VERA_EVAL_N=150 \
  VERA_EVAL_REQS="R01,R02,R05,R06,R12" \
  VERA_CORPUS=data/corpus/banking_synth.jsonl VERA_REQUIRE_NATIVE=1 \
  VERA_EVAL_OUT=manuscript/results/paper_results_n150_<model>.json \
  .venv/bin/python scripts/run_paper_eval.py
# study numbers:
python scripts/analyze_user_study.py data/user_study/template.csv \
  --quiz data/user_study/quiz.csv --survey data/user_study/survey.csv
```
