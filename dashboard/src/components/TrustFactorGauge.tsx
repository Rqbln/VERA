"use client";

import type { TrustFactor } from "@/lib/types";
import { useT } from "@/lib/i18n";

// Semantic band segments, proportional to the real scoring thresholds
// (score_bands.py: green >= 0.70, amber >= 0.40). Swap this array for a
// different segmentation; ticks and arcs derive from it.
export interface GaugeSegment {
  from: number;
  to: number;
  color: string;
}
export const BAND_SEGMENTS: GaugeSegment[] = [
  { from: 0, to: 40, color: "#c0392b" }, // red: action needed
  { from: 40, to: 70, color: "#e8a33d" }, // amber: watch
  { from: 70, to: 100, color: "#00915a" }, // green: compliant
];

const COMPONENT_LABELS: Record<string, string> = {
  R01: "Robustness",
  R02: "Cyber",
  R05: "Privacy",
  R06: "Capabilities",
  R07: "Calibration",
  R12: "Toxicity",
};

const BAND_BADGE: Record<string, string> = {
  green: "badge badge-ok",
  orange: "badge badge-partial",
  red: "badge badge-blocked",
  unknown: "badge badge-neutral",
};

// Geometry: viewBox 220x130, center (110,110), score 0 at 180deg (left),
// score 100 at 0deg (right). SVG y grows downward, so decreasing angle sweeps
// clockwise (sweep flag 1). Every segment spans < 180deg (large-arc flag 0).
const CX = 110;
const CY = 110;
const R = 90;
const STROKE = 18;
const SEGMENT_PAD = 0.7; // score points; ~2px surface gap between touching fills

function angleOf(score: number): number {
  return 180 - 1.8 * Math.min(100, Math.max(0, score));
}

function point(r: number, deg: number): [number, number] {
  const rad = (deg * Math.PI) / 180;
  return [CX + r * Math.cos(rad), CY - r * Math.sin(rad)];
}

function arcPath(from: number, to: number): string {
  const [x1, y1] = point(R, angleOf(from));
  const [x2, y2] = point(R, angleOf(to));
  return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${R} ${R} 0 0 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
}

function needlePoints(score: number): string {
  const deg = angleOf(score);
  const [tx, ty] = point(R - 26, deg);
  const [b1x, b1y] = point(4, deg + 90);
  const [b2x, b2y] = point(4, deg - 90);
  return `${tx.toFixed(2)},${ty.toFixed(2)} ${b1x.toFixed(2)},${b1y.toFixed(2)} ${b2x.toFixed(2)},${b2y.toFixed(2)}`;
}

interface Props {
  tf: TrustFactor | null | undefined;
  segments?: GaugeSegment[];
  width?: number;
  showComponents?: boolean;
}

export function TrustFactorGauge({
  tf,
  segments = BAND_SEGMENTS,
  width = 300,
  showComponents = true,
}: Props) {
  const t = useT();

  if (!tf) {
    return (
      <div
        data-testid="trust-factor-card"
        className="rounded-lg border border-default bg-white p-4 text-xs text-ink-secondary"
      >
        {t("summary.trust_factor")}: {t("summary.band.unknown").toLowerCase()}
      </div>
    );
  }

  const score = Math.min(100, Math.max(0, tf.score));
  const band = tf.band in BAND_BADGE ? tf.band : "unknown";
  // Tick values derive from the segment boundaries (0, 40, 70, 100 by default);
  // the visible numbers are the contrast relief for the low-contrast amber arc.
  const ticks = Array.from(
    new Set(segments.flatMap((s) => [s.from, s.to])),
  ).sort((a, b) => a - b);

  return (
    <div
      data-testid="trust-factor-card"
      role="img"
      aria-label={`${t("summary.trust_factor")}: ${Math.round(score)} / 100 (${t(`summary.band.${band}`)})`}
      className="flex flex-col items-center"
      style={{ width }}
    >
      <svg viewBox="-12 0 244 130" width={width} height={(width * 130) / 244}>
        {/* unfilled track under the segments */}
        <path d={arcPath(0, 100)} stroke="#eef1ef" strokeWidth={STROKE} fill="none" />
        {segments.map((s, i) => (
          <path
            key={s.color}
            d={arcPath(
              i === 0 ? s.from : s.from + SEGMENT_PAD,
              i === segments.length - 1 ? s.to : s.to - SEGMENT_PAD,
            )}
            stroke={s.color}
            strokeWidth={STROKE}
            strokeLinecap="butt"
            fill="none"
          />
        ))}
        {ticks.map((v) => {
          const [x, y] = point(R + 16, angleOf(v));
          return (
            <text
              key={v}
              x={x}
              y={y + 3}
              textAnchor="middle"
              fontSize="10"
              fill="#5a6b62"
            >
              {v}
            </text>
          );
        })}
        <polygon points={needlePoints(score)} fill="#1f2a24" />
        <circle cx={CX} cy={CY} r={6} fill="#1f2a24" stroke="#ffffff" strokeWidth={2} />
      </svg>
      <div className="-mt-1 flex items-baseline gap-2">
        <span className="text-5xl font-semibold text-ink">{Math.round(score)}</span>
        <span className="text-sm text-ink-secondary">/ 100</span>
      </div>
      <div className="mt-1.5 flex items-center gap-2">
        <span className="kpi-label">{t("summary.trust_factor")}</span>
        <span className={BAND_BADGE[band]}>{t(`summary.band.${band}`)}</span>
      </div>
      {showComponents && Object.keys(tf.components ?? {}).length > 0 ? (
        <div className="mt-2 flex flex-wrap justify-center gap-x-3 gap-y-0.5 text-[11px] text-ink-secondary">
          {Object.entries(tf.components).map(([k, v]) => (
            <span key={k}>
              {COMPONENT_LABELS[k] ?? k}: {Math.round(v)}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
