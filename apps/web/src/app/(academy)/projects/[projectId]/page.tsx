"use client";
import { PortfolioBrief } from "@/components/portfolio-brief";

import { use, useState } from "react";
import Link from "next/link";
import { api, useApi } from "@/lib/api";
import type {
  ProjectArtifact,
  ProjectHistory,
  ProjectSubmission,
} from "@/lib/types";
import { ErrorNotice, Loading, PageHeading } from "@/components/ui";
import {
  FeedbackHistory,
  ReviewForm,
  Rubric,
  SubmissionEvidence,
} from "@/components/project-review";

function DraftForm({
  row,
  onSaved,
}: {
  row: ProjectSubmission;
  onSaved: (row: ProjectSubmission) => void;
}) {
  const [artifact, setArtifact] = useState<ProjectArtifact>(row.artifact);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  function update(key: keyof ProjectArtifact, value: string) {
    setArtifact((old) => ({ ...old, [key]: value }));
    setMessage("");
  }
  async function save(submit: boolean) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const saved = await api<ProjectSubmission>(
        `/project-submissions/${row.id}`,
        "PUT",
        artifact,
      );
      onSaved(saved);
      if (submit)
        onSaved(
          await api<ProjectSubmission>(
            `/project-submissions/${row.id}/submit`,
            "POST",
          ),
        );
      else setMessage("Draft saved. You can return to it later.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      className="panel submission-section submission-form"
      aria-label="Project submission draft"
      onSubmit={(e) => {
        e.preventDefault();
        void save(false);
      }}
    >
      <p className="overline">DRAFT · VERSION {row.revision}</p>
      <h2>Present your work</h2>
      <p>
        Save a draft at any time. Submitting fixes this version and its rubric
        so feedback stays tied to the same work.
      </p>
      {error && <ErrorNotice message={error} />}
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
      <fieldset disabled={busy}>
        <label>
          Repository URL
          <input
            type="url"
            value={artifact.repository_url}
            onChange={(e) => update("repository_url", e.target.value)}
            maxLength={2000}
            placeholder="https://…"
          />
        </label>
        <p className="small muted">
          Use HTTPS. The academy stores the link; reviewers need repository
          access. Keep secrets out of submitted evidence.
        </p>
        <label>
          Revision reference
          <input
            value={artifact.revision_ref}
            onChange={(e) => update("revision_ref", e.target.value)}
            maxLength={120}
            placeholder="Commit SHA or fixed tag"
          />
        </label>
        <label>
          Design explanation
          <textarea
            value={artifact.design_notes}
            onChange={(e) => update("design_notes", e.target.value)}
            maxLength={12000}
            rows={5}
          />
        </label>
        <p className="small muted">
          Explain the main choices, boundaries and trade-offs. At least 30
          characters when submitting.
        </p>
        <label>
          Implementation evidence
          <textarea
            value={artifact.evidence}
            onChange={(e) => update("evidence", e.target.value)}
            maxLength={12000}
            rows={5}
          />
        </label>
        <p className="small muted">
          Point to concrete files, cases and observed behavior for the rubric.
          At least 30 characters when submitting.
        </p>
        <label htmlFor="local-test-status">Local test result</label>
        <select
          id="local-test-status"
          value={artifact.test_status}
          onChange={(e) => update("test_status", e.target.value)}
        >
          <option value="not-run">Not run / no result reported</option>
          <option value="passed">Reported as passed</option>
          <option value="failed">Reported as failed</option>
        </select>
        <label>
          Test command
          <input
            value={artifact.test_command}
            onChange={(e) => update("test_command", e.target.value)}
            maxLength={500}
          />
        </label>
        <label>
          Test output
          <textarea
            value={artifact.test_output}
            onChange={(e) => update("test_output", e.target.value)}
            maxLength={20000}
            rows={5}
          />
        </label>
        <p className="small muted">
          Reported results require a command and output. These are saved as
          learner-reported evidence.
        </p>
        {row.parent_id && (
          <>
            <label>
              What changed since the previous version
              <textarea
                value={artifact.change_summary}
                onChange={(e) => update("change_summary", e.target.value)}
                maxLength={6000}
                rows={4}
              />
            </label>
            <p className="small muted">
              Describe fixes and feedback addressed; at least 20 characters when
              submitting.
            </p>
          </>
        )}
        <div className="submission-actions">
          <button className="button secondary" type="submit">
            {busy ? "Saving…" : "Save draft"}
          </button>
          <button
            className="button"
            type="button"
            onClick={() => void save(true)}
            disabled={busy}
          >
            Save and submit for review
          </button>
        </div>
      </fieldset>
    </form>
  );
}

