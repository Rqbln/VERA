# RAIP Research Brief — APSEC 2026 Technical Track

> **Purpose:** Single source of truth for SciOrchestrator (`skills/sci-orchestrator/`) before outline/LaTeX.  
> **Target venue:** APSEC 2026 Technical Track (IEEE two-column, 10 pages incl. references, double-blind).  
> **Profile:** `skills/SciOrchestrator/assets/venue-profiles/apsec2026-technical-raip.yaml`  
> **Playbook:** `skills/SciOrchestrator/skills/sci-orchestrator/apsec-raip-playbook.md`  
> **Last updated:** 2026-06-26 (native 3-model run + banking + measured GaaS; earlier 2026-05-27 discovery retained for history)

---

## 0. Document control

| Field | Value |
|-------|--------|
| Paper working title | **RAIP: A Lifecycle-Aware Open Platform for Responsible AI Evaluation Aligned with COMPL-AI and the EU AI Act** |
| Artifact | Open-source evaluation platform + lab (Python package `raip`, v0.2.0) |
| Repository | RAIP monorepo (`src/raip/`, `docs/`, `examples/`, `tests/`) |
| Manuscript folder | `manuscript/` (main.tex, outline.md, references.bib) |
| `references.bib` | **Not present** at workspace root — all `\cite{key}` blocked until authored |
| `conference-papers/` | Present under `skills/SciOrchestrator/conference-papers/` (README + `.gitkeep` only; PDFs not in workspace) |
| `venue-profile.yaml` | **Not copied** to root — use APSEC profile path above |
| Language of paper | English |
| Contribution confidence | **medium** |

**Confidence rationale (medium):** Implementation and architecture are well documented in code and `docs/`; COMPL-AI mapping and harness provenance are implemented in MVP2. **Missing for a locked empirical paper:** finalized experimental results (numeric scores, tables), participant-based user study (if claimed), and a verified bibliography. Not `low` (no contradictory goals); not `high` (evaluation evidence for publication not yet consolidated).

---

## 1. Venue alignment (APSEC 2026)

| Constraint | Value (from venue profile) |
|------------|----------------------------|
| Conference | 33rd Asia-Pacific Software Engineering Conference (APSEC 2026), Bali |
| Track | Technical research |
| Page limit | 10 pages (references included) |
| Format | IEEEtran, two-column, A4, 10pt body |
| Anonymization | Double-blind |
| Abstract + Index Terms | Required |
| Introduction pattern | Problem → **platform requirements R1–Rk** → *"In this paper, we make the following contributions:"* → **C1–C3** |
| Evaluation style (chosen) | **Explicit RQs** with Results subsections per RQ (defect-prediction style), supplemented by **requirements traceability** to COMPL-AI R01–R12 (Histree-style questionnaire optional for MVP3 UI) |
| Reference papers (expected filenames) | `apsec2025_promptops_llm_trustworthiness.pdf`, `apsec2023_histree_experiment_tracking.pdf`, `apsec2018_restricted_use_case_controlled_experiment.pdf`, `apsec2022_cross_project_defect_prediction.pdf`, `apsec2017_gui_layout_testing_tool.pdf` — **TODO: [USER: add PDFs to `conference-papers/` or confirm alternate set]** |
| Deadlines (2026) | Abstract 2026-07-06; paper 2026-07-13; notification 2026-09-14; camera-ready 2026-10-19 |

**Narrative paradigm:** `se_tool_and_empirical_evaluation` — tool + framework + targeted evaluation (case study and/or controlled scenarios; optional practitioner study).

---

## 2. Central contribution (one sentence)

**Draft (REVIEW — confirm):**  
We present **RAIP**, an open-source, self-hostable software engineering platform that operationalizes the COMPL-AI technical requirements for the EU AI Act through a unified evaluation pipeline (CLI, API, asynchronous workers, LangGraph orchestration), extending inference-time benchmarking with **lifecycle-aware** dataset and checkpoint evaluation, signed governance artifacts, and explicit harness provenance—unlike prior LLM trustworthiness tools that focus primarily on single-shot model prompts without longitudinal or data-stage coverage.

---

## 3. Problem statement and motivation

### 3.1 Context (grounded)

