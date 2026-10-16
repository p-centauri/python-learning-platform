"use client";
import Link from "next/link";
import { ArrowRight, CalendarClock } from "lucide-react";
import { useApi } from "@/lib/api";
import type { RecallOverview, Review } from "@/lib/types";
import {
  RecallDueTime,
  RecallEvidenceCard,
} from "@/components/recall-evidence";
import {
  DateLabel,
  Empty,
  ErrorNotice,
  Loading,
  PageHeading,
} from "@/components/ui";
export default function ReviewPage() {
  const recall = useApi<RecallOverview>("/recall");
  const legacy = useApi<Review[]>("/reviews");
  if (recall.error)
    return <ErrorNotice message={recall.error} retry={recall.reload} />;
  if (!recall.data) return <Loading />;
  const data = recall.data;
  return (
    <>
      <PageHeading
        eyebrow="RETRIEVE. REINFORCE. RETAIN."
        title="Make your knowledge last."
        description="Find repeated mistakes, try a different question, and return later to check what you remember."
      />
      <p className="notice">
        {data.note} A delayed check needs at least 24 hours since your last
        recorded practice or review of that topic. Help use is self-reported.
      </p>
      <div
        className="recall-stats"
        role="region"
        aria-label="Separate review evidence"
      >
        <RecallEvidenceCard
          title="Scenario recognition"
          value={data.summary.source_recognition}
          description="Original multiple-choice attempts, including hints and repeated answers. These are separate from short-answer checks."
        />
        <RecallEvidenceCard
          title="Fresh delayed checks"
          value={data.summary.fresh_delayed}
          description="Scheduled short answers to questions you have not seen in this lab, with no reported help. Limited evidence, not a mastery score."
        />
        <RecallEvidenceCard
          title="Immediate practice"
          value={data.summary.immediate}
          description="Short answers practised now. Useful learning, but not a delayed retention check."
        />
        <RecallEvidenceCard
          title="Repeated or assisted work"
          value={{
            correct:
              data.summary.repeated_delayed.correct +
              data.summary.assisted.correct,
            total:
              data.summary.repeated_delayed.total + data.summary.assisted.total,
          }}
          description="Seen questions and work with help stay out of the fresh delayed-check result."
        />
      </div>
      <section aria-label="Mistake-focused topics">
        <div className="submission-row">
          <h2>Your review topics</h2>
          <span className="badge">
            {data.summary.due} delayed checks due · {data.summary.recurring}{" "}
            {data.summary.recurring === 1 ? "topic" : "topics"} with repeated
            errors
          </span>
        </div>
        <p>
          Counts show recorded wrong answers grouped by lesson topic. They
          suggest where to practise; they do not diagnose what you believe.
        </p>
        {!data.topics.length ? (
          <Empty title="Your review queue starts with practice.">
            Answer a scenario in the <Link href="/practice">practice lab</Link>,
            or explore a short-answer topic below. No retention result is
            assumed.
          </Empty>
        ) : (
          <div className="review-list">
            {data.topics.map((topic) => (
              <article key={topic.id} className="panel recall-topic">
                <div className="submission-row">
                  <small>{topic.skill}</small>
                  <span className="badge">
                    {topic.recurring
                      ? "Repeated errors recorded"
                      : topic.incorrect
                        ? "A mistake to revisit"
                        : "Topic visited"}
                  </span>
                </div>
                <h3>
                  <Link href={`/review/${topic.id}`}>{topic.title}</Link>
                </h3>
                <p>
                  {topic.source_incorrect} incorrect scenario answers across{" "}
                  {topic.source_questions_missed}{" "}
                  {topic.source_questions_missed === 1
                    ? "question"
                    : "questions"}{" "}
                  · {topic.check_incorrect} incorrect short-answer checks
                </p>
                <p>
                  {topic.active_id ? (
                    "An unfinished check is saved."
                  ) : topic.due ? (
                    "Delayed check ready."
                  ) : (
                    <>
                      Delayed check scheduled
                      {topic.due_at && (
                        <>
                          {" "}
                          for <RecallDueTime value={topic.due_at} />
                        </>
                      )}
                      .
                    </>
                  )}{" "}
                  {topic.unseen_questions}/{topic.question_count} variations
                  unseen.
                </p>
                <Link
                  className="button secondary"
                  href={
                    topic.active_id
                      ? `/review/checks/${topic.active_id}`
                      : `/review/${topic.id}`
                  }
                >
                  {topic.active_id ? "Resume check" : "Open topic"}
                  <ArrowRight size={15} />
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
      <details className="panel recall-catalog">
        <summary>
          Explore all {data.catalog.length} published review topics
        </summary>
        <p>
          Each topic has two authored short-answer variations. Once both have
          been viewed, further checks are labelled as repeated questions.
        </p>
        <div className="recall-catalog-grid">
          {data.catalog.map((topic) => (
            <Link
              className="text-link"
              key={topic.id}
              href={`/review/${topic.id}`}
            >
              {topic.title}
            </Link>
          ))}
        </div>
      </details>
      <section aria-label="Same-question review">
        <h2>Same-question practice</h2>
        <p>
          This earlier queue repeats the original multiple-choice scenario. Its
          results remain separate from fresh delayed checks.
        </p>
        {legacy.error ? (
          <ErrorNotice message={legacy.error} retry={legacy.reload} />
        ) : !legacy.data ? (
          <Loading />
        ) : !legacy.data.length ? (
          <p>No scenario reviews scheduled yet.</p>
        ) : (
          <div className="review-list">
            {legacy.data.map((r) => (
              <article key={r.exercise_id} className="review-row">
                <CalendarClock size={21} />
                <div>
                  <small>
                    {r.skill} · {r.repetitions} reviews completed
                  </small>
                  <h3>{r.title}</h3>
                  <p>
                    {r.due ? (
                      "Ready to recall"
                    ) : (
                      <>
                        Scheduled for <DateLabel value={r.due_at} />
                      </>
                    )}{" "}
                    · {r.interval_days}-day interval
                  </p>
                </div>
                {r.due ? (
                  <Link
                    className="button primary"
                    href={`/practice/${r.exercise_id}?review=1`}
                  >
                    Review now
                    <ArrowRight size={15} />
                  </Link>
                ) : (
                  <span className="badge">Upcoming</span>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
