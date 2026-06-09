# RAIP — APSEC 2026 Detailed Outline (Technical Track)

> **Status:** Outline only — no LaTeX body.  
> **Venue:** 33rd Asia-Pacific Software Engineering Conference (APSEC 2026), Bali — Technical Track.  
> **Format:** IEEEtran two-column, 10 pages including references, double-blind, English.  
> **Profile:** [skills/SciOrchestrator/venue-profile.yaml](../skills/SciOrchestrator/venue-profile.yaml)  
> **Source brief:** [research-brief.md](research-brief.md)

---

## Document control

| Field | Value |
|-------|--------|
| Working title | RAIP: A Lifecycle-Aware Open Platform for Responsible AI Evaluation Aligned with COMPL-AI and the EU AI Act |
| Narrative paradigm | SE tool + empirical evaluation (Histree / PromptOps / defect-prediction RQ style) |
| `references.bib` | **[manuscript/references.bib](references.bib)** — 30 verified keys; use `\cite{key}` only for keys in this file |
| Reference PDF set | **5/5 present** (verified 2026-06-01) |

### Reference PDF checklist (local) ↔ bibliography keys

| PDF | BibTeX key | Role for RAIP |
|-----|------------|---------------|
| `apsec2025_promptops_llm_trustworthiness.pdf` | `sunetnanta2025promptops` | Closest thematic neighbor — LLM trustworthiness tool |
| `apsec2023_histree_experiment_tracking.pdf` | `studtmann2023histree` | Platform requirements R1–Rk; tool + user study pattern |
| `apsec2018_restricted_use_case_controlled_experiment.pdf` | `weninger2018usecase` | Controlled experiment; threats to validity |
| `apsec2022_cross_project_defect_prediction.pdf` | `liu2022mscpdp` | Explicit RQ1–Rn; Results per RQ (§5 structure) |
| `apsec2017_gui_layout_testing_tool.pdf` | `hasselknippe2017guilayout` | Classic SE tool + technical validation |

### Bibliography map (for §2 Related Work / §3 citations)

*All keys below exist in [references.bib](references.bib). Tools without a bib entry (e.g. Garak, Presidio, Detoxify) are named in prose only.*

| Block | Keys | Use in RAIP paper |
|-------|------|-------------------|
| **Regulatory & governance frameworks** | `guldimann2024complai`, `euaiact2024`, `hleg2019trustworthyai`, `nist2023airmf`, `iso42001_2023` | §2.1 motivation; construct validity; RAIP addresses Measure/Manage slice, not full GRC |
| **Governance artifacts** | `mitchell2019modelcard`, `gebru2021datasheets` | §3.5 model card + datasheet (N04) |
| **Capabilities (R06)** | `hendrycks2021mmlu`, `cobbe2021gsm8k`, `chen2021humaneval`, `lin2022truthfulqa`, `suzgun2023bbh`, `gao2021lmevalharness` | §2.2, §3.3, Appendix A; lm-eval runner |
| **Toxicity (R12)** | `gehman2020realtoxicity` | §2.2, Appendix A |
| **Bias & fairness (R10–R11)** | `parrish2022bbq`, `dhamala2021bold`, `nadeem2021stereoset`, `wang2023decodingtrust`, `hardt2016equality` | §2.2, §3.3; DPD/EOD for R11 |
| **Calibration (R07)** | `guo2017calibration` | §3.3 ECE formula |
| **Privacy / extraction (R04–R05)** | `carlini2021membership`, `carlini2023extracting` | §2.2, §3.4; MVP2 simplified probes |
| **Security / backdoors (R02 ext.)** | `hubinger2024sleeperagents` | §3.4 poisoning lab, BSR motivation |
| **Watermark (R09)** | `kirchenbauer2023watermark` | §3.3 statistical detector baseline |
| **Environmental (N03)** | `henderson2020mlco2` | §3.5 energy hooks; future work |
| **HITL reliability (N01–N02)** | `hayes2007krippendorff` | §6 / future work (MVP3 panels) |
| **Trustworthiness suites** | `wang2023decodingtrust`, `gao2021lmevalharness` | §2.2 orchestration positioning |
| **APSEC tool-paper style** | `studtmann2023histree`, `weninger2018usecase`, `liu2022mscpdp`, `hasselknippe2017guilayout`, `sunetnanta2025promptops` | Structure, RQs, validity; §2.3 positioning |

---

## Contribution lock (Step 1)

**One-sentence contribution (locked):**