function Reviewers({
  row,
  onSaved,
}: {
  row: ProjectSubmission;
  onSaved: (row: ProjectSubmission) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  async function invite(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onSaved(
        await api<ProjectSubmission>(
          `/project-submissions/${row.id}/reviewers`,
          "POST",
          { email },
        ),
      );
      setEmail("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function revoke(id: number) {
    setBusy(true);
    setError("");
    try {
      onSaved(
        await api<ProjectSubmission>(
          `/project-submissions/${row.id}/reviewers/${id}`,
          "DELETE",
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel submission-section" aria-label="Reviewer access">
      <h2>Invite a human reviewer</h2>
      <p>
        Enter the email they use for their registered academy account. This
        version appears in their Review workspace when they sign in. Share the
        page address yourself; no email is sent.
      </p>
      <p className="small muted">
        They can see this version's artifact, rubric and feedback. Invitations
        apply to this version only. Removing access keeps previously recorded
        feedback.
      </p>
      {error && <ErrorNotice message={error} />}
      <form onSubmit={invite} className="reviewer-invite">
        <label>
          Reviewer account email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            maxLength={254}
            required
            disabled={busy}
          />
        </label>
        <button className="button secondary" disabled={busy}>
          Invite reviewer
        </button>
      </form>
      <p className="review-address">
        Reviewer page:{" "}
        <a
          className="text-link"
          href={`/project-reviews/${row.id}`}
        >{`/project-reviews/${row.id}`}</a>
      </p>
      <ul className="reviewer-list">
        {row.assignments.map((assignment) => (
          <li key={assignment.id}>
            <span>
              {assignment.email} ·{" "}
              {assignment.active ? "Access granted" : "Access removed"}
            </span>
            {assignment.active && (
              <button
                className="text-button"
                disabled={busy}
                onClick={() => void revoke(assignment.id)}
              >
                Remove access for {assignment.email}
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function ProjectWorkspace({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { data, error, reload, setData } = useApi<ProjectHistory>(
    `/projects/${projectId}/submissions`,
  );
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  function update(row: ProjectSubmission) {
    setData((old) =>
      old
        ? {
            ...old,
            submissions: [
              row,
              ...old.submissions.filter((s) => s.id !== row.id),
            ].sort((a, b) => b.revision - a.revision),
          }
        : old,
    );
    setSelectedId(row.id);
  }
  async function create() {
    setBusy(true);
    setActionError("");
    try {
      update(
        await api<ProjectSubmission>(
          `/projects/${projectId}/submissions`,
          "POST",
        ),
      );
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function discard(id: number) {
    setBusy(true);
    setActionError("");
    try {
      await api(`/project-submissions/${id}`, "DELETE");
      setData((old) =>
        old
          ? { ...old, submissions: old.submissions.filter((s) => s.id !== id) }
          : old,
      );
      setSelectedId(null);
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  const row =
    data.submissions.find((s) => s.id === selectedId) || data.submissions[0];
  const draft = data.submissions.find((s) => s.status === "draft");
  return (
    <>
      <Link className="text-link" href={`/projects#${projectId}`}>
        ← All projects and milestones
      </Link>
      <PageHeading
        eyebrow="WORK, FEEDBACK, REVISION"
        title={data.project.title}
        description="Submit a specific implementation, learn from feedback, then show what improved."
      />
      <div className="submission-actions">
        <button
          className="button"
          onClick={() => (draft ? setSelectedId(draft.id) : void create())}
          disabled={busy}
        >
          {draft
            ? "Continue draft"
            : data.submissions.length
              ? "Start next revision"
              : "Start submission draft"}
        </button>
        {data.project.starter_url && (
          <a
            className="button secondary"
            href={data.project.starter_url}
            download
          >
            Download starter and tests
          </a>
        )}
      </div>
      {actionError && <ErrorNotice message={actionError} />}
      {["backend", "enterprise-rag", "finance"].includes(projectId) && (
        <PortfolioBrief id={projectId} />
      )}
      {data.submissions.length > 0 && (
        <section
          className="panel submission-section"
          aria-label="Submission history"
        >
          <h2>Your submission history</h2>
          <p>
            Choose a version to see its work, rubric and feedback. Earlier
            submissions stay fixed.
          </p>
          <div className="version-list">
            {data.submissions.map((s) => (
              <button
                className={`version-button ${s.id === row?.id ? "selected" : ""}`}
                key={s.id}
                aria-pressed={s.id === row?.id}
                onClick={() => setSelectedId(s.id)}
              >
                <strong>
                  Version {s.revision} ·{" "}
                  {s.status === "draft" ? "Draft" : "Submitted"}
                </strong>
                <span>
                  {s.feedback.filter((f) => f.kind === "human").length} human
                  reviews ·{" "}
                  {s.feedback.some((f) => f.kind === "self")
                    ? "Self-reviewed"
                    : "No self-review"}
                </span>
              </button>
            ))}
          </div>
        </section>
      )}
      <Rubric rubric={row?.rubric || data.rubric} />
      {row?.status === "draft" && (
        <>
          <DraftForm key={row.id} row={row} onSaved={update} />
          <details className="discard-draft">
            <summary>Discard this draft</summary>
            <p>
              This removes the saved draft. Submitted versions and feedback
              remain available.
            </p>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => void discard(row.id)}
            >
              Discard saved draft
            </button>
          </details>
        </>
      )}
      {row?.status === "submitted" && (
        <>
          <SubmissionEvidence row={row} />
          <FeedbackHistory row={row} />
          <Reviewers key={row.id} row={row} onSaved={update} />
          <ReviewForm key={`review-${row.id}`} row={row} onSaved={update} />
        </>
      )}
    </>
  );
}
