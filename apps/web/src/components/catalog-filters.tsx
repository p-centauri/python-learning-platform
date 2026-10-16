"use client";
import { Search, X } from "lucide-react";
import { useId } from "react";
import type { Track } from "@/lib/types";

export function CatalogFilters({
  query,
  onQuery,
  track,
  onTrack,
  status,
  onStatus,
  tracks,
  count,
  total,
  noun = "lessons",
}: {
  query: string;
  onQuery: (value: string) => void;
  track: string;
  onTrack: (value: string) => void;
  status?: string;
  onStatus?: (value: string) => void;
  tracks: Track[];
  count: number;
  total: number;
  noun?: string;
}) {
  const id = useId();
  const filtered = Boolean(query || track || (status && status !== "all"));
  return (
    <section className="catalog-toolbar" aria-label="Filter curriculum">
      <div className="catalog-controls">
        <label className="catalog-search" htmlFor={`${id}-search`}>
          <span className="sr-only">Search topics</span>
          <Search size={19} aria-hidden="true" />
          <input
            id={`${id}-search`}
            type="search"
            placeholder="Find a topic or lesson…"
            value={query}
            onChange={(event) => onQuery(event.target.value)}
          />
        </label>
        <label className="catalog-select">
          <span className="sr-only">Track</span>
          <select
            aria-label="Track"
            value={track}
            onChange={(event) => onTrack(event.target.value)}
          >
            <option value="">All tracks</option>
            {tracks.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        </label>
        {onStatus && (
          <label className="catalog-select">
            <span className="sr-only">Reading status</span>
            <select
              aria-label="Reading status"
              value={status}
              onChange={(event) => onStatus(event.target.value)}
            >
              <option value="all">All reading</option>
              <option value="unread">Not yet read</option>
              <option value="completed">Reading complete</option>
            </select>
          </label>
        )}
      </div>
      <div className="catalog-result-row">
        <p role="status">
          {count} of {total} {noun}
          {filtered ? " match your filters" : " available"}
        </p>
        {filtered && (
          <button
            className="text-button clear-filters"
            onClick={() => {
              onQuery("");
              onTrack("");
              onStatus?.("all");
            }}
          >
            <X size={15} aria-hidden="true" />
            Clear filters
          </button>
        )}
      </div>
    </section>
  );
}

export function CatalogMore({
  shown,
  total,
  onMore,
}: {
  shown: number;
  total: number;
  onMore: () => void;
}) {
  if (!total) return null;
  return (
    <div className="catalog-more">
      <p>
        Showing {shown} of {total} topics
      </p>
      {shown < total && (
        <button className="button secondary" onClick={onMore}>
          Show more topics
        </button>
      )}
    </div>
  );
}
