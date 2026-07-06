import { test, expect, type Page } from "@playwright/test";

// Exercises the N01/N02 multi-criteria rubric review flow against a mocked API
// (guided no-login mode, same conventions as guided-mode.spec.ts).

const RUN_ID = "hitl0001-aaaa-bbbb-cccc-000000000001";

const RUBRICS = {
  N01: ["faithfulness", "completeness", "clarity", "actionability"],
  N02: ["responsiveness", "reversibility", "oversight", "safety"],
};

const SUMMARY = {
  run_id: RUN_ID,
  status: "completed",
  model_id: "ollama/llama3.1:8b-instruct-q8_0",
  lifecycle_stage: "inference",
  catalog_version: "v2",
  created_at: "2026-07-01T10:00:00Z",
  updated_at: "2026-07-01T10:05:00Z",
  error: null,
  mlflow_run_id: null,
  git_sha: "anon0000",
  signature: { digest: "sha256:anon", key_id: "openbao-transit-dev", algo: "sha256" },
  requirements: [
    {
      id: "R02",
      name: "Cyber resilience",
      rationale: "",
      principle: "robustness_safety",
      aiact: "Art. 15",
      triage: "ok",
      score: 0.5,
      score_ci_lower: 0.2,
      score_ci_upper: 0.8,
      contributing_benchmarks: [],
      fallback_benchmarks: [],
      band: "orange",
    },
  ],
  triage_counts: { failed: 0, fallback: 0, uncovered: 0, ok: 1, na: 0 },
  harness_provenance: [],
  artifacts: {},
  non_measurable: {
    n01: { status: "queued", queue_count: 1, reviewed: 0 },
    n02: { status: "pending", queue_count: 0, reviewed: 0 },
    n03: { status: "measured", kwh: 0.012, co2eq_kg: 0.004 },
    n04: { status: "available" },
    n05: { status: "pending", fields: {} },
    n06: { status: "pending", fields: {} },
  },
  requested_requirements: ["R02"],
  trust_factor: { score: 62, band: "orange", components: {} },
};

interface MockState {
  tasks: Array<Record<string, unknown>>;
  submitted: Record<string, unknown> | null;
}

async function mockApi(page: Page, state: MockState) {
  await page.route("**/api/v1/health/stack", (r) =>
    r.fulfill({
      json: {
        ok: true,
        degraded: true,
        checks: {
          redis: { ok: true, required: true },
          minio: { ok: true, required: false, backend: "local" },
          mlflow: { ok: true, required: false, status: "disabled" },
          ollama: { ok: true, required: true, model_count: 1 },
        },
      },
    }),
  );
  await page.route("**/api/v1/governance/kill-switch", (r) =>
    r.fulfill({ json: { engaged: false, reason: "" } }),
  );
  await page.route("**/api/v1/runs?*", (r) =>
    r.fulfill({
      json: {
        runs: [
          {
            run_id: RUN_ID,
            status: "completed",
            model_id: SUMMARY.model_id,
            lifecycle_stage: "inference",
            catalog_version: "v2",
            created_at: SUMMARY.created_at,
            updated_at: SUMMARY.updated_at,
          },
        ],
        total: 1,
      },
    }),
  );
  await page.route("**/api/v1/runs/*/summary*", (r) => r.fulfill({ json: SUMMARY }));
  await page.route("**/api/v1/runs/*/forms", (r) =>
    r.fulfill({ json: { run_id: RUN_ID, meta: {}, forms: {} } }),
  );
  await page.route("**/api/v1/series*", (r) =>
    r.fulfill({ json: { available: false, requirement: "R02", series: [] } }),
  );
  await page.route("**/api/v1/hitl/rubrics", (r) => r.fulfill({ json: { rubrics: RUBRICS } }));
  await page.route("**/api/v1/hitl/tasks?*", (r) => r.fulfill({ json: { tasks: state.tasks } }));
  await page.route("**/api/v1/hitl/tasks/*/review", (r) => {
    state.submitted = r.request().postDataJSON();
    const criteria = (state.submitted?.criteria ?? {}) as Record<string, number>;
    const values = Object.values(criteria);
    const likert = values.length
      ? Math.round(values.reduce((a, b) => a + b, 0) / values.length)
      : (state.submitted?.likert_score as number);
    state.tasks = state.tasks.map((t) => ({
      ...t,
      status: "done",
      likert_score: likert,
      criteria,
      comment: (state.submitted?.comment as string) ?? "",
    }));
    r.fulfill({ json: { task: state.tasks[0] } });
  });
}

function pendingN01Task(): Record<string, unknown> {
  return {
    task_id: "task-n01-0001",
    run_id: RUN_ID,
    requirement: "N01",
    prompt: "Panel review of N01",
    sample_ref: "",
    status: "pending",
    reviewer: "",
    likert_score: null,
    criteria: {},
    comment: "",
    created_at: "2026-07-01T10:05:00Z",
    updated_at: "2026-07-01T10:05:00Z",
  };
}

async function openHitlPanel(page: Page) {
  await page.goto(`/dashboards/compliance?run=${RUN_ID}`);
  await expect(page.getByTestId("run-summary-view")).toBeVisible({ timeout: 20_000 });
  await page.getByText("Governance & trends").click();
  await expect(page.getByTestId("hitl-panel")).toBeVisible({ timeout: 20_000 });
}

test("rubric criteria are fetched and rendered for a pending task", async ({ page }) => {
  const state: MockState = { tasks: [pendingN01Task()], submitted: null };
  await mockApi(page, state);
  await openHitlPanel(page);
  for (const criterion of RUBRICS.N01) {
    await expect(page.getByTestId(`hitl-criterion-${criterion}`)).toBeVisible({
      timeout: 10_000,
    });
  }
});

test("submits a rubric review with per-criterion scores and a comment", async ({ page }) => {
  const state: MockState = { tasks: [pendingN01Task()], submitted: null };
  await mockApi(page, state);
  await openHitlPanel(page);

  await page.getByTestId("hitl-criterion-faithfulness").selectOption("4");
  await page.getByTestId("hitl-criterion-completeness").selectOption("5");
  await page.getByTestId("hitl-criterion-clarity").selectOption("3");
  await page.getByTestId("hitl-criterion-actionability").selectOption("4");
  await page.getByTestId("hitl-comment").fill("clear rationale, actionable output");
  await page.getByTestId("hitl-submit").click();

  await expect(page.getByText("Likert 4/5")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("done")).toBeVisible();
  expect(state.submitted?.criteria).toEqual({
    faithfulness: 4,
    completeness: 5,
    clarity: 3,
    actionability: 4,
  });
  expect(state.submitted?.comment).toBe("clear rationale, actionable output");
  // The done row shows the per-criterion breakdown.
  await expect(page.getByText("completeness: 5/5")).toBeVisible();
});
