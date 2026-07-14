"use client";

import { useEffect, useRef, useState } from "react";
import {
  createStudySession,
  startStudyTask,
  submitStudyResponse,
  type StudySessionInfo,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { useT } from "@/lib/i18n";

const TASK_IDS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"] as const;
const ROLES = [
  "compliance_officer",
  "risk_manager",
  "legal",
  "audit",
  "ai_researcher",
  "other_non_ml",
];
const BANDS = ["green", "orange", "red"] as const;
const TASK_CAP_MS = 300_000; // the protocol's 5-minute cap

type Phase = "intro" | "task" | "done";

interface Saved {
  session: StudySessionInfo;
  taskIndex: number;
}

function loadSaved(): Saved | null {
  try {
    const raw = sessionStorage.getItem("vera-study");
    return raw ? (JSON.parse(raw) as Saved) : null;
  } catch {
    return null;
  }
}

export function StudyRunner() {
  const t = useT();
  const token = getToken();
  const [phase, setPhase] = useState<Phase>("intro");
  const [session, setSession] = useState<StudySessionInfo | null>(null);
  const [taskIndex, setTaskIndex] = useState(0);
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [giveupArmed, setGiveupArmed] = useState(false);
  const [consent, setConsent] = useState(false);
  const [role, setRole] = useState("");
  const [error, setError] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const [answer, setAnswer] = useState<Record<string, unknown>>({});
  const startRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const saved = loadSaved();
    if (saved) {
      setSession(saved.session);
      setTaskIndex(saved.taskIndex);
      setPhase(saved.taskIndex >= TASK_IDS.length ? "done" : "task");
    }
  }, []);

  const persist = (s: StudySessionInfo, index: number) => {
    sessionStorage.setItem("vera-study", JSON.stringify({ session: s, taskIndex: index }));
  };

  const begin = async () => {
    try {
      const s = await createStudySession(token, { role });
      setSession(s);
      setTaskIndex(0);
      persist(s, 0);
      setPhase("task");
    } catch {
      setError(true);
    }
  };

  const taskId = TASK_IDS[Math.min(taskIndex, TASK_IDS.length - 1)];

  const startTask = async () => {
    if (!session) return;
    try {
      await startStudyTask(token, session.session_id, taskId);
    } catch {
      // Server start ping is a sanity channel; the client clock still runs.
    }
    startRef.current = performance.now();
    setRunning(true);
    setTimedOut(false);
    timeoutRef.current = setTimeout(() => {
      setTimedOut(true);
      void finish(true, "timeout");
    }, TASK_CAP_MS);
  };

  const finish = async (gaveUp: boolean, reason = "") => {
    if (!session || submitting) return;
    setSubmitting(true);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    const seconds = Math.max(1, Math.round((performance.now() - startRef.current) / 1000));
    try {
      await submitStudyResponse(token, session.session_id, {
        task_id: taskId,
        answer,
        seconds,
        gave_up: gaveUp,
        reason,
      });
    } catch {
      setError(true);
      setSubmitting(false);
      return;
    }
    const next = taskIndex + 1;
    setAnswer({});
    setRunning(false);
    setGiveupArmed(false);
    setSubmitting(false);
    setTaskIndex(next);
    persist(session, next);
    if (next >= TASK_IDS.length) setPhase("done");
  };

  if (phase === "intro") {
    return (
      <section data-testid="study-intro" className="card p-6 shadow-sm">
        <h1 className="mb-3 text-lg font-semibold text-ink">{t("study.intro.heading")}</h1>
        <p className="mb-4 text-sm text-ink-secondary">{t("study.intro.consent")}</p>
        <label className="mb-3 flex items-center gap-2 text-sm text-ink">
          <input
            type="checkbox"
            data-testid="study-consent"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
          />
          {t("study.intro.consent_check")}
        </label>
        <label className="mb-4 block text-sm text-ink">
          <span className="kpi-label mb-1 block">{t("study.intro.role")}</span>
          <select
            data-testid="study-role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="input"
          >
            <option value="" disabled>
              —
            </option>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {t(`study.role.${r}`)}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          data-testid="study-begin"
          disabled={!consent || !role}
          onClick={() => void begin()}
          className="btn-primary disabled:opacity-40"
        >
          {t("study.intro.begin")}
        </button>
        {error ? <p className="mt-3 text-xs text-status-blocked">{t("study.error")}</p> : null}
      </section>
    );
  }

  if (phase === "done") {
    return (
      <section data-testid="study-done" className="card p-6 text-center shadow-sm">
        <h1 className="mb-2 text-lg font-semibold text-ink">{t("study.done.title")}</h1>
        <p className="text-sm text-ink-secondary">{t("study.done.body")}</p>
        {session ? (
          <p className="mt-3 font-mono text-xs text-ink-secondary">{session.participant}</p>
        ) : null}
      </section>
    );
  }

  return (
    <section data-testid="study-task" className="card p-6 shadow-sm">
      <div className="mb-3 flex items-center justify-between text-xs text-ink-secondary">
        <span>
          {t("study.progress")} {taskIndex + 1} {t("study.of")} {TASK_IDS.length}
        </span>
        {running ? (
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 animate-pulse rounded-full bg-status-blocked" />
            {t("study.recording")}
          </span>
        ) : null}
      </div>
      <p className="mb-4 text-sm font-medium text-ink">{t(`study.${taskId.toLowerCase()}.instruction`)}</p>

      {!running ? (
        <button
          type="button"
          data-testid="study-task-start"
          onClick={() => void startTask()}
          className="btn-primary"
        >
          {t("study.start")}
        </button>
      ) : (
        <div className="space-y-4">
          <button
            type="button"
            data-testid="study-open-dashboard"
            onClick={() => window.open("/home", "vera-study-dashboard")}
            className="btn-secondary"
          >
            {t("study.open_dashboard")} ↗
          </button>

          <TaskFields taskId={taskId} session={session} answer={answer} setAnswer={setAnswer} />

          <div className="flex items-center gap-3">
            <button
              type="button"
              data-testid="study-task-submit"
              disabled={submitting}
              onClick={() => void finish(false)}
              className="btn-primary disabled:opacity-40"
            >
              {t("study.submit")}
            </button>
            <button
              type="button"
              data-testid="study-task-giveup"
              disabled={submitting}
              onClick={() => (giveupArmed ? void finish(true) : setGiveupArmed(true))}
              className="rounded border border-default px-3 py-1 text-xs text-ink-secondary hover:text-ink"
            >
              {giveupArmed ? t("study.giveup_confirm") : t("study.giveup")}
            </button>
          </div>
          {timedOut ? <p className="text-xs text-status-partial">{t("study.timeout_note")}</p> : null}
          {error ? <p className="text-xs text-status-blocked">{t("study.error")}</p> : null}
        </div>
      )}
    </section>
  );
}

