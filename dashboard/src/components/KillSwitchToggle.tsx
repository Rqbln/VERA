"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getKillSwitch, setKillSwitch } from "@/lib/api";
import { getToken } from "@/lib/auth";

export function KillSwitchToggle() {
  const token = getToken();
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["kill-switch"],
    queryFn: () => getKillSwitch(token),
    refetchInterval: 20_000,
  });
  const engaged = data?.engaged ?? false;

  const toggle = useMutation({
    mutationFn: () =>
      setKillSwitch(token, !engaged, engaged ? "" : "engaged from dashboard"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kill-switch"] }),
  });

  return (
    <div
      data-testid="kill-switch"
      className={`flex items-center justify-between rounded border p-3 text-xs ${
        engaged ? "border-status-blocked/40 bg-status-blocked/5" : "border-default"
      }`}
    >
      <div>
        <span className="font-medium text-ink">Kill-switch</span>
        <span className="ml-2 text-ink-secondary">
          {engaged ? "engaged — new runs are blocked" : "off — evaluations can run"}
        </span>
      </div>
      <button
        type="button"
        onClick={() => toggle.mutate()}
        disabled={toggle.isPending}
        className={`rounded px-3 py-1 font-medium ${
          engaged
            ? "bg-brand text-white hover:bg-brand-deep"
            : "bg-status-blocked text-white hover:brightness-95"
        } disabled:opacity-40`}
      >
        {engaged ? "Re-enable" : "Engage"}
      </button>
    </div>
  );
}
