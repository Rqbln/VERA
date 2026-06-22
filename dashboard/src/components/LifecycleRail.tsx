"use client";

const STAGES = [
  { id: "data", label: "Dataset", reqs: "R03–R05" },
  { id: "finetune", label: "Checkpoint", reqs: "BSR / eval" },
  { id: "inference", label: "Inference", reqs: "R01–R12" },
];

interface Props {
  active: string;
  onSelect: (stage: string) => void;
}

export function LifecycleRail({ active, onSelect }: Props) {
  return (
    <div className="mb-4 flex gap-1 border-b border-default pb-2 text-xs">
      {STAGES.map((s) => (
        <button
          key={s.id}
          type="button"
          onClick={() => onSelect(s.id)}
          className={`rounded px-3 py-1.5 text-left ${
            active === s.id
              ? "bg-surface-2 text-ink"
              : "text-ink-secondary hover:bg-hover hover:text-ink"
          }`}
        >
          <div className="font-medium">{s.label}</div>
          <div className="text-[10px] text-ink-secondary">{s.reqs}</div>
        </button>
      ))}
    </div>
  );
}
