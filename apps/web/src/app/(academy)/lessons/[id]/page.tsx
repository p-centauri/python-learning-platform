"use client";
import { useParams } from "next/navigation";
import { LessonView } from "@/components/lesson-view";
export default function LessonPage() {
  const { id } = useParams<{ id: string }>();
  return <LessonView key={id} id={id} />;
}
