"use client";
import Link from "next/link";
import { Bookmark, ArrowRight } from "lucide-react";
import { useApi } from "@/lib/api";
import type { Lesson } from "@/lib/types";
import { Empty, ErrorNotice, Loading, PageHeading } from "@/components/ui";
export default function Bookmarks() {
  const { data, error, reload } = useApi<Lesson[]>("/bookmarks");
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeading
        eyebrow="YOUR PERSONAL LIBRARY"
        title="Keep the useful things close."
        description="Saved lessons for the concepts you want to return to."
      />
      {data.length ? (
        <div className="panel">
          {data.map((l) => (
            <Link className="lesson-row" key={l.id} href={`/lessons/${l.id}`}>
              <span>
                <Bookmark size={17} />
                {l.title}
              </span>
              <small>
                {l.skill}
                <ArrowRight size={15} />
              </small>
            </Link>
          ))}
        </div>
      ) : (
        <Empty title="A library worth building.">
          Bookmark a lesson while reading to find it here.{" "}
          <Link href="/learn">Explore lessons →</Link>
        </Empty>
      )}
    </>
  );
}
