import React, { useState } from "react";
import { ArrowRight, CircleDollarSign, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { API_BASE_URL, saveSession, friendlyErrorMessage, describeError } from "./api";

// Login and registration use the shared Financial OS theme tokens.
export default function AuthPage({ initialMode = "login" }) {
  const [mode, setMode] = useState(initialMode);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [currency, setCurrency] = useState("INR");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    setLoading(true);
    try {
      const isRegister = mode === "register";
      const response = await fetch(`${API_BASE_URL}/api/auth/${isRegister ? "register" : "login"}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(
          isRegister
            ? { name: name.trim(), email: email.trim(), password, currency }
            : { email: email.trim(), password }
        ),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = friendlyErrorMessage(response.status, data);
        throw new Error(detail);
      }
      if (isRegister) {
        setMode("login");
        setPassword("");
        setNotice("Account created. Please sign in to open your workspace.");
        return;
      }
      saveSession(data);
      window.location.replace("/app");
    } catch (err) {
      setError(describeError(err, "Unable to connect. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (next) => {
    setMode(next);
    setError("");
    setNotice("");
  };

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-heading">
        <a href="/" className="auth-brand wealth-auth-brand">
          <img src="/wealth-manager-mark.svg" alt="" className="auth-brand-logo" />
          <span className="wealth-auth-wordmark"><strong>WEALTH</strong><small>MANAGER</small></span>
        </a>
        <div className="auth-eyebrow"><ShieldCheck size={16} /> Secure customer workspace</div>
        <h1 id="auth-heading">{mode === "register" ? "Create your account" : "Welcome back"}</h1>
        <p className="auth-description">
          {mode === "register"
            ? "Create your own private financial workspace."
            : "Sign in to access your personal financial workspace."}
        </p>

        {error && <div className="auth-message is-error" role="alert">{error}</div>}
        {notice && <div className="auth-message is-success" role="status">{notice}</div>}

        <form className="auth-form" onSubmit={submit}>
          {mode === "register" && (
            <label>Full name
              <input autoComplete="name" required maxLength={150} value={name}
                onChange={(event) => setName(event.target.value)} placeholder="Your name" />
            </label>
          )}
          <label>{mode === "register" ? "Email address" : "Email or phone number"}
            <input autoComplete={mode === "register" ? "email" : "username"}
              type={mode === "register" ? "email" : "text"} required
              minLength={5} maxLength={255} value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder={mode === "register" ? "you@example.com" : "Email address or phone number"} />
          </label>
          <label>Password <span className="auth-field-hint">
            {mode === "register" ? "(minimum 12 characters)" : ""}
          </span>
            <span className="auth-password-field">
              <input autoComplete={mode === "register" ? "new-password" : "current-password"}
                type={showPassword ? "text" : "password"} required
                minLength={mode === "register" ? 12 : 1} maxLength={128}
                value={password} onChange={(event) => setPassword(event.target.value)}
                placeholder={mode === "register" ? "At least 12 characters" : "Enter your password"} />
              <button type="button" className="auth-password-toggle"
                aria-label={showPassword ? "Hide password" : "Show password"}
                onClick={() => setShowPassword((value) => !value)}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </span>
          </label>
          {mode === "register" && (
            <label>Currency
              <select value={currency} onChange={(event) => setCurrency(event.target.value)}>
                <option value="INR">INR — Indian Rupee</option>
                <option value="USD">USD — US Dollar</option>
                <option value="GBP">GBP — British Pound</option>
                <option value="EUR">EUR — Euro</option>
              </select>
            </label>
          )}
          <button className="auth-submit" disabled={loading} type="submit">
            {loading ? "Please wait…" : mode === "register" ? "Create account" : "Sign in"}
            {!loading && <ArrowRight size={17} />}
          </button>
        </form>

        <div className="auth-switch">
          {mode === "register" ? "Already registered? " : "New to Financial OS? "}
          <button type="button" onClick={() => switchMode(mode === "register" ? "login" : "register")}>
            {mode === "register" ? "Sign in" : "Create an account"}
          </button>
        </div>
        <p className="auth-security-note">
          Your financial records should be accessible only to your authenticated account.
          Admin activation and subscription billing are managed separately.
        </p>
      </section>
    </main>
  );
}
