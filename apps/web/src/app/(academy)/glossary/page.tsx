"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useApi } from "@/lib/api";
import type { GlossaryTerm } from "@/lib/types";
import { Empty, ErrorNotice, Loading, PageHeading } from "@/components/ui";
export default function GlossaryPage() {
  const { data, error, reload } = useApi<{
    version: string;
    terms: GlossaryTerm[];
  }>("/glossary");
  const [query, setQuery] = useState("");
  const [target, setTarget] = useState<{ id: string; revision: number } | null>(
    null,
  );
  useEffect(() => {
    function open(id: string) {
      setQuery("");
      setTarget((current) => ({ id, revision: (current?.revision ?? 0) + 1 }));
    }
    function hash() {
      open(window.location.hash.slice(1));
    }
    function navigate(event: Event) {
      open((event as CustomEvent<string>).detail);
    }
    hash();
    window.addEventListener("hashchange", hash);
    window.addEventListener("academy:glossary-navigation", navigate);
    return () => {
      window.removeEventListener("hashchange", hash);
      window.removeEventListener("academy:glossary-navigation", navigate);
    };
  }, []);
  useEffect(() => {
    if (!data || !target?.id) return;
    const frame = requestAnimationFrame(() => {
      const element = document.getElementById(target.id);
      element?.scrollIntoView();
      element?.focus({ preventScroll: true });
    });
    return () => cancelAnimationFrame(frame);
  }, [data, target]);
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  const text = query.trim().toLocaleLowerCase();
  const terms = data.terms.filter((term) =>
    `${term.term} ${term.definition}`.toLocaleLowerCase().includes(text),
  );
  return (
    <>
      <PageHeading
        eyebrow="A WORD, A SIMPLE EXPLANATION"
        title="Engineering glossary."
        description="Find a term, read its meaning and return to a lesson that uses it."
      />
      <div className="glossary-search">
        <label htmlFor="glossary-query">Find a term</label>
        <input
          id="glossary-query"
          type="search"
          maxLength={100}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <p role="status">
          Showing {terms.length} of {data.terms.length} terms from published
          lessons.
        </p>
      </div>
      {!terms.length ? (
        <Empty title="No matching term.">
          Try another word or clear your search.
        </Empty>
      ) : (
        <dl className="glossary-grid">
          {terms.map((term) => (
            <div
              className="panel glossary-entry"
              id={term.id}
              tabIndex={-1}
              key={term.id}
            >
              <dt>{term.term}</dt>
              <dd>{term.definition}</dd>
              <dd className="glossary-lessons">
                {term.lessons.map((lesson) => (
                  <Link
                    className="text-link"
                    key={lesson.id}
                    href={`/lessons/${lesson.id}#lesson-glossary`}
                  >
                    {lesson.title} →
                  </Link>
                ))}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </>
  );
}
