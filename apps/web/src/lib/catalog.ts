import type { Lesson } from "./types";

export function filterLessons(
  lessons: Lesson[],
  query: string,
  track: string,
  status = "all",
) {
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return lessons.filter((lesson) => {
    const text =
      `${lesson.title} ${lesson.summary} ${lesson.skill}`.toLowerCase();
    return (
      (!track || lesson.track_id === track) &&
      terms.every((term) => text.includes(term)) &&
      (status === "all" ||
        (status === "completed" ? lesson.completed : !lesson.completed))
    );
  });
}
