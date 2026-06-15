"use client";

import type { TrustFactor } from "@/lib/types";

const BAND_COLOR: Record<string, string> = {
  green: "text-emerald-400 border-emerald-900/50",
  orange: "text-amber-400 border-amber-900/50",
  red: "text-red-400 border-red-900/50",
  unknown: "text-zinc-400 border-zinc-800",
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
      <div className="rounded border border-zinc-800 p-3 text-xs text-zinc-600">
        Trust Factor: <span className="text-zinc-500">not available</span>
      </div>
    );
  }
  const color = BAND_COLOR[tf.band] || BAND_COLOR.unknown;
  return (
    <div data-testid="trust-factor-card" className={`rounded border ${color} bg-zinc-950 p-3`}>
      <div className="flex items-baseline gap-2">
        <span className="text-[11px] uppercase tracking-wide text-zinc-500">Trust Factor</span>
        <span className={`text-2xl font-semibold ${color.split(" ")[0]}`}>{tf.score}</span>
        <span className="text-xs text-zinc-600">/ 100</span>
      </div>
      {!compact && (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-zinc-500">
          {Object.entries(tf.components).map(([k, v]) => (
            <span key={k}>
              {COMPONENT_LABELS[k] || k}: <span className="text-zinc-300">{Math.round(v)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