- Regulated and high-risk AI systems require **evidence** that models and data pipelines meet technical expectations derived from the EU AI Act’s trustworthy-AI principles.
- **COMPL-AI** (Guldimann et al., 2024; arXiv:2410.07959v2 — cited in `docs/ROADMAP.md`, `docs/framework_open_source_ia_responsable.md`) decomposes the Act into **18 technical requirements** (**12 measurable**, **6 non-measurable**).
- Industrial practice still relies on **ad hoc** benchmark runs, spreadsheets, and non-reproducible scripts; scores are hard to tie to **lifecycle stages** (data curation, training checkpoints, inference, production).

### 3.2 Pain points RAIP addresses (from project docs + code)

| Pain point | Evidence in repo |
|------------|------------------|
| Fragmented tooling (cyber, fairness, capabilities, dataset quality) | MVP1 architecture lists Garak, lm-eval-harness, Detoxify, Presidio, BBQ, etc.; MVP2 adds dataset scans and poisoning lab |
| Weak traceability from metric → requirement → artifact | `benchmark_run.yaml` schema in `docs/ROADMAP.md`; `benchmarks_catalog.yaml` signed weights; model card lists COMPL-AI rows |
| “Pilot” evaluations that silently degrade (heuristic fallbacks) | MVP2 adds `fallback: true` and `harness` fields in `raw_outputs`; model card **Harness provenance** section |
| No longitudinal view across training | TimescaleDB `metric_timeseries`; checkpoint eval in `src/raip/checkpoint/eval_job.py` |
| Sovereignty / on-prem constraints | Roadmap doctrine: OSS self-hosted stack; LiteLLM → Ollama/vLLM default; proprietary APIs only as **evaluation targets** |

### 3.3 Running example (for Introduction — REVIEW)

REVIEW: Use a **compliance engineer** preparing an internal release gate for an instruction-tuned LLM: they must show scores for robustness (R01), cyber resilience (R02), fairness/toxicity (R10–R12), dataset adequacy (R03–R05), and a signed model card (N04)—today often assembled manually from disconnected tools.

---

## 4. Platform requirements (paper-level R1–R4)

*These are **evaluation-platform requirements** for the APSEC paper (distinct from COMPL-AI requirement IDs R01–R12).*

| ID | Requirement | Grounding in RAIP | Status |
|----|-------------|-------------------|--------|
| **R1** | **Lifecycle coverage** — evaluate targets at multiple lifecycle stages (dataset, checkpoint, inference), not only a frozen model endpoint | MVP2 lab: `scan_dataset`, checkpoint eval, poisoning pipeline; `lifecycle_stage` in `benchmark_run` schema | **Implemented** (training GPU at scale → MVP2.2) |
| **R2** | **Regulatory traceability** — every reported score maps to a COMPL-AI requirement ID with contributing benchmarks and bootstrap CI | LangGraph `aggregate_node`, `benchmarks_catalog.yaml`, `ComplaiRequirementScore`, model card table | **Implemented** |
| **R3** | **Reproducibility and automation** — declarative runs (YAML), async jobs, versioned catalog, git SHA and signatures on artifacts | `raip-eval` CLI, `POST /api/v1/runs`, Celery, `sign_artifact`, Cosign hooks | **Implemented** (full OpenBao production → partial) |
| **R4** | **Sovereign, self-hosted operation** — core path runs without mandatory cloud APIs; sensitive red-teaming stays on-prem | LiteLLM + Ollama default; Docker Compose stack; roadmap bans managed deps for infra | **Implemented** (MVP3 Next.js UI not in scope for this paper) |

---

## 5. Contributions (C1–C3)

*Introduction bullet list per APSEC pattern: "In this paper, we make the following contributions:"*

