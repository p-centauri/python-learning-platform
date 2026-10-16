import type { RecallEvidence, RecallKind } from "@/lib/types";

export const recallLabels: Record<RecallKind, string> = {
  "fresh-delayed": "Delayed check · unseen question",
  "repeated-delayed": "Delayed practice · repeated question",
  immediate: "Immediate practice",
  assisted: "Assisted practice",
};
export function RecallDueTime({ value }: { value: string }) {
  return (
    <time dateTime={value}>
      {new Date(value).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short",
      })}
    </time>
  );
}
export function RecallEvidenceCard({
  title,
  value,
  description,
}: {
  title: string;
  value: RecallEvidence;
  description: string;
}) {
  return (
    <section className="panel recall-evidence">
      <h3>{title}</h3>
      <p className="recall-count">
        {value.total
          ? `${value.correct}/${value.total} correct`
          : "Not checked yet"}
      </p>
      <p className="small muted">{description}</p>
    </section>
  );
}
