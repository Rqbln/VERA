import type { InspectorData, RunListItem, RunSummary, StackHealth } from "./types";

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
  params?: { lifecycle?: string; status?: string },
): Promise<{ runs: RunListItem[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.lifecycle) q.set("lifecycle", params.lifecycle);
  if (params?.status) q.set("status", params.status);
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
