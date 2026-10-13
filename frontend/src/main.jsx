// ============================================================
// FINANCIAL OS — WEBSITE + AUTHENTICATED APP ROUTING
// ============================================================
import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import LandingPage from "./LandingPage";
import AuthPage from "./AuthPage";
import { API_BASE_URL, apiFetch, clearSession, getAccessToken } from "./api";
import "./styles.css";

class AppRenderBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error) { console.error("Financial OS render error:", error); }
  render() {
    if (this.state.hasError) {
      return <main style={{ minHeight: "100vh", padding: 28, background: "#090b16", color: "#f4f5ff", fontFamily: "system-ui, sans-serif" }}>
        <h2>This page could not be displayed</h2>
        <p style={{ color: "#b9bfd2", lineHeight: 1.6 }}>The page encountered a rendering error. Your saved financial records have not been changed by this screen.</p>
        <button type="button" onClick={() => window.location.reload()} style={{ padding: "10px 14px", borderRadius: 8, border: 0, cursor: "pointer" }}>Reload page</button>
      </main>;
    }
    return this.props.children;
  }
}

function ProtectedApp() {
  const [status, setStatus] = useState("checking");
  useEffect(() => {
    let cancelled = false;
    let checking = false;

    const verify = async () => {
      // Back/Forward can restore a page from browser cache without remounting React.
      if (checking) return;
      checking = true;
      if (!getAccessToken()) {
        clearSession();
        if (!cancelled) setStatus("signed-out");
        checking = false;
        return;
      }
      try {
        const response = await apiFetch(`${API_BASE_URL}/api/auth/me`, {
          cache: "no-store",
          headers: { Accept: "application/json" },
        });
        if (!response.ok) throw new Error("Session expired or revoked");
        const user = await response.json();
        let stored = null;
        try { stored = JSON.parse(sessionStorage.getItem("financial_os_user") || "null"); } catch { /* clear malformed cached identity below */ }
        if (!stored || Number(stored.id) !== Number(user.id) || stored.name !== user.name || stored.email !== user.email) {
          sessionStorage.setItem("financial_os_user", JSON.stringify(user));
        }
        if (!cancelled) setStatus("authenticated");
      } catch {
        clearSession();
        if (!cancelled) setStatus("signed-out");
      } finally {
        checking = false;
      }
    };

    const onPageShow = () => {
      // Synchronously cover a BFCache-restored page before making any network
      // request. The old DOM must not remain visible while /auth/me is pending.
      const root = document.getElementById("root");
      if (root) root.style.visibility = "hidden";
      setStatus("checking");
      if (!getAccessToken()) {
        clearSession();
        if (!cancelled) {
          setStatus("signed-out");
          window.location.replace("/login");
        }
        return;
      }
      verify().then(() => {
        // Only reveal the app if verification succeeded. On failure the effect
        // changes status to signed-out and navigates to /login.
        if (!cancelled && getAccessToken()) {
          // status may still be checking if verify is already in flight; only
          // the authenticated state is allowed to reveal protected content.
          setTimeout(() => {
            if (document.getElementById("root") && getAccessToken()) {
              document.getElementById("root").style.visibility = "";
            }
          }, 0);
        }
      });
    };
    verify();
    window.addEventListener("pageshow", onPageShow);
    window.addEventListener("focus", onPageShow);
    return () => {
      cancelled = true;
      window.removeEventListener("pageshow", onPageShow);
      window.removeEventListener("focus", onPageShow);
    };
  }, []);

  useEffect(() => {
    if (status === "signed-out") {
      const next = `${window.location.pathname}${window.location.search}`;
      window.location.replace(`/login?next=${encodeURIComponent(next)}`);
    }
  }, [status]);

  if (status !== "authenticated") {
    return <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#090b16", color: "#f4f5ff", fontFamily: "system-ui, sans-serif" }}>Checking secure session…</main>;
  }
  return <App />;
}

function RootRouter() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  if (path === "/app" || path.startsWith("/app/")) return <ProtectedApp />;
  if (path === "/login") return <AuthPage initialMode="login" />;
  if (path === "/register") return <AuthPage initialMode="register" />;
  return <LandingPage />;
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppRenderBoundary><RootRouter /></AppRenderBoundary>
  </React.StrictMode>
);
