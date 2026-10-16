"use client";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ExerciseView } from "@/components/exercise-view";
export default function ExercisePage() {
  const { id } = useParams<{ id: string }>();
  const [review, setReview] = useState(false);
  useEffect(() => {
    setReview(
      new URLSearchParams(window.location.search).get("review") === "1",
    );
  }, []);
  return <ExerciseView key={id} id={id} review={review} />;
}
