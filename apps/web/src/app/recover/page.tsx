"use client";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { ErrorNotice } from "@/components/ui";
export default function Recover() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      await api("/account/recover", "POST", {
        email: form.get("email"),
        recovery_key: form.get("recovery_key"),
        new_password: form.get("new_password"),
        confirm_password: form.get("confirm_password"),
      });
      setDone(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main-content" className="recovery-page">
      <section className="panel account-section">
        <p className="eyebrow">OFFLINE ACCOUNT RECOVERY</p>
        <h1>{done ? "Your password has changed." : "Recover your account."}</h1>
        {done ? (
          <>
            <p>
              Your recovery key was consumed and all sessions are signed out.
              Sign in with your new password, then save a new key in Account &
              evidence.
            </p>
            <Link className="button primary" href="/login?mode=signin">
              Return to sign in
            </Link>
          </>
        ) : (
          <>
            <p>
              Use the recovery key you previously saved from your account. No
              recovery email is sent. Without that key, this app cannot reset a
              forgotten password automatically.
            </p>
            <form onSubmit={submit}>
              <fieldset disabled={busy}>
                <label>
                  Email address
                  <input
                    name="email"
                    type="email"
                    autoComplete="username"
                    required
                  />
                </label>
                <label>
                  Offline recovery key
                  <input
                    name="recovery_key"
                    type="password"
                    autoComplete="off"
                    required
                    maxLength={128}
                  />
                </label>
                <label>
                  New password
                  <input
                    name="new_password"
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={12}
                    maxLength={256}
                  />
                </label>
                <label>
                  Confirm new password
                  <input
                    name="confirm_password"
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={12}
                    maxLength={256}
                  />
                </label>
                {error && <ErrorNotice message={error} />}
                <button className="button primary">
                  {busy ? "Resetting…" : "Reset password and sign out sessions"}
                </button>
              </fieldset>
            </form>
            <p>
              <Link className="text-link" href="/login?mode=signin">
                Return to sign in
              </Link>
            </p>
          </>
        )}
      </section>
    </main>
  );
}
