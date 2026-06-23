"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Boxes, CheckCircle2, Loader2, Rocket, Scale, ShieldCheck, Table2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { getConnectedModels, listRuns } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { useT } from "@/lib/i18n";
import { KpiRow } from "./KpiTiles";

type ActionKey =
  | "home.action.launch"
  | "home.action.runs"
  | "home.action.compliance"
  | "home.action.governance";

const ACTIONS: { href: string; key: ActionKey; icon: LucideIcon }[] = [
  { href: "/launch", key: "home.action.launch", icon: Rocket },
  { href: "/runs-overview", key: "home.action.runs", icon: Table2 },
  { href: "/governance", key: "home.action.governance", icon: ShieldCheck },
  { href: "/dashboards/compliance", key: "home.action.compliance", icon: Scale },
];

export function HomeOverview() {
  const token = getToken();
  const t = useT();
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
  const modelCount = models?.models.length ?? 0;

  return (
    <div data-testid="home-overview" className="space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-ink">{t("home.welcome")}</h1>
        <p className="mt-1 max-w-3xl text-xs leading-relaxed text-ink-secondary">{t("home.intro")}</p>
      </div>

      <KpiRow
        kpis={[
          { label: t("home.kpi.models"), value: modelCount, icon: Boxes, accent: modelCount ? t("home.kpi.connected") : undefined },
          { label: t("home.kpi.completed"), value: completed, icon: CheckCircle2, tone: "ok" },
          { label: t("home.kpi.running"), value: running, icon: Loader2, tone: running ? "partial" : "neutral" },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {ACTIONS.map((a) => {
          const Icon = a.icon;
          return (
            <Link
              key={a.href}
              href={a.href}
              className="card group flex flex-col justify-between p-4 transition hover:border-brand hover:shadow-sm"
            >
              <div>
                <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand/10 text-brand">
                  <Icon size={18} strokeWidth={1.75} />
                </span>
                <div className="mt-3 text-sm font-medium text-ink">{t(`${a.key}.title`)}</div>
                <p className="mt-1 text-[11px] leading-relaxed text-ink-secondary">
                  {t(`${a.key}.body`)}
                </p>
              </div>
              <span className="mt-3 inline-flex items-center gap-1 text-[11px] font-medium text-brand-accent">
                {t("home.action.cta")} <ArrowRight size={12} className="transition group-hover:translate-x-0.5" />
              </span>
            </Link>
          );
        })}
      </div>

      <div className="section text-[11px] leading-relaxed text-ink-secondary">{t("home.bands")}</div>
    </div>
  );
}
