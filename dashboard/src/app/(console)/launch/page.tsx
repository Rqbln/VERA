"use client";

import { AuthGuard } from "@/components/AuthGuard";
import { LaunchWizard } from "@/components/LaunchWizard";

// Launching evaluations is a data-science action; in enterprise mode it is gated to DS roles.
// In guided mode the single persona holds these roles, so the wizard is open.
const LAUNCH_ROLES = ["data_scientist", "ml_researcher"];

export default function LaunchPage() {
  return (
    <AuthGuard roles={LAUNCH_ROLES}>
      <LaunchWizard />
    </AuthGuard>
  );
}