| ID | Contribution | Grounding | Empirical support in paper |
|----|--------------|-----------|----------------------------|
| **C1** | **Conceptual framework** — lifecycle-aware responsible-AI evaluation model aligning EU AI Act principles, COMPL-AI requirement IDs, lifecycle stages, and stakeholder views | `docs/ROADMAP.md` §1–3, `docs/framework_open_source_ia_responsable.md` §5–8 | Conceptual + mapping tables; no new theory beyond operationalization |
| **C2** | **RAIP platform** — integrated implementation: CLI (`raip-eval`), REST API, Celery workers, LangGraph supervisor, benchmark registry, optional lm-eval/Garak/hf runners, lab routes, MinIO/MLflow/Timescale | `src/raip/*`, `docker-compose.yml`, `examples/*.yaml` | Architecture figure + component table; open-source availability |
| **C3** | **Empirical evaluation** — native 3-model panel (RQ1 cross-model scores), non-degenerate weighting sensitivity (RQ2), design-validation walkthrough (RQ3), data-stage results on a synthetic banking corpus, and an in-process GaaS-runtime benchmark; grounded by an EU AI Act ↔ DORA/EBA/ACPR mapping | `scripts/run_paper_eval.py`, `scripts/bench_gaas.py`, `data/corpus/banking_synth.jsonl`, `manuscript/results/*.json` | **DONE** — `tab:complai-multi` (12×3), `tab:triage-stability` (CR06/CR10 band-flip), `sec:banking` (CR03 0.84 / CR04 0.94 / CR05 0.73), GaaS overhead 5.7 ms / detection 3/3 |

---

## 6. Research questions (RQ1–RQ3)

> **NOTE (2026-06-26):** the final paper (`main.tex`) re-scoped the RQs for the software/dashboard
> focus — **RQ2 is now weighting sensitivity** (not lifecycle coverage) and **RQ3 is a
> design-validation walkthrough**. The rows below keep the original planning wording for history; the
> "Evidence status" column points to what actually shipped.

| RQ | Question | Maps to | Primary metrics / artifacts | Evidence status |
|----|----------|---------|----------------------------|-----------------|
| **RQ1** | Can RAIP **automatically produce reproducible, COMPL-AI-aligned scores** across the 12 measurable requirements for a given LLM target under a declarative configuration? | C2, platform R2–R3 | Per-requirement score `s ∈ [0,1]`; bootstrap 95% CI; `benchmark_run.yaml`; MLflow metrics; `raw_outputs.jsonl` with `harness` / `fallback` | **DONE** — native 3-model panel, `tab:complai-multi`, determinism check |
| **RQ2** | *(final: weighting sensitivity)* How sensitive are scores/bands/triage to the aggregation weights, and is that auditable? | C2 | Per-requirement spread `Δ`, reweighting range, band-flips (`tab:triage-stability`) | **DONE** — non-degenerate: CR01 invariant (Δ=0), CR06/CR10 flip band (Δ=1.0) |
| **RQ3** | Is RAIP **usable and interpretable** for practitioners responsible for compliance documentation (model cards, datasheets, audit trails)? | C3, platform R2 | Task time, Likert/triage tasks; correctness of artifact interpretation | **DONE** — design-validation walkthrough (8 triage tasks); external N-participant study deferred |

**Alternative (if no user study):** Replace RQ3 with a **case study** on documented scenarios (e.g., clean vs poisoned checkpoint, dataset with injected PII) — REVIEW: confirm with authors.

---

## 7. RAIP system — architecture facts (from code)

*Use for Approach section; no invented components.*

### 7.1 High-level flow

```text
User / CI → CLI (raip-eval) or POST /api/v1/runs
         → Redis queue → Celery worker
         → LangGraph: evaluate → aggregate
         → LiteLLM → target model (default Ollama llama3.1:8b-instruct-q8_0)
         → MLflow metrics + MinIO artifacts (model_card.md, benchmark_run.yaml, raw_outputs.jsonl)
```

### 7.2 Major components

