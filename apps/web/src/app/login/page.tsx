"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BookOpen,
  Command,
  Eye,
  EyeOff,
  FlaskConical,
  RotateCcw,
} from "lucide-react";
import { api } from "@/lib/api";
import { ErrorNotice } from "@/components/ui";
export default function Login() {
  const [register, setRegister] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();
  useEffect(() => {
    setRegister(
      new URLSearchParams(window.location.search).get("mode") !== "signin",
    );
  }, []);
  function changeMode(next: boolean) {
    setRegister(next);
    setError("");
    setShowPassword(false);
    window.history.replaceState(
      null,
      "",
      next ? "/login" : "/login?mode=signin",
    );
  }
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    try {
      await api(`/auth/${register ? "register" : "login"}`, "POST", {
        name: form.get("name"),
        email: form.get("email"),
        password: form.get("password"),
      });
      router.push("/");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-page" id="main-content" tabIndex={-1}>
      <section className="login-story">
        <div className="brand">
          <span className="brand-mark">
            <Command size={24} />
          </span>
          <span>form.</span>
        </div>
        <div>
          <p className="eyebrow">Backend engineering & applied AI</p>
          <h2>Build the skills behind reliable systems.</h2>
          <p>
            A personal workspace to study the ideas, practise the decisions, and
            build evidence of what you know.
          </p>
          <ol className="login-learning-loop">
            <li>
              <BookOpen size={20} />
              <span>
                Learn<small>Clear lessons. Connected ideas.</small>
              </span>
            </li>
            <li>
              <FlaskConical size={20} />
              <span>
                Practise<small>Real problems. Useful feedback.</small>
              </span>
            </li>
            <li>
              <RotateCcw size={20} />
              <span>
                Revisit<small>Keep your understanding active.</small>
              </span>
            </li>
          </ol>
        </div>
        <footer>Your next chapter in engineering.</footer>
      </section>
      <section className="login-form">
        <div>
          <div className="brand login-mobile-brand">
            <span className="brand-mark">
              <Command size={22} />
            </span>
            <span>form.</span>
          </div>
          <p className="eyebrow">Your engineering academy</p>
          <h1>{register ? "Create your workspace." : "Welcome back."}</h1>
          <p>
            {register
              ? "A place for your learning, practice and progress."
              : "Sign in to continue your learning."}
          </p>
          <form onSubmit={submit}>
            {register && (
              <label>
                Your name
                <input
                  name="name"
                  required
                  minLength={1}
                  maxLength={80}
                  autoComplete="name"
                  placeholder="How should we call you?"
                />
              </label>
            )}
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoCapitalize="none"
                spellCheck={false}
                required
                autoComplete="email"
                placeholder="you@example.com"
              />
            </label>
            <label htmlFor="login-password">Password</label>
            <div className="password-input">
              <input
                id="login-password"
                name="password"
                type={showPassword ? "text" : "password"}
                required
                minLength={12}
                maxLength={256}
                autoComplete={register ? "new-password" : "current-password"}
                aria-describedby={register ? "password-help" : undefined}
                placeholder={
                  register ? "Choose a strong password" : "Your password"
                }
              />
              <button
                type="button"
                className="icon-button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {register && (
              <small id="password-help" className="field-help">
                Use at least 12 characters. Pasting a password is welcome.
              </small>
            )}
            {error && <ErrorNotice message={error} />}
            <button className="button primary" disabled={busy} aria-busy={busy}>
              {busy
                ? "Opening your workspace…"
                : register
                  ? "Create workspace"
                  : "Sign in"}
              <ArrowRight size={17} />
            </button>
          </form>
          <p className="auth-switch">
            {register ? "Already have an account?" : "New to the academy?"}{" "}
            <button
              onClick={() => {
                changeMode(!register);
              }}
            >
              {register ? "Sign in" : "Create workspace"}
            </button>
          </p>
          <div className="login-footnote">
            Your notes and progress are saved to your account. No AI account is
            needed.
          </div>
          <p>
            <Link className="text-link" href="/recover">
              Forgot password? Use your saved recovery key.
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
