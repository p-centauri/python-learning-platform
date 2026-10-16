"use client";
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { CodingCatalog } from "@/lib/types";
import { ErrorNotice, Loading, PageHeading } from "@/components/ui";

export default function CodingLab() {
  const { data, error, reload } = useApi<CodingCatalog>("/coding");
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeading
        eyebrow="WRITE, TEST, IMPROVE"
        title="Coding and SQL lab"
        description="Implement small contracts, inspect failing cases, and keep a record of what your code actually passed."
      />
      <div className="notice">
        <p>{data.note}</p>
        <p>{data.runner.message}</p>
        <button className="text-button" onClick={() => void reload()}>
          Check runner status
        </button>
      </div>
      <div className="practice-grid">
        {data.exercises.map((exercise) => (
          <Link
            className="practice-card"
            href={`/coding/${exercise.id}`}
            key={exercise.id}
          >
            <span className="badge">
              {exercise.language === "python" ? "Python 3.13" : "PostgreSQL 17"}
            </span>
            <h2>{exercise.title}</h2>
            <p>{exercise.prompt}</p>
            <footer>
              <span>
                {exercise.check_count} checks · {exercise.attempt_count} runs
              </span>
              <span>
                {exercise.passed ? "Suite passed" : "Ready to practise"} →
              </span>
            </footer>
          </Link>
        ))}
      </div>
    </>
  );
}
