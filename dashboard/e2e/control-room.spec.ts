import { test, expect } from "@playwright/test";

const VIEWS: { path: string; allowed: string[] }[] = [
  {
    path: "/dashboards/compliance",
    allowed: [
      "legal_compliance",
      "risk_manager",
      "domain_expert",
      "external_auditor",
      "executive",
      "secops",
    ],
  },
  {
    path: "/dashboards/cyber",
    allowed: ["secops", "legal_compliance", "risk_manager", "external_auditor"],
  },
  {
    path: "/dashboards/ds",
    allowed: ["data_scientist", "ml_researcher"],
  },
];

const ALL_PERSONAS = [
  "legal_compliance",
  "data_scientist",
  "secops",
  "ml_researcher",
  "domain_expert",
  "external_auditor",
  "risk_manager",
  "executive",
];

function urlWithRole(path: string, role: string) {
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}e2e_role=${encodeURIComponent(role)}`;
}

for (const view of VIEWS) {
  for (const role of ALL_PERSONAS) {
    const shouldAllow = view.allowed.includes(role);
    test(`${view.path} · ${role} → ${shouldAllow ? "allow" : "403"}`, async ({ page }) => {
      await page.goto(urlWithRole(view.path, role));
      if (shouldAllow) {
        await expect(page.getByText("VERA Control Room")).toBeVisible();
        await expect(page.getByTestId("run-summary-view")).toBeVisible({ timeout: 15_000 });
      } else {
        await expect(page.getByTestId("auth-forbidden")).toBeVisible({ timeout: 15_000 });
      }
    });
  }
}

test("stack health strip visible on compliance", async ({ page }) => {
  await page.goto(urlWithRole("/dashboards/compliance", "legal_compliance"));
  await expect(page.getByText("Stack")).toBeVisible();
});
