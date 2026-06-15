export type TriageStatus = "failed" | "fallback" | "uncovered" | "ok" | "na";
export type ScoreBand = "green" | "orange" | "red" | "unknown";

export interface RequirementRow {
  id: string;
  name: string;
  rationale: string;
  principle: string;
  aiact: string;
  triage: TriageStatus;
  score: number | null;
  score_ci_lower: number | null;
  score_ci_upper: number | null;
  bootstrap_n?: number;
  contributing_benchmarks: string[];
  fallback_benchmarks: string[];
  band: ScoreBand;
}

export interface RunSummary {
  run_id: string;
  status: string;
  model_id: string;
  lifecycle_stage: string;
  catalog_version: string;
  created_at: string;
  updated_at: string;
  error: string | null;
  mlflow_run_id: string | null;
  git_sha: string;
  signature: Record<string, string> | null;
  requirements: RequirementRow[];
  triage_counts: Record<TriageStatus, number>;
  harness_provenance: HarnessRow[];
  artifacts: Record<string, string>;
  non_measurable: NonMeasurableSlots;
  requested_requirements: string[];
}

export interface HarnessRow {
  benchmark_id: string;
  harness: string;
  agent: string;
  fallback: string | boolean;
}

export interface NonMeasurableSlots {
  n01: { status: string; queue_count: number; tasks: unknown[] };
  n02: { status: string; queue_count: number; tasks: unknown[] };
  n03: { status: string; ref?: string };
  n04: { status: string; model_card_uri?: string; datasheet_uri?: string };
  n05: { status: string };
  n06: { status: string };
}

export interface RunListItem {
  run_id: string;
  status: string;
  model_id: string;
  lifecycle_stage: string;
  catalog_version: string;
  created_at: string;
  updated_at: string;
}

export interface InspectorData {
  run_id: string;
  status: string;
  stages: { name: string; status: string; ts: string; detail?: string }[];
  parse_qa: { valid: boolean; errors: string[]; warnings: string[] };
  git_sha: string;
  catalog_version: string;
  signature: Record<string, string> | null;
  cosign_status: string;
  harness_provenance: HarnessRow[];
  artifacts: {
    name: string;
    key: string;
    uri: string;
    presigned_url: string | null;
  }[];
  mlflow_run_id: string | null;
}

export interface StackHealth {
  ok: boolean;
  checks: Record<string, { ok: boolean; error?: string; [key: string]: unknown }>;
}
