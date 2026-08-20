# SEIP data pack — answers to the annotated TODOs, in document order

Companion to your annotated `main_apsec.tex`. **The tex file is untouched**: every
answer below is keyed to your own note, in the order the notes appear in the document,
ready to paste. Counts: the draft carries **53 `\todo{}` markers on 42 lines**. This
pack **answers 29 of them with measured data**; **17 are prose calls that stay yours**;
**7 are items only Robin can supply** (some markers count twice when a note asks for
both data and a rewrite).

Data provenance: a refreshed evaluation run on four open-weight models of comparable
size (Llama 3.1 8B instruct-q8_0, Qwen2.5 7B, Gemma 2 9B, Mistral 7B), **150 items per
benchmark, seed 42**, executed 2026-08-20 on an Apple M4 Max (36 GB): 85 + 66 + 79 + 68
minutes = **4 h 58 total**. Plus the final user-study exports (10 completers). JSONs in
`manuscript/results/` (`paper_results_n150_*.json`, merged `paper_results_multi.json`;
the old n=10 panel is preserved as `paper_results_multi_n10.json`).

---

## The notes, one by one, in document order

### 1. Introduction — the reviewer anecdote (`\todo{v}`, `\todo{n}` ×3 + note)
**→ ROBIN.** The score, the minutes and the log length must come from the internal
review record. If no single case can be reconstructed, use your own fallback wording
("the typical time to answer one such question…").

### 2. Related-work table — tool versions and access dates
**→ YOURS (prose).** No measurement involved; record version + access date per row.

### 3. Requirements section — one reference per requirement
**→ YOURS (prose).** The bibliography now contains Wohlin et al. 2012 and
Ko/LaToza/Burnett 2015 if you want them among the anchors.

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
**→ YOURS (prose).** Design judgement, no data involved.

### 7. Energy figures (`\todo{v}` kWh, `\todo{v}` kgCO₂e + method note)
**ANSWER:** the refreshed 8B run (five requirements, fifteen benchmarks) reports
**0.0169 kWh and 0.00095 kgCO₂e** — CodeCarbon **3.2.8**, online mode (live
grid-intensity API), French grid factor, `energy.source == "codecarbon"` verified in
the JSON for all four models. Full column: Llama 0.0169 · Qwen 0.0134 · Gemma 0.0156 ·
Mistral 0.0139 kWh. ⚠️ Wording: the measured set is the five-requirement table, not
"a full requirement set" — phrase accordingly.

### 8. Energy-claim uniqueness check against other Act-oriented tools
**→ YOURS (prose check).** COMPL-AI's published interpretation collects training-time
resources through a form; none of the tools in the related-work table measures the
evaluation run itself. Verify before the claim goes in.

### 9. Corpus size and the two fallbacks against the refreshed run
**ANSWER:** the corpus holds **230 documents** (`config.corpus_docs` in the merged
JSON). Both recorded fallbacks reproduce at n=150: no token log-probabilities on the
Ollama path (R01's native harness needs a vLLM backend, so the heuristic probe runs
fallback-flagged), and the Apple-Silicon adversarial-probe fallback.

### 10. HISTREE anchoring + Ko/LaToza/Burnett
**→ YOURS (prose).** The `ko2015practical` BibTeX entry is already in `references.bib`.

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

**On your load-bearing note:** the baseline is *small* — 119 fully searchable lines —
and participants still scored 45% on it. Real artifacts at n=150 run to thousands of
per-item lines, so a small baseline *favours* the raw-files condition: the measured gap
is a conservative lower bound, not a straw man. Recommend saying exactly this.

### 12. T8 wizard-launch outcome (only direct evidence for R1)
**ANSWER:** nine completers reached it (P26's session was cut by a tunnel outage
first). **5 of 9 launched successfully at the first attempt, median 55 s among
successes (22–180 s)**; one hit the five-minute cap, two gave up within seconds, one
pasted the wrong page's address.

### 13. Ethics statement
**→ ROBIN.** No name/email collected, server-assigned codes, closed lists, aggregate
reporting; the review-body / exemption status is Robin's to state.

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
note). **Headline for the caption:** Gemma's n=10 cyber zero becomes 0.375 [.355,.395]
at n=150 — a resolution artefact, not a property of the model; no model reaches green;
Qwen's TF is stable across n (58.9 at both budgets).

### 15. Constant calibration row (0.90)
**ANSWER (one clause):** the value is a property of the confidence-binning procedure at
this sampling budget, not of the models. (With the reduced table the row can also
simply be cut.)

### 16. Drop-out phases of the four partial sessions
**ANSWER:** all four dropped during or at the end of the **baseline** phase — two after
its first question (P2, P18), two at the transition screen without ever seeing the
dashboard phase (P20, P24). Conservative direction: it biases the retained sample
toward people who can read raw files.

### 17. Pre-registration
**ANSWER:** none exists. Your honest sentence is the correct form; the note can go.

### 18. P25 censoring + Pairs column + five-minute-cap counts
**ANSWER — Pairs surviving time-censoring:** P1 6/6 · P3 4/6 · P15 6/6 · P16 5/6 ·
P17 6/6 · P19 6/6 · P21 6/6 · **P25 2/6** · P26 6/6 · P27 6/6. **No question reached
the five-minute cap in either condition**; every censored pair is an explicit give-up.
(Your table also lacks the two newest completers: P26 = 5 & 5 & 66 & 38; P27 = 4 & 5 &
24 & 30.)

### 19. Redundant band label in the build
**→ YOURS (build check).** Verify in the compiled figure before submission.

### 20. Cite the taxonomy (Wohlin)
**ANSWER:** `wohlin2012experimentation` is now in `references.bib` — just cite it.

### 21. Clock-gap cases revealed by server timestamps
**ANSWER:** **2 cases** consistent with a mid-question reload (P2 Q1B: 74 s client vs
135 s server; P3 Q1A: 99 vs 137), both in the baseline phase; the eight other
divergences are ≤ 10 s and consistent with tunnel transport latency.

### 22. Usage figures (months, runs, release reviews)
**→ ROBIN.** The deployment's Redis can give a floor for run counts, but the period and
"fed a release review" need Robin's records.

### 23. Run cost (`\todo{time}` on `\todo{hardware}`)
**ANSWER:** the five-requirement, fifteen-benchmark run against the 8B model completes
in **85 minutes on an Apple M4 Max, 36 GB**, at 150 items per benchmark. (Same wording
caveat as item 7: not "a full requirement set".)

### 24. Guided-mode observation without a measure
**→ YOURS (prose).** No before/after count exists; state it plainly as an observation
from review meetings.

---

## Also done, outside the tex

- `references.bib` gained `wohlin2012experimentation`, `ko2015practical`, `codecarbon`,
  and **three STUBS to replace with your exact Overleaf entries**: `rajput2024fecom`,
  `rajput2024greenlight`, `mehditabar2025smart`.
- Build note: the draft's `\usepackage{etc}` does not compile outside Overleaf
  (`etc.sty` does not exist), and `\todo`/`\nax` need definitions locally — nothing was
  changed, just flagged.
- User-study final state: 10 completers (your draft's tables carry 8 — P26 and P27
  arrived after your pass; their rows are in items 14/18 above), quality 27/60 vs 42/60,
  exact Wilcoxon p = .016; time 56 s vs 30 s, p = .065.

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
