import { ChangeEvent, FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";

const PASSWORD_MIN = 8; // matches backend/auth.py

export default function CreateAccount() {
  const { user, signup } = useAuth();
  const navigate = useNavigate();
  const [fields, setFields] = useState({ first_name: "", last_name: "", email: "", password: "" });
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user && !busy) return <Navigate to="/" replace />;

  const set = (key: keyof typeof fields) => (e: ChangeEvent<HTMLInputElement>) =>
    setFields((f) => ({ ...f, [key]: e.target.value }));

  const mismatch = confirm.length > 0 && confirm !== fields.password;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (fields.password.length < PASSWORD_MIN) {
      setError(`Password must be at least ${PASSWORD_MIN} characters.`);
      return;
    }
    if (fields.password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
    setBusy(true);
    try {
      await signup(fields);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "We couldn't reach the server. Please try again.");
      setBusy(false);
    }
  }

  return (
    <section className="form-card">
      <h1>Create account</h1>
      <form onSubmit={submit}>
        <div className="form-row">
          <label>
            First name
            <input
              name="first_name"
              autoComplete="given-name"
              value={fields.first_name}
              onChange={set("first_name")}
              maxLength={60}
              required
            />
          </label>
          <label>
            Last name
            <input
              name="last_name"
              autoComplete="family-name"
              value={fields.last_name}
              onChange={set("last_name")}
              maxLength={60}
              required
            />
          </label>
        </div>
        <label>
          Email
          <input
            type="email"
            name="email"
            autoComplete="email"
            value={fields.email}
            onChange={set("email")}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            value={fields.password}
            onChange={set("password")}
            minLength={PASSWORD_MIN}
            maxLength={128}
            aria-describedby="password-hint"
            required
          />
          <span id="password-hint" className="field-hint">
            At least {PASSWORD_MIN} characters.
          </span>
        </label>
        <label>
          Confirm password
          <input
            type="password"
            name="confirm_password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            aria-invalid={mismatch}
            aria-describedby={mismatch ? "confirm-hint" : undefined}
            required
          />
          {mismatch && (
            <span id="confirm-hint" className="field-hint field-hint-error">
              Passwords don't match yet.
            </span>
          )}
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="button" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className="form-footer">
        Already have an account? <Link to="/login" className="text-link">Log in</Link>
      </p>
    </section>
  );
}
