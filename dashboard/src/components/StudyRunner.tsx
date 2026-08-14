"use client";

import { useEffect, useRef, useState } from "react";
import {
  createStudySession,
  getBenchmarkRun,
  getProvenance,
  getRawOutputs,
  startStudyTask,
  submitStudyResponse,
  submitStudySurvey,
  type StudyQuizItem,
  type StudySessionInfo,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { useI18n, useT } from "@/lib/i18n";

const ROLES = [
  "compliance_officer",
  "risk_manager",
  "legal",
  "audit",
  "ai_researcher",
  "other_non_ml",
];
const AI_EXPERIENCE = ["none", "user", "reviewer", "builder"];
const AIACT_FAMILIARITY = ["none", "heard", "working", "expert"];
const SENIORITY = ["lt2", "2to5", "6to10", "gt10"];
const PU_ITEMS = ["PU1", "PU2", "PU3", "PU4"] as const;
const PEOU_ITEMS = ["PEOU1", "PEOU2", "PEOU3", "PEOU4"] as const;
const SURVEY_ITEMS = [...PU_ITEMS, ...PEOU_ITEMS];
const LIKERT = [1, 2, 3, 4, 5] as const;
const TASK_CAP_MS = 300_000; // the protocol's 5-minute cap
const BASELINE_COUNT = 6; // six baseline items, then six dashboard items, then T8

type Phase = "intro" | "task" | "transition" | "survey" | "done";

/** One step of the session: a quiz item, or the non-comparative T8 epilogue. */
interface Step {
  id: string;
  condition: "baseline" | "vera";
  params: Record<string, string>;
}

interface Saved {
  session: StudySessionInfo;
  taskIndex: number;
  surveyDone?: boolean; // optional: records written before the survey existed still load
}

function loadSaved(): Saved | null {
  try {
    const raw = sessionStorage.getItem("vera-study");
    const saved = raw ? (JSON.parse(raw) as Saved) : null;
    // Pre-quiz sessions carry no item plan; they cannot be resumed meaningfully.
    if (saved && !Array.isArray(saved.session.items)) {
      sessionStorage.removeItem("vera-study");
      return null;
    }
    return saved;
  } catch {
    return null;
  }
}

function buildSteps(session: StudySessionInfo | null): Step[] {
  if (!session) return [];
  return [
    ...session.items.map((i: StudyQuizItem) => ({
      id: i.id,
      condition: i.condition,
      params: i.params ?? {},
    })),
    { id: "T8", condition: "vera" as const, params: {} },
  ];
}

export function StudyRunner() {
  const t = useT();
  const { locale } = useI18n();
  const token = getToken();
  const [phase, setPhase] = useState<Phase>("intro");
  const [session, setSession] = useState<StudySessionInfo | null>(null);
  const [taskIndex, setTaskIndex] = useState(0);
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [giveupArmed, setGiveupArmed] = useState(false);
  const [consent, setConsent] = useState(false);
  const [role, setRole] = useState("");
  const [aiExperience, setAiExperience] = useState("");
  const [aiactFamiliarity, setAiactFamiliarity] = useState("");
  const [seniority, setSeniority] = useState("");
  const [error, setError] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const [answer, setAnswer] = useState<Record<string, unknown>>({});
  const [survey, setSurvey] = useState<Record<string, number>>({});
  const [comment, setComment] = useState("");
  const startRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const steps = buildSteps(session);

  useEffect(() => {
    const saved = loadSaved();
    if (saved) {
      setSession(saved.session);
      setTaskIndex(saved.taskIndex);
      const total = saved.session.items.length + 1;
      if (saved.taskIndex >= total) setPhase(saved.surveyDone ? "done" : "survey");
      else if (saved.taskIndex === BASELINE_COUNT) setPhase("transition");
      else setPhase("task");
    }
  }, []);

  const persist = (s: StudySessionInfo, index: number, surveyDone = false) => {
    sessionStorage.setItem(
      "vera-study",
      JSON.stringify({ session: s, taskIndex: index, surveyDone }),
    );
  };

  const begin = async () => {
    try {
      const s = await createStudySession(token, {
        role,
        ai_experience: aiExperience,
        aiact_familiarity: aiactFamiliarity,
        seniority,
        locale,
      });
      setSession(s);
      setTaskIndex(0);
      persist(s, 0);
      setPhase("task");
    } catch {
      setError(true);
    }
  };

  const finishSurvey = async () => {
    if (!session || submitting) return;
    setSubmitting(true);
    try {
      await submitStudySurvey(token, session.session_id, {
        items: survey,
        comment: comment || undefined,
      });
    } catch {
      setError(true);
      setSubmitting(false);
      return; // the button stays enabled: task data is already server-side
    }
    persist(session, steps.length, true);
    setSubmitting(false);
    setPhase("done");
  };

  const step: Step | undefined = steps[Math.min(taskIndex, Math.max(steps.length - 1, 0))];

  const startTask = async () => {
    if (!session || !step) return;
    try {
      await startStudyTask(token, session.session_id, step.id);
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
    if (!session || !step || submitting) return;
    setSubmitting(true);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    const seconds = Math.max(1, Math.round((performance.now() - startRef.current) / 1000));
    try {
      await submitStudyResponse(token, session.session_id, {
        task_id: step.id,
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
    if (next >= steps.length) setPhase("survey");
    else if (next === BASELINE_COUNT) setPhase("transition");
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
        <div className="mb-4 space-y-3">
          <Choice
            testid="study-role"
            label={t("study.intro.role")}
            value={role}
            onChange={setRole}
            options={ROLES.map((r) => [r, t(`study.role.${r}`)])}
          />
          <Choice
            testid="study-ai-experience"
            label={t("study.intro.ai_experience")}
            value={aiExperience}
            onChange={setAiExperience}
            options={AI_EXPERIENCE.map((r) => [r, t(`study.ai_exp.${r}`)])}
          />
          <Choice
            testid="study-aiact-familiarity"
            label={t("study.intro.aiact")}
            value={aiactFamiliarity}
            onChange={setAiactFamiliarity}
            options={AIACT_FAMILIARITY.map((r) => [r, t(`study.aiact.${r}`)])}
          />
          <Choice
            testid="study-seniority"
            label={t("study.intro.seniority")}
            value={seniority}
            onChange={setSeniority}
            options={SENIORITY.map((r) => [r, t(`study.seniority.${r}`)])}
          />
        </div>
        <button
          type="button"
          data-testid="study-begin"
          disabled={!consent || !role || !aiExperience || !aiactFamiliarity || !seniority}
          onClick={() => void begin()}
          className="btn-primary disabled:opacity-40"
        >
          {t("study.intro.begin")}
        </button>
        {error ? <p className="mt-3 text-xs text-status-blocked">{t("study.error")}</p> : null}
      </section>
    );
  }

  if (phase === "transition") {
    return (
      <section data-testid="study-transition" className="card p-6 shadow-sm">
        <h1 className="mb-2 text-lg font-semibold text-ink">{t("study.transition.heading")}</h1>
        <p className="mb-4 text-sm text-ink-secondary">{t("study.transition.body")}</p>
        <button
          type="button"
          data-testid="study-transition-continue"
          onClick={() => setPhase("task")}
          className="btn-primary"
        >
          {t("study.transition.continue")}
        </button>
      </section>
    );
  }

  if (phase === "survey") {
    const remaining = SURVEY_ITEMS.length - Object.keys(survey).length;
    return (
      <section data-testid="study-survey" className="card p-6 shadow-sm">
        <h1 className="mb-2 text-lg font-semibold text-ink">{t("study.survey.heading")}</h1>
        <p className="mb-1 text-sm text-ink-secondary">{t("study.survey.intro")}</p>
        <p className="mb-4 text-xs text-ink-secondary">{t("study.survey.scale_hint")}</p>

        {([["study.survey.pu_heading", PU_ITEMS], ["study.survey.peou_heading", PEOU_ITEMS]] as const).map(
          ([heading, items]) => (
            <div key={heading} className="mb-5">
              <div className="kpi-label mb-2">{t(heading)}</div>
              <div className="space-y-3">
                {items.map((item) => (
                  <div key={item} data-testid={`study-survey-item-${item}`}>
                    <p className="mb-1 text-sm text-ink">{t(`study.survey.${item.toLowerCase()}`)}</p>
                    <div className="flex flex-wrap gap-3">
                      {LIKERT.map((n) => (
                        <label key={n} className="flex items-center gap-1 text-xs text-ink-secondary">
                          <input
                            type="radio"
                            name={item}
                            data-testid={`study-survey-${item}-${n}`}
                            checked={survey[item] === n}
                            onChange={() => setSurvey({ ...survey, [item]: n })}
                          />
                          {n}
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ),
        )}

        <label className="mb-1 block text-sm text-ink">
          <span className="kpi-label mb-1 block">{t("study.survey.comment")}</span>
          <textarea
            data-testid="study-survey-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={t("study.survey.comment_placeholder")}
            maxLength={500}
            rows={3}
            className="input w-full"
          />
        </label>
        <p className="mb-4 text-[11px] text-ink-secondary">{t("study.survey.comment_privacy")}</p>

        <div className="flex items-center gap-3">
          <button
            type="button"
            data-testid="study-survey-submit"
            disabled={remaining > 0 || submitting}
            onClick={() => void finishSurvey()}
            className="btn-primary disabled:opacity-40"
          >
            {t("study.survey.submit")}
          </button>
          {remaining > 0 ? (
            <span data-testid="study-survey-remaining" className="text-xs text-ink-secondary">
              {remaining} {t("study.survey.remaining")}
            </span>
          ) : null}
        </div>
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

  const isBaseline = step?.condition === "baseline";
  const isBonus = step?.id === "T8";
  const partLabel = isBonus
    ? t("study.bonus")
    : isBaseline
      ? t("study.part1")
      : t("study.part2");
  const withinIndex = isBonus ? 1 : isBaseline ? taskIndex + 1 : taskIndex - BASELINE_COUNT + 1;
  const withinTotal = isBonus ? 1 : BASELINE_COUNT;

  return (
    <section data-testid="study-task" className="card p-6 shadow-sm">
      <div className="mb-3 flex items-center justify-between text-xs text-ink-secondary">
        <span data-testid="study-progress">
          {partLabel} · {t("study.question")} {withinIndex} {t("study.of")} {withinTotal}
        </span>
        {running ? (
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 animate-pulse rounded-full bg-status-blocked" />
            {t("study.recording")}
          </span>
        ) : null}
      </div>
      <p className="mb-4 text-sm font-medium text-ink">{instructionFor(t, step)}</p>

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
          {isBaseline ? (
            <MaterialsPanel
              token={token}
              runId={session?.run_id ?? ""}
              benchmarks={session?.benchmark_options ?? []}
            />
          ) : (
            <button
              type="button"
              data-testid="study-open-dashboard"
              data-href={step ? dashboardHref(step, session?.run_id ?? "") : "/home"}
              onClick={() =>
                window.open(
                  step ? dashboardHref(step, session?.run_id ?? "") : "/home",
                  "vera-study-dashboard",
                )
              }
              className="btn-secondary"
            >
              {t("study.open_dashboard")} ↗
            </button>
          )}

          <TaskFields step={step} session={session} answer={answer} setAnswer={setAnswer} />

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

/** Dashboard-phase deep link: the view that holds the item's answer.
 *  Same granularity as the baseline document tabs: a view, never the answer. */
function dashboardHref(step: Step, runId: string): string {
  const base = `/dashboards/compliance?run=${encodeURIComponent(runId)}`;
  if (step.id === "T8") return "/launch";
  const pair = step.id.slice(0, 2);
  if (pair === "Q2" || step.id === "Q3B" || pair === "Q6") {
    const rid = step.params.requirement_id;
    return rid ? `${base}&req=${encodeURIComponent(rid)}` : base;
  }
  if (step.id === "Q3A" || step.id === "Q4B") return `${base}&details=1`;
  return base; // Q1*, Q4A, Q5*: hero gauge, coverage bar and triage table
}

function instructionFor(t: (k: string) => string, step: Step | undefined): string {
  if (!step) return "";
  if (step.id === "T8") return t("study.t8.instruction");
  const pair = step.id.slice(0, 2); // "Q1".."Q6"
  const variant = step.id.slice(2).toLowerCase(); // "a" | "b"
  if (pair === "Q2")
    return t("study.q2.instruction").replace(
      "{name}",
      step.params.requirement_name || step.params.requirement_id || "",
    );
  if (step.id === "Q3B")
    return t("study.q3b.instruction").replace(
      "{name}",
      step.params.requirement_name || step.params.requirement_id || "",
    );
  if (pair === "Q6")
    return t("study.q6.instruction").replace("{benchmark}", step.params.benchmark_id || "");
  if (pair === "Q4" || pair === "Q5" || pair === "Q1" || pair === "Q3")
    return t(`study.${pair.toLowerCase()}${variant}.instruction`);
  return "";
}

/** Baseline materials: the raw artifacts of the run, displayed in-page so the
 *  clock keeps measuring. No VERA presentation: pretty-printed JSON only. */
function MaterialsPanel({
  token,
  runId,
  benchmarks,
}: {
  token: string | undefined;
  runId: string;
  benchmarks: string[];
}) {
  const t = useT();
  const [tab, setTab] = useState<"run" | "provenance" | "raw">("run");
  const [runDoc, setRunDoc] = useState<unknown>(null);
  const [provenance, setProvenance] = useState<unknown>(null);
  const [rawRows, setRawRows] = useState<Record<string, unknown>[] | null>(null);
  const [benchmark, setBenchmark] = useState(benchmarks[0] ?? "");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    setFailed(false);
    if (tab === "run" && runDoc === null) {
      getBenchmarkRun(token, runId)
        .then((r) => alive && setRunDoc(r.document))
        .catch(() => alive && setFailed(true));
    }
    if (tab === "provenance" && provenance === null) {
      getProvenance(token, runId)
        .then((r) => alive && setProvenance(r.provenance))
        .catch(() => alive && setFailed(true));
    }
    if (tab === "raw" && benchmark) {
      setRawRows(null);
      getRawOutputs(token ?? "", runId, benchmark, page)
        .then((r) => {
          if (!alive) return;
          setRawRows(r.rows);
          setTotal(r.total);
        })
        .catch(() => alive && setFailed(true));
    }
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, benchmark, page, runId]);

  const body =
    tab === "run" ? runDoc : tab === "provenance" ? provenance : rawRows;

  return (
    <div data-testid="study-materials" className="rounded border border-default">
      <div className="border-b border-default px-3 py-2">
        <div className="kpi-label">{t("study.materials.title")}</div>
        <p className="text-[11px] text-ink-secondary">{t("study.materials.hint")}</p>
      </div>
      <div className="flex items-center gap-2 border-b border-default px-3 py-1.5 text-xs">
        {(
          [
            ["run", "study.materials.tab_run"],
            ["provenance", "study.materials.tab_provenance"],
            ["raw", "study.materials.tab_raw"],
          ] as const
        ).map(([id, key]) => (
          <button
            key={id}
            type="button"
            data-testid={`study-materials-tab-${id}`}
            onClick={() => setTab(id)}
            className={
              tab === id
                ? "rounded bg-surface-strong px-2 py-0.5 font-medium text-ink"
                : "px-2 py-0.5 text-ink-secondary hover:text-ink"
            }
          >
            {t(key)}
          </button>
        ))}
        {tab === "raw" ? (
          <span className="ml-auto flex items-center gap-2">
            <select
              data-testid="study-materials-benchmark"
              value={benchmark}
              onChange={(e) => {
                setBenchmark(e.target.value);
                setPage(1);
              }}
              className="input py-0.5 text-xs"
            >
              {benchmarks.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="text-ink-secondary disabled:opacity-40"
            >
              ← {t("study.materials.prev")}
            </button>
            <button
              type="button"
              disabled={page * 20 >= total}
              onClick={() => setPage((p) => p + 1)}
              className="text-ink-secondary disabled:opacity-40"
            >
              {t("study.materials.next")} →
            </button>
          </span>
        ) : null}
      </div>
      <pre
        data-testid="study-materials-body"
        className="max-h-80 overflow-auto whitespace-pre-wrap break-words px-3 py-2 font-mono text-[11px] leading-relaxed text-ink"
      >
        {failed
          ? t("study.error")
          : body === null
            ? t("common.loading")
            : JSON.stringify(body, null, 2)}
      </pre>
    </div>
  );
}

function TaskFields({
  step,
  session,
  answer,
  setAnswer,
}: {
  step: Step | undefined;
  session: StudySessionInfo | null;
  answer: Record<string, unknown>;
  setAnswer: (a: Record<string, unknown>) => void;
}) {
  const t = useT();
  const set = (key: string, value: unknown) => setAnswer({ ...answer, [key]: value });
  const num = (key: string) => (value: string) =>
    set(key, value === "" ? undefined : Number(value));
  if (!step) return null;
  const pair = step.id.slice(0, 2);

  if (pair === "Q1") {
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
  if (pair === "Q2") {
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
  if (pair === "Q3") {
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
  if (pair === "Q4") {
    return (
      <Labeled label={t("study.t4.label")}>
        <input
          data-testid="study-answer-count"
          type="number"
          min={0}
          max={30}
          value={answer.count === undefined ? "" : String(answer.count)}
          onChange={(e) => num("count")(e.target.value)}
          className="input w-24"
        />
      </Labeled>
    );
  }
  if (step.id === "Q5A") {
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
  if (step.id === "Q5B") {
    return (
      <div className="flex flex-wrap gap-3">
        {(["red", "orange", "green"] as const).map((field) => (
          <Labeled key={field} label={t(`study.q5b.${field}`)}>
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
  if (pair === "Q6") {
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
          {t("study.q6.confirm")}
        </label>
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

function Choice({
  testid,
  label,
  value,
  onChange,
  options,
}: {
  testid: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: [string, string][];
}) {
  return (
    <label className="block text-sm text-ink">
      <span className="kpi-label mb-1 block">{label}</span>
      <select
        data-testid={testid}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input w-full"
      >
        <option value="" disabled>
          —
        </option>
        {options.map(([code, text]) => (
          <option key={code} value={code}>
            {text}
          </option>
        ))}
      </select>
    </label>
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
