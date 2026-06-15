"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { AuthGuard } from "@/components/AuthGuard";
import { DashboardShell } from "@/components/DashboardShell";
import { RunInspectorView } from "@/components/RunInspectorView";
import { getInspector } from "@/lib/api";
import { getToken, ROUTE_ROLES } from "@/lib/auth";

export default function InspectorPage() {
  const params = useParams();
  const runId = String(params.runId);
  const token = getToken();

  const { data, isLoading } = useQuery({
    queryKey: ["inspector", runId],
    queryFn: () => getInspector(token || "", runId),
    enabled: !!runId && (!!token || process.env.NEXT_PUBLIC_AUTH_DISABLED === "1"),
  });

  return (
    <AuthGuard roles={ROUTE_ROLES["/inspector"]}>
      <DashboardShell>
        {isLoading ? (
          <div className="text-xs text-zinc-600">Loading inspector…</div>
        ) : data ? (
          <RunInspectorView data={data} />
        ) : (
          <div className="text-xs text-red-400">Inspector data unavailable</div>
        )}
      </DashboardShell>
    </AuthGuard>
  );
}
