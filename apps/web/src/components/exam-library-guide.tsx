import type { ExamDefinition } from "@/lib/types";

export function ExamLibraryGuide({ exam }: { exam: ExamDefinition }) {
  if (!exam.libraries.length) return null;
  return (
    <details className="library-guide">
      <summary>{exam.level} Python: libraries and expected abilities</summary>
      <p className="muted small">{exam.library_note}</p>
      <ul className="library-list">
        {exam.libraries.map((library) => (
          <li key={library.name}>
            <div>
              <a href={library.url} target="_blank" rel="noopener noreferrer">
                {library.name} ↗
              </a>
              <span className="badge">{library.kind}</span>
            </div>
            <p>{library.expectation}</p>
          </li>
        ))}
      </ul>
      <h3>Prove it in code next</h3>
      <p className="muted small">{exam.practical_followup}</p>
    </details>
  );
}