| Component | Path / technology | Role |
|-----------|-------------------|------|
| CLI | `src/raip/cli/main.py` | Local run launch |
| API | `src/raip/api/main.py`, `lab_routes.py` | Runs, registry, lab dataset scan |
| Orchestration | `src/raip/graph/supervisor.py` (LangGraph) | Benchmark dispatch + COMPL-AI aggregation |
| Runner dispatch | `src/raip/benchmarks/runners/evaluate.py` | `lm_eval`, `garak`, `hf_dynamic`, `dataset_scan`, `robustness_r01`, `hf_bbq`, `fairness_r11`, `toxicity_r12`, `watermark` |
| Registry | `src/raip/api/benchmark_registry.py` | Benchmark ID → implementation |
| Weights | `src/raip/benchmarks/benchmarks_catalog.yaml` | Signed catalogue `mvp2-v1` |
| Dataset agent | `src/raip/data/pipeline.py` | R03–R05 scans + datasheet |
| Poisoning lab | `src/raip/lab/poison.py`, injectors | Backdoor/trigger experiments |
| Training stubs | `src/raip/training/peft_sft.py`, `dpo.py` | Signed manifests; micro-run if `RAIP_LAB_TRAIN=1` |
| Checkpoint eval | `src/raip/checkpoint/eval_job.py` | Reuses graph; writes Timescale |
| Governance | `src/raip/governance/signing.py`, `energy.py`, `datasheet.py` | Signatures, N03/N04 templates |
| Storage | Redis runs, MinIO, MLflow, TimescaleDB | Per roadmap |

### 7.3 Default evaluation target (documented)

- **Model:** `ollama/llama3.1:8b-instruct-q8_0` (`RAIP_TARGET_MODEL`, `examples/mvp2_ollama_e2e_full.yaml`)
- **Judge:** same as target unless `RAIP_JUDGE_MODEL` set (dev only; production should use separate judge per MVP1 spec)

### 7.4 MVP scope for the paper (honest boundary)

| In scope (MVP2.1 codebase) | Deferred (cite as future work) |
|----------------------------|--------------------------------|
| Inference eval R01–R12 (+ R03–R05 via `dataset_corpus`) | Full GPU Llama 8B training |
| Dataset scan + poisoning lab + BSR | LiRA membership inference (MVP2.2) |
| Model card + datasheet generation | HITL N01/N02 panels (MVP3) |
| Harness provenance, signed manifests | Production proxy / Trust Factor (MVP4) |
| Statistical watermark heuristic (R09) | SynthID production detector (MVP2.2) |

---

## 8. COMPL-AI operationalization (measurable R01–R12)

*Map every planned metric to COMPL-AI ID (paper Evaluation Setup table).*

| COMPL-AI ID | Name (short) | RAIP benchmark(s) | Runner / harness | Score formula (from docs/code) |
|-------------|--------------|-------------------|------------------|------------------------------|
| **R01** | Robustness predictability | `r01_robustness`, `mmlu_robust`, `boolq_contrast` | `robustness_r01`, lm_eval/hf_dynamic | `s = acc_perturbed / max(acc_clean, ε)` |
| **R02** | Cyber resilience | advbench, tensortrust, llm_rules, decodingtrust_adv | garak / hf_dynamic (+ BSR lab) | Attack success → `s = 1 - ASR`; BSR = ASR_post/ASR_pre |
| **R03** | Training data adequacy | `dataset_quality_scan` | `dataset_scan` | `s = 1 - ½(tox_avg + gini)` |
| **R04** | Copyright compliance | `dataset_copyright_scan` | `dataset_scan` | `s = 1 - leak_rate` |
| **R05** | Privacy protection | `dataset_privacy_scan` | `dataset_scan` | `s = 1 - combined PII/extraction rate` |
| **R06** | Capabilities | mmlu, gsm8k, humaneval, truthfulqa, bbh | lm_eval / hf_dynamic | Accuracy / task metric → `s` |
| **R07** | Calibration | `ece_mmlu` | hf_dynamic (`ece` harness) | `s = 1 - ECE` (Guo et al. 2017) |
| **R08** | AI disclosure | `self_disclosure_probes` | hf_dynamic | Probe success rate |
| **R09** | Watermark / traceability | `watermark_kirchenbauer` | `watermark` statistical or `na` | TPR heuristic or excluded from aggregate |
| **R10** | Representation bias | bbq, bold, stereoset | `hf_bbq` / hf_dynamic fallback | `s = 1 - |bias|` |
| **R11** | Fairness | `decodingtrust_adult` | `fairness_r11` | `s = 1 - max(DPD, EOD)` simplified |
| **R12** | Toxicity / harmful content | realtoxicityprompts, advbench_instruction, truthfulqa | `toxicity_r12` | `s = 1 - ½(EMT + (1 - comply_rate))` |

**Non-measurable (N01–N06) — paper handling:**

