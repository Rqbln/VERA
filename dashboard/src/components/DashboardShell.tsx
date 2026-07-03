"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  Home,
  Rocket,
  Table2,
  ShieldCheck,
  Scale,
  ShieldAlert,
  FlaskConical,
  Languages,
  LogOut,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { StackHealthBar } from "./StackHealthBar";
import { getRoles, hasAnyRole, isGuided, logout } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";

const GUIDED_NAV: { href: string; key: "nav.home" | "nav.launch" | "nav.runs" | "nav.governance"; icon: LucideIcon }[] = [
  { href: "/home", key: "nav.home", icon: Home },
  { href: "/launch", key: "nav.launch", icon: Rocket },
  { href: "/runs-overview", key: "nav.runs", icon: Table2 },
  { href: "/governance", key: "nav.governance", icon: ShieldCheck },
];

const LENS_NAV: { href: string; key: "nav.compliance" | "nav.cyber" | "nav.ds"; icon: LucideIcon; roles: string[] }[] = [
  { href: "/dashboards/compliance", key: "nav.compliance", icon: Scale, roles: ["legal_compliance", "risk_manager", "domain_expert", "external_auditor", "executive", "secops"] },
  { href: "/dashboards/cyber", key: "nav.cyber", icon: ShieldAlert, roles: ["secops", "legal_compliance", "risk_manager", "external_auditor"] },
  { href: "/dashboards/ds", key: "nav.ds", icon: FlaskConical, roles: ["data_scientist", "ml_researcher"] },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const roles = getRoles();
  const guided = isGuided();
  const { t, toggle, locale } = useI18n();

  function navLink(href: string, label: string, Icon: LucideIcon) {
    const active = pathname === href || (href !== "/home" && pathname.startsWith(href));
    return (
      <Link
        key={href}
        href={href}
        className={clsx(
          "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition",
          active
            ? "bg-white/15 text-white"
            : "text-white/70 hover:bg-white/10 hover:text-white",
        )}
      >
        <Icon size={14} strokeWidth={1.75} />
        {label}
      </Link>
    );
  }

  return (
    <div className="min-h-screen bg-surface-2 text-ink">
      <header className="bg-brand-deep px-4 py-2.5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-5">
            <Link href={guided ? "/home" : "/dashboards/compliance"} className="flex items-center gap-2 text-sm font-semibold tracking-tight text-white">
              <span className="grid h-6 w-6 place-items-center rounded bg-brand-accent text-[13px] font-bold text-brand-deep">V</span>
              {t("app.title")}
            </Link>
            <nav className="flex flex-wrap gap-1">
              {guided && GUIDED_NAV.map((n) => navLink(n.href, t(n.key), n.icon))}
              {LENS_NAV.filter((n) => guided || hasAnyRole(n.roles)).map((n) => navLink(n.href, t(n.key), n.icon))}
            </nav>
          </div>
          <div className="flex items-center gap-3 text-xs text-white/80">
            <button
              type="button"
              onClick={toggle}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-white/80 hover:bg-white/10 hover:text-white"
              aria-label="toggle language"
              data-testid="lang-toggle"
            >
              <Languages size={14} strokeWidth={1.75} />
              {locale.toUpperCase()}
            </button>
            {guided ? (
              <span className="hidden text-white/60 sm:inline">{t("nav.guided")}</span>
            ) : (
              <>
                <span className="hidden sm:inline">{roles.slice(0, 2).join(", ")}</span>
                <button type="button" onClick={() => logout()} className="inline-flex items-center gap-1 text-white/70 hover:text-white">
                  <LogOut size={14} strokeWidth={1.75} />
                  {t("nav.signout")}
                </button>
              </>
            )}
          </div>
        </div>
      </header>
      <StackHealthBar />
      <main className="mx-auto max-w-7xl p-4 md:p-6">{children}</main>
    </div>
  );
}
