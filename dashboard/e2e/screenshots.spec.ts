import { test, type Page } from "@playwright/test";

// Screenshot CAPTURE is a manual task, not part of the hermetic e2e suite: these tests write into
// the tracked ../manuscript/figures/*.png. They are skipped unless RAIP_CAPTURE_SHOTS=1 so CI and
// contributors do not get noisy diffs.
const CAPTURE = process.env.RAIP_CAPTURE_SHOTS === "1";
test.beforeEach(() => {
  test.skip(!CAPTURE, "screenshot capture is manual; run with RAIP_CAPTURE_SHOTS=1");
});

// Captures dashboard screenshots for the APSEC paper using the REAL S1 scores
// (from manuscript/results/paper_results.json), in guided no-login mode (double-blind safe).
const META: Record<string, { name: string; principle: string; aiact: string }> = {
  R01: { name: "Robustness predictability", principle: "robustness_safety", aiact: "Art. 15" },
  R06: { name: "Capabilities", principle: "transparency", aiact: "Art. 15" },
  R07: { name: "Calibration / interpretability", principle: "transparency", aiact: "Art. 13" },
  R08: { name: "AI disclosure", principle: "transparency", aiact: "Art. 13" },
  R10: { name: "Representation bias", principle: "fairness", aiact: "Art. 10" },
  R12: { name: "Toxicity / harmful content", principle: "fairness", aiact: "Art. 10" },
};
// Real scores from the S1 run on llama3.1:8b (seed 42, n=10).
const S1 = {
  R08: { score: 0.5, lo: 0.2, hi: 0.8, band: "orange", triage: "fallback" },
  R10: { score: 0.67, lo: 0.67, hi: 0.67, band: "orange", triage: "ok" },
  R06: { score: 0.8, lo: 0.8, hi: 0.8, band: "green", triage: "fallback" },
  R07: { score: 0.9, lo: 0.9, hi: 0.9, band: "green", triage: "ok" },
  R01: { score: 1.0, lo: 1.0, hi: 1.0, band: "green", triage: "ok" },
  R12: { score: 1.0, lo: 1.0, hi: 1.0, band: "green", triage: "ok" },
};
const ORDER = ["R08", "R10", "R06", "R07", "R01", "R12"] as const;

const requirements = ORDER.map((id) => ({
  id,
  name: META[id].name,
  rationale: "",
  principle: META[id].principle,
  aiact: META[id].aiact,
  triage: S1[id].triage,
  score: S1[id].score,
  score_ci_lower: S1[id].lo,
  score_ci_upper: S1[id].hi,
  contributing_benchmarks: [],
  fallback_benchmarks: S1[id].triage === "fallback" ? ["hf_dynamic"] : [],
  band: S1[id].band,
}));

const SUMMARY = {
  run_id: "demo0001-aaaa-bbbb-cccc-000000000001",
  status: "completed",
  model_id: "ollama/llama3.1:8b-instruct-q8_0",
  lifecycle_stage: "inference",
  catalog_version: "mvp2-v1",
  created_at: "2026-06-15T11:45:00Z",
  updated_at: "2026-06-15T11:48:00Z",
  error: null,
  mlflow_run_id: null,
  git_sha: "anon0000",
  signature: { digest: "sha256:anon", key_id: "openbao-transit-dev", algo: "sha256" },
  requirements,
  triage_counts: { failed: 0, fallback: 2, uncovered: 0, ok: 4, na: 0 },
  harness_provenance: [
    { benchmark_id: "mmlu", harness: "hf_dynamic", agent: "hf_dynamic", fallback: "yes" },
    { benchmark_id: "r01_robustness", harness: "paired_acc_ratio", agent: "robustness", fallback: "no" },
  ],
  artifacts: { benchmark_run: "local://demo/benchmark_run.yaml", model_card: "local://demo/model_card.md", raw_outputs: "local://demo/raw_outputs.jsonl" },
  non_measurable: {
    n01: { status: "pending", queue_count: 0, tasks: [] },
    n02: { status: "pending", queue_count: 0, tasks: [] },
    n03: { status: "n/a" },
    n04: { status: "available" },
    n05: { status: "mvp3" },
    n06: { status: "mvp3" },
  },
  requested_requirements: ORDER,
  trust_factor: { score: 75, band: "green", components: { R01: 100, R12: 100 } },
};

