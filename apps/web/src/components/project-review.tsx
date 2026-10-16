"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { ProjectRubric, ProjectSubmission } from "@/lib/types";
import { DateLabel, ErrorNotice } from "./ui";

export function Rubric({ rubric }: { rubric: ProjectRubric }) {
  return (
    <section
      className="panel submission-section"
      aria-label="Project review rubric"
    >
      <p className="overline">REVIEW EXPECTATIONS</p>
      <h2>What the reviewer will check</h2>
      <p>{rubric.note}</p>
      <ol className="rubric-criteria">
        {rubric.criteria.map((criterion) => (
          <li key={criterion.id}>
            <strong>{criterion.title}</strong>
            <p>{criterion.expectation}</p>
          </li>
        ))}
      </ol>
      <details>
        <summary>How the 0–3 ratings work</summary>
        <dl className="rubric-scale">
          {rubric.scale.map((entry) => (
            <div key={entry.score}>
              <dt>
                {entry.score} · {entry.label}
              </dt>
              <dd>{entry.description}</dd>
            </div>
          ))}
        </dl>
      </details>
      <p className="small muted">
        Rubric version: {rubric.version}. Each submission keeps its own rubric.
      </p>
    </section>
  );
}

export function SubmissionEvidence({ row }: { row: ProjectSubmission }) {
  const artifact = row.artifact;
  return (
    <section
      className="panel submission-section"
      aria-label="Submitted implementation"
    >
      <p className="overline">FIXED SUBMISSION · VERSION {row.revision}</p>
      <h2>Implementation evidence</h2>
      {artifact.repository_url && (
        <a
          className="text-link"
          href={artifact.repository_url}
          target="_blank"
          rel="noreferrer"
        >
          Open repository ↗
        </a>
      )}
      <p className="submission-reference">
        Revision reference: <code>{artifact.revision_ref}</code>
      </p>
      {artifact.change_summary && (
        <>
          <h3>What changed</h3>
          <p className="preserve-lines">{artifact.change_summary}</p>
        </>
      )}
      <h3>Design explanation</h3>
      <p className="preserve-lines">{artifact.design_notes}</p>
      <h3>Implementation evidence</h3>
      <p className="preserve-lines">{artifact.evidence}</p>
      {artifact.exam_evidence && (
        <section aria-label="Fixed exam attachment">
          <h3>
            Fixed exam attachment · attempt #{artifact.exam_evidence.attempt_id}
          </h3>
          <p>
            Content version: {artifact.exam_evidence.version}. Responses and
            source came from the submitted exam. Reviewer judgments remain
            separate.
          </p>
          {artifact.exam_evidence.responses.map((response) => (
            <details key={response.id}>
              <summary>{response.prompt}</summary>
              <p className="preserve-lines">
                {Array.isArray(response.answer)
                  ? response.answer.join(", ")
                  : response.answer}
              </p>
            </details>
          ))}
          {artifact.exam_evidence.source && (
            <details>
              <summary>Submitted source</summary>
              <pre className="test-output">{artifact.exam_evidence.source}</pre>
            </details>
          )}
          {artifact.exam_evidence.objective && (
            <p>
              Isolated finite checks: {artifact.exam_evidence.objective.passed}/
              {artifact.exam_evidence.objective.total}. Private expected outputs
              are withheld. This is independent of manual review.
            </p>
          )}
        </section>
      )}
      <h3>Local tests — learner-reported</h3>
      <p>
        {artifact.test_status === "not-run"
          ? "Not run / no result reported"
          : artifact.test_status === "passed"
            ? "Reported as passed"
            : "Reported as failed"}
        . The academy has not executed or verified this output.
      </p>
      {artifact.test_command && <pre>{artifact.test_command}</pre>}
      {artifact.test_output && (
        <pre className="test-output">{artifact.test_output}</pre>
      )}
    </section>
  );
}

