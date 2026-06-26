"use client";

import type { NonMeasurableSlot, NonMeasurableSlots } from "@/lib/types";

interface Props {
  slots: NonMeasurableSlots;
  runId: string;
}

const OK = new Set(["reviewed", "measured", "completed", "available"]);

export function NonMeasurableStrip({ slots, runId }: Props) {
  const items: { id: string; title: string; slot: NonMeasurableSlot; kind: string }[] = [
    { id: "N01", title: "Explainability", slot: slots.n01, kind: "hitl" },
    { id: "N02", title: "Corrigibility", slot: slots.n02, kind: "hitl" },
    { id: "N03", title: "Environmental impact", slot: slots.n03, kind: "energy" },
    { id: "N04", title: "Datasheet / model card", slot: slots.n04, kind: "form" },
    { id: "N05", title: "Evaluation summary", slot: slots.n05, kind: "form" },
    { id: "N06", title: "Risk summary", slot: slots.n06, kind: "form" },
  ];
  return (
    <div className="mt-6 border border-default bg-surface-2 p-3 text-xs">
      <div className="mb-2 text-ink-secondary">Non-measurable (N01–N06)</div>
      <div className="grid gap-2 sm:grid-cols-3">
        {items.map((it) => (
          <Slot key={it.id} {...it} />
        ))}
      </div>
      <div className="mt-2 text-[10px] text-ink-secondary">
        Run {runId.slice(0, 8)} · N01/N02 from the HITL review queue · N03 measured (CodeCarbon) ·
        N04–N06 from the declarative forms
      </div>
    </div>
  );
}

function Slot({ id, title, slot, kind }: { id: string; title: string; slot: NonMeasurableSlot; kind: string }) {
  const status = String(slot?.status ?? "pending");
  const ok = OK.has(status);
  return (
    <div className="rounded border border-default p-2">
      <div className="flex items-center justify-between">
        <span className="font-mono text-ink-secondary">{id}</span>
        <span className={ok ? "text-status-ok" : "text-ink-secondary"}>{status}</span>
      </div>
      <div className="text-ink">{title}</div>
      {kind === "hitl" ? (
        <div className="mt-1 text-[10px] text-ink-secondary">
          {slot.reviewed ?? 0}/{slot.queue_count ?? 0} reviewed
          {slot.avg_likert != null ? ` · avg ${slot.avg_likert}/5` : ""}
        </div>
      ) : null}
      {kind === "energy" && status === "measured" ? (
        <div className="mt-1 text-[10px] text-ink-secondary">
          {slot.kwh} kWh · {slot.co2eq_kg} kgCO₂e
        </div>
      ) : null}
      {kind === "form" ? (
        <div className="mt-1 text-[10px] text-ink-secondary">
          {Object.keys(slot.fields ?? {}).length} field(s)
          {slot.model_card_uri ? " · model card linked" : ""}
        </div>
      ) : null}
    </div>
  );
}
