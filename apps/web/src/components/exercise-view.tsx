"use client";
import Link from "next/link";
import { useState } from "react";
import { Lightbulb, ArrowRight, CheckCircle2 } from "lucide-react";
import { api, useApi } from "@/lib/api";
import type { ExerciseDetail } from "@/lib/types";
import { DateLabel, ErrorNotice, Loading } from "./ui";
export function ExerciseView({ id, review }: { id: string; review: boolean }) {
  const { data, error, reload } = useApi<ExerciseDetail>(`/exercises/${id}`);
  const [selected, setSelected] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [feedback, setFeedback] = useState<{
    score: number;
    feedback: string;
    solution: string | null;
    review_topic_id?: string;
  } | null>(null);
  async function action(kind: "hint" | "reveal" | "attempts") {
    setBusy(true);
    setActionError("");
    try {
      if (kind === "attempts") {
        setFeedback(
          await api(`/exercises/${id}/${kind}`, "POST", {
            answer: selected,
            review,
          }),
        );
      } else {
        await api(`/exercises/${id}/${kind}`, "POST");
      }
      await reload();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <div className="exercise-workspace">
      <Link
        className="back-link"
        href={review ? "/review" : `/lessons/${data.lesson_id}`}
      >
        ← {review ? "Spaced review" : "Back to lesson"}
      </Link>
      <div className="exercise-meta">
        <span className="badge green">{data.kind}</span>
        <span className="badge">{data.difficulty}</span>
        <span>{data.skill}</span>
        {review && <span className="badge">Retrieval review</span>}
      </div>
      <h1>{data.title}</h1>
      <p className="exercise-subtitle">
        Reason through the failure. Then choose the strongest answer.
      </p>
      <div className="exercise-layout">
        <section className="panel question-panel">
          <p className="eyebrow">THE SCENARIO</p>
          <h2>{data.prompt}</h2>
          <fieldset className="answer-options">
            <legend className="sr-only">Choose your answer</legend>
            {data.options.map((option, index) => (
              <label key={index} className={selected === index ? "chosen" : ""}>
                <input
                  type="radio"
                  name="answer"
                  value={index}
                  checked={selected === index}
                  onChange={() => {
                    setSelected(index);
                    setFeedback(null);
                  }}
                  disabled={busy || !!(review && feedback)}
                />
                <span className="option-letter">
                  {String.fromCharCode(65 + index)}
                </span>
                <span>{option}</span>
              </label>
            ))}
          </fieldset>
          {actionError && <ErrorNotice message={actionError} />}
          <button
            className="button primary"
            disabled={selected === null || busy || !!(review && feedback)}
            onClick={() => action("attempts")}
          >
            {busy
              ? "Saving…"
              : review && feedback
                ? "Review recorded"
                : "Submit answer"}
            <ArrowRight size={16} />
          </button>
          {feedback && (
            <div
              className={`feedback ${feedback.score ? "correct" : "incorrect"}`}
              role="status"
            >
              <h3>
                {feedback.score ? (
                  <>
                    <CheckCircle2 size={18} />
                    Well reasoned.
                  </>
                ) : (
                  "There’s another failure mode to consider."
                )}
              </h3>
              <p>{feedback.feedback}</p>
              {feedback.review_topic_id && (
                <Link
                  className="text-link"
                  href={`/review/${feedback.review_topic_id}`}
                >
                  Try a different short-answer question →
                </Link>
              )}
            </div>
          )}
          {!review && data.solution && (
            <div className="solution">
              <p className="eyebrow">REFERENCE REASONING</p>
              <p>{data.solution}</p>
            </div>
          )}
          {review && feedback?.solution && (
            <div className="solution">
              <p>{feedback.solution}</p>
              <Link className="text-link" href="/review">
                Back to review queue →
              </Link>
            </div>
          )}
        </section>
        <aside>
          <section className="panel hint-panel">
            <Lightbulb size={21} />
            <h3>A nudge, not the answer.</h3>
            <p>
              Try to reason independently first. Hints reduce the evidence score
              for this exercise.
            </p>
            {data.hints.map((hint, index) => (
              <div className="hint" key={hint}>
                <small>HINT {index + 1}</small>
                <p>{hint}</p>
              </div>
            ))}
            <button
              className="button secondary"
              disabled={busy || data.hints.length >= 3 || review}
              onClick={() => action("hint")}
            >
              {review
                ? "Hints off during review"
                : `Reveal hint ${Math.min(data.hints.length + 1, 3)} of 3`}
            </button>
            {!review && !data.solution && (
              <details className="reveal-details">
                <summary>Still stuck?</summary>
                <p>
                  Revealing the explanation ends mastery credit for future
                  attempts on this question.
                </p>
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={() => action("reveal")}
                >
                  Reveal explanation
                </button>
              </details>
            )}
          </section>
          <section className="attempt-history">
            <h3>Attempt history</h3>
            {data.attempts.length ? (
              data.attempts.slice(0, 8).map((a) => (
                <div key={a.id}>
                  <span>
                    {a.score ? "Correct" : "Needs work"}
                    {a.is_review ? " · Review" : ""}
                  </span>
                  <small>
                    <DateLabel value={a.created_at} /> · {a.hints_used} hints
                  </small>
                </div>
              ))
            ) : (
              <p>No attempts yet. A wrong answer is useful evidence too.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
