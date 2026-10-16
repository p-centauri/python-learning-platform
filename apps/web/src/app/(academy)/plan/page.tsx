"use client";
import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Clock3, RefreshCw } from "lucide-react";
import { api, useApi } from "@/lib/api";
import type { LearningPreferences, PersonalPlanResponse } from "@/lib/types";
import {
  DateLabel,
  Empty,
  ErrorNotice,
  Loading,
  PageHeading,
} from "@/components/ui";

export default function PersonalPlanPage() {
  const { data, error, reload, setData } =
    useApi<PersonalPlanResponse>("/learning-plan");
  const [notice, setNotice] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  const plan = data.plan;
  async function refresh() {
    setRefreshing(true);
    await reload();
    setRefreshing(false);
  }
  return (
    <>
      <PageHeading
        eyebrow="A PLAN THAT FITS YOU"
        title="Your personal learning plan"
        description="Choose a direction and a realistic weekly pace. Your next actions adapt as you study and practise."
      />
      {notice && (
        <p className="notice" role="status">
          {notice}
        </p>
      )}
      <PreferencesForm
        key={JSON.stringify(data.preferences)}
        data={data}
        onSaved={(next) => {
          setData(next);
          setNotice("Plan saved. Your recommendations are up to date.");
        }}
      />
      {!plan ? (
        <section className="panel plan-intro">
          <h2>Start with a plan you can change</h2>
          <p>
            Save your choices to see an estimated weekly study queue. You can
            start immediately without taking a test.
          </p>
          <p>
            Want a more informed starting point?{" "}
            <Link className="text-link" href="/exams">
              Take a knowledge assessment
            </Link>
            . Only submitted results influence recommendations.
          </p>
        </section>
      ) : (
        <>
          <section
            className="panel plan-summary"
            aria-label="Your plan summary"
          >
            <div>
              <p className="overline">YOUR DIRECTION</p>
              <h2>{plan.goal_title}</h2>
              <p>
                {data.preferences?.weekly_hours} hours available each week ·{" "}
                {plan.scheduled_minutes} minutes in this queue
              </p>
            </div>
            <button
              className="button secondary"
              onClick={refresh}
              disabled={refreshing}
            >
              <RefreshCw size={15} />
              {refreshing ? "Refreshing…" : "Refresh recommendations"}
            </button>
          </section>
          <section
            className="panel plan-start"
            aria-label="Recommended starting point"
          >
            <h2>Why this starting point?</h2>
            {plan.starting_point ? (
              <>
                <Link
                  className="text-link"
                  href={`/lessons/${plan.starting_point.id}`}
                >
                  {plan.starting_point.title} <ArrowRight size={15} />
                </Link>
                <p>{plan.starting_point.reason}</p>
                {plan.starting_point.prerequisites.length > 0 && (
                  <p className="small muted">
                    Earlier reading to check if needed:{" "}
                    {plan.starting_point.prerequisites.map((item, i) => (
                      <span key={item.id}>
                        {i > 0 && ", "}
                        <Link
                          className="text-link"
                          href={`/lessons/${item.id}`}
                        >
                          {item.title}
                        </Link>
                      </span>
                    ))}
                    .
                  </p>
                )}
              </>
            ) : (
              <p>
                You have read every published lesson in this path. Your
                remaining practice and due reviews still appear below.
              </p>
            )}
            <p className="small muted">
              A recommended entry point does not complete earlier lessons or
              certify practical skill. You can change the approach above at any
              time.
            </p>
          </section>
          <section className="plan-queue" aria-label="Weekly study queue">
            <div className="section-title">
              <h2>Your next study queue</h2>
              <span className="muted small">
                <Clock3 size={13} /> {plan.scheduled_minutes} /{" "}
                {plan.weekly_minutes} min
              </span>
            </div>
            <p className="muted">
              Due reviews come first, then weak areas and your chosen path. This
              queue updates from recorded work; it is not a calendar or a record
              of time spent.
            </p>
            {plan.items.length ? (
              <ol className="plan-actions">
                {plan.items.map((item, index) => (
                  <li
                    key={`${item.kind}-${item.id}`}
                    className="panel plan-action"
                  >
                    <span className="plan-number">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <div>
                      <span className="badge">
                        {item.kind === "lesson"
                          ? "Read"
                          : item.kind === "review"
                            ? "Review"
                            : "Practise"}{" "}
                        · ~{item.minutes} min
                      </span>
                      <h3>{item.title}</h3>
                      <p>{item.reason}</p>
                      <Link className="text-link" href={item.href}>
                        {index === 0 ? "Start next action" : "Open activity"}{" "}
                        <ArrowRight size={15} />
                      </Link>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <Empty title="Your published study queue is clear.">
                You have recorded reading and correct practice responses for
                this path, with no reviews due. This does not certify mastery.
                Use a project to demonstrate implementation and check back for
                due reviews.
              </Empty>
            )}
            {plan.remaining_minutes > 0 && (
              <p className="muted small">
                {plan.remaining_minutes} minutes are unallocated. Use them for
                notes, extra practice or project work; activities are not added
                just to fill the budget.
              </p>
            )}
          </section>
          <div className="plan-details-grid">
            <section className="panel">
              <h2>Assessment evidence</h2>
              {plan.evidence.length ? (
                <ul className="plan-evidence">
                  {plan.evidence.map((exam) => (
                    <li key={exam.id}>
                      <Link className="text-link" href={`/exams/${exam.id}`}>
                        {exam.title}
                      </Link>
                      <p>
                        {exam.score === null
                          ? "Manual review required"
                          : `${exam.score}% objective`}{" "}
                        · <DateLabel value={exam.submitted_at} />
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>
                  No submitted assessment yet. Your plan uses your chosen path
                  and recorded practice.
                </p>
              )}
              <Link className="text-link" href="/exams">
                Open assessments <ArrowRight size={15} />
              </Link>
              {plan.uncovered_topics.length > 0 && (
                <p className="small muted">
                  Some weak topics have no dedicated published lesson yet:{" "}
                  {plan.uncovered_topics.join(", ")}. Use the study guidance in
                  your assessment results.
                </p>
              )}
            </section>
            <section className="panel">
              <h2>What this plan covers</h2>
              <p>{plan.coverage_note}</p>
              <p>
                Reading, practice responses and project evidence remain
                separate. Correct answers using hints can finish a practice task
                without proving independent competence.
              </p>
              <Link className="text-link" href="/projects">
                Explore practical projects <ArrowRight size={15} />
              </Link>
              <details className="plan-route">
                <summary>
                  See the {plan.route.length} published lessons in your path
                </summary>
                <ol>
                  {plan.route.map((lesson) => (
                    <li key={lesson.id}>
                      <Link href={`/lessons/${lesson.id}`}>{lesson.title}</Link>
                      {lesson.completed && (
                        <span className="muted small"> · read</span>
                      )}
                    </li>
                  ))}
                </ol>
              </details>
            </section>
          </div>
        </>
      )}
    </>
  );
}

function PreferencesForm({
  data,
  onSaved,
}: {
  data: PersonalPlanResponse;
  onSaved: (data: PersonalPlanResponse) => void;
}) {
  const [goal, setGoal] = useState(data.preferences?.goal ?? "backend-ai");
  const [hours, setHours] = useState(
    String(data.preferences?.weekly_hours ?? 3),
  );
  const [mode, setMode] = useState<LearningPreferences["starting_mode"]>(
    data.preferences?.starting_mode ?? "recommended",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    const value = Number(hours);
    if (!Number.isInteger(value) || value < 1 || value > 20) {
      setError("Choose a whole number from 1 to 20 hours.");
      return;
    }
    setBusy(true);
    try {
      onSaved(
        await api<PersonalPlanResponse>("/learning-plan", "PUT", {
          goal,
          weekly_hours: value,
          starting_mode: mode,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      className="panel plan-preferences"
      onSubmit={save}
      aria-label="Learning preferences"
    >
      <fieldset disabled={busy}>
        <legend>Your learning goal</legend>
        <div className="plan-goals">
          {data.goals.map((item) => (
            <label
              className={`plan-goal ${goal === item.id ? "selected" : ""}`}
              key={item.id}
            >
              <input
                type="radio"
                name="goal"
                value={item.id}
                checked={goal === item.id}
                onChange={() => setGoal(item.id)}
              />
              <span>
                <strong>{item.title}</strong>
                <small>{item.description}</small>
              </span>
            </label>
          ))}
        </div>
        <div className="plan-inputs">
          <label htmlFor="weekly-hours">
            Weekly study hours
            <input
              id="weekly-hours"
              type="number"
              min="1"
              max="20"
              step="1"
              required
              value={hours}
              onChange={(event) => setHours(event.target.value)}
              aria-describedby="hours-help"
            />
            <small id="hours-help">
              1–20 whole hours. Estimates include reading and practice.
            </small>
          </label>
          <label htmlFor="starting-mode">
            Starting approach
            <select
              id="starting-mode"
              value={mode}
              onChange={(event) =>
                setMode(
                  event.target.value as LearningPreferences["starting_mode"],
                )
              }
            >
              <option value="recommended">
                Use assessment recommendations
              </option>
              <option value="from-start">Start from the beginning</option>
            </select>
            <small>
              Existing progress stays saved when you change your plan.
            </small>
          </label>
        </div>
      </fieldset>
      {error && <ErrorNotice message={error} />}
      <button className="button primary" type="submit" disabled={busy}>
        {busy
          ? "Saving…"
          : data.preferences
            ? "Save changes"
            : "Create my plan"}
        <ArrowRight size={16} />
      </button>
    </form>
  );
}
