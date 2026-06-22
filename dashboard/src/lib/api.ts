import type {
  BenchmarkEntry,
  ConnectedModelsResponse,
  InspectorData,
  RunCreateRequest,
  RunCreateResponse,
  RunListItem,
  RunSummary,
  StackHealth,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function apiBase(): string {
  return API_BASE.replace(/\/$/, "");
}

async function fetchApi<T>(
  path: string,
  token: string | undefined,
  init?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${apiBase()}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function getStackHealth(): Promise<StackHealth> {
  return fetchApi<StackHealth>("/api/v1/health/stack", undefined);
}

export async function listRuns(
  token: string,
  params?: { lifecycle?: string; status?: string; includeTriage?: boolean },
): Promise<{ runs: RunListItem[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.lifecycle) q.set("lifecycle", params.lifecycle);
  if (params?.status) q.set("status", params.status);
  if (params?.includeTriage) q.set("include_triage", "true");
  const qs = q.toString();
  return fetchApi(`/api/v1/runs${qs ? `?${qs}` : ""}`, token);
}

export async function getRunSummary(
  token: string,
  runId: string,
  lens?: string,
): Promise<RunSummary> {
  const q = lens ? `?lens=${lens}` : "";
  return fetchApi(`/api/v1/runs/${runId}/summary${q}`, token);
}

export async function getInspector(token: string, runId: string): Promise<InspectorData> {
  return fetchApi(`/api/v1/runs/${runId}/inspector`, token);
}

export async function getRawOutputs(
  token: string,
  runId: string,
  benchmark: string,
  page = 1,
): Promise<{ rows: Record<string, unknown>[]; total: number }> {
  return fetchApi(
    `/api/v1/runs/${runId}/raw-outputs?benchmark=${encodeURIComponent(benchmark)}&page=${page}&limit=20`,
    token,
  );
}

export async function presignArtifact(
  token: string,
  runId: string,
  artifact: string,
): Promise<{ url: string }> {
  return fetchApi(
    `/api/v1/artifacts/${runId}/presign?artifact=${artifact}`,
    token,
  );
}

export async function getConnectedModels(
  token: string | undefined,
): Promise<ConnectedModelsResponse> {
  return fetchApi("/api/v1/models/connected", token);
}

export async function listBenchmarks(
  token: string | undefined,
): Promise<{ benchmarks: BenchmarkEntry[] }> {
  return fetchApi("/api/v1/benchmarks", token);
}

export async function createRun(
  token: string | undefined,
  body: RunCreateRequest,
): Promise<RunCreateResponse> {
  return fetchApi("/api/v1/runs", token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getRun(
  token: string | undefined,
  runId: string,
): Promise<{ run_id: string; status: string; aggregate_scores?: Record<string, number> }> {
  return fetchApi(`/api/v1/runs/${runId}`, token);
}

export async function getDrift(
  token: string | undefined,
  modelId: string,
): Promise<{
  available: boolean;
  drift?: boolean;
  delta?: number;
  latest?: number;
  baseline?: number;
  direction?: string;
  reason?: string;
}> {
  return fetchApi(`/api/v1/monitor/drift?model_id=${encodeURIComponent(modelId)}`, token);
}

export async function getKillSwitch(
  token: string | undefined,
): Promise<{ engaged: boolean; reason: string }> {
  return fetchApi("/api/v1/governance/kill-switch", token);
}

export async function setKillSwitch(
  token: string | undefined,
  engaged: boolean,
  reason = "",
): Promise<{ engaged: boolean; reason: string }> {
  return fetchApi("/api/v1/governance/kill-switch", token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ engaged, reason }),
  });
}

export interface SeriesPoint {
  ts: string;
  value: number;
  run_id: string;
  model_id: string;
}

export async function getSeries(
  token: string | undefined,
  requirement: string,
  modelId?: string,
): Promise<{ available: boolean; requirement: string; series: SeriesPoint[] }> {
  const q = new URLSearchParams({ requirement });
  if (modelId) q.set("model_id", modelId);
  return fetchApi(`/api/v1/series?${q.toString()}`, token);
}

export interface HitlTask {
  task_id: string;
  run_id: string;
  requirement: string;
  prompt: string;
  status: string;
  reviewer: string;
  likert_score: number | null;
  comment: string;
}

export async function listHitlTasks(
  token: string | undefined,
  runId?: string,
): Promise<{ tasks: HitlTask[] }> {
  const q = runId ? `?run_id=${encodeURIComponent(runId)}` : "";
  return fetchApi(`/api/v1/hitl/tasks${q}`, token);
}

export async function createHitlTask(
  token: string | undefined,
  body: { run_id: string; requirement: string; prompt?: string },
): Promise<{ task: HitlTask }> {
  return fetchApi("/api/v1/hitl/tasks", token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function submitHitlReview(
  token: string | undefined,
  taskId: string,
  body: { likert_score: number; comment?: string },
): Promise<{ task: HitlTask }> {
  return fetchApi(`/api/v1/hitl/tasks/${taskId}/review`, token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getForms(
  token: string | undefined,
  runId: string,
): Promise<{ meta: Record<string, { name: string; principle: string }>; forms: Record<string, { fields: Record<string, unknown>; completed: boolean }> }> {
  return fetchApi(`/api/v1/runs/${runId}/forms`, token);
}

export async function putForm(
  token: string | undefined,
  runId: string,
  formId: string,
  body: { fields: Record<string, unknown>; completed: boolean },
): Promise<unknown> {
  return fetchApi(`/api/v1/runs/${runId}/forms/${formId}`, token, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// ── Governance runtime (MVP4 gaas) admin API ────────────────────────────────────────
export interface ProxyHealth {
  gaas_enabled: boolean;
  bus: string;
  opa: boolean;
  opensearch: boolean;
  proxy_target: string;
  default_mode: string;
  kill_switch: { engaged: boolean; reason: string };
  modes: Record<string, string>;
}

export interface GovTrust {
  model: string;
  current: { score: number; band: string; components: Record<string, number> } | null;
  signals: Record<string, number>;
  series: { ts: string; score: number; band: string }[];
}

export interface Incident {
  event_id: string;
  ts: string;
  kind: string;
  model: string;
  decision: string | null;
  trust_score: number | null;
}

export async function getProxyHealth(token: string | undefined): Promise<ProxyHealth> {
  return fetchApi("/admin/v1/proxy/health", token);
}

export async function getGovModes(
  token: string | undefined,
): Promise<{ default: string; models: Record<string, string> }> {
  return fetchApi("/admin/v1/mode", token);
}

export async function setGovMode(
  token: string | undefined,
  model: string,
  mode: string,
): Promise<{ model: string; mode: string }> {
  return fetchApi(`/admin/v1/mode/${model}`, token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
}

export async function getGovTrust(token: string | undefined, model: string): Promise<GovTrust> {
  return fetchApi(`/admin/v1/trust/${model}`, token);
}

export async function getIncidents(
  token: string | undefined,
): Promise<{ incidents: Incident[] }> {
  return fetchApi("/admin/v1/incidents", token);
}

export async function downloadAuditPdf(token: string | undefined, runId: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${apiBase()}/api/v1/runs/${runId}/audit-pdf`, { headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `raip_audit_${runId.slice(0, 8)}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}
