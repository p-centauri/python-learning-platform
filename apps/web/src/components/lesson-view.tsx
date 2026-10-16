"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowRight,
  Bookmark,
  Check,
  CheckCircle2,
  Clock3,
  MessageSquare,
  FlaskConical,
  List,
} from "lucide-react";
import { api, useApi } from "@/lib/api";
import type { LessonDetail } from "@/lib/types";
import { ErrorNotice, Loading } from "./ui";
import { LessonActivitiesView } from "./lesson-activities";
import { lessonAnchors } from "@/lib/lesson-anchors";
export function LessonView({ id }: { id: string }) {
  const { data, error, reload, setData } = useApi<LessonDetail>(
    `/lessons/${id}`,
  );
  const [note, setNote] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  useEffect(() => {
    if (data) setNote(data.note);
  }, [data?.id, data?.note]);
  useEffect(() => {
    if (!data || note === data.note) return;
    function beforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
    }
    window.addEventListener("beforeunload", beforeUnload);
    return () => window.removeEventListener("beforeunload", beforeUnload);
  }, [note, data?.note]);
  useEffect(() => {
    if (!data || !window.location.hash.startsWith("#lesson-")) return;
    const target = document.getElementById(window.location.hash.slice(1));
    target?.scrollIntoView();
    target?.focus({ preventScroll: true });
  }, [data?.id]);
  async function mutate(path: string, body?: unknown) {
    setBusy(true);
    setActionError("");
    try {
      await api(`/lessons/${id}/${path}`, "PUT", body);
      if (path === "note") {
        setStatus("Note saved");
        setData((v) => (v ? { ...v, note } : v));
      } else await reload();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <Link className="back-link" href="/learn">
        ← Learning path <span>/ {data.skill}</span>
      </Link>
      <div className="lesson-heading">
        <p className="eyebrow">{data.skill.toUpperCase()} · PUBLISHED LESSON</p>
        <h1>{data.title}</h1>
        <p>{data.summary}</p>
        <div>
          <span>
            <Clock3 size={15} />
            {data.minutes} min read
          </span>
          <span>{data.exercise_count} practice exercises</span>
          {data.completed && (
            <span className="green-text">
              <CheckCircle2 size={15} />
              Reading completed
            </span>
          )}
        </div>
      </div>
      {actionError && <ErrorNotice message={actionError} />}
      <nav className="lesson-tools" aria-label="Lesson study tools">
        <a href="#lesson-objectives">
          <List size={17} aria-hidden="true" />
          Overview
        </a>
        <a href="#lesson-practice">
          <FlaskConical size={17} aria-hidden="true" />
          Practice
        </a>
        <a href="#lesson-note">
          <MessageSquare size={17} aria-hidden="true" />
          Notes
          {note !== data.note && (
            <span className="unsaved-dot" aria-label="Unsaved changes" />
          )}
        </a>
        <button
          className={data.bookmarked ? "selected" : ""}
          disabled={busy}
          onClick={() => mutate("bookmark", { enabled: !data.bookmarked })}
          aria-pressed={data.bookmarked}
        >
          <Bookmark
            size={17}
            aria-hidden="true"
            fill={data.bookmarked ? "currentColor" : "none"}
          />
          {data.bookmarked ? "Bookmarked" : "Bookmark lesson"}
        </button>
      </nav>
      <details className="lesson-toc panel">
        <summary>Jump to a section</summary>
        <nav aria-label="On this lesson">
          <a href="#lesson-objectives">Learning objectives</a>
          {data.sections.map((section) => (
            <a key={section.id} href={`#${section.id}`}>
              {section.title}
            </a>
          ))}
          <a href="#lesson-diagram">See the idea</a>
          <a href="#lesson-checkpoints">Pause and try it</a>
          <a href="#lesson-glossary">Words in this lesson</a>
          <a href="#lesson-practice">Scenario practice</a>
          <a href="#lesson-note">Your working notes</a>
        </nav>
      </details>
      <div className="lesson-layout">
        <article className="lesson-article">
          <div className="objectives">
            <h2 id="lesson-objectives" tabIndex={-1}>
              What you’ll be able to do
            </h2>
            {data.objectives.map((o) => (
              <p key={o}>
                <Check size={16} />
                {o}
              </p>
            ))}
          </div>
          <div className="prose">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, lessonAnchors]}
              components={{
                h2: ({ node, ...props }) => <h2 {...props} tabIndex={-1} />,
                pre: ({ node, ...props }) => (
                  <pre
                    {...props}
                    tabIndex={0}
                    role="region"
                    aria-label="Code example"
                  />
                ),
                table: ({ node, ...props }) => (
                  <div
                    className="table-scroll"
                    tabIndex={0}
                    role="region"
                    aria-label="Lesson table"
                  >
                    <table {...props} />
                  </div>
                ),
              }}
            >
              {data.body}
            </ReactMarkdown>
          </div>
          <LessonActivitiesView lessonId={id} />
          <section className="reading">
            <h3>Go to the source</h3>
            {data.reading.map((url) => (
              <a key={url} href={url} target="_blank" rel="noopener noreferrer">
                {new URL(url).hostname}
                <ArrowRight size={14} />
              </a>
            ))}
          </section>
          <button
            className="button primary"
            disabled={busy || data.completed}
            onClick={() => mutate("complete")}
          >
            {data.completed ? "Reading completed" : "Mark reading complete"}
            <Check size={16} />
          </button>
          <p className="muted small">
            Reading progress, guided checkpoints and mastery are separate.
            Scenario practice below builds the existing exercise evidence.
          </p>
          <section className="lesson-practice">
            <p className="eyebrow">NOW MAKE IT YOURS</p>
            <h2 id="lesson-practice" tabIndex={-1}>
              Test your understanding.
            </h2>
            {data.exercises.map((e, i) => (
              <Link
                className="exercise-link"
                key={e.id}
                href={`/practice/${e.id}`}
              >
                <span className="exercise-number">0{i + 1}</span>
                <div>
                  <small>
                    {e.kind} · {e.difficulty}
                  </small>
                  <h3>{e.title}</h3>
                </div>
                <ArrowRight size={18} />
              </Link>
            ))}
          </section>
          <nav className="lesson-pagination" aria-label="Lesson navigation">
            {data.navigation.previous && (
              <Link
                className="button secondary"
                href={`/lessons/${data.navigation.previous.id}`}
              >
                ← Previous: {data.navigation.previous.title}
              </Link>
            )}
            {data.navigation.next ? (
              <Link
                className="button secondary"
                href={`/lessons/${data.navigation.next.id}`}
              >
                Next: {data.navigation.next.title} →
              </Link>
            ) : (
              <Link className="button secondary" href="/learn">
                Return to the learning path →
              </Link>
            )}
          </nav>
        </article>
        <aside className="lesson-context">
          <div className="context-section">
            <h3>Before this lesson</h3>
            {data.navigation.prerequisites.length ? (
              data.navigation.prerequisites.map((p) => (
                <Link key={p.id} href={`/lessons/${p.id}`}>
                  {p.title} <ArrowRight size={13} />
                </Link>
              ))
            ) : (
              <p>Your existing development experience is enough to begin.</p>
            )}
          </div>
          <div className="context-section">
            <label htmlFor="lesson-note">Your working notes</label>
            <p>
              Capture an insight, a question, or a failure mode worth
              remembering.
            </p>
            <textarea
              id="lesson-note"
              value={note}
              maxLength={20000}
              onChange={(e) => {
                setNote(e.target.value);
                setStatus("Unsaved changes");
              }}
              placeholder="What clicked? What needs a second look?"
              rows={8}
            />
            <button
              className="button secondary small-button"
              disabled={busy || note === data.note}
              onClick={() => mutate("note", { body: note })}
            >
              Save note
            </button>
            <small role="status" aria-live="polite">
              {status}
            </small>
          </div>
          <div className="context-tip">
            Close the lesson before you answer. Retrieval is part of learning.
          </div>
        </aside>
      </div>
    </>
  );
}
