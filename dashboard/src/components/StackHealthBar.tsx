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
    <div className="flex flex-wrap items-center gap-3 border-b border-zinc-800 bg-zinc-950 px-4 py-1.5 text-xs text-zinc-400">
      <span className="font-medium text-zinc-500">Stack</span>
      {data
        ? Object.entries(data.checks).map(([key, check]) => {
            // Required services that are down are red; optional services degrade to amber.
            const dot = check.ok
              ? "bg-emerald-600"
              : check.required
                ? "bg-red-600"
                : "bg-amber-500";
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
                {note ? <span className="text-zinc-600">({note})</span> : null}
              </span>
            );
          })
        : (
          <span className="text-zinc-600">checking…</span>
        )}
      {data?.degraded ? (
        <span className="text-amber-600/90">lite mode — optional services off</span>
      ) : null}
    </div>
  );
}
