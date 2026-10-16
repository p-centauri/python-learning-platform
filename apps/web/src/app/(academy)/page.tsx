"use client";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  Clock3,
  Code2,
  Flame,
  Layers3,
  Sparkles,
} from "lucide-react";
import { useApi } from "@/lib/api";
import { PlanOverview } from "@/components/plan-overview";
import type { PersonalPlanResponse } from "@/lib/types";
import type { Dashboard } from "@/lib/types";
import { useUser } from "@/components/shell";
import {
  Empty,
  ErrorNotice,
  Loading,
  Meter,
  PageHeading,
  SectionTitle,
} from "@/components/ui";
export default function Overview() {
  const { data, error, reload } = useApi<Dashboard>("/dashboard");
  const user = useUser();
  const personal = useApi<PersonalPlanResponse>("/learning-plan");
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  const assessed = data.skills.filter((s) => s.assessed).length;
  return (
    <>
      <PageHeading
        eyebrow="Your workspace"
        title={`Welcome ${data.attempts ? "back" : "aboard"}, ${user?.name.split(" ")[0]}.`}
        description="Pick up a lesson, practise a skill, or revisit what you’ve learned."
        action={
          data.streak > 0 ? (
            <div className="streak">
              <Flame size={17} />
              <strong>
                {data.streak} day{data.streak === 1 ? "" : "s"}
              </strong>
              <span>learning streak</span>
            </div>
          ) : (
            <Link className="button secondary" href="/plan">
              Create my learning plan
              <ArrowRight size={16} />
            </Link>
          )
        }
      />
      {personal.error && (
        <ErrorNotice
          message="Your learning plan could not be loaded."
          retry={personal.reload}
        />
      )}
      {personal.data?.plan && <PlanOverview data={personal.data} />}
      {data.retention_due > 0 && (
        <p className="notice">
          {data.retention_due} delayed short-answer checks are due.{" "}
          <Link className="text-link" href="/review">
            Open your review topics →
          </Link>
        </p>
      )}
      {!personal.data?.plan && (
        <div className="overview-grid">
          <section className="continue-card">
            <div className="continue-top">
              <span className="pill">
                <span className="tiny-dot" />
                {data.completed_lessons
                  ? "CONTINUE LEARNING"
                  : "YOUR STARTING POINT"}
              </span>
              <Code2 className="code-symbol" size={92} aria-hidden="true" />
            </div>
            <div className="continue-content">
              <p className="overline">
                {data.next_lesson.skill} <span> / </span> FOUNDATIONS
              </p>
              <h2>{data.next_lesson.title}</h2>
              <p>{data.next_lesson.summary}</p>
            </div>
            <div className="continue-footer">
              <Link
                className="button primary"
                href={`/lessons/${data.next_lesson.id}`}
              >
                {data.completed_lessons ? "Continue lesson" : "Start learning"}
                <ArrowRight size={17} />
              </Link>
              <span>
                <Clock3 size={14} />
                {data.next_lesson.minutes} min read{" "}
                <span className="separator-dot">·</span>{" "}
                {data.next_lesson.exercise_count} exercises
              </span>
            </div>
          </section>
          <aside className="focus-card">
            <div className="focus-heading">
              <Sparkles size={18} />
              <span>TODAY’S FOCUS</span>
            </div>
            <h3>
              {data.review_due
                ? "Make it stick."
                : "Understanding comes from doing."}
            </h3>
            <p>
              {data.review_due
                ? `${data.review_due} concepts are ready for retrieval practice. Revisit them before moving on.`
                : "Read with intent, then close the lesson and test what you can explain."}
            </p>
            <ol>
              <li>
                <span>01</span>Study the mental model
              </li>
              <li>
                <span>02</span>Predict the failure mode
              </li>
              <li>
                <span>03</span>Test your understanding
              </li>
            </ol>
            <Link href={data.review_due ? "/review" : "/practice"}>
              {data.review_due
                ? "Open spaced review"
                : "Explore the practice lab"}
              <ArrowUpRight size={16} />
            </Link>
          </aside>
        </div>
      )}
      <div className="stats-row">
        {[
          {
            label: "Lessons explored",
            value: `${data.completed_lessons}`,
            sub: `of ${data.total_lessons} published lessons`,
            icon: BookOpen,
          },
          {
            label: "Exercises solved",
            value: String(data.solved_exercises),
            sub: `${data.attempts} total attempts`,
            icon: Code2,
          },
          {
            label: "Evidence coverage",
            value: `${data.mastery}%`,
            sub: `${assessed} skills assessed`,
            icon: Layers3,
          },
          {
            label: "Ready for review",
            value: String(data.review_due),
            sub: "keep your knowledge active",
            icon: Clock3,
          },
        ].map((s) => (
          <div className="stat" key={s.label}>
            <div>
              <span>{s.label}</span>
              <s.icon size={16} />
            </div>
            <strong>{s.value}</strong>
            <small>{s.sub}</small>
          </div>
        ))}
      </div>
      <div className="dashboard-lower">
        <section className="panel skills-panel">
          <SectionTitle
            title="Your skill landscape"
            href="/progress"
            label="See progress"
          />
          <p className="muted small">
            Understanding is earned through practice, not page views.
          </p>
          <div className="skills-list">
            {data.skills.slice(0, 6).map((skill) => (
              <div className="skill-row" key={skill.skill}>
                <div>
                  <span>{skill.skill}</span>
                  <small>
                    {skill.assessed ? `${skill.score}%` : "Not assessed"}
                  </small>
                </div>
                <Meter value={skill.score} label={`${skill.skill} evidence`} />
              </div>
            ))}
          </div>
        </section>
        <section className="panel activity-panel">
          <SectionTitle
            title="Recent practice"
            href="/practice"
            label="Open lab"
          />
          {data.recent_attempts.length ? (
            <div className="activity-list">
              {data.recent_attempts.map((a) => (
                <Link key={a.id} href={`/practice/${a.exercise_id}`}>
                  <span className={`activity-icon ${a.score ? "success" : ""}`}>
                    {a.score ? <Check size={15} /> : <Code2 size={15} />}
                  </span>
                  <div>
                    {a.title}
                    <small>
                      {a.score ? "Correct answer" : "Keep investigating"}
                    </small>
                  </div>
                  <ArrowUpRight size={14} />
                </Link>
              ))}
            </div>
          ) : (
            <Empty title="Your first insight is waiting.">
              Solve an exercise to start building a record of your engineering
              judgment.
            </Empty>
          )}
        </section>
      </div>
      <section className="project-banner">
        <div className="project-icon">
          <FolderIcon />
        </div>
        <div>
          <h3>Build beyond the lesson.</h3>
          <p>Apply your skills in Python, backend and AI projects.</p>
        </div>
        <Link className="button secondary" href="/projects">
          Explore projects
          <ArrowUpRight size={16} />
        </Link>
      </section>
    </>
  );
}
function FolderIcon() {
  return <Layers3 size={24} />;
}