async function mock(page: Page) {
  await page.route("**/api/v1/health/stack", (r) =>
    r.fulfill({ json: { ok: true, degraded: true, checks: {
      redis: { ok: true, required: true }, minio: { ok: true, required: false, backend: "local" },
      mlflow: { ok: true, required: false, status: "disabled" }, ollama: { ok: true, required: true, model_count: 3 },
    } } }),
  );
  await page.route("**/api/v1/runs?*", (r) => r.fulfill({ json: { runs: [
    { run_id: SUMMARY.run_id, status: "completed", model_id: SUMMARY.model_id, lifecycle_stage: "inference", catalog_version: "mvp2-v1", created_at: SUMMARY.created_at, updated_at: SUMMARY.updated_at },
  ], total: 1 } }));
  await page.route("**/api/v1/runs/*/summary*", (r) => r.fulfill({ json: SUMMARY }));
  await page.route("**/api/v1/models/connected", (r) => r.fulfill({ json: { models: [
    { model_id: "ollama/llama3.1:8b-instruct-q8_0", name: "llama3.1:8b-instruct-q8_0", provider: "ollama", connected: true, recommended: true },
    { model_id: "ollama/ministral-3:3b", name: "ministral-3:3b", provider: "ollama", connected: true, recommended: false },
    { model_id: "ollama/phi3:mini", name: "phi3:mini", provider: "ollama", connected: true, recommended: false },
  ], ollama_base: "http://localhost:11434", recommended_model: "ollama/llama3.1:8b-instruct-q8_0" } }));
  await page.route("**/api/v1/governance/kill-switch", (r) => r.fulfill({ json: { engaged: false, reason: "" } }));
  await page.route("**/admin/v1/proxy/health", (r) => r.fulfill({ json: {
    gaas_enabled: true, bus: "kafka", opa: true, opensearch: true,
    proxy_target: "http://ollama:11434", default_mode: "advisory",
    kill_switch: { engaged: false, reason: "" },
    modes: { "ollama/llama3.1:8b-instruct-q8_0": "enforcement", "ollama/ministral-3:3b": "advisory" },
  } }));
  await page.route("**/admin/v1/mode", (r) => r.fulfill({ json: { default: "advisory", models: {
    "ollama/llama3.1:8b-instruct-q8_0": "enforcement", "ollama/ministral-3:3b": "advisory",
  } } }));
  await page.route("**/admin/v1/incidents*", (r) => r.fulfill({ json: { incidents: [
    { event_id: "e1", ts: "2026-06-22T09:14:00Z", kind: "policy_deny", model: "ollama/llama3.1:8b-instruct-q8_0", decision: "deny", trust_score: 0.22 },
    { event_id: "e2", ts: "2026-06-22T08:51:00Z", kind: "low_trust", model: "ollama/ministral-3:3b", decision: "flag", trust_score: 0.41 },
  ] } }));
}

test("capture control room", async ({ page }) => {
  await mock(page);
  await page.goto(`/dashboards/compliance?run=${SUMMARY.run_id}`);
  await page.getByTestId("run-summary-view").waitFor({ timeout: 15000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: "../manuscript/figures/shot_control_room.png", fullPage: true });
});

test("capture launch wizard", async ({ page }) => {
  await mock(page);
  await page.goto("/launch");
  await page.getByTestId("launch-wizard").waitFor({ timeout: 15000 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: "../manuscript/figures/shot_wizard.png" });
});

test("capture governance runtime", async ({ page }) => {
  await mock(page);
  await page.goto("/governance");
  await page.getByTestId("governance-panel").waitFor({ timeout: 15000 });
  await page.waitForTimeout(600);
  await page.screenshot({ path: "../manuscript/figures/shot_governance.png", fullPage: true });
});

test("capture guided home", async ({ page }) => {
  await mock(page);
  await page.goto("/home");
  await page.getByTestId("home-overview").waitFor({ timeout: 15000 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: "../manuscript/figures/shot_home.png", fullPage: true });
});
