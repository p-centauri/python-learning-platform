"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="empty" role="alert">
      <h2>Something interrupted this page.</h2>
      <p>Your saved work is still in the academy database.</p>
      <button className="button primary" onClick={reset}>
        Try again
      </button>
    </div>
  );
}
