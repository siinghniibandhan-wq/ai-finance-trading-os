// ============================================================
// FINANCIAL OS
// PUBLIC WEBSITE + LOGIN + REGISTRATION + DASHBOARD ROUTING
//
// Public website: /
// Login:          /login
// Registration:   /register
// Dashboard:      /app
//
// Backend: FastAPI deployed on Render
// ============================================================

import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import LandingPage from "./LandingPage";
import "./styles.css";

// ============================================================
// API CONFIGURATION
// ============================================================

const API_BASE_URL =
  "https://ai-finance-trading-os-api.onrender.com";

// ============================================================
// AUTHENTICATION PAGE
// Supports login and registration.
// ============================================================

function AuthPage({ mode }) {
  const isLogin = mode === "login";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [currency, setCurrency] = useState("INR");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // ----------------------------------------------------------
  // HANDLE LOGIN OR REGISTRATION
  // ----------------------------------------------------------

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const endpoint = isLogin
        ? "/api/auth/login"
        : "/api/auth/register";

      const payload = isLogin
        ? {
            email: email.trim().toLowerCase(),
            password,
          }
        : {
            name: name.trim(),
            email: email.trim().toLowerCase(),
            password,
            currency,
          };

      const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const message =
          typeof data.detail === "string"
            ? data.detail
            : "Request failed. Please check your details and try again.";

        throw new Error(message);
      }

      // ------------------------------------------------------
      // LOGIN SUCCESS
      // ------------------------------------------------------

      if (isLogin) {
        if (!data.access_token || !data.user) {
          throw new Error(
            "Login response did not contain the required account details."
          );
        }

        // Store the session for the current browser.
        // This is a frontend session mechanism, not a replacement
        // for server-side authorization.
        sessionStorage.setItem(
          "financial_os_token",
          data.access_token
        );

        sessionStorage.setItem(
          "financial_os_user",
          JSON.stringify(data.user)
        );

        // Keep existing application modules compatible with
        // their current USER_ID = 1 implementation.
        // Full multi-user data isolation is a separate required step.
        sessionStorage.setItem(
          "financial_os_user_id",
          String(data.user.id)
        );

        window.location.replace("/app");
        return;
      }

      // ------------------------------------------------------
      // REGISTRATION SUCCESS
      // ------------------------------------------------------

      setSuccess(
        "Account created successfully. Please sign in."
      );

      setPassword("");

      // Return the new user to login.
      window.setTimeout(() => {
        window.location.href = "/login";
      }, 1200);
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  // ==========================================================
  // AUTHENTICATION PAGE UI
  // ==========================================================

  const inputStyle = {
    width: "100%",
    boxSizing: "border-box",
    padding: "13px 14px",
    borderRadius: "10px",
    border: "1px solid rgba(255,255,255,0.16)",
    background: "#101426",
    color: "#ffffff",
    fontSize: "15px",
    outline: "none",
  };

  const labelStyle = {
    display: "block",
    marginBottom: "8px",
    color: "#d5d9e8",
    fontSize: "14px",
    fontWeight: 600,
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "24px",
        background:
          "radial-gradient(circle at top, #17172f 0%, #090d1b 55%)",
        color: "#ffffff",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <section
        style={{
          width: "100%",
          maxWidth: "440px",
          padding: "28px",
          borderRadius: "20px",
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.045)",
          boxShadow: "0 20px 60px rgba(0,0,0,0.25)",
          boxSizing: "border-box",
        }}
      >
        {/* BRAND */}

        <div style={{ marginBottom: "26px" }}>
          <div
            style={{
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "2px",
              color: "#c4b5fd",
              marginBottom: "12px",
            }}
          >
            FINANCIAL OS
          </div>

          <h1
            style={{
              margin: "0 0 10px",
              fontSize: "28px",
            }}
          >
            {isLogin ? "Welcome back" : "Create your account"}
          </h1>

          <p
            style={{
              margin: 0,
              color: "#aeb8d0",
              lineHeight: 1.6,
              fontSize: "14px",
            }}
          >
            {isLogin
              ? "Sign in to access your financial workspace."
              : "Start organizing your financial life in one place."}
          </p>
        </div>

        {/* ERROR MESSAGE */}

        {error && (
          <div
            role="alert"
            style={{
              padding: "12px",
              marginBottom: "18px",
              borderRadius: "10px",
              background: "rgba(239,68,68,0.12)",
              border: "1px solid rgba(239,68,68,0.35)",
              color: "#fca5a5",
              fontSize: "14px",
              overflowWrap: "anywhere",
            }}
          >
            {error}
          </div>
        )}

        {/* SUCCESS MESSAGE */}

        {success && (
          <div
            role="status"
            style={{
              padding: "12px",
              marginBottom: "18px",
              borderRadius: "10px",
              background: "rgba(34,197,94,0.12)",
              border: "1px solid rgba(34,197,94,0.35)",
              color: "#86efac",
              fontSize: "14px",
            }}
          >
            {success}
          </div>
        )}

        {/* FORM */}

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div style={{ marginBottom: "18px" }}>
              <label style={labelStyle} htmlFor="name">
                Full name
              </label>

              <input
                id="name"
                type="text"
                autoComplete="name"
                placeholder="Enter your name"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                required
                minLength={1}
                maxLength={150}
                style={inputStyle}
              />
            </div>
          )}

          <div style={{ marginBottom: "18px" }}>
            <label style={labelStyle} htmlFor="email">
              Email address
            </label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
              maxLength={255}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: "18px" }}>
            <label style={labelStyle} htmlFor="password">
              Password
            </label>

            <input
              id="password"
              type="password"
              autoComplete={
                isLogin ? "current-password" : "new-password"
              }
              placeholder={
                isLogin
                  ? "Enter your password"
                  : "At least 12 characters"
              }
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              required
              minLength={isLogin ? 1 : 12}
              maxLength={128}
              style={inputStyle}
            />

            {!isLogin && (
              <p
                style={{
                  color: "#929bb5",
                  fontSize: "12px",
                  marginBottom: 0,
                }}
              >
                Use at least 12 characters.
              </p>
            )}
          </div>

          {!isLogin && (
            <div style={{ marginBottom: "22px" }}>
              <label style={labelStyle} htmlFor="currency">
                Preferred currency
              </label>

              <select
                id="currency"
                value={currency}
                onChange={(event) =>
                  setCurrency(event.target.value)
                }
                style={inputStyle}
              >
                <option value="INR">INR — Indian Rupee</option>
                <option value="USD">USD — US Dollar</option>
                <option value="EUR">EUR — Euro</option>
                <option value="GBP">GBP — British Pound</option>
              </select>
            </div>
          )}

          {/* SUBMIT BUTTON */}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "14px",
              border: 0,
              borderRadius: "11px",
              background: loading
                ? "#6254a4"
                : "linear-gradient(90deg, #8b5cf6, #ec4899, #f97316)",
              color: "#ffffff",
              fontSize: "15px",
              fontWeight: 700,
              cursor: loading ? "wait" : "pointer",
              opacity: loading ? 0.8 : 1,
            }}
          >
            {loading
              ? "Please wait..."
              : isLogin
              ? "Sign In"
              : "Create Account"}
          </button>
        </form>

        {/* SWITCH AUTH MODE */}

        <p
          style={{
            marginTop: "24px",
            textAlign: "center",
            color: "#aeb8d0",
            fontSize: "14px",
            lineHeight: 1.7,
          }}
        >
          {isLogin
            ? "Don't have an account? "
            : "Already have an account? "}

          <a
            href={isLogin ? "/register" : "/login"}
            style={{
              color: "#c4b5fd",
              fontWeight: 700,
              textDecoration: "none",
            }}
          >
            {isLogin ? "Register" : "Sign in"}
          </a>
        </p>

        <div style={{ textAlign: "center" }}>
          <a
            href="/"
            style={{
              color: "#8d96b2",
              fontSize: "13px",
              textDecoration: "none",
            }}
          >
            ← Back to home
          </a>
        </div>
      </section>
    </main>
  );
}

