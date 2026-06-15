import { test, expect, type Page } from "@playwright/test";

// The dashboard runs in guided (no-login) mode under test (NEXT_PUBLIC_AUTH_DISABLED=1).
// We mock the read API so the guided surfaces are deterministic without a live backend.
async function mockApi(page: Page) {
  await page.route("**/api/v1/health/stack", (r) =>
    r.fulfill({
      json: {
        ok: true,
        degraded: true,
        checks: {
          redis: { ok: true, required: true },
          minio: { ok: true, required: false, backend: "local" },
          mlflow: { ok: true, required: false, status: "disabled" },
          ollama: { ok: true, required: true, model_count: 2 },
        },
      },
    }),
  );
  await page.route("**/api/v1/models/connected", (r) =>
    r.fulfill({
      json: {
        models: [
          { model_id: "ollama/llama3.1:8b-instruct-q8_0", name: "llama3.1:8b-instruct-q8_0", provider: "ollama", connected: true, recommended: true },
          { model_id: "ollama/phi3:mini", name: "phi3:mini", provider: "ollama", connected: true, recommended: false },
        ],
        ollama_base: "http://localhost:11434",
        recommended_model: "ollama/llama3.1:8b-instruct-q8_0",
      },
    }),
  );
  await page.route("**/api/v1/runs**", (r) => r.fulfill({ json: { runs: [], total: 0 } }));
  await page.route("**/api/v1/governance/kill-switch", (r) => r.fulfill({ json: { engaged: false, reason: "" } }));
}

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test("root redirects to guided home", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/home$/);
  await expect(page.getByTestId("home-overview")).toBeVisible();
});

test("home shows quick actions and no login chrome", async ({ page }) => {
  await page.goto("/home");
  await expect(page.getByTestId("home-overview")).toBeVisible();
  await expect(page.getByText("Launch an evaluation", { exact: true })).toBeVisible();
  await expect(page.getByText("Guided mode · no login")).toBeVisible();
  // No "Sign out" button in guided mode.
  await expect(page.getByRole("button", { name: "Sign out" })).toHaveCount(0);
});

test("launch wizard renders connected models", async ({ page }) => {
  await page.goto("/launch");
  await expect(page.getByTestId("launch-wizard")).toBeVisible();
  await expect(page.getByText("llama3.1:8b-instruct-q8_0")).toBeVisible();
  await expect(page.getByText("recommended").first()).toBeVisible();
});

test("runs overview renders empty state", async ({ page }) => {
  await page.goto("/runs-overview");
  await expect(page.getByTestId("runs-overview")).toBeVisible();
  await expect(page.getByText("Launch your first evaluation →")).toBeVisible();
});

test("all three lenses render for the guided persona", async ({ page }) => {
  for (const lens of ["compliance", "cyber", "ds"]) {
    await page.goto(`/dashboards/${lens}`);
    await expect(page.getByTestId("run-summary-view")).toBeVisible({ timeout: 15_000 });
  }
});
