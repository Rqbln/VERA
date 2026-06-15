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
    <div className="mb-4 flex gap-1 border-b border-zinc-800 pb-2 text-xs">
      {STAGES.map((s) => (
        <button
          key={s.id}
          type="button"
          onClick={() => onSelect(s.id)}
          className={`rounded px-3 py-1.5 text-left ${
            active === s.id
              ? "bg-zinc-800 text-zinc-100"
              : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300"
          }`}
        >
          <div className="font-medium">{s.label}</div>
          <div className="text-[10px] text-zinc-600">{s.reqs}</div>
        </button>
      ))}
    </div>
  );
}
