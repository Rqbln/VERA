"use client";

import { AuthGuard } from "@/components/AuthGuard";
import { RunSummaryView } from "@/components/RunSummaryView";
import { ROUTE_ROLES } from "@/lib/auth";

export function ComplianceClient({
  defaultRunId,
  initialReq,
  initialDetails,
  e2eRole,
}: {
  defaultRunId?: string;
  initialReq?: string;
  initialDetails?: boolean;
  e2eRole?: string;
}) {
  return (
    <AuthGuard roles={ROUTE_ROLES["/dashboards/compliance"]} simulateRole={e2eRole}>
      <RunSummaryView
        lens="compliance"
        defaultRunId={defaultRunId}
        initialReq={initialReq}
        initialDetails={initialDetails}
      />
    </AuthGuard>
  );
}
