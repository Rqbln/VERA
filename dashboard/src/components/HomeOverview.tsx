"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getConnectedModels, listRuns } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { KillSwitchToggle } from "./KillSwitchToggle";

const ACTIONS = [
  {
    href: "/launch",
    title: "Launch an evaluation",
    body: "Pick a connected model and check it against EU AI Act requirements. Guided, no setup.",
    cta: "Start →",
  },
  {
    href: "/runs-overview",
    title: "View runs & scores",
    body: "A summary table of every evaluation: status, model, and the R01–R12 compliance picture.",
    cta: "Open →",
  },
  {
    href: "/dashboards/compliance",
    title: "Compliance control room",
    body: "The full triage view: failed/fallback/uncovered requirements first, with rationale and CIs.",
    cta: "Inspect →",
  },
];

export function HomeOverview() {
  const token = getToken();
  const { data: models } = useQuery({
    queryKey: ["connected-models"],
    queryFn: () => getConnectedModels(token),
    refetchInterval: 30_000,
  });
  const { data: runs } = useQuery({
    queryKey: ["runs", ""],
    queryFn: () => listRuns(token || "", {}),
    refetchInterval: 15_000,
  });

  const completed = runs?.runs.filter((r) => r.status === "completed").length ?? 0;
  const running = runs?.runs.filter((r) => r.status === "running" || r.status === "queued").length ?? 0;

  return (
    <div data-testid="home-overview" className="mx-auto max-w-4xl">
      <h1 className="text-base font-semibold text-zinc-100">Welcome to RAIP</h1>
      <p className="mt-1 max-w-2xl text-xs text-zinc-400">
        RAIP checks whether an AI model meets the European AI Act (EU AI Act) requirements. You launch
        an evaluation on a connected model and read a clear summary of results — no code, no login.
      </p>

      <div className="mt-4 flex gap-4 text-xs text-zinc-400">
        <Stat label="Connected models" value={models?.models.length ?? 0} />
        <Stat label="Completed runs" value={completed} />
        <Stat label="In progress" value={running} />
      </div>

      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {ACTIONS.map((a) => (
          <Link
            key={a.href}
            href={a.href}
            className="flex flex-col justify-between rounded border border-zinc-800 bg-zinc-950 p-3 transition hover:border-zinc-700"
          >
            <div>
              <div className="text-xs font-medium text-zinc-100">{a.title}</div>
              <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">{a.body}</p>
            </div>
            <span className="mt-3 text-[11px] text-emerald-500">{a.cta}</span>
          </Link>
        ))}
      </div>

      <div className="mt-5 rounded border border-zinc-800 p-3 text-[11px] text-zinc-500">
        <span className="font-medium text-zinc-400">How to read scores: </span>
        each requirement gets a band — <span className="text-emerald-500">green</span> (compliant),{" "}
        <span className="text-amber-500">orange</span> (watch), <span className="text-red-500">red</span>{" "}
        (action needed). There are no hard pass/fail cut-offs: a human reviews the trade-offs.
      </div>

      <div className="mt-3">
        <KillSwitchToggle />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded border border-zinc-800 px-3 py-1.5">
      <div className="text-sm font-semibold text-zinc-200">{value}</div>
      <div className="text-zinc-600">{label}</div>
    </div>
  );
}