We present **RAIP**, an open-source, self-hostable software engineering platform that operationalizes the COMPL-AI technical requirements for the EU AI Act through a unified evaluation pipeline (CLI, API, asynchronous workers, LangGraph orchestration), extending inference-time benchmarking with **lifecycle-aware** dataset and checkpoint evaluation, signed governance artifacts, and explicit harness provenance—unlike prior LLM trustworthiness tools that focus primarily on single-shot model prompts without longitudinal or data-stage coverage.

**Confidence:** `medium` — bibliography ready; LaTeX draft still gated on numeric results tables (`[RESULT: …]` slots).

**Fixed interpretive choices (from research-brief REVIEW):**

| Choice | Resolution |
|--------|------------|
| RQ3 | Case study on artifact interpretability (model card, datasheet, harness provenance) — not a formal user study with N |
| Running example | Compliance engineer preparing an internal LLM release gate |
| Platform R1–R4 | Lifecycle, traceability, reproducibility, sovereignty (paper-level requirements) |
| C1–C3 | Framework / platform / empirical (S1–S3 scenarios) |
| Default evaluation target | `ollama/llama3.1:8b-instruct-q8_0` |

---

## Page budget (10 pages total)

| Section | Target pages |
|---------|----------------|
| Abstract + Index Terms | 0.25 |
| 1. Introduction | 1.0–1.5 |
| 2. Background and Related Work | 1.0–1.5 |
| 3. RAIP Framework and Architecture | 2.0–2.5 |
| 4. Evaluation Setup | ~1.0 |
| 5. Results and Analysis | ~2.0 |
| 6. Threats to Validity | ~0.5 |
| 7. Conclusion and Future Work | ~0.5 |
| References | within 10-page limit |

---

## Abstract (bullet plan, ~150–200 words target)

1. **Context:** High-risk and regulated AI systems under the EU AI Act \cite{euaiact2024} require reproducible technical evidence across trustworthy-AI principles \cite{hleg2019trustworthyai}; COMPL-AI \cite{guldimann2024complai} translates these into 18 technical requirements (12 measurable).
2. **Gap:** Software teams still run fragmented benchmark scripts (cyber, capabilities, fairness, dataset quality) with weak links from raw metrics to requirement IDs, lifecycle stages, and audit artifacts; LLM trustworthiness tools often evaluate a frozen model endpoint only.
3. **Approach:** RAIP — a lifecycle-aware, self-hostable evaluation platform orchestrating benchmarks via LangGraph, persisting signed runs to MLflow/MinIO, and emitting model cards with explicit harness provenance.
4. **Key results (qualitative — no numbers in outline):** End-to-end pipeline on a representative open-weight target; coverage of COMPL-AI measurable requirements R01–R12; extended coverage when dataset and checkpoint/lab scenarios are enabled; traceable fallback reporting when optional harnesses are absent.
5. **Takeaway:** RAIP demonstrates how software engineering for responsible AI can treat compliance-oriented evaluation as an automated, reproducible pipeline rather than ad hoc spreadsheet assembly.

**REVIEW:** Emphasize *engineering contribution* and *traceability*, not SOTA accuracy on a single benchmark.

---

## Index Terms

- Responsible AI
- EU AI Act
- COMPL-AI
- software engineering tools
- LLM evaluation
- model card
- benchmark orchestration
- lifecycle evaluation

---

## 1. Introduction

### 1.1 Context and motivation

- EU AI Act \cite{euaiact2024} and trustworthy-AI principles \cite{hleg2019trustworthyai} require technical evidence before deployment; NIST AI RMF \cite{nist2023airmf} and ISO 42001 \cite{iso42001_2023} frame organizational risk management but do not provide an executable LLM benchmark pipeline.
- COMPL-AI \cite{guldimann2024complai} provides a measurable requirement set for LLMs but not an execution platform.
- Existing benchmark suites \cite{wang2023decodingtrust,gao2021lmevalharness,hendrycks2021mmlu} answer *measurement* in isolation, not *orchestration, aggregation, and governance artifacts* \cite{mitchell2019modelcard,gebru2021datasheets}.

### 1.2 Problem statement

- **Pain 1:** Manual assembly of scores across tools → error-prone, non-reproducible release gates.
- **Pain 2:** Inference-only evaluation misses dataset-stage risks (R03–R05) and training-time persistence (e.g., backdoor survival).
- **Pain 3:** Silent degradation when optional dependencies are missing (heuristic fallbacks without provenance).
- **Vignette (REVIEW):** A compliance engineer must attach a model card showing R01, R02, R10–R12, dataset adequacy (R03–R05), and signed run metadata before approving an instruction-tuned LLM — today requiring days of scripting.

