"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getSeries } from "@/lib/api";
import { getToken } from "@/lib/auth";

// Mirrors RAIP_BAND_GREEN_MIN / RAIP_BAND_ORANGE_MIN defaults in score_bands.py.
const GREEN_MIN = 0.7;
const ORANGE_MIN = 0.4;

export function TrendCurve({ requirement, modelId }: { requirement: string; modelId?: string }) {
  const token = getToken();
  const { data, isLoading } = useQuery({
    queryKey: ["series", requirement, modelId],
    queryFn: () => getSeries(token, requirement, modelId),
  });

  if (isLoading) return <p className="text-xs text-zinc-600">Loading trend…</p>;

  // Preserve the "no false time-series until data exists" design decision.
  if (!data?.available) {
    return (
      <p className="text-xs text-zinc-600">
        {requirement}: not enough history for a trend yet (need ≥2 completed runs of this model).
      </p>
    );
  }

  const chart = data.series.map((p, i) => ({
    idx: i + 1,
    value: p.value,
    run: p.run_id.slice(0, 8),
  }));

  return (
    <div data-testid="trend-curve" className="h-48 w-full">
      <div className="mb-1 text-xs text-zinc-400">{requirement} score over runs</div>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chart} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="run" tick={{ fontSize: 10, fill: "#71717a" }} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 10, fill: "#71717a" }} />
          <Tooltip
            contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 11 }}
            labelStyle={{ color: "#a1a1aa" }}
          />
          <ReferenceLine y={GREEN_MIN} stroke="#059669" strokeDasharray="4 4" />
          <ReferenceLine y={ORANGE_MIN} stroke="#d97706" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="value" stroke="#e4e4e7" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
