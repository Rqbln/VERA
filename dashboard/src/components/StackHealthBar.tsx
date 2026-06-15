"use client";

import { useQuery } from "@tanstack/react-query";
import { getStackHealth } from "@/lib/api";

const LABELS: Record<string, string> = {
  redis: "Redis",
  minio: "MinIO",
  mlflow: "MLflow",
  ollama: "Ollama/LiteLLM",
};

export function StackHealthBar() {
  const { data } = useQuery({
    queryKey: ["stack-health"],
    queryFn: getStackHealth,
    refetchInterval: 30_000,
  });

  return (
    <div className="flex flex-wrap gap-3 border-b border-zinc-800 bg-zinc-950 px-4 py-1.5 text-xs text-zinc-400">
      <span className="font-medium text-zinc-500">Stack</span>
      {data
        ? Object.entries(data.checks).map(([key, check]) => (
        <span key={key} className="inline-flex items-center gap-1">
          <span
            className={`h-1.5 w-1.5 rounded-full ${check.ok ? "bg-emerald-600" : "bg-amber-500"}`}
          />
          {LABELS[key] || key}
          {!check.ok && check.error ? (
            <span className="text-amber-600/90">({String(check.error).slice(0, 40)})</span>
          ) : null}
        </span>
      ))
        : (
          <span className="text-zinc-600">checking…</span>
        )}
    </div>
  );
}
