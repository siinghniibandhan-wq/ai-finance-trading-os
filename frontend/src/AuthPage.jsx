import React, { useEffect, useState } from "react";
import { ArrowRight, CircleDollarSign, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { API_BASE_URL, saveSession, friendlyErrorMessage, describeError } from "./api";
import "./social-login.css";

// Plain-language reasons shown when Google / GitHub sign-in does not complete.
const SOCIAL_ERRORS = {
  not_configured: "This sign-in option is not available yet.",
  cancelled: "Sign-in was cancelled. You can try again.",
  invalid_state: "That sign-in link expired. Please try again.",
  email_unverified: "Your account has no verified email address, so we could not sign you in.",
  account_disabled: "This account is switched off. Please contact support.",
  provider_error: "We could not reach the sign-in provider. Please try again.",
  try_again: "Something went wrong. Please try again.",
};

function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.1C12.4 13.6 17.7 9.5 24 9.5z"/>
      <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4.1 7.1-10.1 7.1-17.5z"/>
      <path fill="#FBBC05" d="M10.5 28.7c-.5-1.5-.8-3-.8-4.7s.3-3.2.8-4.7l-7.9-6.1C.9 16.4 0 20.1 0 24s.9 7.6 2.6 10.8l7.9-6.1z"/>
      <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.5-5.8c-2.1 1.4-4.8 2.3-8.4 2.3-6.3 0-11.6-4.1-13.5-9.8l-7.9 6.1C6.5 42.6 14.6 48 24 48z"/>
    </svg>
  );
}

function GitHubMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
    </svg>
  );
}

const SOCIAL_MARKS = { google: <GoogleMark />, github: <GitHubMark /> };

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
  const [socialProviders, setSocialProviders] = useState([]);

  // Show only the sign-in buttons the server has set up, and any message from a previous attempt.
  useEffect(() => {
    const reason = new URLSearchParams(window.location.search).get("social_error");
    if (reason) {
      setError(SOCIAL_ERRORS[reason] || SOCIAL_ERRORS.try_again);
      window.history.replaceState({}, "", window.location.pathname);
    }
    let cancelled = false;
    fetch(`${API_BASE_URL}/api/auth/social/providers`, { headers: { Accept: "application/json" } })
      .then((response) => (response.ok ? response.json() : { providers: [] }))
      .then((data) => { if (!cancelled && Array.isArray(data?.providers)) setSocialProviders(data.providers); })
      .catch(() => { /* Email sign-in still works without the buttons. */ });
    return () => { cancelled = true; };
  }, []);

  const startSocialLogin = (providerId) => {
    window.location.href = `${API_BASE_URL}/api/auth/social/${encodeURIComponent(providerId)}/start`;
  };

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

        {socialProviders.length > 0 && (
          <div className="auth-social">
            <div className="auth-social-divider"><span>or continue with</span></div>
            <div className="auth-social-buttons">
              {socialProviders.map((provider) => (
                <button key={provider.id} type="button" className="auth-social-button"
                  onClick={() => startSocialLogin(provider.id)}>
                  {SOCIAL_MARKS[provider.id]}
                  <span>{provider.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

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
