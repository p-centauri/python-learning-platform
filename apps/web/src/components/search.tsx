"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Search, X, ArrowUpRight } from "lucide-react";
import { api } from "@/lib/api";

export function SearchDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<
    { type: string; title: string; href: string }[]
  >([]);
  const [status, setStatus] = useState("");
  useEffect(() => {
    if (open) {
      dialog.current?.showModal();
      input.current?.focus();
    } else dialog.current?.close();
  }, [open]);
  useEffect(() => {
    let live = true;
    if (query.trim().length < 2) {
      setResults([]);
      setStatus("");
      return;
    }
    setResults([]);
    setStatus("Searching…");
    const timer = setTimeout(async () => {
      try {
        const found = await api<typeof results>(
          `/search?q=${encodeURIComponent(query.trim())}`,
        );
        if (live) {
          setResults(found);
          setStatus(
            found.length
              ? `${found.length} results`
              : "No matching content found. Try another topic.",
          );
        }
      } catch (e) {
        if (live) setStatus(e instanceof Error ? e.message : "Search failed.");
      }
    }, 200);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [query]);
  return (
    <dialog
      ref={dialog}
      className="search-dialog"
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === dialog.current) onClose();
      }}
      aria-label="Search academy"
    >
      <div className="search-field">
        <Search size={20} />
        <input
          ref={input}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search lessons, exercises, projects, notes, glossary…"
          aria-label="Search query"
        />
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close search"
        >
          <X size={18} />
        </button>
      </div>
      <div className="search-results">
        {status && <p role="status">{status}</p>}
        {query.trim().length < 2 && (
          <p>
            Find a lesson, exercise, project or saved note. Type at least two
            characters.
          </p>
        )}
        {results.map((result, i) => {
          return (
            <Link
              key={`${result.type}-${i}`}
              href={result.href}
              onClick={() => {
                onClose();
                if (result.type === "Glossary") {
                  window.dispatchEvent(
                    new CustomEvent("academy:glossary-navigation", {
                      detail: result.href.split("#")[1],
                    }),
                  );
                }
              }}
            >
              <span>
                <small>{result.type}</small>
                {result.title}
              </span>
              <ArrowUpRight size={16} />
            </Link>
          );
        })}
      </div>
      <footer>
        <kbd>esc</kbd> to close <span>Search never includes answer keys.</span>
      </footer>
    </dialog>
  );
}
