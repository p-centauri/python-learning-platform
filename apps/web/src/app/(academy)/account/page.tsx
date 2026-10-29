"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, useApi } from "@/lib/api";
import { useUser } from "@/components/shell";
import { DateLabel, ErrorNotice, Loading, PageHeading } from "@/components/ui";

type Account = {
  recovery_enabled: boolean;
  recovery_created_at: string | null;
  recovery_used_at: string | null;
  note: string;
};
type Session = { id: string; current: boolean; expires_at: string };
export default function AccountPage() {
  const { data, error, reload } = useApi<Account>("/account");
  const {
    data: sessions,
    error: sessionError,
    reload: reloadSessions,
  } = useApi<Session[]>("/account/sessions");
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [status, setStatus] = useState("");
  const router = useRouter();
  const user = useUser();
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setActionError("");
    setStatus("");
    try {
      await work();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function generate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const password = new FormData(form).get("current_password");
    await action(async () => {
      const row = await api<{ recovery_key: string }>(
        "/account/recovery-key",
        "POST",
        { current_password: password },
      );
      setKey(row.recovery_key);
      form.reset();
      await reload();
      setStatus("New recovery key created. The previous key no longer works.");
    });
  }
  function downloadKey() {
    const url = URL.createObjectURL(
      new Blob(
        [
          `Forge academy offline recovery\nAccount: ${user?.email}\nRecovery key: ${key}\n\nKeep this private and offline. It works once until revoked or your password changes. No email is sent.\n`,
        ],
        { type: "text/plain" },
      ),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "academy-recovery-key.txt";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function changePassword(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      await api("/account/password", "POST", {
        current_password: form.get("current_password"),
        new_password: form.get("new_password"),
        confirm_password: form.get("confirm_password"),
      });
      router.replace("/login?mode=signin");
    });
  }
  if (error) return <ErrorNotice message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeading
        eyebrow="YOUR ACCOUNT AND EVIDENCE"
        title="Keep access. Keep your work."
        description="Protect your sign-in and download the learning evidence you have saved."
      />
      {actionError && <ErrorNotice message={actionError} />}
      <p role="status">{status}</p>
      <section
        className="panel account-section"
        aria-label="Offline account recovery"
      >
        <h2>Save an offline recovery key</h2>
        <p>{data.note}</p>
        <p>
          Set this up while you can sign in. A key is shown only when created.
          Keep it private and offline. If you lose both your password and key,
          this app cannot recover your account automatically.
        </p>
        <p>
          {data.recovery_enabled
            ? "Recovery key is active."
            : data.recovery_used_at
              ? "The last key was used. Create a new one."
              : "No active recovery key."}
          {data.recovery_created_at && (
            <>
              {" "}
              Created <DateLabel value={data.recovery_created_at} />.
            </>
          )}
        </p>
        <form onSubmit={generate}>
          <fieldset disabled={busy}>
            <label>
              Current password for recovery setup
              <input
                name="current_password"
                type="password"
                minLength={12}
                maxLength={256}
                autoComplete="current-password"
                required
              />
            </label>
            <button className="button primary">
              {data.recovery_enabled
                ? "Generate a replacement recovery key"
                : "Generate recovery key"}
            </button>
          </fieldset>
        </form>
        {key && (
          <div className="notice">
            <h3>Your new recovery key</h3>
            <label>
              New recovery key
              <input
                readOnly
                value={key}
                className="recovery-value"
                autoComplete="off"
              />
            </label>
            <p>
              This key grants password-reset access. It will not appear again
              after leaving or reloading this page.
            </p>
            <button className="button secondary" onClick={downloadKey}>
              Save recovery key file
            </button>
            <button className="text-button" onClick={() => setKey("")}>
              Hide this key
            </button>
          </div>
        )}
        {data.recovery_enabled && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const form = e.currentTarget;
              const password = new FormData(form).get("current_password");
              void action(async () => {
                await api("/account/recovery-key", "DELETE", {
                  current_password: password,
                });
                setKey("");
                form.reset();
                await reload();
                setStatus("Recovery key revoked.");
              });
            }}
          >
            <fieldset disabled={busy}>
              <label>
                Current password to revoke key
                <input
                  name="current_password"
                  type="password"
                  minLength={12}
                  maxLength={256}
                  autoComplete="current-password"
                  required
                />
              </label>
              <button className="button secondary">Revoke recovery key</button>
            </fieldset>
          </form>
        )}
      </section>
      <section
        className="panel account-section"
        aria-label="Evidence downloads"
      >
        <h2>Download your learning evidence</h2>
        <p>
          Includes your saved notes, drafts, attempts, results, checklists and
          owned project feedback. Active answer keys and credentials are
          excluded. Keep the file private if it contains sensitive notes or
          source code.
        </p>
        <p>
          JSON preserves the complete structure. Markdown provides a readable
          report. These exports do not restore the database or certify mastery.
        </p>
        <div className="submission-actions">
          <a
            className="button secondary"
            href="/api/account/export?format=json"
            download
          >
            Download evidence JSON
          </a>
          <a
            className="button secondary"
            href="/api/account/export?format=markdown"
            download
          >
            Download evidence Markdown
          </a>
        </div>
      </section>
      <section
        className="panel account-section"
        aria-label="Signed-in sessions"
      >
        <h2>Manage signed-in sessions</h2>
        <p>
          Remove a session to require sign-in again. Device identity is not
          inferred; each row is a separate sign-in.
        </p>
        {sessionError && (
          <ErrorNotice message={sessionError} retry={reloadSessions} />
        )}
        <ul className="session-list">
          {sessions?.map((s, i) => (
            <li key={s.id}>
              <span>
                {s.current ? "This session" : `Other sign-in ${i + 1}`} ·
                expires <DateLabel value={s.expires_at} />
              </span>
              <button
                className="button secondary"
                disabled={busy}
                onClick={() =>
                  void action(async () => {
                    await api(`/account/sessions/${s.id}`, "DELETE");
                    if (s.current) router.replace("/login?mode=signin");
                    else {
                      await reloadSessions();
                      setStatus("Session signed out.");
                    }
                  })
                }
              >
                {s.current ? "Sign out this session" : "Sign out session"}
              </button>
            </li>
          ))}
        </ul>
      </section>
      <section className="panel account-section" aria-label="Change password">
        <h2>Change your password</h2>
        <p>
          Changing it signs out every session and revokes the previous recovery
          key. Sign in again and save a new recovery key.
        </p>
        <form onSubmit={changePassword}>
          <fieldset disabled={busy}>
            <label>
              Current password
              <input
                name="current_password"
                type="password"
                minLength={12}
                maxLength={256}
                autoComplete="current-password"
                required
              />
            </label>
            <label>
              New password
              <input
                name="new_password"
                type="password"
                minLength={12}
                maxLength={256}
                autoComplete="new-password"
                required
              />
            </label>
            <label>
              Confirm new password
              <input
                name="confirm_password"
                type="password"
                minLength={12}
                maxLength={256}
                autoComplete="new-password"
                required
              />
            </label>
            <button className="button primary">
              Change password and sign out
            </button>
          </fieldset>
        </form>
      </section>
    </>
  );
}