### 1.3 Platform requirements (paper-level R1–R4)

*Distinct from COMPL-AI requirement IDs R01–R12.*

| ID | Requirement | One-line rationale |
|----|-------------|-------------------|
| **R1** | **Lifecycle coverage** | Evaluate at dataset, checkpoint, and inference stages — not only a static API endpoint |
| **R2** | **Regulatory traceability** | Every score maps to a COMPL-AI ID, contributing benchmarks, and bootstrap confidence interval |
| **R3** | **Reproducibility and automation** | Declarative YAML runs, async jobs, versioned catalogue, git SHA and signatures on artifacts |
| **R4** | **Sovereign self-hosted operation** | Core path on OSS stack (Ollama/vLLM, on-prem storage); proprietary APIs only as evaluation *targets* |

### 1.4 Contributions

**Lead-in phrase (required):** *In this paper, we make the following contributions:*

- **C1 — Conceptual framework:** A lifecycle-aware evaluation model aligning EU AI Act principles, COMPL-AI requirement IDs, lifecycle stages (`data` | `finetune` | `inference` | …), and stakeholder-oriented artifacts (model card, datasheet, `benchmark_run.yaml`).
- **C2 — RAIP platform:** Open-source implementation: CLI `raip-eval`, REST API, Celery workers, LangGraph supervisor, benchmark registry with dedicated runners, lab routes (dataset scan, poisoning), MinIO + MLflow + Timescale integration.
- **C3 — Empirical evaluation:** Three scenarios — (S1) full inference COMPL-AI run, (S2) lifecycle extension with dataset/checkpoint lab, (S3) case study on interpretability of generated governance artifacts — answering RQ1–RQ3 without fabricated statistics in this outline.

### 1.5 Paper organization

- §2 background and related tools; §3 framework and architecture; §4 evaluation setup; §5 results per RQ; §6 threats; §7 conclusion.

### 1.6 Figures (planned)

- `[FIG: motivating_compliance_workflow]` — optional: release gate flow from run request to model card (anonymous, no org logos).

**REVIEW:** Keep introduction under ~1.5 pages; defer COMPL-AI formula table to §2 or §3.1.

---

## 2. Background and Related Work

### 2.1 Regulatory framing and COMPL-AI operationalization

- EU AI Act \cite{euaiact2024}; six HLEG trustworthy-AI principles \cite{hleg2019trustworthyai} → COMPL-AI’s 18 technical requirements \cite{guldimann2024complai} (12 measurable scores in [0,1], 6 non-measurable / HITL / declarative).
- Broader risk-management context: NIST AI RMF \cite{nist2023airmf}, ISO/IEC 42001 \cite{iso42001_2023} — **REVIEW:** RAIP implements the *Measure* slice (automated benchmarks + artifacts), not full organizational governance.
- COMPL-AI contributions: legal-to-technical mapping, benchmark association, multi-model study \cite{guldimann2024complai}.
- **Gap:** COMPL-AI is a benchmark framework, not a lifecycle orchestration platform with signed audit chain.

### 2.2 Benchmark suites and metrics (components RAIP orchestrates)

| COMPL-AI area | Benchmarks / metrics | Bibliography (verified keys) |
|---------------|----------------------|------------------------------|
| R06 Capabilities | MMLU, GSM8K, HumanEval, TruthfulQA, BBH | \cite{hendrycks2021mmlu,cobbe2021gsm8k,chen2021humaneval,lin2022truthfulqa,suzgun2023bbh,gao2021lmevalharness} |
| R07 Calibration | ECE | \cite{guo2017calibration} |
| R10–R11 Bias / fairness | BBQ, BOLD, StereoSet; DPD/EOD | \cite{parrish2022bbq,dhamala2021bold,nadeem2021stereoset,hardt2016equality,wang2023decodingtrust} |
| R12 Toxicity | RealToxicityPrompts (+ refusal probes in RAIP) | \cite{gehman2020realtoxicity} |
| R03–R05 Dataset | Corpus toxicity, leakage, PII/extraction (MVP2 heuristics + optional libs) | \cite{carlini2021membership,carlini2023extracting} — **REVIEW:** simplified vs full Carlini-style attacks |
| R02 Cyber (ext.) | AdvBench/Garak-class probes in implementation (no bib key yet) | prose only |
| R09 Watermark | Statistical heuristic inspired by | \cite{kirchenbauer2023watermark} |

- RAIP **integrates** suites such as DecodingTrust \cite{wang2023decodingtrust} and lm-evaluation-harness \cite{gao2021lmevalharness}; it does not claim new benchmark science.