function TaskFields({
  taskId,
  session,
  answer,
  setAnswer,
}: {
  taskId: string;
  session: StudySessionInfo | null;
  answer: Record<string, unknown>;
  setAnswer: (a: Record<string, unknown>) => void;
}) {
  const t = useT();
  const set = (key: string, value: unknown) => setAnswer({ ...answer, [key]: value });
  const num = (key: string) => (value: string) =>
    set(key, value === "" ? undefined : Number(value));

  if (taskId === "T1") {
    return (
      <Labeled label={t("study.t1.label")}>
        <select
          data-testid="study-answer-requirement"
          value={String(answer.requirement_id ?? "")}
          onChange={(e) => set("requirement_id", e.target.value)}
          className="input"
        >
          <option value="" disabled>
            —
          </option>
          {(session?.requirement_options ?? []).map((r) => (
            <option key={r.id} value={r.id}>
              {r.id} — {r.name}
            </option>
          ))}
        </select>
      </Labeled>
    );
  }
  if (taskId === "T2") {
    return (
      <div className="flex flex-wrap gap-3">
        {(["score", "ci_lower", "ci_upper"] as const).map((field) => (
          <Labeled key={field} label={t(`study.t2.${field}`)}>
            <input
              data-testid={`study-answer-${field}`}
              type="number"
              step="0.01"
              value={answer[field] === undefined ? "" : String(answer[field])}
              onChange={(e) => num(field)(e.target.value)}
              className="input w-28"
            />
          </Labeled>
        ))}
      </div>
    );
  }
  if (taskId === "T3") {
    const selected = new Set((answer.benchmarks as string[]) ?? []);
    return (
      <div className="grid gap-1 sm:grid-cols-2">
        {(session?.benchmark_options ?? []).map((b) => (
          <label key={b} className="flex items-center gap-2 text-xs text-ink">
            <input
              type="checkbox"
              data-testid={`study-answer-benchmark-${b}`}
              checked={selected.has(b)}
              onChange={(e) => {
                const next = new Set(selected);
                if (e.target.checked) next.add(b);
                else next.delete(b);
                set("benchmarks", Array.from(next).sort());
              }}
            />
            <span className="font-mono">{b}</span>
          </label>
        ))}
      </div>
    );
  }
  if (taskId === "T4") {
    return (
      <Labeled label={t("study.t4.label")}>
        <input
          data-testid="study-answer-count"
          type="number"
          min={0}
          max={12}
          value={answer.count === undefined ? "" : String(answer.count)}
          onChange={(e) => num("count")(e.target.value)}
          className="input w-24"
        />
      </Labeled>
    );
  }
  if (taskId === "T5") {
    return (
      <div className="space-y-2">
        <textarea
          data-testid="study-answer-excerpt"
          value={String(answer.excerpt ?? "")}
          onChange={(e) => set("excerpt", e.target.value)}
          placeholder={t("study.t5.placeholder")}
          rows={3}
          className="input w-full"
        />
        <label className="flex items-center gap-2 text-xs text-ink">
          <input
            type="checkbox"
            data-testid="study-answer-confirmed"
            checked={Boolean(answer.confirmed)}
            onChange={(e) => set("confirmed", e.target.checked)}
          />
          {t("study.t5.confirm")}
        </label>
      </div>
    );
  }
  if (taskId === "T6") {
    return (
      <div className="flex flex-wrap gap-3">
        {(["failed", "fallback", "ok"] as const).map((field) => (
          <Labeled key={field} label={t(`study.t6.${field}`)}>
            <input
              data-testid={`study-answer-${field}`}
              type="number"
              min={0}
              value={answer[field] === undefined ? "" : String(answer[field])}
              onChange={(e) => num(field)(e.target.value)}
              className="input w-20"
            />
          </Labeled>
        ))}
      </div>
    );
  }
  if (taskId === "T7") {
    return (
      <div className="flex flex-wrap gap-3">
        <Labeled label={t("study.t7.score")}>
          <input
            data-testid="study-answer-trust"
            type="number"
            min={0}
            max={100}
            value={answer.score === undefined ? "" : String(answer.score)}
            onChange={(e) => num("score")(e.target.value)}
            className="input w-24"
          />
        </Labeled>
        <Labeled label={t("study.t7.band")}>
          <select
            data-testid="study-answer-band"
            value={String(answer.band ?? "")}
            onChange={(e) => set("band", e.target.value)}
            className="input"
          >
            <option value="" disabled>
              —
            </option>
            {BANDS.map((b) => (
              <option key={b} value={b}>
                {t(`summary.band.${b}`)}
              </option>
            ))}
          </select>
        </Labeled>
      </div>
    );
  }
  // T8
  return (
    <Labeled label={t("study.t8.label")}>
      <input
        data-testid="study-answer-runurl"
        value={String(answer.run_id ?? "")}
        onChange={(e) => set("run_id", e.target.value)}
        placeholder="http://…/runs/…"
        className="input w-full"
      />
    </Labeled>
  );
}

function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm text-ink">
      <span className="kpi-label mb-1 block">{label}</span>
      {children}
    </label>
  );
}
