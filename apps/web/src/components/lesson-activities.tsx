"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api, useApi } from "@/lib/api";
import type {
  CheckpointAttempt,
  LessonActivities,
  LessonCheckpoint,
} from "@/lib/types";
import { DateLabel, ErrorNotice, Loading } from "./ui";

function Checkpoint({
  lessonId,
  question,
  version,
  history,
  onRecorded,
  reload,
}: {
  lessonId: string;
  question: LessonCheckpoint;
  version: string;
  history: CheckpointAttempt[];
  onRecorded: (row: CheckpointAttempt) => void;
  reload: () => void;
}) {
  const latest = history.find((row) => row.version === version);
  const [answer, setAnswer] = useState<number | null>(latest?.answer ?? null);
  const [result, setResult] = useState<CheckpointAttempt | null>(
    latest ?? null,
  );
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const requestKey = useRef("");
  async function check() {
    if (answer === null || busy) return;
    setBusy(true);
    setError("");
    requestKey.current ||= crypto.randomUUID();
    try {
      const row = await api<CheckpointAttempt>(
        `/lesson-activities/${lessonId}/checkpoints/${question.id}/attempts`,
        "POST",
        { answer, version, request_key: requestKey.current },
      );
      setResult(row);
      onRecorded(row);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="checkpoint panel" aria-label={question.title}>
      <p className="eyebrow">
        {question.kind === "predict" ? "PAUSE AND PREDICT" : "SPOT THE BUG"}
      </p>
      <h3>{question.title}</h3>
      <p>{question.prompt}</p>
      <pre className="recall-code">{question.code}</pre>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void check();
        }}
      >
        <fieldset disabled={busy || !!result}>
          <legend>
            Choose your {question.kind === "predict" ? "prediction" : "fix"}
          </legend>
          <div className="checkpoint-options">
            {question.options.map((option, index) => (
              <label key={index} className={answer === index ? "selected" : ""}>
                <input
                  type="radio"
                  name={question.id}
                  checked={answer === index}
                  onChange={() => {
                    setAnswer(index);
                    requestKey.current = "";
                  }}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        </fieldset>
        {error && <ErrorNotice message={error} retry={reload} />}
        {!result && (
          <button
            className="button primary"
            type="submit"
            disabled={busy || answer === null}
          >
            {busy ? "Checking…" : "Check my answer"}
          </button>
        )}
      </form>
      {result && (
        <section
          className="checkpoint-feedback"
          aria-label={`${question.title} feedback`}
          role="status"
        >
          <h4>
            {result.result.correct
              ? "That matches the checkpoint."
              : "Try tracing it once more."}
          </h4>
          <p>
            <strong>Expected:</strong> {result.result.expected}
          </p>
          <p>{result.result.explanation}</p>
          <p className="small muted">
            Saved guided feedback. Retrying the same question is practice, not
            new mastery or retention evidence.
          </p>
          <button
            className="button secondary"
            onClick={() => {
              setResult(null);
              setAnswer(null);
              requestKey.current = "";
              setError("");
            }}
          >
            Try this checkpoint again
          </button>
        </section>
      )}
      {!!history.length && (
        <details className="checkpoint-history">
          <summary>
            Saved attempts ({history.length} in recent lesson history)
          </summary>
          {history.map((row) => (
            <div className="recall-history" key={row.id}>
              <p>
                <strong>
                  {row.result.correct ? "Matched" : "Needs another look"}
                </strong>{" "}
                · <DateLabel value={row.created_at} /> · {row.version}
              </p>
              <p>{row.question.prompt}</p>
              <pre className="recall-code">{row.question.code}</pre>
              <p>Your choice: {row.question.options[row.answer]}</p>
              <p>Expected: {row.result.expected}</p>
              <p>{row.result.explanation}</p>
            </div>
          ))}
        </details>
      )}
    </article>
  );
}

export function LessonActivitiesView({ lessonId }: { lessonId: string }) {
  const { data, error, reload, setData } = useApi<LessonActivities>(
    `/lesson-activities/${lessonId}`,
  );
  useEffect(() => {
    if (!data || !window.location.hash.startsWith("#lesson-")) return;
    const target = document.getElementById(window.location.hash.slice(1));
    target?.scrollIntoView();
    target?.focus({ preventScroll: true });
  }, [data?.version, lessonId]);
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  function recorded(row: CheckpointAttempt) {
    setData((v) =>
      v
        ? {
            ...v,
            history: [row, ...v.history.filter((r) => r.id !== row.id)].slice(
              0,
              v.history_limit,
            ),
          }
        : v,
    );
  }
  return (
    <>
      <section className="lesson-interactive" aria-labelledby="lesson-diagram">
        <h2 id="lesson-diagram" tabIndex={-1}>
          See the idea
        </h2>
        <figure className="lesson-diagram">
          <h3>{data.diagram.title}</h3>
          <ol>
            {data.diagram.steps.map((step, index) => (
              <li key={step.label}>
                <span className="diagram-number" aria-hidden="true">
                  {index + 1}
                </span>
                <strong>{step.label}</strong>
                <p>{step.detail}</p>
              </li>
            ))}
          </ol>
          <figcaption>{data.diagram.caption}</figcaption>
        </figure>
      </section>
      <section
        className="lesson-interactive"
        aria-labelledby="lesson-checkpoints"
      >
        <h2 id="lesson-checkpoints" tabIndex={-1}>
          Pause and try it
        </h2>
        <p>{data.note}</p>
        <p className="small muted">
          Choose a prediction or a fix, then check the explanation. These tasks
          do not run your code. For executable practice, use the{" "}
          <Link href="/coding">coding and SQL lab</Link>. The latest{" "}
          {data.history_limit} recorded attempts for this lesson are available
          here.
        </p>
        {data.checkpoints.map((question) => (
          <Checkpoint
            key={`${data.version}-${question.id}`}
            lessonId={lessonId}
            question={question}
            version={data.version}
            history={data.history.filter(
              (row) => row.checkpoint_id === question.id,
            )}
            onRecorded={recorded}
            reload={reload}
          />
        ))}
      </section>
      <section className="lesson-interactive" aria-labelledby="lesson-glossary">
        <h2 id="lesson-glossary" tabIndex={-1}>
          Words in this lesson
        </h2>
        <dl className="lesson-glossary">
          {data.glossary.map((term) => (
            <div key={term.id}>
              <dt>
                <Link href={`/glossary#${term.id}`}>{term.term}</Link>
              </dt>
              <dd>{term.definition}</dd>
            </div>
          ))}
        </dl>
        <Link href="/glossary" className="text-link">
          Explore the full glossary →
        </Link>
      </section>
    </>
  );
}
