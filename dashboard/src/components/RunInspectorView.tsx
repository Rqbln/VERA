"use client";

import Link from "next/link";
import type { InspectorData } from "@/lib/types";
import { HarnessProvenanceTable } from "./HarnessProvenanceTable";

export function RunInspectorView({ data }: { data: InspectorData }) {
  return (
    <div className="text-xs">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="font-mono text-sm text-zinc-100">Run inspector · {data.run_id}</h1>
        <Link
          href={`/dashboards/compliance?run=${data.run_id}`}
          className="text-zinc-500 hover:text-zinc-300"
        >
          ← summary
        </Link>
      </div>

      <section className="mb-4 border border-zinc-800 p-3">
        <h2 className="mb-2 text-zinc-500">Job stages</h2>
        <ol className="space-y-1">
          {data.stages.map((s, i) => (
            <li key={`${s.name}-${i}`} className="flex gap-3 font-mono text-zinc-400">
              <span className="text-zinc-600">{s.ts}</span>
              <span className={s.status === "failed" ? "text-red-400" : "text-zinc-300"}>
                {s.name}
              </span>
              {s.detail ? <span className="text-red-400/80">{s.detail}</span> : null}
            </li>
          ))}
        </ol>
      </section>

      <section className="mb-4 border border-zinc-800 p-3">
        <h2 className="mb-2 text-zinc-500">benchmark_run.yaml parse QA</h2>
        <div className={data.parse_qa.valid ? "text-emerald-600" : "text-red-400"}>
          {data.parse_qa.valid ? "Schema valid" : "Schema invalid"}
        </div>
        {data.parse_qa.errors.map((e) => (
          <div key={e} className="text-red-400">
            {e}
          </div>
        ))}
        {data.parse_qa.warnings.map((w) => (
          <div key={w} className="text-amber-500">
            {w}
          </div>
        ))}
      </section>

      <section className="mb-4 border border-zinc-800 p-3">
        <h2 className="mb-2 text-zinc-500">Reproducibility signatures</h2>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 font-mono text-zinc-400">
          <dt className="text-zinc-600">git_sha</dt>
          <dd>{data.git_sha}</dd>
          <dt className="text-zinc-600">catalog</dt>
          <dd>{data.catalog_version}</dd>
          <dt className="text-zinc-600">cosign</dt>
          <dd>{data.cosign_status}</dd>
          <dt className="text-zinc-600">signature</dt>
          <dd className="break-all">{data.signature?.digest || "—"}</dd>
          <dt className="text-zinc-600">mlflow</dt>
          <dd>{data.mlflow_run_id || "—"}</dd>
        </dl>
      </section>

      <section className="mb-4 border border-zinc-800 p-3">
        <h2 className="mb-2 text-zinc-500">Artifacts</h2>
        <ul className="space-y-2">
          {data.artifacts.map((a) => (
            <li key={a.name} className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-zinc-400">{a.name}</span>
              <span className="truncate text-zinc-600">{a.key}</span>
              {a.presigned_url ? (
                <a
                  href={a.presigned_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-zinc-500 underline hover:text-zinc-300"
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
