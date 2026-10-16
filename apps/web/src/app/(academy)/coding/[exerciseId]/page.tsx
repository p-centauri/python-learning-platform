"use client";
import { use, useState } from "react";
import Link from "next/link";
import { api, ApiError, useApi } from "@/lib/api";
import type { CodingAttempt, CodingDetail } from "@/lib/types";
import { DateLabel, ErrorNotice, Loading, PageHeading } from "@/components/ui";

function Editor({
  data,
  onAttempt,
  onUnavailable,
  refresh,
}: {
  data: CodingDetail;
  onAttempt: (attempt: CodingAttempt) => void;
  onUnavailable: (message: string) => void;
  refresh: () => void;
}) {
  const [code, setCode] = useState(data.code);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [savedCode, setSavedCode] = useState(data.code);
  const [hasSaved, setHasSaved] = useState(data.draft_saved);
  const [selected, setSelected] = useState<CodingAttempt | null>(
    data.attempts[0] || null,
  );
  const [request, setRequest] = useState<{ code: string; key: string } | null>(
    null,
  );
  const changed = code !== savedCode;
  async function save(run: boolean) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api(`/coding/${data.id}/draft`, "PUT", { code });
      setSavedCode(code);
      setHasSaved(true);
      if (!run) setNotice("Draft saved. It will be here when you return.");
      else {
        const key = request?.code === code ? request.key : crypto.randomUUID();
        setRequest({ code, key });
        const attempt = await api<CodingAttempt>(
          `/coding/${data.id}/attempts`,
          "POST",
          { code, request_key: key, version: data.version },
        );
        setSelected(attempt);
        onAttempt(attempt);
        setRequest(null);
        setNotice("Run recorded. Review the checks below.");
      }
    } catch (e) {
      const message = (e as Error).message;
      setError(message);
      if (e instanceof ApiError && e.status === 503) onUnavailable(message);
    } finally {
      setBusy(false);
    }
  }
  function replaceSource(value: string) {
    setCode(value);
    setRequest(null);
    setNotice("");
  }
  const result = selected?.result;
  return (
    <>
      <section className="panel coding-editor-panel" aria-label="Code editor">
        <div className="submission-row">
          <h2>Your {data.language === "sql" ? "query" : "implementation"}</h2>
          <span className="badge">
            {changed
              ? "Unsaved changes"
              : hasSaved
                ? "Saved draft"
                : "Starter loaded"}
          </span>
        </div>
        <p id="editor-help">
          Plain-text editor. Use spaces for indentation and Tab to move between
          controls. Ctrl/Cmd + Enter runs the checks.
        </p>
        <label className="sr-only" htmlFor="learner-code">
          {data.language === "sql" ? "SQL query" : "Python code"}
        </label>
        <textarea
          id="learner-code"
          className="code-editor"
          aria-describedby="editor-help"
          value={code}
          onChange={(e) => replaceSource(e.target.value)}
          disabled={busy}
          spellCheck={false}
          autoCapitalize="off"
          autoCorrect="off"
          rows={16}
          maxLength={12000}
          onKeyDown={(e) => {
            if (
              (e.ctrlKey || e.metaKey) &&
              e.key === "Enter" &&
              data.runner.ready &&
              !busy &&
              code.trim()
            ) {
              e.preventDefault();
              void save(true);
            }
          }}
        />
        {error && <ErrorNotice message={error} />}
        {notice && (
          <p className="notice" role="status">
            {notice}
          </p>
        )}
        <div className="submission-actions">
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => void save(false)}
          >
            Save draft
          </button>
          <button
            className="button"
            disabled={busy || !data.runner.ready || !code.trim()}
            onClick={() => void save(true)}
          >
            {busy ? "Working…" : "Run checks"}
          </button>
        </div>
        <p className="small muted">
          Up to {data.limits.runs} runs per {data.limits.window_minutes} minutes
          across the lab. Each run uses a fresh isolated container per check;
          startup time is included in its limit. No package installation or
          network access.
        </p>
        <p>
          {data.runner.message}{" "}
          <button className="text-button" disabled={busy} onClick={refresh}>
            Check runner status
          </button>
        </p>
        <details>
          <summary>Replace editor content</summary>
          <p>
            This replaces the text in your editor. Save it if you want to keep
            it.
          </p>
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => replaceSource(data.starter)}
          >
            Use starter code
          </button>
        </details>
      </section>
      <section className="panel coding-editor-panel" aria-label="Run feedback">
        <h2>
          {selected
            ? `Run ${selected.id}: ${result?.status === "passed" ? "suite passed" : "needs work"}`
            : "Run feedback"}
        </h2>
        {!result && (
          <p>
            No runs yet. Save your draft, then run the checks to see objective
            feedback.
          </p>
        )}
        {result && (
          <>
            <p className="badge">
              {result.passed}/{result.total} checks passed
            </p>
            <p>{result.note}</p>
            <ul className="coding-checks">
              {result.checks.map((check, index) => (
                <li key={index}>
                  <div className="submission-row">
                    <strong>{check.name}</strong>
                    <span>{check.status}</span>
                  </div>
                  {check.public && check.actual !== null && (
                    <pre>Returned: {JSON.stringify(check.actual, null, 2)}</pre>
                  )}
                  {check.message && <pre>{check.message}</pre>}
                  {!check.public && (
                    <p className="small muted">
                      Additional input and expected output stay private.
                    </p>
                  )}
                </li>
              ))}
            </ul>
            {result.checks.length < result.total && (
              <p>
                Remaining checks were skipped after an execution limit was
                reached.
              </p>
            )}
            <p className="small muted">
              {(result.duration_ms / 1000).toFixed(1)} seconds including
              container setup · {selected?.version} · {result.profile}
            </p>
            <details>
              <summary>Code used for this run</summary>
              <pre>{selected?.code}</pre>
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => replaceSource(selected!.code)}
              >
                Load this code into editor
              </button>
            </details>
          </>
        )}
      </section>
      <section
        className="panel coding-editor-panel"
        aria-label="Coding run history"
      >
        <h2>Your run history</h2>
        <p>
          Earlier runs keep their code, test version and results. Loading old
          code does not change a recorded run.
        </p>
        {!data.attempts.length && <p>No recorded runs yet.</p>}
        <div className="version-list">
          {data.attempts.map((attempt) => (
            <button
              className={`version-button ${selected?.id === attempt.id ? "selected" : ""}`}
              key={attempt.id}
              onClick={() => setSelected(attempt)}
              aria-pressed={selected?.id === attempt.id}
            >
              <strong>
                Run {attempt.id} · {attempt.result.passed}/
                {attempt.result.total} passed
              </strong>
              <span>
                <DateLabel value={attempt.created_at} /> · {attempt.version}
              </span>
            </button>
          ))}
        </div>
      </section>
    </>
  );
}

