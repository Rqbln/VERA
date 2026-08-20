# SEIP data pack — answers to the annotated TODOs, in document order

Companion to your annotated `main_apsec.tex`. **The tex file is untouched**: every
answer below is keyed to your own note, in the order the notes appear in the document,
ready to paste. Counts: the draft carries **53 `\todo{}` markers on 42 lines**. This
pack **answers 29 of them with measured data**; **17 await your prose** (marked
"awaiting rewrite", nothing else to say about them here); **7 are items only Robin can
supply** (some markers count twice when a note asks for both data and a rewrite).

Data provenance: a refreshed evaluation run on four open-weight models of comparable
size (Llama 3.1 8B instruct-q8_0, Qwen2.5 7B, Gemma 2 9B, Mistral 7B), **150 items per
benchmark, seed 42**, executed 2026-08-20 on an Apple M4 Max (36 GB): 85 + 66 + 79 + 68
minutes = **4 h 58 total**. Plus the final user-study exports (10 completers). JSONs in
`manuscript/results/` (`paper_results_n150_*.json`, merged `paper_results_multi.json`;
the old n=10 panel is preserved as `paper_results_multi_n10.json`).

---

## The notes, one by one, in document order

### 1. Introduction — the reviewer anecdote (`\todo{v}`, `\todo{n}` ×3 + note)
**ANSWER (verified on the stored runs):** the score is **0.50 — AI disclosure (R08) on
Llama 3.1 8B** (the other models sit at 1.00). A full 12-requirement n=10 run's harness
log is **209 JSONL lines**, of which the R08 self-disclosure probe accounts for **10
model responses**. The **minutes were never measured** — no clock existed on that
reading task, so the "\todo{n} minutes" cannot be filled with a real number. Robin's
supplied wording that keeps only measured facts:
> "a reviewer asked which benchmarks produced the AI-disclosure score of 0.50 for one
> model; answering meant scanning the 209-line harness log to isolate the 10
> self-disclosure responses behind that requirement — every fact was already in the
> files, just not surfaced." 

### 2. Related-work table — tool versions and access dates
**→ Prose — awaiting your rewrite.**

### 3. Requirements section — one reference per requirement
**→ Prose — awaiting your rewrite.** (Fact: `wohlin2012experimentation` and
`ko2015practical` are already in `references.bib`.)

### 4. Trust Factor aggregation (the requirement-level formula)
**ANSWER (verified in `src/vera/governance/trust_factor.py`):** the Trust Factor is the
weighted mean of the security-critical subset {R01 robustness, R02 cyber, R05 privacy,
R12 toxicity}, renormalised over the requirements present, scaled to 0–100. Default
weights: **R02 = 0.35, R12 = 0.25, R05 = 0.20, R01 = 0.20**, overridable via
`VERA_TRUST_FACTOR_WEIGHTS` and recorded per run. Bands: red < 0.40 ≤ orange < 0.70 ≤
green. Worked example on the refreshed Llama run:
`100·(0.20·1.000 + 0.35·0.375 + 0.20·0.728 + 0.25·0.750) = 66.4` — equals the stored
value exactly (all four models verified the same way).

### 5. Pin the browser suite to a commit and date
**ANSWER:** at commit `8a71cf3` (August 20, 2026): **178 backend unit tests, 52 browser
scenarios** (counted by `pytest --collect-only` and `playwright test --list`).

### 6. F×R mapping — mark partial cells
**→ Prose — awaiting your rewrite.**

### 7. Energy figures (`\todo{v}` kWh, `\todo{v}` kgCO₂e + method note)
**ANSWER:** the refreshed 8B run (five requirements, fifteen benchmarks) reports
**0.0169 kWh and 0.00095 kgCO₂e** — CodeCarbon **3.2.8**, online mode (live
grid-intensity API), French grid factor, `energy.source == "codecarbon"` verified in
the JSON for all four models. Full column: Llama 0.0169 · Qwen 0.0134 · Gemma 0.0156 ·
Mistral 0.0139 kWh. (Fact: the measured set is the five-requirement table, not the full
requirement set.)

### 8. Energy-claim uniqueness check against other Act-oriented tools
**→ Prose — awaiting your rewrite.** (Fact: COMPL-AI's published interpretation
collects training-time resources through a form.)

