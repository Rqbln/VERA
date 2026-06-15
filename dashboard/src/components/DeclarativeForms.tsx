"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getForms, putForm } from "@/lib/api";
import { getToken } from "@/lib/auth";

// Field templates per declarative requirement (N03–N06).
const FORM_FIELDS: Record<string, { id: string; label: string }[]> = {
  N03: [
    { id: "gpu_hours", label: "GPU hours" },
    { id: "kwh", label: "Energy (kWh)" },
    { id: "co2eq_kg", label: "CO₂eq (kg)" },
  ],
  N04: [
    { id: "architecture", label: "Architecture" },
    { id: "params", label: "Parameters" },
    { id: "training_data", label: "Training data summary" },
  ],
  N05: [{ id: "summary", label: "Evaluation summary" }],
  N06: [
    { id: "misuse", label: "Misuse scenarios" },
    { id: "mitigations", label: "Mitigations" },
    { id: "residual_risk", label: "Residual risk" },
  ],
};

const FORM_LABELS: Record<string, string> = {
  N03: "N03 · Environmental",
  N04: "N04 · Datasheet",
  N05: "N05 · Eval summary",
  N06: "N06 · Risk summary",
};

export function DeclarativeForms({ runId }: { runId: string }) {
  const token = getToken();
  const qc = useQueryClient();
  const [active, setActive] = useState("N03");
  const { data } = useQuery({
    queryKey: ["forms", runId],
    queryFn: () => getForms(token, runId),
  });

  const [fields, setFields] = useState<Record<string, string>>({});
  const [completed, setCompleted] = useState(false);

  // Load the active form's saved values when it changes.
  useEffect(() => {
    const saved = data?.forms?.[active];
    const f: Record<string, string> = {};
    for (const def of FORM_FIELDS[active]) {
      f[def.id] = String(saved?.fields?.[def.id] ?? "");
    }
    setFields(f);
    setCompleted(Boolean(saved?.completed));
  }, [active, data]);

  const save = useMutation({
    mutationFn: () => putForm(token, runId, active, { fields, completed }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["forms", runId] }),
  });

  return (
    <div data-testid="declarative-forms" className="rounded border border-zinc-800 p-3">
      <h3 className="mb-2 text-xs font-medium text-zinc-300">Declarative forms (N03–N06)</h3>
      <div className="mb-3 flex flex-wrap gap-1">
        {Object.keys(FORM_FIELDS).map((fid) => {
          const isDone = data?.forms?.[fid]?.completed;
          return (
            <button
              key={fid}
              type="button"
              onClick={() => setActive(fid)}
              className={`rounded px-2 py-1 text-[11px] ${
                active === fid ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {FORM_LABELS[fid]}
              {isDone ? <span className="ml-1 text-emerald-500">✓</span> : null}
            </button>
          );
        })}
      </div>
      <div className="space-y-2 text-xs">
        {FORM_FIELDS[active].map((def) => (
          <label key={def.id} className="block">
            <span className="mb-1 block text-zinc-500">{def.label}</span>
            <input
              value={fields[def.id] ?? ""}
              onChange={(e) => setFields((p) => ({ ...p, [def.id]: e.target.value }))}
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-200"
            />
          </label>
        ))}
        <label className="flex items-center gap-2 text-zinc-400">
          <input type="checkbox" checked={completed} onChange={(e) => setCompleted(e.target.checked)} />
          Mark as completed
        </label>
        <button
          type="button"
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="rounded bg-zinc-100 px-3 py-1 font-medium text-zinc-900 disabled:opacity-40"
        >
          {save.isPending ? "Saving…" : "Save form"}
        </button>
        {save.isError ? (
          <p className="text-red-400">Save failed (compliance role required in enterprise mode).</p>
        ) : null}
      </div>
    </div>
  );
}