| ID | RAIP status | Paper treatment |
|----|-------------|-----------------|
| N01, N02 | MVP3 HITL | Future work |
| N03 | `energy.py`, CodeCarbon hook | Declarative / inference-only placeholder in model card unless lab train run |
| N04 | Datasheet + model card Jinja2 | Generated URIs; example `datasets/{id}/datasheet.md` |
| N05, N06 | MVP3 | Future work |

---

## 9. Experimental design (Evaluation Setup)

### 9.1 Study types (proposed — REVIEW)

| Study | Purpose | Supports |
|-------|---------|----------|
| **S1 — Technical pipeline validation** | End-to-end run on default Ollama model with full R01–R12 benchmark list | RQ1 |
| **S2 — Lifecycle scenario** | Same stack + `examples/mvp2_dataset_eval.yaml` (R03–R05) + optional checkpoint eval after poisoned/clean train manifest | RQ2 |
| **S3 — Practitioner study (optional)** | Questionnaire after guided tasks (launch run, read model card, interpret COMPL-AI row) | RQ3 |

### 9.2 Systems / subjects

| Subject | Configuration | Source |
|---------|---------------|--------|
| **Target LLM** | `ollama/llama3.1:8b-instruct-q8_0` | README, examples, config defaults |
| Additional models | TODO: [USER: list models actually evaluated for the paper — e.g., Mixtral, proprietary API target] | MVP1 doc mentions 70B trio — **not confirmed as executed** |
| **Dataset corpus** | User-provided `dataset_corpus` on run payload or lab scan API | `examples/mvp2_dataset_eval.yaml` |
| **Poisoning scenarios** | Hydra `examples/poisoning_experiment.yaml`, 5 injector types | MVP2 lab docs |

### 9.3 Independent variables (controlled)

| Variable | Levels (proposed) |
|----------|-------------------|
| Evaluation mode | inference-only vs inference + dataset scan vs checkpoint (+ poisoned) |
| Harness availability | lm-eval installed vs fallback hf_dynamic (`fallback: true`) |
| Watermark mode | `RAIP_WATERMARK_MODE=statistical` vs `na` |
| Lab extras | `[lab]` installed (Detoxify, Presidio) vs heuristic_fallback |

### 9.4 Dependent variables (metrics)

| Metric | Definition | Requirement / RQ |
|--------|------------|------------------|
| `complai_Rxx` score + CI | Bootstrap weighted mean over benchmarks | RQ1 |
| Requirement **coverage** | Count of R01–R12 with non-empty aggregate | RQ2 |
| **BSR** | `ASR_post / ASR_pre` | R02 extension, RQ2 |
| Wall-clock / cost | TODO: [USER: log from MLflow or manual] | RQ1 optional |
| Questionnaire means | TODO: [USER: Likert items per feature] | RQ3 |
| Harness fallback rate | Fraction of benchmarks with `fallback: true` in `raw_outputs` | RQ1 transparency |

### 9.5 Procedure (reproducibility)

1. `docker compose up` (Redis, MinIO, MLflow, Postgres/Timescale per compose file).  
2. `pip install -e ".[dev,lab,benchmarks]"` (Python 3.11).  
3. `raip-eval run examples/mvp2_ollama_e2e_full.yaml` and/or API `POST /api/v1/runs`.  
4. Collect `runs/{run_id}/model_card.md`, `benchmark_run.yaml`, MLflow run.  
5. **TODO: [USER: freeze commit SHA, catalog version, and environment for paper replication package]**

### 9.6 Hypotheses (draft — REVIEW, no numbers)

- **H1 (RQ1):** RAIP completes an end-to-end run producing all requested COMPL-AI requirement scores with documented provenance.  
- **H2 (RQ2):** Lifecycle configuration yields strictly broader requirement coverage than inference-only (includes R03–R05 and checkpoint-linked metrics).  
- **H3 (RQ3):** Practitioners rate interpretability of model card / COMPL-AI table above neutral threshold — **TODO: [USER: define threshold and instrument]**

---

## 10. Results and evidence inventory

**Rule:** No invented experimental numbers. Only what the repository documents today.

### 10.1 Engineering / test evidence (available now)