### 2.3 Governance artifacts (model cards, datasheets)

- Model Cards \cite{mitchell2019modelcard} — RAIP Jinja2 template: intended use, per-requirement metrics, limitations.
- Datasheets for Datasets \cite{gebru2021datasheets} — RAIP `datasheet.md` for corpus scans (R03–R05, N04).

### 2.4 Software engineering tools — APSEC neighbors and structure

| Paper | Key | Pattern RAIP reuses |
|-------|-----|---------------------|
| PromptOps | \cite{sunetnanta2025promptops} | LLM trustworthiness **tool**; closest neighbor — RAIP extends with COMPL-AI breadth + lifecycle |
| Histree | \cite{studtmann2023histree} | Platform requirements R1–Rk; tool design + empirical evaluation |
| Use-case experiment | \cite{weninger2018usecase} | Controlled experimental design; validity threats |
| Cross-project defect prediction | \cite{liu2022mscpdp} | **RQ1–Rn** + dedicated Results subsections (our §5) |
| GUI layout testing tool | \cite{hasselknippe2017guilayout} | SE tool architecture + technical validation without mandatory user study |

**REVIEW:** Cite \cite{sunetnanta2025promptops} in §2.5 gap paragraph as “inference-centric trustworthiness tooling”; contrast lifecycle + COMPL-AI orchestration.

### 2.5 Related work comparison table (outline)

`[TABLE: related_work_comparison]`

| Tool / framework | Lifecycle stages | COMPL-AI map | Automated pipeline | Harness provenance | Self-hosted default |
|------------------|------------------|--------------|--------------------|--------------------|---------------------|
| COMPL-AI \cite{guldimann2024complai} | Inference-focused | Yes (definition) | No | N/A | Partial |
| PromptOps \cite{sunetnanta2025promptops} | Primarily inference / prompts | Partial | Yes | Limited | REVIEW |
| Histree \cite{studtmann2023histree} | Experiment tracking | No | Yes | N/A | Yes |
| **RAIP** | Data + checkpoint + inference + lab | Yes (12 measurable) | Yes | Yes (`fallback` flag) | Yes |

### 2.6 Gap summary

- No prior work in our reference set combines **COMPL-AI-complete orchestration** \cite{guldimann2024complai}, **lifecycle stages**, **Model Card/Datasheet artifacts** \cite{mitchell2019modelcard,gebru2021datasheets}, and **explicit harness provenance** in one self-hostable platform—extending PromptOps-class tools \cite{sunetnanta2025promptops} toward regulatory traceability.

---

## 3. RAIP Framework and Architecture

*Venue section alias: Approach / Design / Implementation.*

### 3.1 Conceptual evaluation model (C1)

#### 3.1.1 Evaluation target and lifecycle stage

- **Evaluation target:** model API, checkpoint, dataset corpus, or poisoned training manifest.
- **Lifecycle stage** field on every run (`data`, `pretrain`, `finetune`, `inference`, …) per canonical `benchmark_run.yaml` schema in project roadmap.

#### 3.1.2 COMPL-AI requirement layer

- 12 measurable IDs (R01–R12) per COMPL-AI \cite{guldimann2024complai}, aggregated from weighted benchmarks (`benchmarks_catalog.yaml`, version `mvp2-v1`).
- Bootstrap 95% CI per requirement after LangGraph `aggregate_node`.
- Score formulas align with COMPL-AI where applicable (e.g., ECE \cite{guo2017calibration}, fairness metrics \cite{hardt2016equality}).

#### 3.1.3 Artifact layer (audit trail)

- `benchmark_run.yaml` — structured scores and metadata.
- `model_card.md` — 12 requirement rows, dataset evaluation block, harness provenance table.
- `datasheet.md` — N04 for datasets (from `scan_dataset`).
- `raw_outputs.jsonl` — per-benchmark harness, agent, optional `fallback: true`.

#### 3.1.4 Stakeholder views (REVIEW)

- **Compliance / risk:** requirement table, signatures, limitations section.
- **ML engineer:** MLflow metrics, raw traces, harness debugging.
- **Data steward:** R03–R05 dataset scans, DVC hash, group Gini.

`[FIG: conceptual_model]` — three layers: lifecycle → COMPL-AI scores → artifacts (Histree-style theory figure).

### 3.2 System architecture (C2)

#### 3.2.1 Runtime flow

```
User/CI → raip-eval CLI or POST /api/v1/runs
       → Redis → Celery worker
       → LangGraph (evaluate → aggregate)
       → LiteLLM → target model (default Ollama)
       → MLflow + MinIO (+ Timescale for checkpoint metrics)
```

