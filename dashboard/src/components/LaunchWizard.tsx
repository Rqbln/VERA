"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createRun, getConnectedModels } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { INFERENCE_REQUIREMENTS, PRINCIPLES, REQUIREMENTS } from "@/lib/requirements";
import type { RunCreateRequest } from "@/lib/types";

const SAMPLE_PRESETS = [
  { label: "Quick (8 / benchmark)", value: 8 },
  { label: "Standard (50 / benchmark)", value: 50 },
  { label: "Thorough (200 / benchmark)", value: 200 },
];

const STEPS = ["Model", "What to evaluate", "Options", "Review"];

export function LaunchWizard() {
  const token = getToken();
  const router = useRouter();

  const [step, setStep] = useState(0);
  const [modelId, setModelId] = useState<string | null>(null);
  const [mode, setMode] = useState<"recommended" | "custom">("recommended");
  const [selected, setSelected] = useState<Set<string>>(new Set(INFERENCE_REQUIREMENTS));
  const [lifecycle, setLifecycle] = useState("inference");
  const [nSamples, setNSamples] = useState(8);
  const [owner, setOwner] = useState("");
  const [intendedUse, setIntendedUse] = useState("");

  const { data: connected, isLoading: modelsLoading } = useQuery({
    queryKey: ["connected-models"],
    queryFn: () => getConnectedModels(token),
    refetchInterval: 15_000,
  });

  // Preselect the recommended model once models load.
  useEffect(() => {
    if (!modelId && connected?.models?.length) {
      const rec = connected.models.find((m) => m.recommended) || connected.models[0];
      setModelId(rec.model_id);
    }
  }, [connected, modelId]);

  const requirements = mode === "recommended" ? INFERENCE_REQUIREMENTS : Array.from(selected);

  const launch = useMutation({
    mutationFn: () => {
      const body: RunCreateRequest = {
        model_id: modelId!,
        // Always send the explicit requirement set so the dashboard triages exactly what ran;
        // the backend expands these into their catalogue benchmarks.
        complai_requirements: requirements,
        config: { n_samples_per_benchmark: nSamples, seed: 42 },
        lifecycle_stage: lifecycle,
        governance: { owner, intended_use: intendedUse || "Not specified" },
      };
      return createRun(token, body);
    },
    onSuccess: (res) => router.push(`/runs/${res.run_id}`),
  });

  function toggleReq(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const canNext =
    (step === 0 && !!modelId) ||
    (step === 1 && (mode === "recommended" || selected.size > 0)) ||
    step === 2;

  return (
    <div data-testid="launch-wizard" className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-sm font-medium text-zinc-100">Launch an evaluation</h1>
      <p className="mb-4 text-xs text-zinc-500">
        Pick a connected model and what to check. RAIP runs the benchmarks and shows a compliance
        summary — no configuration files needed.
      </p>

      <Stepper step={step} />

      <div className="mt-4 rounded border border-zinc-800 bg-zinc-950 p-4">
        {step === 0 && (
          <div data-testid="wizard-step-model">
            <h2 className="mb-2 text-xs font-medium text-zinc-300">Connected models</h2>
            {modelsLoading ? (
              <p className="text-xs text-zinc-600">Looking for models…</p>
            ) : connected?.models?.length ? (
              <ul className="space-y-1">
                {connected.models.map((m) => (
                  <li key={m.model_id}>
                    <label className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-xs hover:bg-zinc-900">
                      <input
                        type="radio"
                        name="model"
                        checked={modelId === m.model_id}
                        onChange={() => setModelId(m.model_id)}
                      />
                      <span className="font-mono text-zinc-200">{m.name}</span>
                      {m.recommended ? (
                        <span className="rounded bg-emerald-900/40 px-1.5 text-[10px] text-emerald-400">
                          recommended
                        </span>
                      ) : null}
                    </label>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="rounded border border-amber-900/40 bg-amber-950/20 p-3 text-xs text-amber-300">
                No models connected. Start one with{" "}
                <code className="font-mono text-amber-200">ollama pull llama3.1:8b-instruct-q8_0</code>
                {" "}then refresh.
              </div>
            )}
          </div>
        )}

        {step === 1 && (
          <div data-testid="wizard-step-what">
            <div className="mb-3 flex gap-2 text-xs">
              <ModeButton active={mode === "recommended"} onClick={() => setMode("recommended")}>
                Recommended set
              </ModeButton>
              <ModeButton active={mode === "custom"} onClick={() => setMode("custom")}>
                Choose requirements
              </ModeButton>
            </div>
            {mode === "recommended" ? (
              <p className="text-xs text-zinc-400">
                Evaluates the full set of inference-time requirements (
                {INFERENCE_REQUIREMENTS.length} of 12 — dataset checks R03–R05 need a training
                corpus and are skipped). Best place to start.
              </p>
            ) : (
              <div className="space-y-3">
                {PRINCIPLES.map((p) => (
                  <div key={p}>
                    <div className="mb-1 text-[11px] uppercase tracking-wide text-zinc-600">{p}</div>
                    <div className="grid grid-cols-1 gap-1 sm:grid-cols-2">
                      {REQUIREMENTS.filter((r) => r.principle === p).map((r) => (
                        <label
                          key={r.id}
                          className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-xs hover:bg-zinc-900"
                        >
                          <input
                            type="checkbox"
                            checked={selected.has(r.id)}
                            onChange={() => toggleReq(r.id)}
                          />
                          <span className="font-mono text-zinc-400">{r.id}</span>
                          <span className="text-zinc-300">{r.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {step === 2 && (
          <div data-testid="wizard-step-options" className="space-y-4 text-xs">
            <Field label="Sample size">
              <select
                value={nSamples}
                onChange={(e) => setNSamples(Number(e.target.value))}
                className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-200"
              >
                {SAMPLE_PRESETS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Lifecycle stage">
              <select
                value={lifecycle}
                onChange={(e) => setLifecycle(e.target.value)}
                className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-200"
              >
                {["inference", "data", "finetune", "production"].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Owner (optional)">
              <input
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                placeholder="team or person"
                className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-200"
              />
            </Field>
            <Field label="Intended use (optional)">
              <input
                value={intendedUse}
                onChange={(e) => setIntendedUse(e.target.value)}
                placeholder="e.g. internal customer-support assistant"
                className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-200"
              />
            </Field>
          </div>
        )}

        {step === 3 && (
          <div data-testid="wizard-step-review" className="space-y-2 text-xs">
            <Review label="Model" value={modelId || "—"} mono />
            <Review
              label="Requirements"
              value={
                mode === "recommended"
                  ? `Recommended (${INFERENCE_REQUIREMENTS.length})`
                  : requirements.join(", ") || "—"
              }
            />
            <Review label="Sample size" value={`${nSamples} / benchmark`} />
            <Review label="Lifecycle" value={lifecycle} />
            {owner ? <Review label="Owner" value={owner} /> : null}
            {intendedUse ? <Review label="Intended use" value={intendedUse} /> : null}
            {launch.isError ? (
              <p className="text-red-400">Failed to launch: {String(launch.error)}</p>
            ) : null}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <button
          type="button"
          disabled={step === 0}
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          className="rounded px-3 py-1.5 text-xs text-zinc-500 enabled:hover:text-zinc-300 disabled:opacity-30"
        >
          ← Back
        </button>
        {step < STEPS.length - 1 ? (
          <button
            type="button"
            disabled={!canNext}
            onClick={() => setStep((s) => s + 1)}
            className="rounded bg-zinc-100 px-4 py-1.5 text-xs font-medium text-zinc-900 disabled:opacity-30"
          >
            Next →
          </button>
        ) : (
          <button
            type="button"
            data-testid="wizard-launch"
            disabled={!modelId || launch.isPending}
            onClick={() => launch.mutate()}
            className="rounded bg-emerald-600 px-4 py-1.5 text-xs font-medium text-white disabled:opacity-40"
          >
            {launch.isPending ? "Launching…" : "Launch evaluation"}
          </button>
        )}
      </div>
    </div>
  );
}

function Stepper({ step }: { step: number }) {
  return (
    <ol className="flex gap-2 text-[11px]">
      {STEPS.map((label, i) => (
        <li
          key={label}
          className={`flex items-center gap-1 rounded px-2 py-1 ${
            i === step
              ? "bg-zinc-800 text-zinc-100"
              : i < step
                ? "text-emerald-500"
                : "text-zinc-600"
          }`}
        >
          <span className="font-mono">{i + 1}</span>
          {label}
        </li>
      ))}
    </ol>
  );
}

function ModeButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded px-2 py-1 ${active ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"}`}
    >
      {children}
    </button>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-zinc-500">{label}</span>
      {children}
    </label>
  );
}

function Review({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between border-b border-zinc-900 py-1">
      <span className="text-zinc-500">{label}</span>
      <span className={`text-zinc-200 ${mono ? "font-mono" : ""}`}>{value}</span>
    </div>
  );
}
