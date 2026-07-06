"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createHitlTask,
  getHitlRubrics,
  listHitlTasks,
  submitHitlReview,
  type HitlTask,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { useT } from "@/lib/i18n";

export function HitlReviewPanel({ runId }: { runId: string }) {
  const token = getToken();
  const t = useT();
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["hitl", runId],
    queryFn: () => listHitlTasks(token, runId),
    refetchInterval: 15_000,
  });
  const { data: rubricsData } = useQuery({
    queryKey: ["hitl-rubrics"],
    queryFn: () => getHitlRubrics(token),
    staleTime: Infinity,
  });

  const addTask = useMutation({
    mutationFn: (requirement: string) =>
      createHitlTask(token, { run_id: runId, requirement }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["hitl", runId] }),
  });

  const tasks = data?.tasks ?? [];
  const rubrics = rubricsData?.rubrics ?? {};

  return (
    <div data-testid="hitl-panel" className="rounded border border-default p-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-medium text-ink">{t("hitl.title")}</h3>
        <div className="flex gap-1">
          <AddButton onClick={() => addTask.mutate("N01")} label={t("hitl.add_n01")} />
          <AddButton onClick={() => addTask.mutate("N02")} label={t("hitl.add_n02")} />
        </div>
      </div>
      {tasks.length === 0 ? (
        <p className="text-[11px] text-ink-secondary">{t("hitl.empty")}</p>
      ) : (
        <ul className="space-y-2">
          {tasks.map((task) => (
            <TaskRow
              key={task.task_id}
              task={task}
              runId={runId}
              rubric={rubrics[task.requirement] ?? []}
            />
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
      className="rounded border border-default px-2 py-0.5 text-[11px] text-ink-secondary hover:text-ink"
    >
      {label}
    </button>
  );
}

function TaskRow({ task, runId, rubric }: { task: HitlTask; runId: string; rubric: string[] }) {
  const token = getToken();
  const t = useT();
  const qc = useQueryClient();
  const [score, setScore] = useState(3); // fallback when the rubric is unknown
  const [criteria, setCriteria] = useState<Record<string, number>>(
    Object.fromEntries(rubric.map((c) => [c, 3])),
  );
  const [comment, setComment] = useState("");
  const review = useMutation({
    // Never send an empty criteria object: the backend treats {} as "no rubric" and
    // would fall back to a null likert_score. Untouched selects submit their default (3).
    mutationFn: () =>
      submitHitlReview(
        token,
        task.task_id,
        rubric.length > 0
          ? {
              criteria: Object.fromEntries(rubric.map((c) => [c, criteria[c] ?? 3])),
              comment: comment || undefined,
            }
          : { likert_score: score, comment: comment || undefined },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["hitl", runId] }),
  });

  const values = rubric.map((c) => criteria[c] ?? 3);
  const avg = values.length > 0 ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1) : null;

  return (
    <li className="rounded bg-surface-2 px-2 py-1.5 text-[11px]">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2">
          <span className="font-mono text-ink-secondary">{task.requirement}</span>
          <span
            className={`rounded px-1.5 ${
              task.status === "done" ? "bg-status-ok/10 text-status-ok" : "bg-surface-2 text-ink-secondary"
            }`}
          >
            {task.status}
          </span>
          {task.status === "done" ? (
            <span className="text-ink-secondary">
              {t("hitl.likert")} {task.likert_score}/5
            </span>
          ) : null}
        </span>
        {task.status !== "done" && rubric.length > 0 ? (
          <span className="text-ink-secondary">
            {t("hitl.avg_preview")} {avg}/5
          </span>
        ) : null}
      </div>

      {task.status === "done" ? (
        <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-ink-secondary">
          {Object.entries(task.criteria ?? {}).map(([name, value]) => (
            <span key={name} className="rounded border border-default px-1.5 py-0.5">
              {name}: {value}/5
            </span>
          ))}
          {task.comment ? <span className="italic">“{task.comment}”</span> : null}
        </div>
      ) : (
        <div className="mt-1.5 space-y-1.5">
          {rubric.length > 0 ? (
            <div className="flex flex-wrap items-center gap-2">
              {rubric.map((name) => (
                <label key={name} className="flex items-center gap-1 text-ink-secondary">
                  {name}
                  <select
                    data-testid={`hitl-criterion-${name}`}
                    value={criteria[name] ?? 3}
                    onChange={(e) =>
                      setCriteria((p) => ({ ...p, [name]: Number(e.target.value) }))
                    }
                    className="rounded border border-default bg-surface-2 px-1 text-ink"
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          ) : (
            <select
              value={score}
              onChange={(e) => setScore(Number(e.target.value))}
              className="rounded border border-default bg-surface-2 px-1 text-ink"
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          )}
          <div className="flex items-center gap-2">
            <input
              data-testid="hitl-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={t("hitl.comment_placeholder")}
              className="w-full rounded border border-default bg-surface-2 px-2 py-0.5 text-ink"
            />
            <button
              type="button"
              data-testid="hitl-submit"
              onClick={() => review.mutate()}
              disabled={review.isPending}
              className="rounded bg-brand px-2 py-0.5 font-medium text-white disabled:opacity-40"
            >
              {t("hitl.submit")}
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
