import { test, expect, type Page } from "@playwright/test";

// Two-condition study flow against a mocked study API (guided mode):
// consent + profile, six baseline items on raw materials, a transition screen,
// six dashboard items, the T8 epilogue, then the TAM questionnaire.

interface MockState {
  submissions: Array<Record<string, unknown>>;
  surveys: Array<Record<string, unknown>>;
  sessionBody: Record<string, unknown> | null;
}

function newState(): MockState {
  return { submissions: [], surveys: [], sessionBody: null };
}

const QUIZ_ITEMS = [
  ...["Q1A", "Q2A", "Q3A", "Q4A", "Q5A", "Q6A"].map((id) => ({
    id,
    condition: "baseline",
    params: paramsFor(id),
  })),
  ...["Q1B", "Q2B", "Q3B", "Q4B", "Q5B", "Q6B"].map((id) => ({
    id,
    condition: "vera",
    params: paramsFor(id),
  })),
];

function paramsFor(id: string): Record<string, string> {
  if (id.startsWith("Q2"))
    return { requirement_id: "R01", requirement_name: "Robustness" };
  if (id === "Q3B") return { requirement_id: "R01", requirement_name: "Robustness" };
  if (id.startsWith("Q6"))
    return { benchmark_id: "advbench", requirement_id: "R02", requirement_name: "Cyber resilience" };
  return {};
}

const TOTAL_STEPS = 13; // 12 quiz items + T8

async function mockApi(page: Page, state: MockState) {
  await page.route("**/api/v1/study/sessions", (r) => {
    state.sessionBody = r.request().postDataJSON() as Record<string, unknown>;
    r.fulfill({
      json: {
        session_id: "sess-0001",
        participant: "P1",
        run_id: "run-0001",
        arm: "alpha_first",
        items: QUIZ_ITEMS,
        requirement_options: [
          { id: "R02", name: "Cyber resilience" },
          { id: "R06", name: "Capabilities" },
        ],
        benchmark_options: ["mmlu", "advbench"],
      },
    });
  });
  await page.route("**/api/v1/study/sessions/*/tasks/*/start", (r) =>
    r.fulfill({ json: { task_id: "Q1A", started: true } }),
  );
  await page.route("**/api/v1/study/sessions/*/responses", (r) => {
    state.submissions.push(r.request().postDataJSON() as Record<string, unknown>);
    r.fulfill({ json: { recorded: true } });
  });
  await page.route("**/api/v1/study/sessions/*/survey", (r) => {
    state.surveys.push(r.request().postDataJSON() as Record<string, unknown>);
    r.fulfill({ json: { recorded: true } });
  });
  // Baseline materials (raw artifacts).
  await page.route("**/api/v1/runs/*/benchmark-run", (r) =>
    r.fulfill({
      json: { run_id: "run-0001", document: { seed: 42, scores: { R02: 0.3 } } },
    }),
  );
  await page.route("**/api/v1/runs/*/provenance", (r) =>
    r.fulfill({
      json: { run_id: "run-0001", provenance: [{ benchmark_id: "mmlu", fallback: "yes" }] },
    }),
  );
  await page.route("**/api/v1/runs/*/raw-outputs*", (r) =>
    r.fulfill({ json: { rows: [{ prompt: "p", output: "o" }], total: 1 } }),
  );
}

async function beginStudy(page: Page, role = "risk_manager") {
  await page.goto("/study");
  await expect(page.getByTestId("study-intro")).toBeVisible({ timeout: 20_000 });
  await page.getByTestId("study-consent").check();
  await page.getByTestId("study-role").selectOption(role);
  await page.getByTestId("study-ai-experience").selectOption("reviewer");
  await page.getByTestId("study-aiact-familiarity").selectOption("working");
  await page.getByTestId("study-seniority").selectOption("6to10");
  await page.getByTestId("study-begin").click();
}

/** Give up on every step (crossing the transition screen) to reach the survey. */
async function skipAllSteps(page: Page) {
  for (let i = 0; i < TOTAL_STEPS; i++) {
    if (i === 6) {
      await page.getByTestId("study-transition-continue").click();
    }
    await page.getByTestId("study-task-start").click();
    await page.getByTestId("study-task-giveup").click();
    await page.getByTestId("study-task-giveup").click();
  }
}

