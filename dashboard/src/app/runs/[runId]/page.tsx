"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { getRoles } from "@/lib/auth";

export default function RunDeepLinkPage() {
  const params = useParams();
  const router = useRouter();
  const runId = String(params.runId);

  useEffect(() => {
    const roles = getRoles();
    if (roles.includes("data_scientist") || roles.includes("ml_researcher")) {
      router.replace(`/dashboards/ds?run=${runId}`);
    } else if (roles.includes("secops")) {
      router.replace(`/dashboards/cyber?run=${runId}`);
    } else {
      router.replace(`/dashboards/compliance?run=${runId}`);
    }
  }, [runId, router]);

  return <div className="p-4 text-xs text-ink-secondary">Redirecting…</div>;
}