#### 3.2.2 Major components

| Component | Responsibility |
|-----------|----------------|
| FastAPI + lab routes | Run creation, dataset scan API |
| Celery | Async long-running evaluation jobs |
| LangGraph supervisor | Dispatch benchmarks, aggregate COMPL-AI scores |
| Benchmark registry | Map benchmark ID → runner implementation |
| Runners | `lm_eval`, `garak`, `hf_dynamic`, `dataset_scan`, `robustness_r01`, `hf_bbq`, `fairness_r11`, `toxicity_r12`, `watermark` |
| Data pipeline | R03–R05 `scan_dataset` |
| Poisoning lab | Injectors, BSR for R02 extension |
| Governance | `sign_artifact`, energy hook, datasheet templates |

`[FIG: architecture]` — boxes: CLI, API, Queue, Worker, LangGraph, LiteLLM, stores.

`[FIG: sequence_run]` — sequence diagram: POST run → evaluate benchmarks → aggregate → upload artifacts.

`[TABLE: component_responsibilities]` — expand table above with file paths for replication package footnote.

### 3.3 Benchmark orchestration and provenance

- **Catalogue:** signed weights per requirement (`src/raip/benchmarks/benchmarks_catalog.yaml`).
- **Dispatch:** `evaluate_benchmarks(..., dataset_context=...)` for R03–R05 corpus on run payload.
- **Provenance:** each `raw_outputs` row includes `harness`, `agent`; fallbacks must set `fallback: true` and `fallback_reason` (Garak, lm_eval runners).
- **Runners cite underlying science:** lm-eval harness \cite{gao2021lmevalharness}; BBQ/BOLD/StereoSet \cite{parrish2022bbq,dhamala2021bold,nadeem2021stereoset}; RealToxicityPrompts \cite{gehman2020realtoxicity}.
- **R09:** `RAIP_WATERMARK_MODE=statistical|na` — heuristic inspired by \cite{kirchenbauer2023watermark}; not full SynthID.

**REVIEW:** Present provenance as transparency mechanism for auditors, not as a ML contribution.

### 3.4 Lifecycle lab extensions (R1)

- Dataset scan in-graph via `dataset_quality_scan`, `dataset_copyright_scan`, `dataset_privacy_scan`.
- Checkpoint evaluator reuses graph; writes Timescale `metric_timeseries`.
- Poisoning lab + BSR (`ASR_post/ASR_pre`) for backdoor persistence narrative (R02 extension), motivated by deceptive-agent persistence \cite{hubinger2024sleeperagents}.

### 3.5 Governance artifact generation (R2, N04)

- Jinja2 model card following Model Cards \cite{mitchell2019modelcard}: 12 measurable rows, dataset eval URIs, harness provenance, signature block.
- Datasheet from dataset scan per Datasheets for Datasets \cite{gebru2021datasheets}; MinIO URI `datasets/{id}/datasheet.md`.
- Environmental reporting hooks align with ML CO₂ methodology \cite{henderson2020mlco2} (N03 declarative).
- Signature metadata via `sign_artifact` (OpenBao/Cosign-ready).

### 3.6 Implementation and replication

- Package `raip` v0.2.0; Python 3.11; Docker Compose for Redis, MinIO, MLflow, Postgres/Timescale.
- Example configs: `examples/mvp2_ollama_e2e_full.yaml`, `examples/mvp2_dataset_eval.yaml`.
- Engineering tests: 42+ unit/lab tests passed (qualitative; cite in §4, not as hypothesis p-value).

**REVIEW:** Scope MVP3 Streamlit/Next.js UI out of this paper — use API response + MLflow screenshots for S3 case study if needed.

---

## 4. Evaluation Setup

*Venue alias: Experimental Design / Experimental Setup.*

### 4.1 Research questions

*Structure follows explicit-RQ empirical SE papers \cite{liu2022mscpdp}; experimental design threats informed by \cite{weninger2018usecase}.*

| RQ | Question | Mapped contributions |
|----|----------|----------------------|
| **RQ1** | Can RAIP automatically produce reproducible, COMPL-AI-aligned scores \cite{guldimann2024complai} across the requested measurable requirements for a given LLM target under declarative configuration? | C2, platform R2–R3 |
| **RQ2** | Does lifecycle extension (dataset scans R03–R05 + checkpoint/lab scenarios) increase measurable **requirement coverage** compared to inference-only evaluation? | C1, platform R1 |
| **RQ3** | Are RAIP governance artifacts \cite{mitchell2019modelcard,gebru2021datasheets} (model card, COMPL-AI table, harness provenance) sufficient for a compliance-oriented reader to interpret outcomes without raw logs? | C3, platform R2 |

