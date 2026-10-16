"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, GraduationCap } from "lucide-react";
import { api, useApi } from "@/lib/api";
import type { ExamAttempt, ExamCatalog } from "@/lib/types";
import { DateLabel, ErrorNotice, Loading, PageHeading } from "@/components/ui";
import { ExamLibraryGuide } from "@/components/exam-library-guide";
export default function Exams() {
  const { data, error, reload } = useApi<ExamCatalog>("/exams");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const router = useRouter();
  async function start(exam_id: string) {
    setBusy(true);
    setActionError("");
    try {
      const attempt = await api<ExamAttempt>("/exams/start", "POST", {
        exam_id,
      });
      router.push(`/exams/${attempt.id}`);
    } catch (e) {
      setActionError((e as Error).message);
      setBusy(false);
    }
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeading
        eyebrow="ASSESS YOUR REASONING"
        title="Test the understanding underneath."
        description="A quiet space to find your strengths and the assumptions worth revisiting."
      />
      {actionError && <ErrorNotice message={actionError} />}
      <div className="notice">
        Beginner, intermediate and advanced Python evaluations are available
        below. Choose the level you want to assess. Each test measures
        knowledge; practical follow-ups require separate review.
      </div>
      {data.exams.map((exam) => (
        <section
          className="exam-intro panel"
          key={exam.id}
          aria-label={exam.title}
        >
          <GraduationCap size={32} />
          <span className="badge green">
            {exam.level === "Mixed diagnostic"
              ? "Available · diagnostic pilot"
              : `Available · ${exam.level}`}
          </span>
          <h2>{exam.title}</h2>
          <p>{exam.description}</p>
          <div className="exam-facts">
            <span>{exam.question_count} distinct questions</span>
            <span>
              ~{exam.minutes} minutes ·{" "}
              {exam.level === "Comprehensive"
                ? "advisory elapsed timer"
                : "untimed"}
            </span>
            <span>Saved after each answer</span>
          </div>
          <div className="topic-tags">
            {exam.topics.map((topic) => (
              <span key={topic}>{topic}</span>
            ))}
          </div>
          {exam.evaluation_policy && (
            <p className="small assessment-policy">
              {exam.evaluation_policy.note} Retakes reuse the same bank and may
              reflect memorization.
            </p>
          )}
          <button
            className="button primary"
            onClick={() => start(exam.id)}
            disabled={busy}
          >
            {busy
              ? "Opening…"
              : data.attempts.some(
                    (a) => a.status === "active" && a.exam_id === exam.id,
                  )
                ? exam.level === "Mixed diagnostic"
                  ? "Resume diagnostic"
                  : exam.level === "Comprehensive"
                    ? `Resume ${exam.title}`
                    : `Resume ${exam.level.toLowerCase()} test`
                : exam.level === "Mixed diagnostic"
                  ? "Begin diagnostic"
                  : exam.level === "Comprehensive"
                    ? `Begin ${exam.title}`
                    : `Begin ${exam.level.toLowerCase()} test`}
            <ArrowRight size={16} />
          </button>
          <ExamLibraryGuide exam={exam} />
        </section>
      ))}
      {data.attempts.length > 0 && (
        <section className="panel">
          <h2>Your assessment history</h2>
          {data.attempts.map((a) => (
            <Link className="lesson-row" href={`/exams/${a.id}`} key={a.id}>
              <span>
                {a.title} · Attempt #{a.id}{" "}
                <small>
                  <DateLabel value={a.started_at} />
                </small>
              </span>
              <span>
                {a.result
                  ? a.result.score === null
                    ? "View evidence · Manual review required"
                    : `${a.result.score}% objective · View analysis`
                  : "In progress · Resume"}
                <ArrowRight size={15} />
              </span>
            </Link>
          ))}
        </section>
      )}
      <div className="section-title">
        <h2>The comprehensive exam pathway</h2>
        <span className="badge green">Available · separate evidence types</span>
      </div>
      <div className="exam-roadmap">
        {[
          {
            n: "01",
            title: "Engineering knowledge",
            time: "2–3 hours",
            text: "Mixed-format theory, prediction and conceptual reasoning across the full curriculum.",
          },
          {
            n: "02",
            title: "Practical engineering",
            time: "4–6 hours",
            text: "Repair a broken application with automated tests and architecture review.",
          },
          {
            n: "03",
            title: "Senior design + applied AI",
            time: "3–5 hours",
            text: "Design a multi-tenant AI system and adapt it through staged production incidents.",
          },
        ].map((e) => (
          <article key={e.n}>
            <span className="overline">
              EXAM {e.n} · {e.time}
            </span>
            <h3>{e.title}</h3>
            <p>{e.text}</p>
          </article>
        ))}
      </div>
    </>
  );
}
