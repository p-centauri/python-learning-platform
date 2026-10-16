"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api, useApi } from "@/lib/api";
import type { RecallDetail, RecallSession } from "@/lib/types";
import {
  RecallDueTime,
  RecallEvidenceCard,
  recallLabels,
} from "@/components/recall-evidence";
import {
  DateLabel,
  Empty,
  ErrorNotice,
  Loading,
  PageHeading,
} from "@/components/ui";
export default function ReviewTopic() {
  const { conceptId } = useParams<{ conceptId: string }>();
  const { data, error, reload } = useApi<RecallDetail>(
    `/recall/topics/${conceptId}`,
  );
  const router = useRouter();
  const [busy, setBusy] = useState(false),
    [actionError, setActionError] = useState("");
  async function begin(mode: "practice" | "delayed") {
    setBusy(true);
    setActionError("");
    try {
      const session = await api<RecallSession>(
        `/recall/topics/${conceptId}/sessions`,
        "POST",
        { mode },
      );
      router.push(`/review/checks/${session.id}`);
    } catch (e) {
      setActionError((e as Error).message);
      setBusy(false);
    }
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  const topic = data.topic;
  return (
    <>
      <Link className="text-link" href="/review">
        ← Review queue
      </Link>
      <PageHeading
        eyebrow="MISTAKE-FOCUSED PRACTICE"
        title={topic.title}
        description="Try a short answer without choosing from options. Check the explanation after you submit."
      />
      <section className="panel recall-topic" aria-label="Topic evidence">
        <h2>
          {topic.recurring
            ? "Repeated errors recorded"
            : topic.incorrect
              ? "A mistake to revisit"
              : "Your practice evidence"}
        </h2>
        <p>
          {topic.source_incorrect} incorrect scenario answers across{" "}
          {topic.source_questions_missed}{" "}
          {topic.source_questions_missed === 1 ? "question" : "questions"}.{" "}
          {topic.check_incorrect} incorrect short-answer checks. A count is a
          review signal, not a diagnosis.
        </p>
        <p>
          {topic.due ? (
            "A delayed check is ready."
          ) : topic.due_at ? (
            <>
              Next delayed check: <RecallDueTime value={topic.due_at} />. At
              least 24 hours must pass after the last recorded topic exposure.
            </>
          ) : (
            "Start practice to schedule your first delayed check."
          )}
        </p>
        <p>
          {topic.unseen_questions}/{topic.question_count} variations have not
          been viewed.{" "}
          {topic.unseen_questions === 0 &&
            "All current variations have been seen; the next check will be labelled as repeated practice."}
        </p>
        {actionError && <ErrorNotice message={actionError} />}{" "}
        {data.active ? (
          <>
            <p>
              Resume your saved{" "}
              {data.active.mode === "practice"
                ? "immediate practice"
                : "delayed check"}
              . Finish or discard it before starting another question.
            </p>
            <Link
              className="button primary"
              href={`/review/checks/${data.active.id}`}
            >
              Resume check
            </Link>
          </>
        ) : (
          <div className="submission-actions">
            <button
              className="button primary"
              disabled={busy || !topic.due}
              onClick={() => void begin("delayed")}
            >
              {busy ? "Starting…" : "Start delayed check"}
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => void begin("practice")}
            >
              Practise now
            </button>
          </div>
        )}
        <p className="small muted">
          Practice now is immediate learning. It starts a new 24-hour gap before
          a delayed check. Viewed or discarded questions count as seen. Neither
          mode increases mastery.
        </p>
      </section>
      <div className="recall-stats">
        <RecallEvidenceCard
          title="Scenario recognition"
          value={topic.source_recognition}
          description="Original multiple-choice attempts."
        />
        <RecallEvidenceCard
          title="Fresh delayed checks"
          value={topic.fresh_delayed}
          description="Scheduled unseen questions with no reported help."
        />
        <RecallEvidenceCard
          title="Immediate practice"
          value={topic.immediate}
          description="Learning now, separate from delayed evidence."
        />
        <RecallEvidenceCard
          title="Repeated delayed practice"
          value={topic.repeated_delayed}
          description="Previously viewed questions; no new-question credit."
        />
      </div>
      <section className="panel recall-topic">
        <h2>Revisit the teaching</h2>
        <p>
          Use these links when studying. If you use teaching or another answer
          during a check, record that you used help.
        </p>
        <Link className="text-link" href={`/lessons/${topic.lesson_id}`}>
          Read the related lesson →
        </Link>
        <ul>
          {data.sources.map((source) => (
            <li key={source.id}>
              <Link href={source.href}>{source.title}</Link>
            </li>
          ))}
        </ul>
      </section>
      <section className="panel recall-topic" aria-label="Recall history">
        <h2>Fixed check history</h2>
        <p>
          Saved answers and explanations stay with the question version used.
          Earlier results cannot be edited.
        </p>
        {!data.history.length ? (
          <Empty title="No completed checks yet.">
            Start a question above. Unfinished checks can be resumed.
          </Empty>
        ) : (
          data.history.map((session) => (
            <article className="recall-history" key={session.id}>
              <h3>
                <Link href={`/review/checks/${session.id}`}>
                  Check {session.id} ·{" "}
                  {session.status === "abandoned"
                    ? "Discarded"
                    : session.result?.correct
                      ? "Correct"
                      : "Needs work"}
                </Link>
              </h3>
              <p>
                {session.result
                  ? recallLabels[session.result.evidence_kind]
                  : "Viewed question · no result"}{" "}
                ·{" "}
                <DateLabel value={session.submitted_at || session.created_at} />
              </p>
            </article>
          ))
        )}
      </section>
    </>
  );
}