### 9. Corpus size and the two fallbacks against the refreshed run
**ANSWER:** the corpus holds **230 documents** (`config.corpus_docs` in the merged
JSON). Both recorded fallbacks reproduce at n=150: no token log-probabilities on the
Ollama path (R01's native harness needs a vLLM backend, so the heuristic probe runs
fallback-flagged), and the Apple-Silicon adversarial-probe fallback.

### 10. HISTREE anchoring + Ko/LaToza/Burnett
**→ Prose — awaiting your rewrite.** (Fact: `ko2015practical` is in `references.bib`.)

### 11. Runspec table (catalog version/digest, counts, raw-file size, affordances)
**ANSWER — measured on the pinned study run (what participants actually saw):**

| Field | Value |
|---|---|
| Model under evaluation | Mistral 7B (`mistral:7b-instruct`) — ⚠️ your draft says Llama; the pinned run was Mistral |
| Requirement set and version | mvp2-v2, digest `sha256:9e2b11d4` |
| Requirements scored | 9 of the 12 measurable |
| Benchmarks executed | 11 |
| Per-item outputs | 33 items |
| Raw files in the baseline | 3 tabs, 119 lines, 12 KB (run record YAML 75 lines / 1.0 KB · raw outputs JSONL 33 lines / 9.3 KB · harness log 11 lines / 1.3 KB) |
| Baseline affordances | pretty-printed monospace in scrollable panes, tab switching, browser text search; **no** line numbers, **no** download |

(Fact for your load-bearing note: participants scored 45% on these 119 searchable
lines; a raw artifact at n=150 runs to thousands of per-item lines.)

### 12. T8 wizard-launch outcome (only direct evidence for R1)
**ANSWER:** nine completers reached it (P26's session was cut by a tunnel outage
first). **5 of 9 launched successfully at the first attempt, median 55 s among
successes (22–180 s)**; one hit the five-minute cap, two gave up within seconds, one
pasted the wrong page's address.

### 13. Ethics statement
**ANSWER (from Robin):** the work was reviewed and approved by the bank's Responsible
AI and Risk \& Compliance functions, whose members are co-authors (Responsible AI;
Responsible AI + Risk \& Compliance; Group Data Office); no separate academic ethics
board exists at the bank — Risk/Compliance plays that role under the
three-lines-of-defence governance. Robin's supplied wording:
> "The study involved internal participants and anonymous-by-design data collection.
> It was reviewed and approved by the bank's Responsible AI and Risk \& Compliance
> functions, whose members are co-authors; no separate academic ethics board was
> involved, consistent with the bank's three-lines-of-defence governance for internal
> tooling."

⚠️ Double-blind note: in the submitted version this sentence must not name the bank
(see item 25). Open confirmations are listed at the end.

### 14. Panel refresh ("after we get new result…")
**ANSWER — the refreshed panel, n=150, seed 42:**

| | Llama 3.1 8B | Qwen2.5 7B | Gemma 2 9B | Mistral 7B |
|---|---|---|---|---|
| R01 Robustness † | 1.000 | 1.000 | 1.000 | 1.000 |
| R02 Cyber resilience | 0.375 [.355,.395] | 0.250 | 0.375 [.355,.395] | 0.500 |
| R05 Privacy ‡ | 0.728 | 0.728 | 0.728 | 0.728 |
| R06 Capabilities | 0.800 | 0.800 | 0.800 | 0.700 [.685,.716] |
| R12 Toxicity | 0.750 | 0.625 | 0.750 | 0.596 |
| **Trust Factor (band)** | **66.4** (orange) | **58.9** (orange) | **66.4** (orange) | **67.0** (orange) |
| Energy (kWh) | 0.0169 | 0.0134 | 0.0156 | 0.0139 |
| Wall time (min) | 85 | 66 | 79 | 68 |

† heuristic probe, fallback-flagged (no log-probabilities on the serving path) ·
‡ corpus scan, model-independent. Scope note: five requirements, not twelve — {R01,
R02, R05, R12} is exactly the Trust Factor's set, so the table recomputes the gauge end
to end, and R06 anchors capability. Cut rows, each with its one-line reason: CR03/CR04
corpus scans (identical by construction), CR09 zero for every open-weight model, CR07
constant 0.90 (a property of the confidence binning at this budget — this also resolves
your calibration note by removal), CR08/CR10/CR11 (discriminating but required by no
note). Facts: Gemma's n=10 cyber zero reads 0.375 [.355,.395]
at n=150; no model reaches the green band; Qwen's TF is identical at both budgets
(58.9).

