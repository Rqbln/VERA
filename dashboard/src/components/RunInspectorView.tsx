"use client";

import Link from "next/link";
import type { InspectorData } from "@/lib/types";
import { HarnessProvenanceTable } from "./HarnessProvenanceTable";

export function RunInspectorView({ data }: { data: InspectorData }) {
  return (
    <div className="text-xs">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="font-mono text-sm text-ink">Run inspector · {data.run_id}</h1>
        <Link
          href={`/dashboards/compliance?run=${data.run_id}`}
          className="text-ink-secondary hover:text-ink"
        >
          ← summary
        </Link>
      </div>

      <section className="mb-4 border border-default p-3">
        <h2 className="mb-2 text-ink-secondary">Job stages</h2>
        <ol className="space-y-1">
          {data.stages.map((s, i) => (
            <li key={`${s.name}-${i}`} className="flex gap-3 font-mono text-ink-secondary">
              <span className="text-ink-secondary">{s.ts}</span>
              <span className={s.status === "failed" ? "text-status-blocked" : "text-ink"}>
                {s.name}
              </span>
              {s.detail ? <span className="text-status-blocked/80">{s.detail}</span> : null}
            </li>
          ))}
        </ol>
      </section>

      <section className="mb-4 border border-default p-3">
        <h2 className="mb-2 text-ink-secondary">benchmark_run.yaml parse QA</h2>
        <div className={data.parse_qa.valid ? "text-status-ok" : "text-status-blocked"}>
          {data.parse_qa.valid ? "Schema valid" : "Schema invalid"}
        </div>
        {data.parse_qa.errors.map((e) => (
          <div key={e} className="text-status-blocked">
            {e}
          </div>
        ))}
        {data.parse_qa.warnings.map((w) => (
          <div key={w} className="text-status-partial">
            {w}
          </div>
        ))}
      </section>

      <section className="mb-4 border border-default p-3">
        <h2 className="mb-2 text-ink-secondary">Reproducibility signatures</h2>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 font-mono text-ink-secondary">
          <dt className="text-ink-secondary">git_sha</dt>
          <dd>{data.git_sha}</dd>
          <dt className="text-ink-secondary">catalog</dt>
          <dd>{data.catalog_version}</dd>
          <dt className="text-ink-secondary">cosign</dt>
          <dd>{data.cosign_status}</dd>
          <dt className="text-ink-secondary">signature</dt>
          <dd className="break-all">{data.signature?.digest || "—"}</dd>
          <dt className="text-ink-secondary">mlflow</dt>
          <dd>{data.mlflow_run_id || "—"}</dd>
        </dl>
      </section>

      <section className="mb-4 border border-default p-3">
        <h2 className="mb-2 text-ink-secondary">Artifacts</h2>
        <ul className="space-y-2">
          {data.artifacts.map((a) => (
            <li key={a.name} className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-ink-secondary">{a.name}</span>
              <span className="truncate text-ink-secondary">{a.key}</span>
              {a.presigned_url ? (
                <a
                  href={a.presigned_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-ink-secondary underline hover:text-ink"
                >
                  download
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      <HarnessProvenanceTable rows={data.harness_provenance} />
    </div>
  );
}
