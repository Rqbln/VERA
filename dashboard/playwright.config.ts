import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    // The standalone server needs static assets copied next to it (as the Dockerfile does),
    // otherwise client JS 404s and client-only behaviour (redirects, queries) never runs.
    command: process.env.CI
      ? "cp -r .next/static .next/standalone/.next/ 2>/dev/null; cp -r public .next/standalone/ 2>/dev/null; node .next/standalone/server.js"
      : "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    env: {
      NEXT_PUBLIC_AUTH_DISABLED: "1",
      NEXT_PUBLIC_DEV_ROLES: "legal_compliance,data_scientist,secops",
    },
  },
});