**REVIEW:** RQ3 as **structured case study** (checklist), not Histree-style questionnaire \cite{studtmann2023histree} with N participants—future work may add Krippendorff-validated panels \cite{hayes2007krippendorff}.

### 4.2 Evaluation scenarios

`[TABLE: evaluation_scenarios]`

| ID | Name | Configuration | Requirements touched | Answers |
|----|------|---------------|----------------------|---------|
| **S1** | Inference-only | `examples/mvp2_ollama_e2e_full.yaml`; R01–R12 except R03–R05 | R01–R02, R06–R12 | RQ1 |
| **S2** | Lifecycle-extended | S1 + `examples/mvp2_dataset_eval.yaml`; optional checkpoint eval + poison manifest | + R03–R05, BSR | RQ1, RQ2 |
| **S3** | Artifact case study | Selected run from S1 or S2; anonymized model card + provenance table | N04, traceability | RQ3 |

### 4.3 Subject systems

- **Primary target model:** `ollama/llama3.1:8b-instruct-q8_0` (documented default).
- **Infrastructure:** self-hosted Ollama via LiteLLM; same machine class as CI E2E workflow.
- **REVIEW:** Additional models (70B, proprietary API) listed as future work unless runs are completed before draft — do not invent multi-model table.

### 4.4 Independent variables

| Factor | Levels |
|--------|--------|
| Evaluation mode | inference-only (S1) vs lifecycle-extended (S2) |
| Optional harness deps | `[benchmarks]` / `[lab]` installed vs heuristic fallback |
| Watermark mode | `statistical` vs `na` (sensitivity, not primary claim) |

### 4.5 Dependent variables and metrics

| Metric | Definition | RQ |
|--------|------------|-----|
| `complai_Rxx` | Bootstrap-weighted score ∈ [0,1] + CI | RQ1 |
| Requirement **coverage** | \|{R01..R12} with non-empty aggregate\| | RQ2 |
| **Harness fallback rate** | Share of benchmarks with `fallback: true` in `raw_outputs` | RQ1 |
| **BSR** | `ASR_post / ASR_pre` after poisoning scenario | RQ2 |
| **Artifact checklist score** | Case-study rubric: presence of 12 rows, provenance table, signature, limitations | RQ3 |
| Wall-clock / cost | `[RESULT: optional MLflow duration]` | RQ1 optional |

### 4.6 Procedure (reproducibility)

1. Start Docker Compose stack (Redis, MinIO, MLflow, Timescale as configured).
2. `pip install -e ".[dev,lab,benchmarks]"` on Python 3.11.
3. Execute S1 via `raip-eval run examples/mvp2_ollama_e2e_full.yaml` or `POST /api/v1/runs`.
4. Execute S2 with dataset corpus on run payload; optional lab train/checkpoint path.
5. Collect `runs/{run_id}/model_card.md`, `benchmark_run.yaml`, `raw_outputs.jsonl`, MLflow run ID.
6. For S3, two authors (or one author + external reviewer) apply interpretability checklist — **REVIEW:** document rubric in appendix or replication package.

`[RESULT: frozen git SHA, catalog version mvp2-v1, seed=42]`

### 4.7 Hypotheses (qualitative, no numbers)

- **H1 (RQ1):** S1 completes with all requested requirement aggregates and provenance records for each benchmark.
- **H2 (RQ2):** Coverage(S2) ⊃ Coverage(S1) strictly, including R03–R05.
- **H3 (RQ3):** Case-study readers can answer compliance checklist questions using model card alone for ≥ [RESULT: threshold] items — **placeholder, not filled**.

### 4.8 Engineering validation (supporting evidence)

- Unit/lab test suite passes (42 tests, 2 deselected) — supports implementability, not hypothesis testing.
- CI workflow with optional `RAIP_E2E_OLLAMA=1` — mention as replication path.

---

## 5. Results and Analysis

*One subsection per RQ (APSEC 2022 defect-prediction pattern).*

**Global rule for draft:** Replace every `[RESULT: …]` / `[TABLE: …]` / `[FIG: …]` with actual data before submission. **No fabricated means, CIs, or p-values in this outline.**

### 5.1 RQ1 — Reproducible COMPL-AI-aligned scores (S1)

#### 5.1.1 Narrative goals

- Report successful end-to-end execution on default Ollama target.
- Present per-requirement scores and CIs for R01–R02, R06–R12 (S1 scope).
- Report harness provenance: which benchmarks used `lm_eval`, `garak`, dedicated runners vs `hf_dynamic` fallback.

