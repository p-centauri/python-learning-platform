"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api, useApi } from "@/lib/api";
import type { RecallSession } from "@/lib/types";
import { RecallDueTime, recallLabels } from "@/components/recall-evidence";
import { DateLabel, ErrorNotice, Loading, PageHeading } from "@/components/ui";
function CheckForm({ initial }: { initial: RecallSession }) {
  const [session, setSession] = useState(initial),
    [answer, setAnswer] = useState(initial.answer),
    [usedHelp, setUsedHelp] = useState(initial.used_help);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const active = session.status === "active";
  async function action(kind: "save" | "submit" | "discard") {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const row = await api<RecallSession>(
        `/recall/sessions/${session.id}${kind === "save" ? "" : `/${kind}`}`,
        kind === "save" ? "PUT" : "POST",
        kind === "discard" ? undefined : { answer, used_help: usedHelp },
      );
      setSession(row);
      setNotice(
        kind === "save"
          ? "Answer saved. You can return to this check."
          : kind === "discard"
            ? "Draft discarded. The question remains recorded as seen."
            : "Check recorded. Review your feedback below.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <section className="panel recall-topic" aria-label="Review question">
        <div className="submission-row">
          <span className="badge">
            {session.mode === "practice"
              ? "Immediate practice"
              : "Delayed check"}
          </span>
          <span className="badge">
            {session.fresh ? "Unseen when started" : "Repeated question"}
          </span>
        </div>
        <h2>{session.question.prompt}</h2>
        {session.question.code && (
          <pre className="recall-code">{session.question.code}</pre>
        )}
        <p className="small muted">
          Type the requested value or short term. Grading ignores surrounding
          whitespace
          {session.question.case_sensitive
            ? ", but letter case must match"
            : " and letter case"}
          , and accepts only the stated exact values. No code is executed from
          your answer.
        </p>
        <form
          aria-label="Short-answer check"
          onSubmit={(e) => {
            e.preventDefault();
            void action("submit");
          }}
        >
          <label htmlFor="recall-answer">Your short answer</label>
          <input
            id="recall-answer"
            value={answer}
            onChange={(e) => {
              setAnswer(e.target.value);
              setNotice("");
            }}
            maxLength={120}
            disabled={busy || !active}
            autoComplete="off"
            spellCheck={false}
            aria-describedby="recall-help"
          />
          <label className="recall-help">
            <input
              type="checkbox"
              checked={usedHelp}
              onChange={(e) => {
                setUsedHelp(e.target.checked);
                setNotice("");
              }}
              disabled={busy || !active}
            />
            <span>I used notes, hints, another answer or other help.</span>
          </label>
          <p id="recall-help" className="small muted">
            Help use is self-reported. Assisted work stays out of the
            independent delayed-check result. You can use help to learn; record
            it honestly.
          </p>
          {error && <ErrorNotice message={error} />}{" "}
          {notice && (
            <p className="notice" role="status">
              {notice}
            </p>
          )}
          {active && (
            <div className="submission-actions">
              <button
                type="submit"
                className="button primary"
                disabled={busy || !answer.trim()}
              >
                {busy ? "Saving…" : "Submit check"}
              </button>
              <button
                type="button"
                className="button secondary"
                disabled={busy}
                onClick={() => void action("save")}
              >
                Save answer
              </button>
            </div>
          )}
        </form>
        {active && (
          <details className="reveal-details">
            <summary>Leave this check</summary>
            <p>
              Discarding closes the draft without a grade. This question still
              counts as seen.
            </p>
            <button
              className="text-button"
              disabled={busy}
              onClick={() => void action("discard")}
            >
              Discard draft
            </button>
          </details>
        )}
        {session.status === "abandoned" && (
          <p>
            This draft was discarded. There is no grade or retention evidence.
          </p>
        )}
      </section>
      {session.result && (
        <section className="panel recall-topic" aria-label="Check feedback">
          <h2>
            {session.result.correct
              ? "Correct short answer"
              : "A useful mistake to revisit"}
          </h2>
          <p className="badge">{recallLabels[session.result.evidence_kind]}</p>
          <p>
            Expected: <strong>{session.result.expected}</strong>
          </p>
          <p>{session.result.explanation}</p>
          <p>{session.result.note}</p>
          {session.result.observed_study && (
            <p>
              Other recorded practice in this topic occurred during this check,
              so the result is counted as assisted.
            </p>
          )}
          <p>
            Next delayed check is no earlier than{" "}
            <RecallDueTime value={session.result.next_due_at} />. Later practice
            starts a new 24-hour gap.
          </p>
        </section>
      )}
      <p className="small muted">
        Check {session.id} · {session.version} · {session.policy}. Recorded
        results keep this question and explanation.
      </p>
      <Link className="button secondary" href={`/review/${session.concept_id}`}>
        Back to topic
      </Link>
    </>
  );
}
export default function RecallCheckPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, error, reload } = useApi<RecallSession>(
    `/recall/sessions/${sessionId}`,
  );
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <Link className="text-link" href="/review">
        ← Review queue
      </Link>
      <PageHeading
        eyebrow="CLOSE THE NOTES. TRY THE ANSWER."
        title={data.title}
        description="A short check of one idea. Feedback appears after submission."
      />
      <CheckForm key={data.id} initial={data} />
    </>
  );
}