| Evidence | Value | Source |
|----------|-------|--------|
| Unit + lab tests | **42 passed** (2 deselected) | `docs/MVP2_STATUS.md`, pytest run 2026-05-27 |
| Test command | `pytest tests/unit/ tests/lab/ -m "not gpu and not slow"` | `docs/MVP2_LAB_RUNBOOK.md` |
| Integration tests | Redis, MinIO, CLI, Timescale memory | `tests/integration/`, `tests/lab/` |
| E2E | `RAIP_E2E_OLLAMA=1` workflow (self-hosted Ollama) | `.github/workflows/raip-ci.yml`, MVP2_STATUS |
| pilote_v1 removed | Registry dispatch tests | `tests/unit/test_registry_dispatch.py` |

### 10.2 Qualitative / informal results (conversation & docs — NOT for numeric tables)

- Informal local runs on Ollama were discussed in project chat (e.g., partial R08/R12 scores).  
- **TODO: [USER: export official result tables from MLflow or `benchmark_run.yaml` for paper]**

### 10.3 Planned results tables (placeholders)

| Table | Content | Status |
|-------|---------|--------|
| Table 1 | Evaluation scenarios (inference, dataset, checkpoint, poisoned) | Outline only |
| Table 2 | COMPL-AI scores per requirement (mean, CI) per scenario | **TODO: numbers** |
| Table 3 | Harness provenance summary (% fallback per benchmark) | **TODO: numbers** |
| Table 4 | Questionnaire (if RQ3) | **TODO: study** |

### 10.4 Planned figures

| Fig | Description | Status |
|-----|-------------|--------|
| Fig 1 | RAIP architecture (CLI, API, Celery, LangGraph, LiteLLM, stores) | Draw from §7 |
| Fig 2 | Evaluation workflow sequence (run → aggregate → artifacts) | Draw from code |
| Fig 3 | Bar chart: COMPL-AI scores by requirement | **TODO: data** |
| Fig 4 | UI screenshots | **TODO: [USER: MVP3 UI or API/MLflow screenshots?]** |

---

## 11. Related work positioning (no bib keys yet)

**Positioning axes (for Related Work table columns):**

| Axis | RAIP claim |
|------|------------|
| Regulatory mapping | Explicit COMPL-AI + EU AI Act article fields in artifacts |
| Lifecycle | Data + checkpoint + inference vs inference-only benchmarks |
| Automation | Job queue + declarative YAML + signed catalogue |
| Sovereignty | Self-hosted OSS stack |
| Provenance | Per-benchmark harness and fallback flag |

**Comparison families (cite when `references.bib` exists):**

| Family | Examples (literature names only — keys TODO) | Gap vs RAIP |
|--------|-----------------------------------------------|-------------|
| LLM trustworthiness tools | PromptOps-class (APSEC 2025 reference paper) | RAIP adds COMPL-AI breadth + lifecycle + lab |
| Experiment tracking | Histree-class | RAIP targets compliance metrics not only ML experiments |
| Benchmark suites | COMPL-AI, DecodingTrust, Garak, lm-eval-harness | RAIP **integrates** rather than replaces |
| RAI governance frameworks | NIST AI RMF, ISO 42001 mappings in docs | RAIP **implements** measurement pipeline |

**`references.bib` status:** **File missing.** Suggested keys to add (do not cite until in bib):

- `guldimann2024complai` — COMPL-AI arXiv:2410.07959  
- `mitchell2019modelcard` — Model Cards  
- `gebru2021datasheets` — Datasheets for Datasets  
- TODO: [USER: PromptOps APSEC 2025, Histree APSEC 2023, EU AI Act official text, Garak, lm-eval-harness papers]

---

## 12. Threats to validity (template for paper)

### 12.1 Internal validity

- Author-designed scenarios and benchmark weights (`benchmarks_catalog.yaml`).  
- Fallback to `hf_dynamic` when lm-eval/Garak unavailable — must report fallback rate.  
- Default judge = target model in dev (weak judge bias).  
- R09 statistical watermark is a **heuristic**, not SynthID.  
- PEFT/DPO training is manifest/simulated except optional tiny-gpt2 micro-run.

### 12.2 External validity

- Primary evidence on **8B-class** local model; may not generalize to 70B or proprietary APIs.  
- Single-organization industrial context (anonymized for double-blind review).  
- No longitudinal production deployment study (MVP4).

