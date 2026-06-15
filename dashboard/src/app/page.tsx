"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isGuided } from "@/lib/auth";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    // Guided users land on the friendly home; enterprise users go straight to the RBAC view.
    router.replace(isGuided() ? "/home" : "/dashboards/compliance");
  }, [router]);
  return <div className="p-4 text-xs text-zinc-600">Loading…</div>;
}
