import { ComplianceClient } from "./compliance-client";

export default function CompliancePage({
  searchParams,
}: {
  searchParams: { run?: string; req?: string; details?: string; e2e_role?: string };
}) {
  return (
    <ComplianceClient
      defaultRunId={searchParams.run}
      initialReq={searchParams.req}
      initialDetails={searchParams.details === "1"}
      e2eRole={searchParams.e2e_role}
    />
  );
}
