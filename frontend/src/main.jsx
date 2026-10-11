// ============================================================
// FINANCIAL OS - PUBLIC WEBSITE + AUTHENTICATION ROUTING
// Public website: /
// Login: /login
// Registration: /register
// Dashboard: /app
// ============================================================

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import LandingPage from "./LandingPage";
import "./styles.css";

// ============================================================
// AUTHENTICATION PAGE PLACEHOLDER
// The login and registration forms will be added in the next step.
// ============================================================

function AuthPage({ mode }) {
  const isLogin = mode === "login";

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "24px",
        background: "#090d1b",
        color: "#ffffff",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <section
        style={{
          width: "100%",
          maxWidth: "420px",
          padding: "28px",
          borderRadius: "18px",
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.05)",
          boxSizing: "border-box",
        }}
      >
        <h1 style={{ marginTop: 0 }}>Financial OS</h1>

        <p style={{ color: "#aeb8d0" }}>
          {isLogin
            ? "Sign in to your financial workspace."
            : "Create your Financial OS account."}
        </p>

        <p style={{ color: "#fbbf24", lineHeight: 1.6 }}>
          {isLogin
            ? "Login form integration is the next step."
            : "Registration form integration is the next step."}
        </p>

        <button
          type="button"
          onClick={() => {
            window.location.href = "/";
          }}
          style={{
            width: "100%",
            padding: "12px",
            border: 0,
            borderRadius: "10px",
            background: "linear-gradient(90deg, #8b5cf6, #f97316)",
            color: "#ffffff",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Back to Home
        </button>
      </section>
    </main>
  );
}

// ============================================================
// ROOT ROUTER
// ============================================================

function RootRouter() {
  const path =
    window.location.pathname.replace(/\/+$/, "") || "/";

  // Existing dashboard remains available at /app.
  if (path === "/app" || path.startsWith("/app/")) {
    return <App />;
  }

  // Login page.
  if (path === "/login") {
    return <AuthPage mode="login" />;
  }

  // Registration page.
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
