"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listRuns, getRunSummary } from "@/lib/api";
import { getToken, isGuided } from "@/lib/auth";
import { RunSelector } from "./RunSelector";
import { LifecycleRail } from "./LifecycleRail";
import { CoverageBar } from "./CoverageBar";
import { ComplaiTriageTable } from "./ComplaiTriageTable";
import { NonMeasurableStrip } from "./NonMeasurableStrip";
import { HarnessProvenanceTable } from "./HarnessProvenanceTable";
import { RunHero } from "./RunHero";
import { TrendCurve } from "./TrendCurve";
import { HitlReviewPanel } from "./HitlReviewPanel";
import { DeclarativeForms } from "./DeclarativeForms";
import { downloadAuditPdf } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { useEffect, useState } from "react";

interface Props {
  lens: "compliance" | "cyber" | "ds";
  defaultRunId?: string;
  /** Deep link: open this requirement's drawer on arrival (?req=R02). */
  initialReq?: string;
  /** Deep link: start with the run-details panel (harness log) expanded (?details=1). */
  initialDetails?: boolean;
}

export function RunSummaryView({ lens, defaultRunId, initialReq, initialDetails }: Props) {
  const token = getToken();
  const t = useT();
  const [lifecycleFilter, setLifecycleFilter] = useState("");
  const [stageRail, setStageRail] = useState("inference");
  const [runId, setRunId] = useState<string | null>(defaultRunId || null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showDetails, setShowDetails] = useState(Boolean(initialDetails));
  const [trendReq, setTrendReq] = useState("R02");
  const [pdfError, setPdfError] = useState<string | null>(null);

  const { data: runList } = useQuery({
    queryKey: ["runs", lifecycleFilter],
    queryFn: () => listRuns(token || "", { lifecycle: lifecycleFilter || undefined }),
    enabled: !!token || isGuided(),
    refetchInterval: 10_000,
  });

  useEffect(() => {
    if (!runId && runList?.runs?.[0]) {
      setRunId(runList.runs[0].run_id);
    }
  }, [runList, runId]);

  const { data: summary, isLoading } = useQuery({
    queryKey: ["summary", runId, lens],
    queryFn: () => getRunSummary(token || "", runId!, lens === "compliance" ? undefined : lens),
    enabled: !!runId && (!!token || isGuided()),
    refetchInterval: (q) =>
      q.state.data?.status === "running" || q.state.data?.status === "queued" ? 3000 : false,
  });

  return (
    <div data-testid="run-summary-view">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-base font-semibold capitalize text-ink">
          {lens} · {t("summary.header")}
        </h1>
        {runId ? (
          <Link
            href={`/runs/${runId}/inspector`}
            className="text-xs text-ink-secondary hover:text-ink"
          >
            {t("summary.inspector")}
          </Link>
        ) : null}
      </div>

      <RunSelector
        runs={runList?.runs || []}
        selectedId={runId}
        onSelect={setRunId}
        lifecycle={lifecycleFilter}
        onLifecycleChange={(v) => {
          setLifecycleFilter(v);
          if (v) setStageRail(v);
        }}
      />

      {isLoading ? (
        <div className="text-xs text-ink-secondary">Loading run summary…</div>
      ) : summary ? (
        <>
          <RunHero summary={summary} />

          <CoverageBar requirements={summary.requirements} />
          <ComplaiTriageTable
            requirements={summary.requirements}
            runId={summary.run_id}
            token={token}
            artifactLinks={summary.artifacts}
            initialReq={initialReq}
          />
          <NonMeasurableStrip slots={summary.non_measurable} runId={summary.run_id} />

          <div className="mt-6 border-t border-default pt-3">
            <button
              type="button"
              data-testid="run-details-toggle"
              aria-expanded={showDetails}
              aria-controls="run-details-panel"
              onClick={() => setShowDetails((s) => !s)}
              className="text-xs text-ink-secondary hover:text-ink"
            >
              {showDetails ? "▾" : "▸"} {t("summary.run_details")}
            </button>
            {showDetails ? (
              <div id="run-details-panel" className="mt-3 space-y-4">
                <LifecycleRail active={stageRail} onSelect={setStageRail} />
                <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
                  <Meta label={t("common.status")} value={summary.status} />
                  <Meta label={t("common.model")} value={summary.model_id} mono />
                  <Meta label={t("summary.lifecycle")} value={summary.lifecycle_stage} />
                  <Meta label={t("summary.catalog")} value={summary.catalog_version || "—"} mono />
                </div>
                <HarnessProvenanceTable rows={summary.harness_provenance} />
              </div>
            ) : null}
          </div>

          <div className="mt-3 border-t border-default pt-3">
            <button
              type="button"
              aria-expanded={showAdvanced}
              aria-controls="gov-trends-panel"
              onClick={() => setShowAdvanced((s) => !s)}
              className="text-xs text-ink-secondary hover:text-ink"
            >
              {showAdvanced ? "▾" : "▸"} {t("summary.gov_trends")}
            </button>
            {showAdvanced ? (
              <div id="gov-trends-panel" className="mt-3 space-y-4">
                <div className="rounded border border-default p-3">
                  <div className="mb-2 flex items-center gap-2 text-xs text-ink-secondary">
                    Trend for
                    <select
                      value={trendReq}
                      onChange={(e) => setTrendReq(e.target.value)}
                      className="rounded border border-default bg-surface-2 px-1.5 py-0.5 text-ink"
                    >
                      {summary.requirements.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.id} — {r.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <TrendCurve requirement={trendReq} modelId={summary.model_id} />
                </div>
                <HitlReviewPanel runId={summary.run_id} />
                <DeclarativeForms runId={summary.run_id} />
                <div>
                  <button
                    type="button"
                    onClick={() =>
                      downloadAuditPdf(token, summary.run_id).catch((e) => setPdfError(String(e)))
                    }
                    className="rounded border border-default px-3 py-1 text-xs text-ink hover:bg-hover"
                  >
                    ⬇ Download signed audit PDF
                  </button>
                  {pdfError ? (
                    <p className="mt-1 text-[11px] text-status-partial">
                      PDF export needs the optional &lsquo;pdf&rsquo; extra (WeasyPrint). {pdfError.slice(0, 80)}
                    </p>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        </>
      ) : (
        <div className="text-xs text-ink-secondary">{t("summary.select_run")}</div>
      )}
    </div>
  );
}

function Meta({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-lg border border-default p-2">
      <div className="text-ink-secondary">{label}</div>
      <div className={`truncate text-ink ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  );
}
