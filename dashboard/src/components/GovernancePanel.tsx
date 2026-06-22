"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, GitBranch, Scale, ShieldAlert } from "lucide-react";
import { getIncidents, getGovModes, getProxyHealth, setGovMode } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { useT } from "@/lib/i18n";
import { KpiRow } from "./KpiTiles";
import { Timeline, type Milestone } from "./Timeline";
import { KillSwitchToggle } from "./KillSwitchToggle";

const MODES = ["shadow", "advisory", "enforcement"] as const;

function modeMilestones(active: string): Milestone[] {
  const order = MODES.indexOf((active as (typeof MODES)[number]) || "shadow");
  return MODES.map((m, i) => ({
    label: m,
    state: i < order ? "done" : i === order ? "active" : "todo",
  }));
}

export function GovernancePanel() {
  const token = getToken();
  const t = useT();
  const qc = useQueryClient();

  const { data: health } = useQuery({
    queryKey: ["gov-health"],
    queryFn: () => getProxyHealth(token),
    refetchInterval: 15_000,
  });
  const { data: modes } = useQuery({
    queryKey: ["gov-modes"],
    queryFn: () => getGovModes(token),
    refetchInterval: 15_000,
  });
  const { data: incidents } = useQuery({
    queryKey: ["gov-incidents"],
    queryFn: () => getIncidents(token),
    refetchInterval: 15_000,
  });

  const changeMode = useMutation({
    mutationFn: ({ model, mode }: { model: string; mode: string }) => setGovMode(token, model, mode),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["gov-modes"] });
      qc.invalidateQueries({ queryKey: ["gov-health"] });
    },
  });

  const modelRows = Object.entries(modes?.models ?? {});
  const incidentList = incidents?.incidents ?? [];

  return (
    <div data-testid="governance-panel" className="space-y-5">
      <div>
        <h1 className="text-base font-semibold text-ink">{t("gov.title")}</h1>
        <p className="mt-1 max-w-3xl text-xs text-ink-secondary">{t("gov.subtitle")}</p>
      </div>

      <KpiRow
        kpis={[
          { label: t("gov.bus"), value: health?.bus ?? "—", icon: GitBranch },
          { label: t("gov.policy"), value: health?.opa ? "OPA" : "built-in", icon: Scale },
          { label: t("gov.mode"), value: health?.default_mode ?? "—", icon: Activity },
          {
            label: t("gov.incidents"),
            value: incidentList.length,
            icon: ShieldAlert,
            tone: incidentList.length ? "blocked" : "ok",
          },
        ]}
      />

      <div className="section">
        <div className="mb-3 text-xs font-medium text-ink-secondary">
          {t("gov.mode")}: shadow → advisory → enforcement
        </div>
        <Timeline milestones={modeMilestones(health?.default_mode ?? "shadow")} />
      </div>

      <KillSwitchToggle />

      <div className="section">
        <h2 className="mb-2 text-xs font-medium text-ink">{t("common.model")}</h2>
        {modelRows.length === 0 ? (
          <p className="text-[11px] text-ink-secondary">
            No governed models yet — traffic through the proxy registers them here.
          </p>
        ) : (
          <table className="w-full text-[13px]">
            <thead>
              <tr className="table-header">
                <th className="py-1.5 pr-2 font-medium">{t("common.model")}</th>
                <th className="py-1.5 pr-2 font-medium">{t("gov.mode")}</th>
              </tr>
            </thead>
            <tbody>
              {modelRows.map(([model, mode]) => (
                <tr key={model} className="table-row">
                  <td className="py-1.5 pr-2 font-mono text-ink">{model.replace("ollama/", "")}</td>
                  <td className="py-1.5 pr-2">
                    <select
                      value={mode}
                      onChange={(e) => changeMode.mutate({ model, mode: e.target.value })}
                      className="input max-w-[12rem]"
                    >
                      {MODES.map((m) => (
                        <option key={m} value={m}>
                          {m}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="section">
        <h2 className="mb-2 text-xs font-medium text-ink">{t("gov.incidents")}</h2>
        {incidentList.length === 0 ? (
          <p className="text-[11px] text-ink-secondary">{t("gov.no_incidents")}</p>
        ) : (
          <ul className="space-y-1 text-xs">
            {incidentList.slice(0, 20).map((i) => (
              <li key={i.event_id} className="flex items-center gap-3 border-b border-default/70 py-1">
                <span className="badge badge-blocked">{i.kind}</span>
                <span className="font-mono text-ink-secondary">{i.model.replace("ollama/", "")}</span>
                {i.trust_score != null ? (
                  <span className="text-ink-secondary">trust {(i.trust_score * 100).toFixed(0)}</span>
                ) : null}
                <span className="ml-auto text-[10px] text-ink-secondary">{i.ts.slice(0, 19).replace("T", " ")}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
