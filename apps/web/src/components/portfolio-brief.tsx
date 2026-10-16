"use client";
import Link from "next/link";
import { useApi } from "@/lib/api";
import { ErrorNotice, Loading } from "./ui";
import { Rubric } from "./project-review";
import type { ProjectRubric } from "@/lib/types";
type Brief = {
  version: string;
  title: string;
  summary: string;
  duration: string;
  libraries: string[];
  sections: { title: string; text: string }[];
  learning: string[];
  learning_titles: Record<string, string>;
  references: { title: string; url: string }[];
  milestones: { id: string; title: string; description: string }[];
  rubric: ProjectRubric;
};
export function PortfolioBrief({ id }: { id: string }) {
  const { data, error, reload } = useApi<Brief>(`/projects/${id}/brief`);
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <section aria-label="Portfolio build contract" className="portfolio-brief">
      <section className="panel submission-section">
        <h2>Build the full portfolio product</h2>
        <p>{data.summary}</p>
        <p>
          {data.duration} · pack version {data.version}
        </p>
        <p>
          The pack is an intentional learner build workspace. Implement the
          product, collect actual evidence and request review. Downloading or
          checking a milestone does not certify completion.
        </p>
        <a
          className="button secondary"
          href={`/api/portfolio-packs/${id}`}
          download
        >
          Download portfolio build pack
        </a>
      </section>
      <section className="panel submission-section">
        <h2>Build contract and required failure cases</h2>
        {data.sections.map((s) => (
          <details key={s.title}>
            <summary>{s.title}</summary>
            <p>{s.text}</p>
          </details>
        ))}
        <h3>Libraries and expected abilities</h3>
        <ul>
          {data.libraries.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
        <h3>Ordered milestones</h3>
        <ol>
          {data.milestones.map((m) => (
            <li key={m.id}>
              <strong>{m.title}</strong>
              <p>{m.description}</p>
            </li>
          ))}
        </ol>
        <h3>Relevant academy practice</h3>
        {data.learning.map((l) => (
          <Link className="lesson-row" key={l} href={`/lessons/${l}`}>
            {data.learning_titles?.[l] || "Open related lesson"}
          </Link>
        ))}
        <h3>Official references</h3>
        {data.references.map((r) => (
          <a
            className="lesson-row"
            key={r.url}
            href={r.url}
            target="_blank"
            rel="noreferrer"
          >
            {r.title} ↗
          </a>
        ))}
      </section>
      <Rubric rubric={data.rubric} />
    </section>
  );
}
