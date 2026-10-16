"use client";
import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, Code2 } from "lucide-react";
import { useApi } from "@/lib/api";
import { filterLessons } from "@/lib/catalog";
import { CatalogFilters, CatalogMore } from "@/components/catalog-filters";
import type { Curriculum } from "@/lib/types";
import { Empty, ErrorNotice, Loading, PageHeading } from "@/components/ui";
export default function Practice() {
  const { data, error, reload } = useApi<Curriculum>("/curriculum");
  const [query, setQuery] = useState("");
  const [track, setTrack] = useState("");
  const [limit, setLimit] = useState(24);
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  const lessons = filterLessons(data.lessons, query, track);
  return (
    <>
      <PageHeading
        eyebrow="DELIBERATE PRACTICE"
        title="Put your understanding to work."
        description="Predict outcomes, diagnose failures, and defend a decision. Begin with a lesson’s two scenarios."
      />
      <div className="notice">
        Practise reasoning with the scenarios below, or write implementations in
        the{" "}
        <Link className="text-link" href="/coding">
          Coding and SQL lab →
        </Link>
      </div>
      <CatalogFilters
        query={query}
        onQuery={(value) => {
          setQuery(value);
          setLimit(24);
        }}
        track={track}
        onTrack={(value) => {
          setTrack(value);
          setLimit(24);
        }}
        tracks={data.tracks}
        count={lessons.length}
        total={data.lessons.length}
      />
      {!lessons.length && (
        <Empty title="No practice topics found.">
          Try another topic or clear the filters.
        </Empty>
      )}
      <div className="practice-grid">
        {lessons.slice(0, limit).map((l) => (
          <Link className="practice-card" href={`/lessons/${l.id}`} key={l.id}>
            <Code2 size={22} />
            <span className="badge">{l.skill}</span>
            <h2>{l.title}</h2>
            <p>{l.summary}</p>
            <footer>
              <span>{l.exercise_count} scenarios · Progressive hints</span>
              <ArrowUpRight size={17} />
            </footer>
          </Link>
        ))}
      </div>
      <CatalogMore
        shown={Math.min(limit, lessons.length)}
        total={lessons.length}
        onMore={() => setLimit((value) => value + 24)}
      />
    </>
  );
}
