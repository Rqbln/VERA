"use client";

import { useI18n, useT } from "@/lib/i18n";

// Minimal chrome on purpose: no DashboardShell nav (navigating away would
// unmount the study timer), just the VERA mark and the language toggle.
export default function StudyLayout({ children }: { children: React.ReactNode }) {
  const t = useT();
  const { toggle, locale } = useI18n();
  return (
    <div className="min-h-screen bg-surface-2 text-ink">
      <header className="flex items-center justify-between bg-brand-deep px-4 py-2.5 shadow-sm">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-brand-accent text-xs font-bold text-brand-deep">
            V
          </span>
          <span className="text-sm font-semibold text-white">{t("study.title")}</span>
        </div>
        <button
          type="button"
          data-testid="study-lang-toggle"
          onClick={toggle}
          className="rounded px-2 py-0.5 text-xs text-white/80 hover:text-white"
        >
          {locale === "en" ? "FR" : "EN"}
        </button>
      </header>
      <main className="mx-auto max-w-2xl p-4 md:p-8">{children}</main>
    </div>
  );
}
