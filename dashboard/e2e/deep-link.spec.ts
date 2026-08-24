import { test, expect, type Page } from "@playwright/test";

// Deep links into the compliance view: ?req= opens the requirement drawer,
// ?details=1 expands the run-details panel (harness log). These are the
// targets the study's dashboard-phase buttons point at.

const RUN_ID = "run-0001";

const SUMMARY = {
  run_id: RUN_ID,
  status: "completed",
  model_id: "ollama/mistral:7b-instruct",
  lifecycle_stage: "inference",
  catalog_version: "mvp2-v2",
  created_at: "2026-08-14T08:00:00+00:00",
  updated_at: "2026-08-14T08:10:00+00:00",
  error: null,
  mlflow_run_id: null,
  git_sha: "abc123",
  signature: { digest: "sha256:deadbeef" },
  requirements: [
    {
      id: "R02",
      name: "Cyber resilience",
      rationale: "Adversarial robustness of the deployment",
      principle: "Technical robustness",
      aiact: "Art. 15",
      triage: "failed",
      score: 0.3,
      score_ci_lower: 0.2,
      score_ci_upper: 0.4,
      bootstrap_n: 100,
      contributing_benchmarks: ["advbench"],
      fallback_benchmarks: [],
      band: "red",
    },
    {
      id: "R01",
      name: "Robustness",
      rationale: "Prediction stability",
      principle: "Technical robustness",
      aiact: "Art. 15",
      triage: "ok",
      score: 0.85,
      score_ci_lower: 0.8,
      score_ci_upper: 0.9,
      bootstrap_n: 100,
      contributing_benchmarks: ["mmlu_robust"],
      fallback_benchmarks: [],
      band: "green",
    },
  ],
  triage_counts: { failed: 1, fallback: 0, uncovered: 0, ok: 1, na: 0 },
  harness_provenance: [
    { benchmark_id: "advbench", harness: "hf_dynamic", agent: "hf_dynamic", fallback: "no" },
    { benchmark_id: "mmlu_robust", harness: "hf_dynamic", agent: "hf_dynamic", fallback: "yes" },
  ],
  artifacts: {},
  non_measurable: {
    n01: { status: "pending", queue_count: 0, reviewed: 0, avg_likert: null },
    n02: { status: "pending", queue_count: 0, reviewed: 0, avg_likert: null },
    n03: { status: "pending", fields: {} },
    n04: { status: "pending", fields: {}, model_card_uri: null },
    n05: { status: "pending", fields: {} },
    n06: { status: "pending", fields: {} },
  },
  requested_requirements: ["R01", "R02"],
  trust_factor: { score: 62.0, band: "orange", components: {} },
  band_thresholds: { green_min: 0.7, orange_min: 0.4 },
};

async function mockApi(page: Page) {
  await page.route(`**/api/v1/runs/${RUN_ID}/summary**`, (r) =>
    r.fulfill({ json: SUMMARY }),
  );
  await page.route("**/api/v1/runs?**", (r) =>
    r.fulfill({
      json: {
        runs: [
          {
            run_id: RUN_ID,
            status: "completed",
            model_id: "ollama/mistral:7b-instruct",
            lifecycle_stage: "inference",
            created_at: "2026-08-14T08:00:00+00:00",
          },
        ],
        total: 1,
      },
    }),
  );
  await page.route("**/api/v1/runs/*/raw-outputs*", (r) =>
    r.fulfill({ json: { rows: [], total: 0 } }),
  );
  await page.route("**/api/v1/runs/*/hitl*", (r) => r.fulfill({ json: { tasks: [] } }));
  await page.route("**/api/v1/runs/*/forms", (r) => r.fulfill({ json: { meta: {}, forms: {} } }));
}

test("?req= opens the requirement drawer on arrival", async ({ page }) => {
  await mockApi(page);
  await page.goto(`/dashboards/compliance?run=${RUN_ID}&req=R02&e2e_role=legal_compliance`);
  await expect(page.getByTestId("run-summary-view")).toBeVisible({ timeout: 15_000 });
  // The drawer opens without any click, on the linked requirement.
  const drawer = page.getByTestId("requirement-drawer");
  await expect(drawer).toBeVisible({ timeout: 10_000 });
  await expect(drawer).toContainText("R02");
});

test("?details=1 expands the harness log on arrival", async ({ page }) => {
  await mockApi(page);
  await page.goto(`/dashboards/compliance?run=${RUN_ID}&details=1&e2e_role=legal_compliance`);
  await expect(page.getByTestId("run-summary-view")).toBeVisible({ timeout: 15_000 });
  const toggle = page.getByTestId("run-details-toggle");
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByText("mmlu_robust")).toBeVisible();
});

test("without deep-link params nothing auto-opens", async ({ page }) => {
  await mockApi(page);
  await page.goto(`/dashboards/compliance?run=${RUN_ID}&e2e_role=legal_compliance`);
  await expect(page.getByTestId("run-summary-view")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("run-details-toggle")).toHaveAttribute("aria-expanded", "false");
  await expect(page.getByTestId("requirement-drawer")).toHaveCount(0);
});
