"use client";
import { use } from "react";
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { ProjectSubmission } from "@/lib/types";
import { ErrorNotice, Loading, PageHeading } from "@/components/ui";
import {
  FeedbackHistory,
  ReviewForm,
  Rubric,
  SubmissionEvidence,
} from "@/components/project-review";

export default function ReviewSubmission({
  params,
}: {
  params: Promise<{ submissionId: string }>;
}) {
  const { submissionId } = use(params);
  const { data, error, reload, setData } = useApi<ProjectSubmission>(
    `/project-submissions/${submissionId}`,
  );
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <Link className="text-link" href="/project-reviews">
        ← Review workspace
      </Link>
      <PageHeading
        eyebrow={`REVIEW · VERSION ${data.revision}`}
        title={data.rubric.project_title}
        description={`Work submitted by ${data.owner_name}. Check the revision reference before reviewing.`}
      />
      <Rubric rubric={data.rubric} />
      <SubmissionEvidence row={data} />
      <FeedbackHistory row={data} />
      <ReviewForm row={data} onSaved={setData} />
    </>
  );
}
