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
  await page.route("**/admin/v1/proxy/health", (r) => r.fulfill({ json: {
    gaas_enabled: true, bus: "redis-streams", opa: false, opensearch: false,
    proxy_target: "x", default_mode: "shadow", kill_switch: { engaged: false, reason: "" }, modes: {},
  } }));
  await page.route("**/admin/v1/mode", (r) => r.fulfill({ json: { default: "shadow", models: {} } }));
  await page.route("**/admin/v1/incidents*", (r) => r.fulfill({ json: { incidents: [] } }));
}

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test("governance page renders the runtime panel", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-panel")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("Governance runtime")).toBeVisible({ timeout: 20_000 });
});

test("language toggle switches EN to FR", async ({ page }) => {
  await page.goto("/home");
  await expect(page.getByTestId("home-overview")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("Welcome to VERA")).toBeVisible();
  await page.getByTestId("lang-toggle").click();
  await expect(page.getByText("Bienvenue dans VERA")).toBeVisible({ timeout: 10_000 });
});

test("root redirects to guided home", async ({ page }) => {
  await page.goto("/");
  // The redirect is client-side (useEffect); CI's production server hydrates slower than dev.
  await page.waitForURL(/\/home$/, { timeout: 20_000 });
  await expect(page.getByTestId("home-overview")).toBeVisible({ timeout: 20_000 });
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
  await expect(page.getByTestId("launch-wizard")).toBeVisible({ timeout: 20_000 });
  // Model list comes from a client-side query (mocked); allow for slow CI hydration.
  await expect(page.getByText("llama3.1:8b-instruct-q8_0")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("recommended").first()).toBeVisible({ timeout: 20_000 });
});

test("runs overview renders empty state", async ({ page }) => {
  await page.goto("/runs-overview");
  await expect(page.getByTestId("runs-overview")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("Launch your first evaluation →")).toBeVisible({ timeout: 20_000 });
});

test("all three lenses render for the guided persona", async ({ page }) => {
  for (const lens of ["compliance", "cyber", "ds"]) {
    await page.goto(`/dashboards/${lens}`);
    await expect(page.getByTestId("run-summary-view")).toBeVisible({ timeout: 15_000 });
  }
});
