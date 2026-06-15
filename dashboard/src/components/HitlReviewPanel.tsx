"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createHitlTask, listHitlTasks, submitHitlReview, type HitlTask } from "@/lib/api";
import { getToken } from "@/lib/auth";

export function HitlReviewPanel({ runId }: { runId: string }) {
  const token = getToken();
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["hitl", runId],
    queryFn: () => listHitlTasks(token, runId),
    refetchInterval: 15_000,
  });

  const addTask = useMutation({
    mutationFn: (requirement: string) =>
      createHitlTask(token, { run_id: runId, requirement }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["hitl", runId] }),
  });

  const tasks = data?.tasks ?? [];

  return (
    <div data-testid="hitl-panel" className="rounded border border-zinc-800 p-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-medium text-zinc-300">Human review (N01 / N02)</h3>
        <div className="flex gap-1">
          <AddButton onClick={() => addTask.mutate("N01")} label="+ N01 explainability" />
          <AddButton onClick={() => addTask.mutate("N02")} label="+ N02 corrigibility" />
        </div>
      </div>
      {tasks.length === 0 ? (
        <p className="text-[11px] text-zinc-600">
          No review tasks yet. N01/N02 require a human panel — queue one above.
        </p>
      ) : (
        <ul className="space-y-1">
          {tasks.map((t) => (
            <TaskRow key={t.task_id} task={t} runId={runId} />
          ))}
        </ul>
      )}
    </div>
  );
}

function AddButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded border border-zinc-700 px-2 py-0.5 text-[11px] text-zinc-400 hover:text-zinc-200"
    >
      {label}
    </button>
  );
}

function TaskRow({ task, runId }: { task: HitlTask; runId: string }) {
  const token = getToken();
  const qc = useQueryClient();
  const [score, setScore] = useState(3);
  const review = useMutation({
    mutationFn: () => submitHitlReview(token, task.task_id, { likert_score: score }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["hitl", runId] }),
  });

  return (
    <li className="flex items-center justify-between rounded bg-zinc-900/40 px-2 py-1 text-[11px]">
      <span className="flex items-center gap-2">
        <span className="font-mono text-zinc-400">{task.requirement}</span>
        <span
          className={`rounded px-1.5 ${
            task.status === "done" ? "bg-emerald-900/40 text-emerald-400" : "bg-zinc-800 text-zinc-400"
          }`}
        >
          {task.status}
        </span>
        {task.status === "done" ? (
          <span className="text-zinc-500">Likert {task.likert_score}/5</span>
        ) : null}
      </span>
      {task.status !== "done" ? (
        <span className="flex items-center gap-1">
          <select
            value={score}
            onChange={(e) => setScore(Number(e.target.value))}
            className="rounded border border-zinc-700 bg-zinc-900 px-1 text-zinc-200"
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => review.mutate()}
            disabled={review.isPending}
            className="rounded bg-zinc-100 px-2 py-0.5 font-medium text-zinc-900 disabled:opacity-40"
          >
            Submit
          </button>
        </span>
      ) : null}
    </li>
  );
}
