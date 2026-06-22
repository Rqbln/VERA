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
    <div className="flex flex-wrap items-center gap-3 border-b border-default bg-white px-4 py-1.5 text-xs text-ink-secondary">
      <span className="font-medium text-ink-secondary">Stack</span>
      {data
        ? Object.entries(data.checks).map(([key, check]) => {
            // Required services that are down are red; optional services degrade to amber.
            const dot = check.ok
              ? "bg-brand"
              : check.required
                ? "bg-status-blocked"
                : "bg-status-partial";
            const note =
              check.status === "disabled"
                ? "disabled"
                : check.backend === "local"
                  ? "local"
                  : !check.ok && check.error
                    ? String(check.error).slice(0, 40)
                    : "";
            return (
              <span key={key} className="inline-flex items-center gap-1" title={note}>
                <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
                {LABELS[key] || key}
                {note ? <span className="text-ink-secondary">({note})</span> : null}
              </span>
            );
          })
        : (
          <span className="text-ink-secondary">checking…</span>
        )}
      {data?.degraded ? (
        <span className="text-status-partial/90">lite mode — optional services off</span>
      ) : null}
    </div>
  );
}
