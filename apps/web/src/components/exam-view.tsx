"use client";
import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, ArrowRight, Check, ShieldCheck } from "lucide-react";
import { api, useApi } from "@/lib/api";
import type { ExamAttempt } from "@/lib/types";
import { ErrorNotice, Loading, Meter } from "./ui";
export function ExamView({ id }: { id: string }) {
  const { data, error, reload, setData } = useApi<ExamAttempt>(
    `/exams/attempts/${id}`,
  );
  const [index, setIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [actionError, setActionError] = useState("");
  async function answer(question_id: string, answer: number) {
    const previous = data;
    setData((value) =>
      value
        ? { ...value, answers: { ...value.answers, [question_id]: answer } }
        : value,
    );
    setBusy(true);
    setStatus("Saving…");
    setActionError("");
    try {
      await api(`/exams/attempts/${id}/answer`, "PUT", { question_id, answer });
      setStatus("Answer saved");
    } catch (e) {
      setData(previous);
      setActionError((e as Error).message);
      setStatus("Not saved");
    } finally {
      setBusy(false);
    }
  }
  async function submit() {
    setBusy(true);
    setActionError("");
    try {
      setData(await api<ExamAttempt>(`/exams/attempts/${id}/submit`, "POST"));
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  if (data.result) {
    const result = data.result;
    return (
      <div className="exam-results">
        <p className="eyebrow">DIAGNOSTIC COMPLETE</p>
        <h1>Your next step is clearer.</h1>
        <h2>{data.title}</h2>
        <div className="result-score">
          <strong>
            {result.score}
            <span>%</span>
          </strong>
          <p>
            This is a snapshot of conceptual reasoning.
            <br />
            Practical engineering needs additional evidence.
          </p>
        </div>
        {result.evaluation && (
          <section className="notice" aria-label="Evaluation outcome">
            <h2>{result.evaluation.label}</h2>
            <p>
              {result.correct}/{result.total} correct. Target:{" "}
              {result.evaluation.overall_target}% overall and{" "}
              {result.evaluation.category_target}% in each topic.
            </p>
            <p>{result.evaluation.note}</p>
          </section>
        )}
        <div className="panel">
          <h2>Performance by category</h2>
          {result.categories.map((c) => (
            <div className="skill-row" key={c.skill}>
              <div>
                <span>{c.skill}</span>
                <small>
                  {c.correct}/{c.total} correct · {c.score}%
                </small>
              </div>
              <Meter value={c.score} label={c.skill} />
            </div>
          ))}
        </div>
        <section className="panel">
          <h2>Recommended next steps</h2>
          {result.study_recommendations?.map((resource) => (
            <a
              className="lesson-row"
              href={resource.url}
              key={resource.skill}
              target="_blank"
              rel="noopener noreferrer"
            >
              <span>
                {resource.skill}: {resource.title}
              </span>
              <ArrowRight size={16} />
            </a>
          ))}
          {result.recommendations.length ? (
            result.recommendations.map((l) => (
              <Link className="lesson-row" href={`/lessons/${l.id}`} key={l.id}>
                <span>{l.title}</span>
                <ArrowRight size={16} />
              </Link>
            ))
          ) : !result.study_recommendations?.length ? (
            <p>
              Strong work on this diagnostic. Continue with implementation
              practice and expand your coverage.
            </p>
          ) : null}
          {result.practical_followup && (
            <>
              <h3 className="practical-followup">
                Practical follow-up · not automatically graded
              </h3>
              <p className="muted">{result.practical_followup}</p>
            </>
          )}
        </section>
        <section className="panel">
          <h2>Review your reasoning</h2>
          {data.questions.map((q) => {
            const r = result.explanations.find((e) => e.id === q.id)!;
            return (
              <details className="answer-review" key={q.id}>
                <summary>
                  <span className={`badge ${r.correct ? "green" : ""}`}>
                    {r.correct ? "Correct" : "Revisit"}
                  </span>
                  {q.prompt}
                </summary>
                {q.code && (
                  <pre className="assessment-code">
                    <code>{q.code}</code>
                  </pre>
                )}
                <p>Your answer: {q.options[data.answers[q.id]]}</p>
                <p>
                  <strong>Reference:</strong> {q.options[r.answer]}
                </p>
                <p>{r.explanation}</p>
              </details>
            );
          })}
        </section>
        <Link className="button primary" href="/exams">
          Back to assessments
          <ArrowRight size={16} />
        </Link>
      </div>
    );
  }
  const question = data.questions[index];
  const answered = Object.keys(data.answers).length;
  return (
    <div className="exam-taking">
      <div className="exam-top">
        <span>
          <ShieldCheck size={17} />
          FOCUS MODE
        </span>
        <small role="status">
          {status || "Untimed · resume whenever you need"}
        </small>
      </div>
      <h1>{data.title}</h1>
      <div className="exam-progress">
        <span>
          {answered} of {data.questions.length} answered
        </span>
        <span>Question {index + 1}</span>
      </div>
      <Meter
        value={(answered / data.questions.length) * 100}
        label="Assessment completion"
      />
      <div className="question-numbers" aria-label="Question navigation">
        {data.questions.map((q, i) => (
          <button
            key={q.id}
            aria-label={`Question ${i + 1}${data.answers[q.id] !== undefined ? ", answered" : ""}`}
            aria-current={index === i ? "step" : undefined}
            className={
              index === i
                ? "current"
                : data.answers[q.id] !== undefined
                  ? "answered"
                  : ""
            }
            onClick={() => setIndex(i)}
            disabled={busy}
          >
            {i + 1}
          </button>
        ))}
      </div>
      <section className="panel question-panel">
        <p className="eyebrow">{question.skill}</p>
        <h2>{question.prompt}</h2>
        {question.code && (
          <pre className="assessment-code" aria-label="Python code to analyze">
            <code>{question.code}</code>
          </pre>
        )}
        <fieldset className="answer-options">
          <legend className="sr-only">Choose an answer</legend>
          {question.options.map((option, i) => (
            <label
              key={i}
              className={data.answers[question.id] === i ? "chosen" : ""}
            >
              <input
                type="radio"
                name={question.id}
                checked={data.answers[question.id] === i}
                disabled={busy}
                onChange={() => answer(question.id, i)}
              />
              <span className="option-letter">
                {String.fromCharCode(65 + i)}
              </span>
              <span>{option}</span>
            </label>
          ))}
        </fieldset>
        {actionError && <ErrorNotice message={actionError} />}
        <div className="exam-controls">
          <button
            className="button secondary"
            disabled={index === 0 || busy}
            onClick={() => setIndex((v) => v - 1)}
          >
            <ArrowLeft size={15} />
            Previous
          </button>
          {index < data.questions.length - 1 ? (
            <button
              className="button primary"
              disabled={busy}
              onClick={() => setIndex((v) => v + 1)}
            >
              Next question
              <ArrowRight size={15} />
            </button>
          ) : (
            <button
              className="button primary"
              disabled={busy || answered !== data.questions.length}
              onClick={submit}
            >
              Submit diagnostic
              <Check size={15} />
            </button>
          )}
        </div>
      </section>
      <p className="muted small">
        Answers and explanations are available after submission. Your selections
        are saved to your account.
      </p>
    </div>
  );
}
