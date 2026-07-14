import { test, expect, type Page } from "@playwright/test";

// Self-administered study flow against a mocked study API (guided mode).

interface MockState {
  submissions: Array<Record<string, unknown>>;
}

async function mockApi(page: Page, state: MockState) {
  await page.route("**/api/v1/study/sessions", (r) =>
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
    }),
  );
  await page.route("**/api/v1/study/sessions/*/tasks/*/start", (r) =>
    r.fulfill({ json: { task_id: "T1", started: true } }),
  );
  await page.route("**/api/v1/study/sessions/*/responses", (r) => {
    state.submissions.push(r.request().postDataJSON() as Record<string, unknown>);
    r.fulfill({ json: { recorded: true } });
  });
}

test("consent and role are required before beginning", async ({ page }) => {
  const state: MockState = { submissions: [] };
  await mockApi(page, state);
  await page.goto("/study");
  await expect(page.getByTestId("study-intro")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("study-begin")).toBeDisabled();
  await page.getByTestId("study-consent").check();
  await expect(page.getByTestId("study-begin")).toBeDisabled();
  await page.getByTestId("study-role").selectOption("risk_manager");
  await expect(page.getByTestId("study-begin")).toBeEnabled();
});

test("T1 flow submits the answer with app-measured seconds", async ({ page }) => {
  const state: MockState = { submissions: [] };
  await mockApi(page, state);
  await page.goto("/study");
  await page.getByTestId("study-consent").check();
  await page.getByTestId("study-role").selectOption("risk_manager");
  await page.getByTestId("study-begin").click();
  await expect(page.getByTestId("study-task")).toBeVisible({ timeout: 10_000 });

  await page.getByTestId("study-task-start").click();
  await page.waitForTimeout(1200);
  await page.getByTestId("study-answer-requirement").selectOption("R02");
  await page.getByTestId("study-task-submit").click();

  await expect
    .poll(() => state.submissions.length, { timeout: 5_000 })
    .toBeGreaterThan(0);
  const sub = state.submissions[0];
  expect(sub.task_id).toBe("T1");
  expect((sub.answer as Record<string, unknown>).requirement_id).toBe("R02");
  expect(Number(sub.seconds)).toBeGreaterThanOrEqual(1);
  expect(sub.gave_up).toBe(false);
});

test("give up requires confirmation and posts gave_up", async ({ page }) => {
  const state: MockState = { submissions: [] };
  await mockApi(page, state);
  await page.goto("/study");
  await page.getByTestId("study-consent").check();
  await page.getByTestId("study-role").selectOption("legal");
  await page.getByTestId("study-begin").click();
  await page.getByTestId("study-task-start").click();
  await page.getByTestId("study-task-giveup").click(); // arm
  await page.getByTestId("study-task-giveup").click(); // confirm
  await expect
    .poll(() => state.submissions.length, { timeout: 5_000 })
    .toBeGreaterThan(0);
  expect(state.submissions[0].gave_up).toBe(true);
});

test("done screen never shows correctness", async ({ page }) => {
  const state: MockState = { submissions: [] };
  await mockApi(page, state);
  await page.goto("/study");
  await page.getByTestId("study-consent").check();
  await page.getByTestId("study-role").selectOption("audit");
  await page.getByTestId("study-begin").click();
  for (let i = 0; i < 8; i++) {
    await page.getByTestId("study-task-start").click();
    await page.getByTestId("study-task-giveup").click();
    await page.getByTestId("study-task-giveup").click();
  }
  await expect(page.getByTestId("study-done")).toBeVisible({ timeout: 10_000 });
  const text = await page.getByTestId("study-done").textContent();
  expect(text).not.toMatch(/correct|wrong|score/i);
});
