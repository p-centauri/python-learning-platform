"use client";
import Link from "next/link";
import { useState } from "react";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  Clock3,
} from "lucide-react";
import { useApi } from "@/lib/api";
import { filterLessons } from "@/lib/catalog";
import type { Curriculum } from "@/lib/types";
import { CatalogFilters } from "@/components/catalog-filters";
import { Empty, ErrorNotice, Loading, PageHeading } from "@/components/ui";
export default function LearningPath() {
  const { data, error, reload } = useApi<Curriculum>("/curriculum");
  const [query, setQuery] = useState("");
  const [trackId, setTrackId] = useState("");
  const [status, setStatus] = useState("all");
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  const lessons = filterLessons(data.lessons, query, trackId, status);
  const filtering = Boolean(query.trim() || trackId || status !== "all");
  const tracks = data.tracks.filter(
    (track) =>
      (!trackId || track.id === trackId) &&
      (lessons.some((lesson) => lesson.track_id === track.id) ||
        (!filtering &&
          !data.lessons.some((lesson) => lesson.track_id === track.id))),
  );
  return (
    <>
      <PageHeading
        eyebrow="Your curriculum"
        title="A path to deeper understanding."
        description="Build your backend foundations, then put applied AI into practice. Choose a track or find a specific topic."
      />
      <div className="path-summary">
        <span>
          <strong>{data.tracks.length}</strong> tracks
        </span>
        <span>
          <strong>{data.lessons.length}</strong> published lessons
        </span>
        <span>
          <strong>
            {data.lessons.reduce(
              (count, lesson) => count + lesson.exercise_count,
              0,
            )}
          </strong>{" "}
          practice exercises
        </span>
      </div>
      <CatalogFilters
        query={query}
        onQuery={setQuery}
        track={trackId}
        onTrack={setTrackId}
        status={status}
        onStatus={setStatus}
        tracks={data.tracks}
        count={lessons.length}
        total={data.lessons.length}
      />
      {!tracks.length && (
        <Empty title="No topics match yet.">
          Try a broader phrase or clear your filters to see the full curriculum.
        </Empty>
      )}
      <div className="track-list">
        {tracks.map((track, index) => {
          const published = data.lessons.filter(
            (lesson) => lesson.track_id === track.id,
          );
          const visible = lessons.filter(
            (lesson) => lesson.track_id === track.id,
          );
          const completed = published.filter(
            (lesson) => lesson.completed,
          ).length;
          return (
            <details
              className="track-disclosure"
              key={track.id}
              open={filtering || index === 0}
            >
              <summary>
                <span className="track-number" aria-hidden="true">
                  {String(data.tracks.indexOf(track) + 1).padStart(2, "0")}
                </span>
                <span className="track-summary-content">
                  <span className="track-title">
                    <strong>{track.title}</strong>
                    <span
                      className={`badge ${published.length ? "green" : ""}`}
                    >
                      {published.length
                        ? `${published.length} lessons`
                        : track.optional
                          ? "Optional · planned"
                          : "Planned"}
                    </span>
                  </span>
                  <span className="track-description">{track.description}</span>
                  {published.length > 0 && (
                    <span className="track-reading">
                      <BookOpen size={14} aria-hidden="true" />
                      {completed} of {published.length} read
                    </span>
                  )}
                </span>
                <ChevronDown
                  size={20}
                  className="track-chevron"
                  aria-hidden="true"
                />
              </summary>
              <div className="track-content">
                {!published.length && (
                  <p className="muted">
                    This track is planned. Published lessons will appear here
                    when ready.
                  </p>
                )}
                {data.modules
                  .filter((module) => module.track_id === track.id)
                  .map((module) => {
                    const moduleLessons = visible.filter(
                      (lesson) => lesson.module_id === module.id,
                    );
                    if (!moduleLessons.length) return null;
                    return (
                      <section
                        key={module.id}
                        aria-label={module.title}
                        className="curriculum-module"
                      >
                        <h3>{module.title}</h3>
                        {module.description && <p>{module.description}</p>}
                        {moduleLessons.map((lesson) => (
                          <Link
                            className="lesson-row"
                            key={lesson.id}
                            href={`/lessons/${lesson.id}`}
                          >
                            <span>
                              {lesson.completed ? (
                                <CheckCircle2
                                  size={18}
                                  className="green-text"
                                  aria-label="Reading complete"
                                />
                              ) : (
                                <span className="lesson-dot" />
                              )}
                              {lesson.title}
                            </span>
                            <small>
                              <Clock3 size={14} />
                              {lesson.minutes} min
                              <ArrowRight size={16} />
                            </small>
                          </Link>
                        ))}
                        {module.project_id && (
                          <Link
                            className="text-link module-project"
                            href={`/projects#${module.project_id}`}
                          >
                            Build the module project
                            <ArrowRight size={15} />
                          </Link>
                        )}
                      </section>
                    );
                  })}
                <div className="topic-tags" aria-label="Track topics">
                  {track.topics.map((topic) => (
                    <span key={topic}>{topic}</span>
                  ))}
                </div>
              </div>
            </details>
          );
        })}
      </div>
    </>
  );
}
