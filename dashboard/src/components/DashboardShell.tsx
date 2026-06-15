"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { StackHealthBar } from "./StackHealthBar";
import { getRoles, hasAnyRole, logout } from "@/lib/auth";
import clsx from "clsx";

const NAV = [
  { href: "/dashboards/compliance", label: "Compliance", roles: ["legal_compliance", "risk_manager", "domain_expert", "external_auditor", "executive", "secops"] },
  { href: "/dashboards/cyber", label: "Cyber", roles: ["secops", "legal_compliance", "risk_manager", "external_auditor"] },
  { href: "/dashboards/ds", label: "Data Science", roles: ["data_scientist", "ml_researcher"] },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const roles = getRoles();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200">
      <StackHealthBar />
      <header className="flex items-center justify-between border-b border-zinc-800 px-4 py-2">
        <div className="flex items-center gap-6">
          <span className="text-sm font-semibold tracking-tight text-zinc-100">
            RAIP Control Room
          </span>
          <nav className="flex gap-1">
            {NAV.filter((n) => hasAnyRole(n.roles)).map((n) => (
              <Link
                key={n.href}
                href={n.href}
                className={clsx(
                  "rounded px-2 py-1 text-xs",
                  pathname.startsWith(n.href)
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-300",
                )}
              >
                {n.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-xs text-zinc-500">
          <span>{roles.slice(0, 2).join(", ")}</span>
          <button
            type="button"
            onClick={() => logout()}
            className="text-zinc-500 hover:text-zinc-300"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="p-4">{children}</main>
    </div>
  );
}