#### 5.1.2 Planned tables and figures

- `[TABLE: complai_scores_s1]` — columns: Requirement ID, Name, Score, CI low, CI high, Contributing benchmarks.
- `[TABLE: harness_provenance_s1]` — columns: Benchmark, Harness, Agent, Fallback (Y/N), Notes.
- `[FIG: bar_complai_r01_r12_s1]` — bar chart of scores by requirement (anonymous style, no brand colors).

#### 5.1.3 Analysis bullets

- Discuss fallback rate: transparency vs completeness trade-off when Garak/lm-eval not installed.
- Discuss R09: statistical TPR vs NA mode — report which mode used in S1.
- Link each row to artifact URIs in MinIO (anonymized paths).

`[RESULT: all numeric cells for TABLE complai_scores_s1]`

### 5.2 RQ2 — Lifecycle coverage (S1 vs S2)

#### 5.2.1 Narrative goals

- Compare requirement coverage sets between S1 and S2.
- Present dataset scores R03–R05 from `dataset_scan` runner on provided corpus.
- Optional: checkpoint trajectory points in Timescale; BSR from poisoning lab scenario.

#### 5.2.2 Planned tables and figures

- `[TABLE: coverage_comparison]` — rows: S1, S2; columns: \|coverage\|, list of requirement IDs, new IDs in S2.
- `[TABLE: dataset_scores_s2]` — R03, R04, R05 scores + engine mode (Detoxify/Presidio vs heuristic_fallback).
- `[FIG: timescale_trajectory]` — optional metric lines per checkpoint (if S2 checkpoint path executed).
- `[FIG: bsr_scenario]` — optional clean vs poisoned ASR illustration.

#### 5.2.3 Analysis bullets

- Argue R1 (lifecycle) is necessary for dataset-stage requirements not observable at inference-only.
- **REVIEW:** Do not overclaim legal compliance — coverage is technical observability only.
- Note MVP2.2 limits: full GPU train, SynthID, LiRA not evaluated.

`[RESULT: coverage sets and dataset scores]`

### 5.3 RQ3 — Artifact interpretability case study (S3)

#### 5.3.1 Narrative goals

- Walk through anonymized model card sections: 12 requirements, dataset evaluation, harness provenance, signature, limitations.
- Apply checklist: Can reader identify (a) weakest requirement, (b) benchmarks contributing to it, (c) whether fallback occurred, (d) dataset datasheet URI?
- Compare to raw `raw_outputs.jsonl` — model card reduces inspection effort.

#### 5.3.2 Planned tables and figures

- `[FIG: model_card_excerpt]` — redacted screenshot or rendered markdown excerpt (double-blind safe).
- `[TABLE: case_study_checklist]` — items: traceability, completeness, clarity; columns: Pass/Fail/Partial, Evidence pointer.

#### 5.3.3 Analysis bullets

- Qualitative findings only unless formal study added later.
- **REVIEW:** If checklist passes, claim "practitioner-oriented interpretability" modestly — not "user satisfaction."

`[RESULT: checklist outcomes]`

### 5.4 Summary of findings

- Bullet synthesis mapping each RQ to yes/no/partial — `[RESULT: summary table]`.

---

## 6. Threats to Validity

### 6.1 Internal validity

- Author-designed scenarios and benchmark weights (`mvp2-v1` catalogue).
- Learning effects N/A (no human repeated tasks except optional case study).
- **Judge=model** in dev configuration may bias LLM-judged probes (R02, R12).
- Heuristic fallbacks (`hf_dynamic`) when optional deps missing — mitigated by provenance reporting, not eliminated.
- R09 statistical watermark is a simplified detector, not production SynthID.

### 6.2 External validity

- Primary evidence on 8B-class local model; may not generalize to larger or proprietary APIs.
- Single-application domain in vignette; no multi-industry deployment study.
- Academic/engineering evaluation context; no longitudinal production (MVP4) data.

### 6.3 Construct validity

- COMPL-AI scores are **technical proxies** for regulatory compliance, not legal conclusions \cite{guldimann2024complai,euaiact2024}.
- Simplified fairness/toxicity metrics vs full DecodingTrust-style protocols \cite{wang2023decodingtrust}.
- Dataset privacy/copyright checks are engineering heuristics vs membership/extraction attacks \cite{carlini2021membership,carlini2023extracting}.

### 6.4 Tool limitations (RAIP-specific)

