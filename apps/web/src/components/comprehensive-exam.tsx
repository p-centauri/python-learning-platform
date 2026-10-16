"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, useApi } from "@/lib/api";
import type { CodingResult, ExamResult } from "@/lib/types";
import { ErrorNotice, Loading, Meter } from "./ui";

type Answer = number | number[] | string;
type Question = {
  id: string;
  skill: string;
  prompt: string;
  kind?: "single" | "multiple" | "short";
  options?: string[];
  code?: string;
  min_length?: number;
  max_length?: number;
};
type Run = {
  id: number;
  code: string;
  source_digest: string;
  result: CodingResult;
  created_at: string;
};
export type ComprehensiveAttempt = {
  id: number;
  exam_id: string;
  title: string;
  status: string;
  minutes: number;
  mode: "knowledge" | "repair" | "design";
  started_at: string;
  server_time: string;
  questions: Question[];
  answers: Record<string, Answer>;
  workspace: {
    flags?: string[];
    position?: number;
    code?: string;
    stage?: number;
  };
  stage: { index: number; count: number; title: string } | null;
  execution: {
    starter: string;
    prompt: string;
    check_count: number;
    download_url: string;
  } | null;
  result:
    | (Omit<ExamResult, "explanations"> & {
        explanations?: {
          id: string;
          correct: boolean;
          answer: number | number[];
          explanation: string;
        }[];
        review_submission_id: number;
        review_project: string;
        review_note: string;
        mode?: string;
        objective?: CodingResult;
        manual_count: number;
        note?: string;
        score_note?: string;
      })
    | null;
};

function SavedText({
  value,
  label,
  max,
  save,
  pending,
}: {
  value: string;
  label: string;
  max: number;
  save: (s: string) => Promise<void>;
  pending: (v: boolean) => void;
}) {
  const [text, setText] = useState(value);
  const [saved, setSaved] = useState(value);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    pending(text !== saved || busy);
    if (text === saved || busy || error) return;
    const timer = setTimeout(() => {
      setBusy(true);
      void save(text)
        .then(() => {
          setSaved(text);
          setError("");
        })
        .catch((e) => setError((e as Error).message))
        .finally(() => setBusy(false));
    }, 650);
    return () => clearTimeout(timer);
  }, [text, saved, busy, error, retry, save, pending]);
  useEffect(() => () => pending(false), [pending]);
  return (
    <div>
      <label>
        {label}
        <textarea
          rows={label === "Practical source" ? 18 : 8}
          value={text}
          maxLength={max}
          onChange={(e) => {
            setText(e.target.value);
            setError("");
          }}
          spellCheck={label !== "Practical source"}
        />
      </label>
      <p role="status" className="small">
        {error
          ? "Not saved — keep this page open"
          : text === saved && !busy
            ? "Saved to your account"
            : "Saving changes…"}{" "}
        · {text.length}/{max} characters
      </p>
      {error && (
        <>
          <ErrorNotice message={error} />
          <button
            className="button secondary"
            onClick={() => {
              setError("");
              setRetry((n) => n + 1);
            }}
          >
            Retry saving
          </button>
        </>
      )}
    </div>
  );
}