export default function CodingExercise({
  params,
}: {
  params: Promise<{ exerciseId: string }>;
}) {
  const { exerciseId } = use(params);
  const { data, error, reload, setData } = useApi<CodingDetail>(
    `/coding/${exerciseId}`,
  );
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <Link className="text-link" href="/coding">
        ← Coding and SQL lab
      </Link>
      <PageHeading
        eyebrow={
          data.language === "python"
            ? "PYTHON 3.13 · FUNCTION CONTRACT"
            : "POSTGRESQL 17 · READ-ONLY QUERY"
        }
        title={data.title}
        description={data.prompt}
      />
      <p className="notice">
        {data.note}{" "}
        <Link className="text-link" href={`/lessons/${data.lesson_id}`}>
          Revisit related foundations →
        </Link>
      </p>
      {data.schema && (
        <section className="panel coding-editor-panel">
          <h2>Fixture tables</h2>
          <pre>{data.schema}</pre>
          <p>
            Each check gets its own PostgreSQL database. Only SELECT access to
            the fixture tables is granted.
          </p>
        </section>
      )}
      <section
        className="panel coding-editor-panel"
        aria-label="Public examples"
      >
        <h2>Public examples</h2>
        <p>
          {data.examples.length} examples are shown. The complete suite has{" "}
          {data.check_count} checks, including additional inputs.
        </p>
        {data.examples.map((example, index) => (
          <details key={index} open={index === 0}>
            <summary>{example.name}</summary>
            <pre>
              {example.setup_sql ||
                `Arguments: ${JSON.stringify(example.args, null, 2)}`}
            </pre>
            <pre>
              {example.columns
                ? `Columns: ${example.columns.join(", ")}\n`
                : ""}
              {example.error
                ? `Raise ${example.error}`
                : `Expected: ${JSON.stringify(example.expected, null, 2)}`}
            </pre>
          </details>
        ))}
      </section>
      <Editor
        key={data.id}
        data={data}
        refresh={() => void reload()}
        onUnavailable={(message) =>
          setData((old) =>
            old
              ? { ...old, runner: { ...old.runner, ready: false, message } }
              : old,
          )
        }
        onAttempt={(attempt) =>
          setData((old) =>
            old
              ? {
                  ...old,
                  attempts: [
                    attempt,
                    ...old.attempts.filter((a) => a.id !== attempt.id),
                  ].slice(0, 50),
                }
              : old,
          )
        }
      />
    </>
  );
}
