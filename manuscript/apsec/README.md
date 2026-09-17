# APSEC 2026 paper (submitted, frozen)

*VERA: A Responsible AI Dashboard for Assessing LLM Deployments in Light of the EU AI Act*,
submitted to the Software Engineering in Practice track of APSEC 2026. This folder keeps the
submitted version and its provenance; new work goes to the ICSE 2027 paper in `manuscript/`.
The ICSE paper cites this one and may not reuse its numbers (`../support/apsec_guard.txt`).

| Path | Content |
|---|---|
| `main_apsec.tex`, `references.bib` | The submitted paper (synced with Overleaf) |
| `etc.sty`, `IEEEtran.*` | Local shim and class so the folder compiles on its own |
| `figures/` | The three figures the paper uses, and the two screens of its commented appendix |
| `results/` | The n=150 runs of the four served models, their merge, and the alternative-specification demo |
| `scripts/` | The drivers that produced `results/` (run from the repository root) |
| `study/` | Anonymous exports of the reading study (quiz and questionnaire); analysis: `scripts/analyze_user_study.py` at the repository root |
| `HANDOFF.md` | The handoff notes written while preparing the submission |

Build: `make apsec` from `manuscript/`, or `latexmk -pdf main_apsec.tex` here. The author block
lives in `authors_apsec.tex`, which is not version-controlled.