// ============================================================
// PROTECTED DASHBOARD
// Verify the saved token with the backend before showing App.
// ============================================================

function ProtectedApp() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let cancelled = false;

    async function verifySession() {
      const token = sessionStorage.getItem("financial_os_token");

      // No login token: return to login.
      if (!token) {
        window.location.replace("/login");
        return;
      }

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/auth/me`,
          {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
              Accept: "application/json",
            },
          }
        );

        if (!response.ok) {
          throw new Error("Session invalid or expired.");
        }

        const user = await response.json();

        if (cancelled) return;

        // Keep the logged-in user's details in the browser session.
        sessionStorage.setItem(
          "financial_os_user",
          JSON.stringify(user)
        );

        sessionStorage.setItem(
          "financial_os_user_id",
          String(user.id)
        );

        setStatus("authenticated");
      } catch (error) {
        if (cancelled) return;

        // Clear invalid sessions.
        sessionStorage.removeItem("financial_os_token");
        sessionStorage.removeItem("financial_os_user");
        sessionStorage.removeItem("financial_os_user_id");

        window.location.replace("/login");
      }
    }

    verifySession();

    return () => {
      cancelled = true;
    };
  }, []);

  if (status !== "authenticated") {
    return (
      <main
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "#090d1b",
          color: "#ffffff",
          fontFamily: "Arial, sans-serif",
        }}
      >
        Verifying your secure session...
      </main>
    );
  }

  return <App />;
}
// ============================================================
// ROOT ROUTER
// ============================================================

function RootRouter() {
  const path =
    window.location.pathname.replace(/\/+$/, "") || "/";

  // Existing dashboard.
  if (path === "/app" || path.startsWith("/app/")) {
  return <ProtectedApp />;
  }

  // Login.
  if (path === "/login") {
    return <AuthPage mode="login" />;
  }

  // Registration.
  if (path === "/register") {
    return <AuthPage mode="register" />;
  }

  // Public marketing website.
  return <LandingPage />;
}

// ============================================================
// APPLICATION ENTRY POINT
// ============================================================

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RootRouter />
  </React.StrictMode>
);