export function ComprehensiveExam({ id }: { id: string }) {
  const { data, error, reload, setData } = useApi<ComprehensiveAttempt>(
    `/exams/attempts/${id}`,
  );
  const {
    data: runs,
    reload: reloadRuns,
    error: runLoadError,
  } = useApi<Run[]>(`/exams/attempts/${id}/runs`);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState(false);
  const [sourcePending, setSourcePending] = useState(false);
  const [actionError, setActionError] = useState("");
  const [now, setNow] = useState(Date.now());
  const [key, setKey] = useState<string | null>(null);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  async function action(fn: () => Promise<void>) {
    setBusy(true);
    setActionError("");
    try {
      await fn();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  const row = data;
  const blocked = busy || pending || sourcePending;
  const position = row.workspace.position || 0;
  const q = row.questions[position] || row.questions[0];
  async function saveAnswer(question: Question, value: Answer) {
    const previous = row.answers[question.id];
    setData((old) =>
      old ? { ...old, answers: { ...old.answers, [question.id]: value } } : old,
    );
    try {
      await api(`/exams/attempts/${id}/answer`, "PUT", {
        question_id: question.id,
        answer: value,
      });
    } catch (error) {
      setData((old) => {
        if (!old) return old;
        const answers = { ...old.answers };
        if (previous === undefined) delete answers[question.id];
        else answers[question.id] = previous;
        return { ...old, answers };
      });
      throw error;
    }
  }
  async function workspace(
    changes: Partial<ComprehensiveAttempt["workspace"]>,
  ) {
    const flags = changes.flags ?? row.workspace.flags ?? [];
    const pos = changes.position ?? row.workspace.position ?? 0;
    await api(`/exams/attempts/${id}/workspace`, "PUT", {
      flags,
      position: pos,
      ...(changes.code !== undefined ? { code: changes.code } : {}),
    });
    setData((old) =>
      old ? { ...old, workspace: { ...old.workspace, ...changes } } : old,
    );
  }
  const result = row.result;
  if (result)
    return (
      <div className="exam-results">
        <p className="eyebrow">FIXED SUBMITTED EVIDENCE</p>
        <h1>{row.title}</h1>
        <section className="panel">
          <h2>
            {result.score === null
              ? "Manual review required"
              : `${result.score}% on objective questions`}
          </h2>
          <p>{result.score_note || result.note}</p>
          <p>{result.review_note}</p>
          {result.objective && (
            <p>
              Isolated checks: {result.objective.passed}/
              {result.objective.total}. This finite result is separate from
              reviewer judgment.
            </p>
          )}
          <p>
            {result.manual_count} written responses saved for review. Passing
            checks never awards practical or senior mastery.
          </p>
          <Link
            className="button primary"
            href={`/projects/${result.review_project}`}
          >
            Open fixed evidence and request review
          </Link>
        </section>
        {result.categories?.length > 0 && (
          <section className="panel">
            <h2>Objective performance by category</h2>
            {result.categories.map((c) => (
              <p key={c.skill}>
                {c.skill}: {c.correct}/{c.total} · {c.score}%
              </p>
            ))}
            <h3>Strengths and areas to revisit</h3>
            <p>
              Categories at or above 80% met this provisional knowledge target;
              lower categories need practice. Five objective questions per area
              are a small sample.
            </p>
            {result.recommendations?.map((l) => (
              <Link className="lesson-row" key={l.id} href={`/lessons/${l.id}`}>
                {l.title}
              </Link>
            ))}
          </section>
        )}
        <section className="panel">
          <h2>Your submitted responses</h2>
          {row.questions.map((question) => {
            const reference = result.explanations?.find(
              (e) => e.id === question.id,
            );
            const selected = row.answers[question.id];
            const label = (value: Answer) =>
              Array.isArray(value)
                ? value.map((i) => question.options?.[i]).join("; ")
                : typeof value === "number"
                  ? question.options?.[value]
                  : value;
            return (
              <details key={question.id} className="answer-review">
                <summary>{question.prompt}</summary>
                <p className="preserve-lines">
                  Your response: {label(selected)}
                </p>
                {reference ? (
                  <>
                    <p>
                      {reference.correct ? "Correct" : "Revisit"} · Reference:{" "}
                      {label(reference.answer)}
                    </p>
                    <p>{reference.explanation}</p>
                  </>
                ) : (
                  <p>Written judgment awaits separate rubric review.</p>
                )}
              </details>
            );
          })}
        </section>
        <Link className="button secondary" href="/exams">
          Back to assessments
        </Link>
      </div>
    );
  const elapsed = Math.max(
    0,
    Math.floor((now - Date.parse(row.started_at)) / 60000),
  );
  const committed =
    row.mode === "design" &&
    row.stage &&
    position < (row.stage.index === 0 ? 0 : row.stage.index + 3);
  return (
    <div className="exam-taking">
      <Link className="text-link" href="/exams">
        ← Assessment history
      </Link>
      <h1>{row.title}</h1>
      <div className="notice">
        <p>
          {elapsed} minutes since start · suggested study budget {row.minutes}{" "}
          minutes. Includes breaks; advisory timer, no forced expiry. Resume
          from your account.
        </p>
        <p>
          Expected answers stay private until submission. Written reasoning uses
          separate human/self review.
        </p>
      </div>
      {actionError && <ErrorNotice message={actionError} />}
      {row.stage && (
        <section className="panel">
          <h2>
            Stage {row.stage.index + 1}/{row.stage.count}: {row.stage.title}
          </h2>
          <p>
            Commit the current responses to reveal the next incident. Earlier
            stages stay fixed. Follow-up details are withheld until their stage.
          </p>
        </section>
      )}
      {row.execution && (
        <section className="panel">
          <h2>Repair the application</h2>
          <p>{row.execution.prompt}</p>
          <a
            className="button secondary"
            href={row.execution.download_url}
            download
          >
            Download broken application and public tests
          </a>
          <SavedText
            key={`source-${id}`}
            value={row.workspace.code ?? row.execution.starter}
            label="Practical source"
            max={12000}
            pending={setSourcePending}
            save={async (code) => {
              await workspace({ code });
              setKey(null);
            }}
          />
          <button
            className="button primary"
            disabled={blocked || !row.workspace.code?.trim()}
            onClick={() =>
              void action(async () => {
                const request_key = key || crypto.randomUUID();
                setKey(request_key);
                await api(`/exams/attempts/${id}/runs`, "POST", {
                  request_key,
                });
                setKey(null);
                await reloadRuns();
              })
            }
          >
            {busy ? "Running isolated checks…" : "Run isolated checks"}
          </button>
          <p className="small">
            8 runs per 10 minutes · 64 per attempt. Exact saved source runs in
            fresh containers. A matching run is required to submit; failed
            checks may be submitted honestly.
          </p>
          {runLoadError && (
            <ErrorNotice message={runLoadError} retry={reloadRuns} />
          )}
          {runs?.map((run) => (
            <details key={run.id} className="answer-review">
              <summary>
                Run #{run.id}: {run.result.passed}/{run.result.total} passed
              </summary>
              <p>
                Source digest:{" "}
                <code className="break-word">{run.source_digest}</code>
              </p>
              {run.result.checks.map((check, i) => (
                <p key={i}>
                  {check.name}: {check.status}
                  {check.public && check.message ? ` · ${check.message}` : ""}
                </p>
              ))}
              <pre className="test-output">{run.code}</pre>
            </details>
          ))}
        </section>
      )}
      <div className="exam-progress">
        <span>
          {Object.keys(row.answers).length}/{row.questions.length} visible
          responses saved
        </span>
        <span>Question {position + 1}</span>
      </div>
      <Meter
        value={(Object.keys(row.answers).length / row.questions.length) * 100}
        label="Saved response completion"
      />
      <nav className="question-numbers" aria-label="Question navigation">
        {row.questions.map((question, i) => (
          <button
            key={question.id}
            disabled={blocked}
            aria-current={position === i ? "step" : undefined}
            aria-label={`Question ${i + 1}${row.workspace.flags?.includes(question.id) ? ", flagged" : ""}${row.answers[question.id] !== undefined ? ", saved" : ""}`}
            className={
              position === i
                ? "current"
                : row.answers[question.id] !== undefined
                  ? "answered"
                  : ""
            }
            onClick={() => void action(() => workspace({ position: i }))}
          >
            {i + 1}
            {row.workspace.flags?.includes(question.id) ? " ⚑" : ""}
          </button>
        ))}
      </nav>
      {q && (
        <section className="panel question-panel">
          <p className="eyebrow">{q.skill}</p>
          <h2>{q.prompt}</h2>
          {q.code && <pre className="assessment-code">{q.code}</pre>}
          <button
            className="text-button"
            disabled={blocked}
            aria-pressed={row.workspace.flags?.includes(q.id) || false}
            onClick={() =>
              void action(() =>
                workspace({
                  flags: row.workspace.flags?.includes(q.id)
                    ? row.workspace.flags.filter((f) => f !== q.id)
                    : [...(row.workspace.flags || []), q.id],
                }),
              )
            }
          >
            {row.workspace.flags?.includes(q.id)
              ? "Remove review flag"
              : "Flag for review"}
          </button>
          {q.kind === "short" ? (
            committed ? (
              <>
                <p className="notice">Committed stage · response is fixed.</p>
                <p className="preserve-lines">{row.answers[q.id]}</p>
              </>
            ) : (
              <>
                <p className="small">
                  At least {q.min_length} characters on submission. Explain your
                  reasoning simply and cite concrete evidence.
                </p>
                <SavedText
                  key={q.id}
                  value={String(row.answers[q.id] ?? "")}
                  label="Written response"
                  max={q.max_length || 1000}
                  pending={setPending}
                  save={(text) => saveAnswer(q, text)}
                />
              </>
            )
          ) : (
            <fieldset className="answer-options" disabled={blocked}>
              <legend>
                {q.kind === "multiple"
                  ? "Select all that apply (exact set required)"
                  : "Choose one answer"}
              </legend>
              {q.options?.map((option, i) => {
                const selected = row.answers[q.id];
                const checked = Array.isArray(selected)
                  ? selected.includes(i)
                  : selected === i;
                return (
                  <label key={i} className={checked ? "chosen" : ""}>
                    <input
                      name={q.id}
                      type={q.kind === "multiple" ? "checkbox" : "radio"}
                      checked={checked}
                      onChange={() =>
                        void action(async () => {
                          if (q.kind === "multiple") {
                            const existing = Array.isArray(selected)
                              ? selected
                              : [];
                            const next = checked
                              ? existing.filter((x) => x !== i)
                              : [...existing, i];
                            if (!next.length) {
                              await saveAnswer(q, []);
                              return;
                            }
                            await saveAnswer(q, next);
                          } else await saveAnswer(q, i);
                        })
                      }
                    />
                    <span>{option}</span>
                  </label>
                );
              })}
            </fieldset>
          )}
          <div className="exam-controls">
            <button
              className="button secondary"
              disabled={blocked || position === 0}
              onClick={() =>
                void action(() => workspace({ position: position - 1 }))
              }
            >
              Previous
            </button>
            <button
              className="button secondary"
              disabled={blocked || position === row.questions.length - 1}
              onClick={() =>
                void action(() => workspace({ position: position + 1 }))
              }
            >
              Next question
            </button>
          </div>
        </section>
      )}
      <div className="submission-actions">
        {row.stage && row.stage.index < row.stage.count - 1 ? (
          <button
            className="button primary"
            disabled={blocked}
            onClick={() =>
              void action(async () => {
                await api(`/exams/attempts/${id}/advance`, "POST");
                await reload();
              })
            }
          >
            Commit this stage and reveal next incident
          </button>
        ) : (
          <button
            className="button primary"
            disabled={blocked}
            onClick={() =>
              void action(async () =>
                setData(
                  await api<ComprehensiveAttempt>(
                    `/exams/attempts/${id}/submit`,
                    "POST",
                  ),
                ),
              )
            }
          >
            Submit and freeze exam evidence
          </button>
        )}
      </div>
      <p className="small muted">
        Submission fixes all responses and matching source/check evidence. A
        retake reuses authored content and may reflect familiarity.
      </p>
    </div>
  );
}
