// ============================================================
// FINANCIAL OS — WEBSITE + DIRECT DASHBOARD ACCESS
// Authentication screens and login/session gating removed.
// ============================================================

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import LandingPage from "./LandingPage";
import "./styles.css";

// Keep a rendering error from becoming a completely blank page. The error is
// shown visibly so route/component failures can be diagnosed instead of hidden.
class AppRenderBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("Financial OS render error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main style={{ minHeight: "100vh", padding: "28px", background: "#090b16", color: "#f4f5ff", fontFamily: "system-ui, sans-serif" }}>
          <h2> This page could not be displayed </h2>
          <p style={{ color: "#b9bfd2", lineHeight: 1.6 }}>The page encountered a rendering error. Your saved financial records have not been changed by this screen.</p>
          <button type="button" onClick={() => window.location.reload()} style={{ padding: "10px 14px", borderRadius: "8px", border: "0", cursor: "pointer" }}>Reload page</button>
        </main>
      );
    }
    return this.props.children;
  }
}

function RootRouter() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";

  // Open the application directly without a login screen.
  if (path === "/app" || path.startsWith("/app/")) {
    return <App />;
  }

  // Keep the public marketing website as the default page.
  // Login/register paths now return to the public website.
  return <LandingPage />;
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppRenderBoundary>
      <RootRouter />
    </AppRenderBoundary>
  </React.StrictMode>
);
