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
import "./visual-design.css";
import "./theme-fixes.css";
import "./theme-styles.css";
import "./instrument-interaction-contrast.css";

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
    let verificationPromise = null;

    const coverProtectedUI = () => {
      const root = document.getElementById("root");
      if (root) root.style.visibility = "hidden";
    };

    const showProtectedUI = () => {
      const root = document.getElementById("root");
      if (root) root.style.visibility = "";
    };

    const verify = () => {
      // Share one in-flight verification. In particular, pageshow can fire
      // while the initial mount verification is still running.
      if (verificationPromise) return verificationPromise;

      verificationPromise = (async () => {
        const token = getAccessToken();
        if (!token) {
          clearSession();
          if (!cancelled) setStatus("signed-out");
          return false;
        }

        try {
          const response = await apiFetch(`${API_BASE_URL}/api/auth/me`, {
            cache: "no-store",
            headers: { Accept: "application/json" },
          });
          if (!response.ok) throw new Error("Session expired or revoked");

          const user = await response.json();
          if (!user || !user.id) throw new Error("Invalid session identity");

          // Refresh cached identity only from the authenticated backend response.
          sessionStorage.setItem("financial_os_user", JSON.stringify(user));
          if (!cancelled) setStatus("authenticated");
          return true;
        } catch {
          clearSession();
          if (!cancelled) setStatus("signed-out");
          return false;
        } finally {
          verificationPromise = null;
        }
      })();

      return verificationPromise;
    };

    const onPageShow = async (event) => {
      // The initial load is verified below. Re-verify only when the browser
      // restores a page from its back-forward cache, not on ordinary tab focus.
      if (!event.persisted) return;

      coverProtectedUI();
      if (!cancelled) setStatus("checking");

      const valid = await verify();
      if (cancelled) return;

      if (valid && getAccessToken()) {
        showProtectedUI();
      } else {
        coverProtectedUI();
        window.location.replace("/login");
      }
    };

    const onPageHide = () => {
      // Prevent a previously rendered protected screen from being displayed
      // when the browser restores it from the back-forward cache.
      coverProtectedUI();
    };

    // Cover synchronously before the first async request.
    coverProtectedUI();
    verify().then((valid) => {
      if (cancelled) return;
      if (valid && getAccessToken()) showProtectedUI();
      else {
        coverProtectedUI();
        window.location.replace("/login");
      }
    });

    window.addEventListener("pageshow", onPageShow);
    window.addEventListener("pagehide", onPageHide);
    return () => {
      cancelled = true;
      window.removeEventListener("pageshow", onPageShow);
      window.removeEventListener("pagehide", onPageHide);
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