### 12.3 Construct validity

- COMPL-AI scores are **technical proxies**, not legal compliance conclusions (stated in COMPL-AI limits, `framework_open_source_ia_responsable.md`).  
- Simplified fairness/toxicity metrics vs full DecodingTrust protocols.

### 12.4 Tool-specific limitations

- Incomplete coverage of N01, N02, N05, N06.  
- Streamlit UI replaced by MVP3 — paper may use API/MLflow artifacts only.  
- Catalogue signing: Cosign digest placeholder in catalog file.

---

## 13. Conclusion and future work (bullet plan)

- Summarize C1–C3: framework, RAIP platform, empirical lessons.  
- Emphasize **reproducible COMPL-AI-aligned artifacts** as the practical contribution for software engineering compliance workflows.  
- Future work: MVP3 dashboards + HITL, MVP4 production governance, full SynthID/LiRA, multi-model benchmark campaign, formal user study with compliance officers.

---

## 14. Out of scope for the agent (SciOrchestrator)

The writing agent **must not** without user data:

| Forbidden | Reason |
|-----------|--------|
| Invent experimental means, medians, p-values, participant counts | No consolidated results file in repo |
| Invent `\cite{key}` or bibliography entries | `references.bib` absent |
| Claim user-study outcomes | No study instrument or results in repo |
| Assert legal compliance of any deployed system | Out of project scope |
| Generate full LaTeX manuscript in this step | User task was research-brief only |
| Copy text from `conference-papers/*.pdf` | PDFs not present in workspace |
| Fabricate comparison to commercial products beyond literature categories | Needs verified citations |

**Agent may proceed when:** `references.bib` exists, contribution confidence raised to **high**, and Table 2 numeric cells provided by user.

---

## Appendix A — Traceability matrix (RQ → requirements → artifacts)

| RQ | Platform R1–R4 | COMPL-AI IDs | Primary artifacts |
|----|----------------|--------------|-------------------|
| RQ1 | R2, R3 | R01–R12 (requested subset) | `benchmark_run.yaml`, MLflow, `model_card.md`, `raw_outputs.jsonl` |
| RQ2 | R1 | R03–R05 + R02 BSR + checkpoint metrics | `mvp2_dataset_eval.yaml`, Timescale points, lab poison reports |
| RQ3 | R2 | N04 (+ interpret R01–R12 table) | Model card, datasheet, **questionnaire TODO** |

---

## Appendix B — Repository discovery log

| Area searched | Key paths | Findings |
|---------------|-----------|----------|
| Docs | `docs/ROADMAP.md`, `MVP1_*.md`, `MVP2_*.md`, `framework_open_source_ia_responsable.md` | Full vision, COMPL-AI mapping, MVP boundaries |
| Code | `src/raip/` | MVP2 platform implemented |
| Examples | `examples/mvp2_ollama_e2e_full.yaml`, `mvp2_dataset_eval.yaml` | Runnable configs |
| Tests | `tests/unit/`, `tests/lab/`, `tests/integration/` | 42+ tests; no paper result bundle |
| Slides / manuscript | — | **Not found** |
| Thesis | — | **Not found** |
| `references.bib` | — | **Not found** |
| SciOrchestrator | `skills/SciOrchestrator/` | Venue profile, playbook, prompts; template `research-brief-raip.template.md` **not found** (structure inferred from task + playbook) |

---

## Appendix C — Open inputs for author (grouped, ≤8 question themes)

1. **Contribution:** Confirm one-sentence contribution in §2 or narrow to inference-only vs lifecycle.  
2. **R1–R4:** Accept platform requirements §4 or revise wording.  
3. **RQs:** Keep RQ3 user study vs replace with case study only.  
4. **Systems evaluated:** Which models and APIs were actually run for paper tables?  
5. **Results:** Provide MLflow export or `benchmark_run.yaml` aggregates for Table 2.  
6. **User study:** Participants, tasks, N, questionnaire items (if RQ3).  
7. **Bibliography:** Create `references.bib` with verified keys; add 5 APSEC PDFs to `conference-papers/`.  
8. **Anonymization:** Institution/authors handling for double-blind.

*End of research brief.*
