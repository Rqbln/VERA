"use client";

import type { TrustFactor } from "@/lib/types";

const BAND_COLOR: Record<string, string> = {
  green: "text-status-ok border-status-ok/40",
  orange: "text-status-partial border-status-partial/40",
  red: "text-status-blocked border-status-blocked/40",
  unknown: "text-ink-secondary border-default",
};

const COMPONENT_LABELS: Record<string, string> = {
  R01: "Robustness",
  R02: "Cyber",
  R05: "Privacy",
  R12: "Toxicity",
};

export function TrustFactorCard({ tf, compact }: { tf: TrustFactor | null | undefined; compact?: boolean }) {
  if (!tf) {
    return (
      <div className="rounded border border-default p-3 text-xs text-ink-secondary">
        Trust Factor: <span className="text-ink-secondary">not available</span>
      </div>
    );
  }
  const color = BAND_COLOR[tf.band] || BAND_COLOR.unknown;
  return (
    <div data-testid="trust-factor-card" className={`rounded border ${color} bg-white p-3`}>
      <div className="flex items-baseline gap-2">
        <span className="text-[11px] uppercase tracking-wide text-ink-secondary">Trust Factor</span>
        <span className={`text-2xl font-semibold ${color.split(" ")[0]}`}>{tf.score}</span>
        <span className="text-xs text-ink-secondary">/ 100</span>
      </div>
      {!compact && (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-ink-secondary">
          {Object.entries(tf.components).map(([k, v]) => (
            <span key={k}>
              {COMPONENT_LABELS[k] || k}: <span className="text-ink">{Math.round(v)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
