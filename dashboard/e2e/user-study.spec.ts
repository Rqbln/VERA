import { test, expect, type Page } from "@playwright/test";

// Self-administered study flow against a mocked study API (guided mode):
// consent + participant profile, eight timed tasks, then the TAM questionnaire.

interface MockState {
  submissions: Array<Record<string, unknown>>;
  surveys: Array<Record<string, unknown>>;
  sessionBody: Record<string, unknown> | null;
}

function newState(): MockState {
  return { submissions: [], surveys: [], sessionBody: null };
}

async function mockApi(page: Page, state: MockState) {
  await page.route("**/api/v1/study/sessions", (r) => {
    state.sessionBody = r.request().postDataJSON() as Record<string, unknown>;
    r.fulfill({
      json: {
        session_id: "sess-0001",
        participant: "P1",
        run_id: "run-0001",
        requirement_options: [
          { id: "R02", name: "Cyber resilience" },
          { id: "R06", name: "Capabilities" },
        ],
        benchmark_options: ["mmlu", "advbench"],
      },
    });
  });
  await page.route("**/api/v1/study/sessions/*/tasks/*/start", (r) =>
    r.fulfill({ json: { task_id: "T1", started: true } }),
  );
  await page.route("**/api/v1/study/sessions/*/responses", (r) => {
    state.submissions.push(r.request().postDataJSON() as Record<string, unknown>);
    r.fulfill({ json: { recorded: true } });
  });
  await page.route("**/api/v1/study/sessions/*/survey", (r) => {
    state.surveys.push(r.request().postDataJSON() as Record<string, unknown>);
    r.fulfill({ json: { recorded: true } });
  });
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

/** Give up on every task to reach the survey phase quickly. */
async function skipAllTasks(page: Page) {
  for (let i = 0; i < 8; i++) {
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

test("T1 flow submits the answer with app-measured seconds", async ({ page }) => {
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
  expect(sub.task_id).toBe("T1");
  expect((sub.answer as Record<string, unknown>).requirement_id).toBe("R02");
  expect(Number(sub.seconds)).toBeGreaterThanOrEqual(1);
  expect(sub.gave_up).toBe(false);
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

test("survey phase renders after T8 and posts eight Likert items", async ({ page }) => {
  const state = newState();
  await mockApi(page, state);
  await beginStudy(page, "audit");
  await skipAllTasks(page);

  await expect(page.getByTestId("study-survey")).toBeVisible({ timeout: 10_000 });
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
  await skipAllTasks(page);
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
  await skipAllTasks(page);
  await expect(page.getByTestId("study-survey")).toBeVisible({ timeout: 10_000 });
  for (const item of ["PU1", "PU2", "PU3", "PU4", "PEOU1", "PEOU2", "PEOU3", "PEOU4"]) {
    await page.getByTestId(`study-survey-${item}-5`).check();
  }
  await page.getByTestId("study-survey-submit").click();
  await expect(page.getByTestId("study-done")).toBeVisible({ timeout: 10_000 });
  const text = await page.getByTestId("study-done").textContent();
  expect(text).not.toMatch(/correct|wrong|score/i);
});
