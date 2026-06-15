import { ComplianceClient } from "./compliance-client";

export default function CompliancePage({
  searchParams,
}: {
  searchParams: { run?: string; e2e_role?: string };
}) {
  return (
    <ComplianceClient defaultRunId={searchParams.run} e2eRole={searchParams.e2e_role} />
  );
}
