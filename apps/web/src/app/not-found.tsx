import Link from "next/link";
export default function NotFound() {
  return (
    <main className="auth-loading">
      <h1>This page isn’t in your learning path.</h1>
      <Link className="button primary" href="/">
        Return to your workspace
      </Link>
    </main>
  );
}