test("consent, role and profile are all required before beginning", async ({ page }) => {
  const state = newState();
  await mockApi(page, state);
  await page.goto("/study");
  await expect(page.getByTestId("study-intro")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("study-begin")).toBeDisabled();
  await page.getByTestId("study-consent").check();
  await expect(page.getByTestId("study-begin")).toBeDisabled();
  await page.getByTestId("study-role").selectOption("risk_manager");
  await expect(page.getByTestId("study-begin")).toBeDisabled(); // profile still missing
  await page.getByTestId("study-ai-experience").selectOption("reviewer");
  await page.getByTestId("study-aiact-familiarity").selectOption("working");
  await expect(page.getByTestId("study-begin")).toBeDisabled();
  await page.getByTestId("study-seniority").selectOption("6to10");
  await expect(page.getByTestId("study-begin")).toBeEnabled();
});

test("session creation posts the participant profile and locale", async ({ page }) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page, "legal");
  await expect(page.getByTestId("study-task")).toBeVisible({ timeout: 10_000 });
  expect(state.sessionBody).toMatchObject({
    role: "legal",
    ai_experience: "reviewer",
    aiact_familiarity: "working",
    seniority: "6to10",
    locale: "en",
  });
});

test("baseline items show the materials panel and never the dashboard button", async ({
  page,
}) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page);
  await expect(page.getByTestId("study-progress")).toContainText("Part 1");

  await page.getByTestId("study-task-start").click();
  await expect(page.getByTestId("study-materials")).toBeVisible();
  await expect(page.getByTestId("study-open-dashboard")).toHaveCount(0);
  // The run record loads into the materials body.
  await expect(page.getByTestId("study-materials-body")).toContainText("seed", {
    timeout: 5_000,
  });
  // Tabs switch to the harness log and the raw outputs.
  await page.getByTestId("study-materials-tab-provenance").click();
  await expect(page.getByTestId("study-materials-body")).toContainText("fallback");
  await page.getByTestId("study-materials-tab-raw").click();
  await expect(page.getByTestId("study-materials-body")).toContainText("output");
});

test("Q1A submits the answer with app-measured seconds", async ({ page }) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page);
  await expect(page.getByTestId("study-task")).toBeVisible({ timeout: 10_000 });

  await page.getByTestId("study-task-start").click();
  await page.waitForTimeout(1200);
  await page.getByTestId("study-answer-requirement").selectOption("R02");
  await page.getByTestId("study-task-submit").click();

  await expect.poll(() => state.submissions.length, { timeout: 5_000 }).toBeGreaterThan(0);
  const sub = state.submissions[0];
  expect(sub.task_id).toBe("Q1A");
  expect((sub.answer as Record<string, unknown>).requirement_id).toBe("R02");
  expect(Number(sub.seconds)).toBeGreaterThanOrEqual(1);
  expect(sub.gave_up).toBe(false);
});

test("transition screen separates part 1 from part 2, which uses the dashboard", async ({
  page,
}) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page);
  for (let i = 0; i < 6; i++) {
    await page.getByTestId("study-task-start").click();
    await page.getByTestId("study-task-giveup").click();
    await page.getByTestId("study-task-giveup").click();
  }
  await expect(page.getByTestId("study-transition")).toBeVisible({ timeout: 10_000 });
  await page.getByTestId("study-transition-continue").click();
  await expect(page.getByTestId("study-progress")).toContainText("Part 2");
  await page.getByTestId("study-task-start").click();
  await expect(page.getByTestId("study-open-dashboard")).toBeVisible();
  await expect(page.getByTestId("study-materials")).toHaveCount(0);
  // Q1B deep-links to the run's compliance view (triage table).
  await expect(page.getByTestId("study-open-dashboard")).toHaveAttribute(
    "data-href",
    "/dashboards/compliance?run=run-0001",
  );
  // Part 2 submissions carry set-B item ids.
  await page.getByTestId("study-task-giveup").click();
  await page.getByTestId("study-task-giveup").click();
  await expect
    .poll(() => state.submissions.map((s) => s.task_id).at(-1), { timeout: 5_000 })
    .toBe("Q1B");
  // Q2B deep-links straight to the named requirement's drawer.
  await page.getByTestId("study-task-start").click();
  await expect(page.getByTestId("study-open-dashboard")).toHaveAttribute(
    "data-href",
    "/dashboards/compliance?run=run-0001&req=R01",
  );
});