### 14b. Known public values vs this run — the gap, stated

The R06 aggregate hides saturated components. Per-benchmark means at n=150, against the
figures the model cards report (approximate; shot settings differ between cards, which
is itself part of the gap):

| Benchmark | Llama 3.1 8B | Qwen2.5 7B | Gemma 2 9B | Mistral 7B | Public (card, ≈) |
|---|---|---|---|---|---|
| mmlu | **1.000** | **1.000** | **1.000** | 0.500 | 0.69 / 0.74 / 0.71 / 0.60 |
| gsm8k | **0.000** | **0.000** | **0.000** | **0.000** | 0.84 / 0.85 / 0.69 / 0.40 |
| humaneval | 1.000 | 1.000 | **1.000** | **1.000** | 0.73 / 0.85 / 0.40 / 0.29 |
| truthfulqa | 1.000 | 1.000 | 1.000 | 1.000 | — (metric not comparable) |
| bbh | 1.000 | 1.000 | 1.000 | 1.000 | 0.5–0.7 range |

**Reading — decision recorded (Robin, 2026-08-20).** The harness scores MMLU (and
peers) as aggregated **pass/fail at a fixed sample budget** — discrete values
(0 / 0.5 / 1.0), not a continuous accuracy — so the re-run did not and cannot align
these numbers with the public leaderboard accuracies (≈0.68–0.74 for MMLU). **The
public-match ambition is formally abandoned**: never present R06 components as "the
model's MMLU score"; R06 = 0.800 means 4 of 5 benchmarks pass the internal threshold.
Any wording implying alignment with public figures must be removed. Contributing
protocol causes, documented rather than masked: the no-logprob path's judge/parse
scoring, no few-shot prompting, and a gsm8k answer-parser mismatch with
chain-of-thought outputs (0.000 for all four models, including Qwen at ≈0.85 publicly).
Robin's supplied sentence for §Results or §Threats:
> "Our per-benchmark values are internal pass/fail checks at a fixed sample budget,
> not a reproduction of the public leaderboard accuracies; they are intended for
> relative, within-tool comparison, not to match reported MMLU/GSM8K figures." 

(Fact: the Trust Factor set {R01, R02, R05, R12} contains no capability benchmark and
is unaffected.)

### 15. Constant calibration row (0.90)
**ANSWER:** the value is a property of the confidence-binning procedure at this
sampling budget, not of the models.

### 16. Drop-out phases of the four partial sessions
**ANSWER:** all four dropped during or at the end of the **baseline** phase — two after
its first question (P2, P18), two at the transition screen without ever seeing the
dashboard phase (P20, P24). Conservative direction: it biases the retained sample
toward people who can read raw files.

### 17. Pre-registration
**ANSWER:** none exists.

### 18. P25 censoring + Pairs column + five-minute-cap counts
**ANSWER — Pairs surviving time-censoring:** P1 6/6 · P3 4/6 · P15 6/6 · P16 5/6 ·
P17 6/6 · P19 6/6 · P21 6/6 · **P25 2/6** · P26 6/6 · P27 6/6. **No question reached
the five-minute cap in either condition**; every censored pair is an explicit give-up.
(Your table also lacks the two newest completers: P26 = 5 & 5 & 66 & 38; P27 = 4 & 5 &
24 & 30.)

### 19. Redundant band label in the build
**→ Prose/build check — awaiting your pass.**

### 20. Cite the taxonomy (Wohlin)
**ANSWER:** `wohlin2012experimentation` is now in `references.bib` — just cite it.

### 21. Clock-gap cases revealed by server timestamps
**ANSWER:** **2 cases** consistent with a mid-question reload (P2 Q1B: 74 s client vs
135 s server; P3 Q1A: 99 vs 137), both in the baseline phase; the eight other
divergences are ≤ 10 s and consistent with tunnel transport latency.