export function FeedbackHistory({ row }: { row: ProjectSubmission }) {
  return (
    <section
      className="panel submission-section"
      aria-label="Recorded feedback"
    >
      <h2>Feedback for version {row.revision}</h2>
      {!row.feedback.length && (
        <p>
          No feedback yet. Add a self-review or invite a reviewer after
          submitting.
        </p>
      )}
      {row.feedback.map((feedback) => (
        <article className="recorded-feedback" key={feedback.id}>
          <div className="submission-row">
            <h3>
              {feedback.kind === "self" ? "Self-review" : "Human review"} ·{" "}
              {feedback.reviewer_name}
            </h3>
            <DateLabel value={feedback.created_at} />
          </div>
          <p className="badge">
            {feedback.outcome === "meets-rubric"
              ? "Meets stated rubric"
              : "Changes requested"}
          </p>
          <p className="preserve-lines">{feedback.summary}</p>
          <dl className="feedback-ratings">
            {row.rubric.criteria.map((criterion) => (
              <div key={criterion.id}>
                <dt>
                  {criterion.title} · {feedback.ratings[criterion.id].score}/3
                </dt>
                <dd className="preserve-lines">
                  {feedback.ratings[criterion.id].evidence}
                </dd>
              </div>
            ))}
          </dl>
          <h4>Next actions</h4>
          <p className="preserve-lines">{feedback.next_steps}</p>
          <p className="small muted">
            {feedback.kind === "self"
              ? "Your own assessment."
              : "Judgment recorded by an invited signed-in account; reviewer qualifications are not verified."}{" "}
            This review does not increase mastery.
          </p>
        </article>
      ))}
    </section>
  );
}

export function ReviewForm({
  row,
  onSaved,
}: {
  row: ProjectSubmission;
  onSaved: (row: ProjectSubmission) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!row.can_review || row.status !== "submitted") return null;
  const title = row.is_owner ? "Add a self-review" : "Review this submission";
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const ratings = Object.fromEntries(
      row.rubric.criteria.map((criterion) => [
        criterion.id,
        {
          score: Number(form.get(`score-${criterion.id}`)),
          evidence: form.get(`evidence-${criterion.id}`),
        },
      ]),
    );
    setBusy(true);
    setError("");
    try {
      onSaved(
        await api<ProjectSubmission>(
          `/project-submissions/${row.id}/feedback`,
          "POST",
          {
            ratings,
            summary: form.get("summary"),
            next_steps: form.get("next_steps"),
          },
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      className="panel submission-section submission-form"
      aria-label={title}
      onSubmit={submit}
    >
      <h2>{title}</h2>
      <p>
        Read the exact repository revision, inspect the evidence, then explain
        each rating. Feedback is fixed when recorded. Use a new submission
        version for another review.
      </p>
      {error && <ErrorNotice message={error} />}
      <fieldset disabled={busy}>
        {row.rubric.criteria.map((criterion) => (
          <div className="rating-field" key={criterion.id}>
            <h3>{criterion.title}</h3>
            <p>{criterion.expectation}</p>
            <label htmlFor={`rating-${row.id}-${criterion.id}`}>
              Rating for {criterion.title}
            </label>
            <select
              id={`rating-${row.id}-${criterion.id}`}
              name={`score-${criterion.id}`}
              defaultValue=""
              required
            >
              <option value="" disabled>
                Choose a rating
              </option>
              {row.rubric.scale.map((entry) => (
                <option key={entry.score} value={entry.score}>
                  {entry.score} · {entry.label}
                </option>
              ))}
            </select>
            <label>
              Evidence for {criterion.title}
              <textarea
                name={`evidence-${criterion.id}`}
                minLength={10}
                maxLength={2000}
                required
                rows={3}
              />
            </label>
          </div>
        ))}
        <label>
          Review summary
          <textarea
            name="summary"
            minLength={20}
            maxLength={6000}
            required
            rows={3}
          />
        </label>
        <label>
          Next actions
          <textarea
            name="next_steps"
            minLength={20}
            maxLength={6000}
            required
            rows={3}
          />
        </label>
        <p className="small muted">
          Ratings of 2 or 3 on every criterion produce “Meets stated rubric”;
          any lower rating produces “Changes requested”. Both are manual
          judgment.
        </p>
        <button className="button" type="submit">
          {busy ? "Recording…" : "Record feedback"}
        </button>
      </fieldset>
    </form>
  );
}
