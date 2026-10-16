"use client";
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { ReviewInboxItem } from "@/lib/types";
import {
  DateLabel,
  Empty,
  ErrorNotice,
  Loading,
  PageHeading,
} from "@/components/ui";

export default function ReviewWorkspace() {
  const { data, error, reload } = useApi<ReviewInboxItem[]>("/project-reviews");
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeading
        eyebrow="REVIEW ANOTHER LEARNER'S WORK"
        title="Review workspace"
        description="Read the submitted version, inspect its evidence, and record useful feedback against its rubric."
      />
      <p className="notice">
        Invitations match the email you use to sign in. Reviews record your
        judgment; reviewer qualifications and reported tests are not verified by
        the academy.
      </p>
      {!data.length && (
        <Empty title="No review invitations yet">
          Ask the project owner to invite your account email after submitting
          their work.
        </Empty>
      )}
      <div className="review-inbox">
        {data.map((row) => (
          <Link
            className="panel submission-section"
            href={`/project-reviews/${row.id}`}
            key={row.id}
          >
            <p className="overline">
              VERSION {row.revision} ·{" "}
              {row.reviewed ? "FEEDBACK RECORDED" : "AWAITING YOUR REVIEW"}
            </p>
            <h2>{row.title}</h2>
            <p>
              Submitted by {row.owner_name} ·{" "}
              <DateLabel value={row.submitted_at} />
            </p>
            <span className="text-link">
              {row.reviewed
                ? "Read recorded feedback"
                : "Open submission and rubric"}{" "}
              →
            </span>
          </Link>
        ))}
      </div>
    </>
  );
}
