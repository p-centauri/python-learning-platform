"use client";
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import { ErrorNotice, Loading, Meter, PageHeading } from "@/components/ui";
export default function Progress() {
  const { data, error, reload } = useApi<Dashboard>("/dashboard");
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeading
        eyebrow="EVIDENCE OVER COMPLETION"
        title="Know where you stand."
        description="Reading tells us what you explored. Solving tells us what you can reason about."
      />
      <div className="progress-summary">
        <strong>
          {data.mastery}
          <span>%</span>
        </strong>
        <div>
          <h2>Founding practice coverage</h2>
          <p>
            {data.solved_exercises} exercises solved · {data.attempts} attempts
            · {data.completed_lessons} lessons read
          </p>
        </div>
      </div>
      <div className="panel">
        <div className="skills-list">
          {data.skills.map((skill) => (
            <div className="skill-row" key={skill.skill}>
              <div>
                <span>{skill.skill}</span>
                <small>
                  {skill.assessed
                    ? `${skill.score}% · ${skill.assessed}/${skill.total} assessed`
                    : "Not assessed"}
                </small>
              </div>
              <Meter value={skill.score} label={skill.skill} />
            </div>
          ))}
        </div>
      </div>
      <div className="two-columns">
        <section className="panel">
          <h2>Where to focus next</h2>
          {data.weak_skills.length ? (
            data.weak_skills.map((s) => (
              <div className="weak-row" key={s.skill}>
                <span>{s.skill}</span>
                <strong>{s.score}%</strong>
              </div>
            ))
          ) : (
            <p className="muted">
              {data.attempts
                ? "Your assessed skills have no scores below 70%. Expand your coverage next."
                : "Practice a few scenarios to identify areas that need reinforcement."}
            </p>
          )}
          <Link href="/learn" className="text-link">
            Revisit the learning path →
          </Link>
        </section>
        <section className="panel">
          <h2>What this score means</h2>
          <p className="muted">
            Each exercise contributes once: 70% first-attempt performance and
            30% best eligible performance, with a hint penalty. Unattempted
            exercises remain uncovered. Reading and project checklists add no
            mastery credit.
          </p>
          <p className="muted">
            This initial score measures practice coverage. It is not
            senior-engineer certification or comprehensive-exam readiness.
          </p>
        </section>
      </div>
    </>
  );
}
