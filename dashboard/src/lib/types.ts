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
  trust_factor?: TrustFactor | null;
}

export interface HarnessRow {
  benchmark_id: string;
  harness: string;
  agent: string;
  fallback: string | boolean;
}

export interface NonMeasurableSlot {
  status: string;
  queue_count?: number;
  reviewed?: number;
  avg_likert?: number | null;
  kwh?: number | null;
  co2eq_kg?: number | null;
  source?: string;
  fields?: Record<string, unknown>;
  model_card_uri?: string;
  [key: string]: unknown;
}

export interface NonMeasurableSlots {
  n01: NonMeasurableSlot;
  n02: NonMeasurableSlot;
  n03: NonMeasurableSlot;
  n04: NonMeasurableSlot;
  n05: NonMeasurableSlot;
  n06: NonMeasurableSlot;
}

export interface TrustFactor {
  score: number;
  band: string;
  components: Record<string, number>;
}

export interface RunListItem {
  run_id: string;
  status: string;
  model_id: string;
  lifecycle_stage: string;
  catalog_version: string;
  created_at: string;
  updated_at: string;
  triage_counts?: Record<TriageStatus, number> | null;
  headline_score?: number | null;
  trust_factor?: TrustFactor | null;
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

export interface ConnectedModel {
  model_id: string;
  name: string;
  provider: string;
  size?: number;
  modified_at?: string;
  connected: boolean;
  recommended: boolean;
}

export interface ConnectedModelsResponse {
  models: ConnectedModel[];
  ollama_base: string;
  recommended_model: string;
  error?: string;
}

export interface BenchmarkEntry {
  id: string;
  complai?: string[];
  implementation?: string;
  [key: string]: unknown;
}

export interface RunCreateRequest {
  model_id: string;
  benchmarks?: string[];
  complai_requirements?: string[];
  config?: {
    temperature?: number;
    max_tokens?: number;
    n_samples_per_benchmark?: number;
    seed?: number;
    bootstrap_n?: number;
  };
  governance?: Record<string, unknown>;
  lifecycle_stage?: string;
}

export interface RunCreateResponse {
  run_id: string;
  status: string;
}

export interface StackHealthCheck {
  ok: boolean;
  required?: boolean;
  error?: string;
  status?: string;
  backend?: string;
  [key: string]: unknown;
}

export interface StackHealth {
  ok: boolean;
  degraded?: boolean;
  checks: Record<string, StackHealthCheck>;
}
