"use client";
import { useState } from "react";
import Link from "next/link";
import { api, useApi } from "@/lib/api";
import type { Project } from "@/lib/types";
import { ErrorNotice, Loading, Meter, PageHeading } from "@/components/ui";
export default function Projects() {
  const { data, error, reload, setData } = useApi<Project[]>("/projects");
  const [busy, setBusy] = useState("");
  const [actionError, setActionError] = useState("");
  async function toggle(project: string, task: string, enabled: boolean) {
    const previous = data;
    setBusy(task);
    setActionError("");
    setData(
      (current) =>
        current?.map((item) =>
          item.id === project
            ? {
                ...item,
                tasks: item.tasks.map((entry) =>
                  entry.id === task ? { ...entry, completed: enabled } : entry,
                ),
              }
            : item,
        ) ?? null,
    );
    try {
      await api(`/projects/${project}/tasks/${task}`, "PUT", { enabled });
      await reload();
    } catch (e) {
      setData(previous);
      setActionError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeading
        eyebrow="YOUR PORTFOLIO, WITH PROOF"
        title="Build systems you can defend."
        description="Start with a Python CLI, then build toward production backend and applied AI systems. Every milestone asks for concrete evidence."
      />
      <div className="notice">
        Milestones are a personal work checklist. Marking one complete does not
        automatically certify code quality or increase mastery.
      </div>
      {actionError && <ErrorNotice message={actionError} />}
      <div className="project-list">
        {data.map((p) => {
          const count = p.tasks.filter((t) => t.completed).length;
          return (
            <article
              className="project-detail panel"
              key={p.id}
              id={p.id}
              aria-label={p.title}
            >
              <header>
                <span className="project-number">{p.number}</span>
                <div>
                  <p className="overline">{p.stack}</p>
                  <h2>{p.title}</h2>
                  <p>{p.description}</p>
                </div>
                <span className="badge">
                  {count}/{p.tasks.length} milestones
                </span>
              </header>
              {p.lesson_id && (
                <p>
                  <Link className="text-link" href={`/lessons/${p.lesson_id}`}>
                    Read the project instructions →
                  </Link>
                </p>
              )}
              {["backend", "enterprise-rag", "finance"].includes(p.id) && (
                <p>
                  <Link className="text-link" href={`/projects/${p.id}`}>
                    Read the complete portfolio build contract →
                  </Link>
                </p>
              )}
              {p.starter_url && (
                <p>
                  <a className="button secondary" href={p.starter_url} download>
                    Download starter and tests
                  </a>
                </p>
              )}
              <p>
                <Link className="button secondary" href={`/projects/${p.id}`}>
                  Submit work and view feedback
                </Link>
              </p>
              <Meter
                value={(count / p.tasks.length) * 100}
                label={`${p.title} checklist`}
              />
              <div className="project-tasks">
                {p.tasks.map((t) => (
                  <label className={t.completed ? "done" : ""} key={t.id}>
                    <input
                      type="checkbox"
                      checked={t.completed}
                      disabled={!!busy}
                      onChange={(e) => toggle(p.id, t.id, e.target.checked)}
                    />
                    <span>
                      <strong>{t.title}</strong>
                      <p>{t.description}</p>
                    </span>
                  </label>
                ))}
              </div>
            </article>
          );
        })}
      </div>
    </>
  );
}
