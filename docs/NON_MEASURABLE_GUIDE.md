---
doc:
  title: Filling the non-measurable requirements (N01–N06)
  status: active
  last_reviewed: 2026-06-26
---

# Non-measurable requirements (N01–N06)

The six COMPL-AI requirements that cannot be auto-scored. N03 is now **measured automatically**; the
rest are filled by a human panel and surfaced on the run summary's non-measurable strip (which reads
the real data, not placeholders).

## N01 / N02 — human review (HITL), multi-criteria rubric
N01 (explainability) and N02 (corrigibility) are judged by a panel on a **rubric** of 1–5 criteria;
the Likert score is the mean of the criteria.

| Req | Criteria (GET `/api/v1/hitl/rubrics`) |
|---|---|
| N01 | faithfulness · completeness · clarity · actionability |
| N02 | responsiveness · reversibility · oversight · safety |

Fill per run:
```bash
# queue a task
curl -X POST :8000/api/v1/hitl/tasks -d '{"run_id":"<id>","requirement":"N01"}' -H 'content-type: application/json'
# a reviewer submits the rubric (Likert = mean)
curl -X POST :8000/api/v1/hitl/tasks/<task_id>/review \
  -d '{"reviewer":"alice","criteria":{"faithfulness":4,"completeness":4,"clarity":5,"actionability":3}}' \
  -H 'content-type: application/json'
```
In the dashboard, use the **Human review (N01/N02)** panel (run summary → Governance & trends).
For credibility, have ≥2 reviewers and report inter-rater agreement.

## N03 — environmental impact (automatic)
Measured during the eval run by **CodeCarbon** (`src/raip/governance/energy.py`) and written to the
N03 form automatically (`kwh`, `co2eq_kg`, `source`). No manual entry; it shows as `measured` on the
strip. Install the `[lab]` extra for real measurement (else it degrades to `unavailable`).

## N04 / N05 / N06 — declarative forms
Attested via the **Declarative forms (N03–N06)** panel or `PUT /api/v1/runs/<id>/forms/<Nxx>`:
- **N04** general description / datasheet (architecture, parameters, training-data summary),
- **N05** evaluation summary,
- **N06** risk summary (misuse scenarios, mitigations, residual risk).

All forms feed the **signed audit PDF** (`GET /api/v1/runs/<id>/audit-pdf`). A form is `completed`
once its checkbox is set; the strip and PDF reflect the real status.
