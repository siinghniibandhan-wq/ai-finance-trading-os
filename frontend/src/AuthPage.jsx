import React, { useState } from "react";
import { ArrowRight, CircleDollarSign, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { API_BASE_URL, saveSession } from "./api";

// ============================================================
// LOGIN / REGISTRATION
// Passwords are sent only to the backend over HTTPS.
// ============================================================
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
          isRegister ? { name: name.trim(), email: email.trim(), password, currency } :
            { email: email.trim(), password }
        ),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : `Request failed (${response.status}).`;
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
      setError(err?.message || "Unable to connect. Please try again.");
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
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 20, background: "radial-gradient(circle at top left, #28205a 0, #0b0d1a 44%, #080a12 100%)", color: "#f5f5ff", fontFamily: "Inter, system-ui, sans-serif" }}>
      <section style={{ width: "min(100%, 440px)", padding: 28, borderRadius: 22, border: "1px solid rgba(255,255,255,.12)", background: "rgba(16,19,38,.94)", boxShadow: "0 24px 80px rgba(0,0,0,.3)" }}>
        <a href="/" style={{ display: "flex", alignItems: "center", gap: 12, color: "inherit", textDecoration: "none", marginBottom: 28 }}>
          <span style={{ display: "grid", placeItems: "center", width: 44, height: 44, borderRadius: 14, background: "linear-gradient(135deg,#8b5cf6,#ec4899,#f97316)" }}><CircleDollarSign size={24} /></span>
          <span><strong style={{ display: "block", fontSize: 19 }}>Financial OS</strong><small style={{ color: "#aeb5d0" }}>Your Financial Command Center</small></span>
        </a>
        <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#b9a5ff", fontSize: 12, letterSpacing: 1.1, fontWeight: 700, textTransform: "uppercase" }}><ShieldCheck size={16} /> Secure customer workspace</div>
        <h1 style={{ fontSize: 29, margin: "12px 0 8px" }}>{mode === "register" ? "Create your account" : "Welcome back"}</h1>
        <p style={{ color: "#aeb5d0", lineHeight: 1.55, marginTop: 0 }}>{mode === "register" ? "Create your own private financial workspace." : "Sign in to access your personal financial workspace."}</p>

        {error && <div role="alert" style={{ padding: 12, borderRadius: 10, margin: "16px 0", background: "rgba(248,113,113,.12)", border: "1px solid rgba(248,113,113,.35)", color: "#fecaca" }}>{error}</div>}
        {notice && <div role="status" style={{ padding: 12, borderRadius: 10, margin: "16px 0", background: "rgba(52,211,153,.12)", border: "1px solid rgba(52,211,153,.35)", color: "#a7f3d0" }}>{notice}</div>}

        <form onSubmit={submit} style={{ display: "grid", gap: 14, marginTop: 20 }}>
          {mode === "register" && <label style={labelStyle}>Full name<input autoComplete="name" required maxLength={150} value={name} onChange={e => setName(e.target.value)} placeholder="Your name" style={inputStyle} /></label>}
          <label style={labelStyle}>Email address<input autoComplete="email" type="email" required maxLength={255} value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" style={inputStyle} /></label>
          <label style={labelStyle}>Password <span style={{ color: "#8f97b7", fontWeight: 400 }}>{mode === "register" ? "(minimum 12 characters)" : ""}</span>
            <span style={{ display: "flex", position: "relative" }}>
              <input autoComplete={mode === "register" ? "new-password" : "current-password"} type={showPassword ? "text" : "password"} required minLength={mode === "register" ? 12 : 1} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} placeholder={mode === "register" ? "At least 12 characters" : "Enter your password"} style={{ ...inputStyle, paddingRight: 44 }} />
              <button type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword(v => !v)} style={{ position: "absolute", right: 8, top: 8, background: "transparent", border: 0, color: "#aeb5d0", padding: 6, cursor: "pointer" }}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button>
            </span>
          </label>
          {mode === "register" && <label style={labelStyle}>Currency<select value={currency} onChange={e => setCurrency(e.target.value)} style={inputStyle}><option value="INR">INR — Indian Rupee</option><option value="USD">USD — US Dollar</option><option value="GBP">GBP — British Pound</option><option value="EUR">EUR — Euro</option></select></label>}
          <button disabled={loading} type="submit" style={{ marginTop: 6, display: "flex", justifyContent: "center", alignItems: "center", gap: 9, border: 0, borderRadius: 12, padding: "13px 16px", fontWeight: 750, color: "white", cursor: loading ? "wait" : "pointer", background: "linear-gradient(100deg,#7c3aed,#db2777,#f97316)", opacity: loading ? .7 : 1 }}>{loading ? "Please wait…" : mode === "register" ? "Create account" : "Sign in"} {!loading && <ArrowRight size={17} />}</button>
        </form>

        <div style={{ textAlign: "center", color: "#aeb5d0", marginTop: 22, fontSize: 14 }}>
          {mode === "register" ? "Already registered? " : "New to Financial OS? "}
          <button type="button" onClick={() => switchMode(mode === "register" ? "login" : "register")} style={{ color: "#d8b4fe", fontWeight: 700, background: "none", border: 0, cursor: "pointer" }}>{mode === "register" ? "Sign in" : "Create an account"}</button>
        </div>
        <p style={{ color: "#77809f", fontSize: 11, lineHeight: 1.5, margin: "20px 0 0" }}>Your financial records should be accessible only to your authenticated account. Admin activation and subscription billing are managed separately.</p>
      </section>
    </main>
  );
}

const labelStyle = { display: "grid", gap: 7, color: "#dce0f5", fontSize: 13, fontWeight: 650 };
const inputStyle = { width: "100%", boxSizing: "border-box", borderRadius: 10, padding: "12px 13px", color: "#f5f5ff", background: "#0b0e1c", border: "1px solid #303650", outlineColor: "#a78bfa", font: "inherit" };
