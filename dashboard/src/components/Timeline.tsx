"use client";

import clsx from "clsx";
import { Check } from "lucide-react";

export interface Milestone {
  label: string;
  state: "done" | "active" | "todo";
  hint?: string;
}

// Horizontal graphical timeline. Done = brand green, active = vivid accent green (the one place
// vivid green carries meaning), todo = neutral. Used for the lifecycle / governance roll-out.
export function Timeline({ milestones }: { milestones: Milestone[] }) {
  return (
    <ol className="flex w-full items-start">
      {milestones.map((m, i) => {
        const last = i === milestones.length - 1;
        const dot =
          m.state === "active"
            ? "bg-brand-accent ring-4 ring-brand-accent/20"
            : m.state === "done"
              ? "bg-brand"
              : "bg-default";
        const line = m.state === "todo" ? "bg-default" : "bg-brand";
        return (
          <li key={m.label} className="flex flex-1 flex-col items-center">
            <div className="flex w-full items-center">
              <span className={clsx("z-10 grid h-6 w-6 place-items-center rounded-full text-white", dot)}>
                {m.state === "done" ? <Check size={13} strokeWidth={3} /> : null}
              </span>
              {!last ? <span className={clsx("h-0.5 flex-1", line)} /> : null}
            </div>
            <div className="mt-1.5 w-[88%] text-center">
              <div
                className={clsx(
                  "text-[11px] font-medium",
                  m.state === "active" ? "text-ink" : "text-ink-secondary",
                )}
              >
                {m.label}
              </div>
              {m.hint ? <div className="text-[10px] text-ink-secondary">{m.hint}</div> : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