- N01, N02, N05, N06 not implemented (MVP3+).
- No production governance proxy or Trust Factor (MVP4).
- PEFT/DPO training largely manifest/simulated except optional tiny-model micro-run.
- Catalogue Cosign digest may be placeholder in development builds.
- MVP3 UI absent — case study uses markdown artifacts and optional MLflow UI screenshots.

**REVIEW:** Mirror APSEC tool papers — separate internal / external / tool bullets (Histree, PromptOps style).

---

## 7. Conclusion and Future Work

### 7.1 Conclusion

- Restate problem: fragmented responsible-AI evaluation in SE practice.
- Restate solution: RAIP framework + platform with lifecycle coverage and provenance.
- Summarize RQ answers at high level — `[RESULT: one sentence per RQ after experiments]`.
- Emphasize open-source, self-hostable replication package.

### 7.2 Future work

- MVP3: HITL panels (N01, N02), Next.js dashboards, longitudinal curves.
- MVP4: production proxy, live Trust Factor, kill-switch integration.
- Stronger detectors: SynthID-class R09, LiRA R05, full GPU training campaigns.
- Multi-model benchmark study (70B self-hosted + one proprietary target).
- Formal practitioner study with validated questionnaire (Histree-style \cite{studtmann2023histree}; inter-rater reliability \cite{hayes2007krippendorff}).

### 7.3 Data availability

- `[RESULT: link to anonymized replication package — git tag, compose file, example YAMLs]`

---

## Appendix A — COMPL-AI measurable mapping (draft table for paper body or appendix)

`[TABLE: complai_benchmark_mapping]` — columns: ID, Benchmarks, Runner, Score formula, Primary citation(s).

| ID | Benchmarks (RAIP registry) | Primary cite |
|----|---------------------------|--------------|
| R01 | mmlu_robust, r01_robustness, boolq_contrast | \cite{hendrycks2021mmlu} |
| R02 | advbench, tensortrust, llm_rules, decodingtrust_adv | \cite{wang2023decodingtrust} (+ Garak: prose) |
| R03 | dataset_quality_scan | \cite{gehman2020realtoxicity} (tox); Gini: prose |
| R04 | dataset_copyright_scan | \cite{carlini2023extracting} (leakage motivation) |
| R05 | dataset_privacy_scan | \cite{carlini2021membership,carlini2023extracting} |
| R06 | mmlu, gsm8k, humaneval, truthfulqa, bbh | \cite{hendrycks2021mmlu,cobbe2021gsm8k,chen2021humaneval,lin2022truthfulqa,suzgun2023bbh,gao2021lmevalharness} |
| R07 | ece_mmlu | \cite{guo2017calibration,hendrycks2021mmlu} |
| R08 | self_disclosure_probes | prose (RAIP probes) |
| R09 | watermark_kirchenbauer | \cite{kirchenbauer2023watermark} |
| R10 | bbq, bold, stereoset | \cite{parrish2022bbq,dhamala2021bold,nadeem2021stereoset} |
| R11 | decodingtrust_adult | \cite{hardt2016equality,wang2023decodingtrust} |
| R12 | realtoxicityprompts, advbench_instruction, truthfulqa | \cite{gehman2020realtoxicity,lin2022truthfulqa} |
| R02 ext. | BSR / poisoning lab | \cite{hubinger2024sleeperagents} |

---

## Appendix B — Case study checklist (RQ3, draft)

| # | Question | Evidence location |
|---|----------|-------------------|
| 1 | Are all 12 measurable requirements listed with scores? | Model card §Evaluation Results |
| 2 | Is CI shown per requirement? | Same |
| 3 | Are contributing benchmarks named? | Same |
| 4 | Is dataset evaluation (R03–R05) present when S2 run? | Model card §Dataset evaluation |
| 5 | Does harness provenance list fallbacks? | Model card §Harness provenance |
| 6 | Is signature/digest present? | Model card §Signature |
| 7 | Are limitations stated (pilots, R09, judge)? | Model card §Limitations |
| 8 | Can weakest requirement be identified in < 2 min? | Case study timing `[RESULT]` |

---

## Appendix C — Outline conventions used

- `REVIEW:` — interpretive framing for author confirmation during LaTeX draft.
- `\cite{key}` — only keys present in [manuscript/references.bib](references.bib) (30 entries as of 2026-06-01).
- Tools without bib entries (Garak, Presidio, Detoxify, TensorTrust): **prose only** until keys added.
- `[RESULT: …]`, `[TABLE: …]`, `[FIG: …]` — empirical slots; must not be invented.
- Double-blind: no author names, affiliations, or organization-identifying scenario details in figures.

---

*End of outline — stop before LaTeX body per SciOrchestrator Step 3.*
