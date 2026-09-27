import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../lib/auth";
import type { Role } from "../lib/types";
import { Icon } from "./Icon";

// The demo firm's accounts, so a judge only has to type the password.
const DEMO_EMAIL: Record<Role, string> = {
  admin: "priya.raman@studiomeridian.example",
  employee: "alex.rivera@studiomeridian.example",
};

const CHOICES: { role: Role; title: string; body: string; icon: "chart" | "book" }[] = [
  { role: "admin", title: "Admin", body: "Track onboarding across the firm and set up modules.", icon: "chart" },
  { role: "employee", title: "Employee", body: "Work through your onboarding modules and checklist.", icon: "book" },
];

export function LoginModal({ onClose }: { onClose: () => void }) {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState<Role | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    dialogRef.current?.querySelector<HTMLElement>("button, input")?.focus();
  }, [role]);

  const choose = (r: Role) => {
    setRole(r);
    setEmail(DEMO_EMAIL[r]);
    setPassword("");
    setError(null);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!role) return;
    setBusy(true);
    setError(null);
    try {
      const me = await signIn(email, password, role);
      onClose();
      navigate(me.role === "admin" ? "/admin" : "/app");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="login-title" ref={dialogRef} style={{ color: "var(--color-text)" }}>
        <div className="modal-header">
          <h2 id="login-title">{role ? `Sign in as ${role === "admin" ? "admin" : "employee"}` : "Log in"}</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            <Icon name="close" />
          </button>
        </div>

        {role === null ? (
          <div className="stack">
            <p>How are you signing in?</p>
            {CHOICES.map((c) => (
              <button key={c.role} type="button" className="card login-choice" onClick={() => choose(c.role)}>
                <span className="card-header">
                  <span className="status-row">
                    <Icon name={c.icon} size={22} />
                    <h3>{c.title}</h3>
                  </span>
                  <Icon name="arrowRight" />
                </span>
                <span>{c.body}</span>
              </button>
            ))}
          </div>
        ) : (
          <form className="stack" onSubmit={submit}>
            <div className="field">
              <label htmlFor="login-email">Email</label>
              <input id="login-email" className="input" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="login-password">Password</label>
              <input id="login-password" className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={() => setRole(null)}>
                Back
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                {busy ? "Signing in…" : "Sign in"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