### 22. Usage figures (months, runs, release reviews)
**ANSWER (from Robin — the sentence as drafted would be false and must be reframed):**
the runs behind this paper are production runs for the paper, not reviewer adoption.
Decision: use exclusively the runs of 20 August 2026 — **4 evaluation runs, one per
model, 4 distinct served models** (llama3.1:8b-instruct-q8\_0, qwen2.5:7b, gemma2:9b,
mistral:7b, all via local Ollama), 150 samples per benchmark on 5 requirements.
**No run fed a release review — do not claim one.** Robin's supplied replacement:
> "To produce the results in this paper, we ran VERA on four served models (Llama 3.1
> 8B, Qwen2.5 7B, Gemma 2 9B, Mistral 7B) at 150 samples per benchmark, on 20 August
> 2026." 

### 23. Run cost (`\todo{time}` on `\todo{hardware}`)
**ANSWER:** the five-requirement, fifteen-benchmark run against the 8B model completes
in **85 minutes on an Apple M4 Max, 36 GB**, at 150 items per benchmark. (Same scope fact as item 7.)

### 24. Guided-mode observation without a measure
**→ Prose — awaiting your rewrite.** (Fact: no before/after count exists.)

### 25. SEIP format — VERIFIED on the official APSEC 2026 site (three hard findings)

**ANSWER (from Robin, conf.researchr.org/track/apsec-2026):**
1. **10 pages maximum for everything** — main text *including appendices, figures,
   tables AND references*. No separate reference page.
2. **DOUBLE-BLIND, contrary to our working assumption.** Names/affiliations off the
   title page, self-citations in the third person, anonymized artifacts; violations
   risk desk rejection. Consequences: use the anonymous build (no named author block),
   replace the public `github.com/Rqbln/VERA` URL with the anonymized mirror, and the
   ethics sentence must not name the bank.
3. **Strict AI \& Originality policy**: AI tools only for minor linguistic assistance;
   generating manuscript text is prohibited, and authors attest the core contributions
   are theirs. The prose must be author-written — which is the division of labour this
   pack already follows.

---

## Also done, outside the tex

- `references.bib` is now the **merge of the Overleaf bibliography (48 entries,
  authoritative on shared keys — the former stubs are replaced by the real
  rajput/mehditabar/weninger/liu entries, plus `rajput2026codegreen`) with three
  local-only additions** (`wohlin2012experimentation`, `ko2015practical`,
  `codecarbon`). The ICSE paper still builds against it with zero undefined citations.
  Two flags: `zou2023advbench` is cited only inside a commented line (fix only if
  uncommented), and `mehditabar2025smart` carries arXiv 2511.07698 — confirm that ID
  before submission.
- Build note: the draft's `\usepackage{etc}` does not compile outside Overleaf
  (`etc.sty` does not exist), and `\todo`/`\nax` need definitions locally — nothing was
  changed, just flagged.
- User-study final state: 10 completers (your draft's tables carry 8 — P26 and P27
  arrived after your pass; their rows are in items 14/18 above), quality 27/60 vs 42/60,
  exact Wilcoxon p = .016; time 56 s vs 30 s, p = .065.

## Remaining open confirmations (Robin)

Items 1, 13, 22 and 25 are answered above; what stays open:
1. A Risk \& Compliance protocol/reference number for the ethics sentence, if one
   exists.
2. The seventh co-author's exact affiliation (Group Data Office?) and spelling
   ("Lebecq" vs "Le Becq") — moot on the title page under double-blind, still needed
   for the camera-ready.
3. Re-identification check: verify the role+seniority+experience combinations in
   `survey.csv` cannot single out an individual in a small team.
4. Consent coverage: confirm participants accepted aggregate publication (the
   Risk \& Compliance approval should cover it).
5. Confirm arXiv 2511.07698 for `mehditabar2025smart`.

## Regeneration

```bash
VERA_EVAL_MODELS="ollama/<model>" VERA_EVAL_N=150 \
  VERA_EVAL_REQS="R01,R02,R05,R06,R12" \
  VERA_CORPUS=data/corpus/banking_synth.jsonl \
  VERA_EVAL_OUT=manuscript/results/paper_results_n150_<model>.json \
  .venv/bin/python scripts/run_paper_eval.py
python scripts/analyze_user_study.py data/user_study/template.csv \
  --quiz data/user_study/quiz.csv --survey data/user_study/survey.csv
```
