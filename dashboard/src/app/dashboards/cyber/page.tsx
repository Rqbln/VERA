import { CyberClient } from "./cyber-client";

export default function CyberPage({
  searchParams,
}: {
  searchParams: { e2e_role?: string };
}) {
  return <CyberClient e2eRole={searchParams.e2e_role} />;
}
