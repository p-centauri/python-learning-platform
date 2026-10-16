"use client";
import Link from "next/link";
import { useState } from "react";
import { ArrowDown, ArrowUpRight } from "lucide-react";
import { useApi } from "@/lib/api";
import { filterLessons } from "@/lib/catalog";
import { CatalogFilters, CatalogMore } from "@/components/catalog-filters";
import type { Curriculum } from "@/lib/types";
import { Empty, ErrorNotice, Loading, PageHeading } from "@/components/ui";
export default function KnowledgeMap() {
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
        eyebrow="CONNECTED UNDERSTANDING"
        title="See how the ideas fit."
        description="Prerequisites give advanced topics a foundation. Follow each connection back to its source."
      />
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
        <Empty title="No matching connections.">
          Try another topic or clear the filters to explore the map.
        </Empty>
      )}
      <div className="knowledge-grid">
        {lessons.slice(0, limit).map((l) => (
          <article className="knowledge-node" key={l.id}>
            <span className="overline">{l.skill}</span>
            {l.prerequisites.length ? (
              <div className="prereq-links">
                {l.prerequisites.map((id) => (
                  <Link href={`/lessons/${id}`} key={id}>
                    {data.lessons.find((x) => x.id === id)?.title}
                  </Link>
                ))}
                <ArrowDown size={16} />
              </div>
            ) : (
              <p className="muted small">
                Entry point · existing developer experience
              </p>
            )}
            <Link className="knowledge-title" href={`/lessons/${l.id}`}>
              {l.title}
              <ArrowUpRight size={16} />
            </Link>
          </article>
        ))}
      </div>
      <CatalogMore
        shown={Math.min(limit, lessons.length)}
        total={lessons.length}
        onMore={() => setLimit((value) => value + 24)}
      />
      <div className="notice">
        Connections currently guide study order. Advanced/Senior mastery gates
        and the expanded concept graph are scheduled for the next milestone.
      </div>
    </>
  );
}
