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
        engaged ? "border-red-900/60 bg-red-950/20" : "border-zinc-800"
      }`}
    >
      <div>
        <span className="font-medium text-zinc-300">Kill-switch</span>
        <span className="ml-2 text-zinc-500">
          {engaged ? "engaged — new runs are blocked" : "off — evaluations can run"}
        </span>
      </div>
      <button
        type="button"
        onClick={() => toggle.mutate()}
        disabled={toggle.isPending}
        className={`rounded px-3 py-1 font-medium ${
          engaged
            ? "bg-emerald-600 text-white hover:bg-emerald-500"
            : "bg-red-700 text-white hover:bg-red-600"
        } disabled:opacity-40`}
      >
        {engaged ? "Re-enable" : "Engage"}
      </button>
    </div>
  );
}
