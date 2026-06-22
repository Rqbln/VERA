"use client";

import type { NonMeasurableSlots } from "@/lib/types";

interface Props {
  slots: NonMeasurableSlots;
  runId: string;
}

export function NonMeasurableStrip({ slots, runId }: Props) {
  return (
    <div className="mt-6 border border-default bg-surface-2 p-3 text-xs">
      <div className="mb-2 text-ink-secondary">Non-measurable (N01–N06)</div>
      <div className="grid gap-2 sm:grid-cols-3">
        <QueueCard
          id="N01"
          title="Explicabilité"
          status={slots.n01.status}
          count={slots.n01.queue_count}
          note="HITL review queue"
        />
        <QueueCard
          id="N02"
          title="Corrigibilité"
          status={slots.n02.status}
          count={slots.n02.queue_count}
          note="HITL review queue"
        />
        <div className="rounded border border-default p-2">
          <div className="font-mono text-ink-secondary">N04</div>
          <div className="text-ink">Model card + datasheet</div>
          <div className="mt-1 text-ink-secondary">{slots.n04.status}</div>
          {slots.n04.model_card_uri ? (
            <div className="mt-1 truncate font-mono text-[10px] text-ink-secondary">
              {slots.n04.model_card_uri}
            </div>
          ) : null}
        </div>
      </div>
      <div className="mt-2 text-[10px] text-ink-secondary">
        Run {runId.slice(0, 8)} · N03/N05/N06 deferred to signed forms (MVP3.1)
      </div>
    </div>
  );
}

function QueueCard({
  id,
  title,
  status,
  count,
  note,
}: {
  id: string;
  title: string;
  status: string;
  count: number;
  note: string;
}) {
  return (
    <div className="rounded border border-dashed border-default p-2">
      <div className="flex items-center justify-between">
        <span className="font-mono text-ink-secondary">{id}</span>
        <span className="text-ink-secondary">{count} pending</span>
      </div>
      <div className="text-ink">{title}</div>
      <div className="mt-1 capitalize text-ink-secondary">{status}</div>
      <div className="mt-1 text-[10px] text-ink-secondary">{note}</div>
    </div>
  );
}
