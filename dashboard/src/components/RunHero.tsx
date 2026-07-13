"use client";

import type { RunSummary } from "@/lib/types";
import { useT } from "@/lib/i18n";
import { BAND_SEGMENTS, TrustFactorGauge, segmentsFromThresholds } from "./TrustFactorGauge";
import { BAND_COLOR } from "./CoverageBar";

const STATUS_BADGE: Record<string, string> = {
  completed: "badge badge-ok",
  running: "badge badge-partial",
  queued: "badge badge-partial",
  failed: "badge badge-blocked",
};

interface Props {
  summary: RunSummary;
}

export function RunHero({ summary }: Props) {
  const t = useT();
  const counts = summary.triage_counts ?? {};
  const segments = summary.band_thresholds
    ? segmentsFromThresholds(summary.band_thresholds.green_min, summary.band_thresholds.orange_min)
    : BAND_SEGMENTS;
  const weakest = [...(summary.requirements ?? [])]
    .filter((r) => r.score != null && r.triage !== "na")
    .sort((a, b) => (a.score ?? 0) - (b.score ?? 0))
    .slice(0, 3);

  const verdicts: { key: string; count: number; dot: string }[] = [
    { key: "failed", count: counts.failed ?? 0, dot: "bg-status-blocked" },
    { key: "fallback", count: counts.fallback ?? 0, dot: "bg-status-partial" },
    { key: "ok", count: counts.ok ?? 0, dot: "bg-status-ok" },
  ];
  if ((counts.uncovered ?? 0) > 0) {
    verdicts.push({ key: "uncovered", count: counts.uncovered, dot: "bg-status-neutral" });
  }

  return (
    <section data-testid="run-hero" className="card mb-6 p-6 shadow-sm">
      <div className="grid items-center gap-8 lg:grid-cols-[340px_1fr]">
        <div className="flex justify-center">
          <TrustFactorGauge tf={summary.trust_factor} segments={segments} />
        </div>
        <div className="space-y-5">
          <div className="flex flex-wrap items-start gap-x-10 gap-y-4">
            <div>
              <div className="kpi-label mb-1">{t("common.status")}</div>
              <span className={STATUS_BADGE[summary.status] ?? "badge badge-neutral"}>
                {summary.status}
              </span>
            </div>
            <div className="min-w-0">
              <div className="kpi-label mb-1">{t("common.model")}</div>
              <div
                className="max-w-[320px] truncate font-mono text-sm text-ink"
                title={summary.model_id}
              >
                {summary.model_id}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-x-10 gap-y-3">
            {verdicts.map((v) => (
              <div key={v.key} className="flex items-center gap-2.5">
                <span className={`h-2 w-2 rounded-full ${v.dot}`} />
                <span className="text-2xl font-semibold text-ink">{v.count}</span>
                <span className="text-xs text-ink-secondary">
                  {t(`summary.count.${v.key}`)}
                </span>
              </div>
            ))}
          </div>

          {weakest.length > 0 ? (
            <div>
              <div className="kpi-label mb-1.5">{t("summary.weakest")}</div>
              <div className="flex flex-wrap gap-2">
                {weakest.map((r) => (
                  <span
                    key={r.id}
                    className="flex items-center gap-1.5 rounded-full border border-default bg-surface-2 px-3 py-1 text-xs text-ink"
                  >
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: BAND_COLOR[r.band] || BAND_COLOR.unknown }}
                    />
                    {r.id} · {r.name}
                    <span className="font-mono text-ink-secondary">
                      {r.score?.toFixed(2)}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
