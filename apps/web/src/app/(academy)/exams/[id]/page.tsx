"use client";
import { useParams } from "next/navigation";
import { ExamView } from "@/components/exam-view";
import { ComprehensiveExam } from "@/components/comprehensive-exam";
import { useApi } from "@/lib/api";
import { ErrorNotice, Loading } from "@/components/ui";
export default function ExamPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<{ exam_id: string }>(
    `/exams/attempts/${id}`,
  );
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  if (
    [
      "engineering-knowledge-v1",
      "practical-repair-v1",
      "senior-design-v1",
    ].includes(data.exam_id)
  )
    return <ComprehensiveExam id={id} />;
  return <ExamView id={id} />;
}