test("T8 deep-links to the launch wizard", async ({ page }) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page);
  for (let i = 0; i < 12; i++) {
    if (i === 6) await page.getByTestId("study-transition-continue").click();
    await page.getByTestId("study-task-start").click();
    await page.getByTestId("study-task-giveup").click();
    await page.getByTestId("study-task-giveup").click();
  }
  await page.getByTestId("study-task-start").click();
  await expect(page.getByTestId("study-open-dashboard")).toHaveAttribute(
    "data-href",
    "/launch",
  );
});

test("give up requires confirmation and posts gave_up", async ({ page }) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page, "legal");
  await page.getByTestId("study-task-start").click();
  await page.getByTestId("study-task-giveup").click(); // arm
  await page.getByTestId("study-task-giveup").click(); // confirm
  await expect.poll(() => state.submissions.length, { timeout: 5_000 }).toBeGreaterThan(0);
  expect(state.submissions[0].gave_up).toBe(true);
});

test("survey phase renders after the T8 epilogue and posts eight Likert items", async ({
  page,
}) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page, "audit");
  await skipAllSteps(page);

  await expect(page.getByTestId("study-survey")).toBeVisible({ timeout: 10_000 });
  // 12 quiz items + T8 were all submitted.
  expect(state.submissions).toHaveLength(TOTAL_STEPS);
  expect(state.submissions.map((s) => s.task_id).at(-1)).toBe("T8");
  await expect(page.getByTestId("study-survey-submit")).toBeDisabled();
  for (const item of ["PU1", "PU2", "PU3", "PU4", "PEOU1", "PEOU2", "PEOU3", "PEOU4"]) {
    await page.getByTestId(`study-survey-${item}-4`).check();
  }
  await page.getByTestId("study-survey-comment").fill("clear and quick");
  await page.getByTestId("study-survey-submit").click();

  await expect.poll(() => state.surveys.length, { timeout: 5_000 }).toBeGreaterThan(0);
  const items = state.surveys[0].items as Record<string, number>;
  expect(Object.keys(items)).toHaveLength(8);
  expect(Object.values(items).every((v) => v === 4)).toBe(true);
  expect(state.surveys[0].comment).toBe("clear and quick");
  await expect(page.getByTestId("study-done")).toBeVisible({ timeout: 10_000 });
});

test("survey submit stays disabled until all eight items are answered", async ({ page }) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page);
  await skipAllSteps(page);
  await expect(page.getByTestId("study-survey")).toBeVisible({ timeout: 10_000 });
  for (const item of ["PU1", "PU2", "PU3", "PU4", "PEOU1", "PEOU2", "PEOU3"]) {
    await page.getByTestId(`study-survey-${item}-3`).check();
  }
  await expect(page.getByTestId("study-survey-remaining")).toBeVisible();
  await expect(page.getByTestId("study-survey-submit")).toBeDisabled();
  await page.getByTestId("study-survey-PEOU4-3").check();
  await expect(page.getByTestId("study-survey-submit")).toBeEnabled();
});

test("done screen never shows correctness", async ({ page }) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page, "audit");
  await skipAllSteps(page);
  await expect(page.getByTestId("study-survey")).toBeVisible({ timeout: 10_000 });
  for (const item of ["PU1", "PU2", "PU3", "PU4", "PEOU1", "PEOU2", "PEOU3", "PEOU4"]) {
    await page.getByTestId(`study-survey-${item}-5`).check();
  }
  await page.getByTestId("study-survey-submit").click();
  await expect(page.getByTestId("study-done")).toBeVisible({ timeout: 10_000 });
  const text = await page.getByTestId("study-done").textContent();
  expect(text).not.toMatch(/correct|wrong|score/i);
});
