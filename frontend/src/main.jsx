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
    let verificationInFlight = false;

    // Add a synchronous curtain before async session verification. This is
    // important when Safari/Chrome restores this document from the BFCache.
    const showSecurityCurtain = () => {
      let curtain = document.getElementById("financial-os-session-curtain");
      if (!curtain) {
        curtain = document.createElement("div");
        curtain.id = "financial-os-session-curtain";
        curtain.setAttribute("role", "status");
        curtain.setAttribute("aria-live", "polite");
        curtain.textContent = "Verifying secure session…";
        Object.assign(curtain.style, {
          position: "fixed", inset: "0", zIndex: "2147483647",
          display: "grid", placeItems: "center", background: "#090b16",
          color: "#f4f5ff", font: "16px system-ui, sans-serif"
        });
        document.body.appendChild(curtain);
      }
    };
    const hideSecurityCurtain = () => {
      document.getElementById("financial-os-session-curtain")?.remove();
    };

    const verify = async () => {
      if (verificationInFlight || cancelled) return;
      verificationInFlight = true;
      showSecurityCurtain();
      setStatus("checking");

      if (!getAccessToken()) {
        clearSession();
        if (!cancelled) setStatus("signed-out");
        verificationInFlight = false;
        return;
      }

      try {
        const response = await apiFetch(`${API_BASE_URL}/api/auth/me`, {
          cache: "no-store",
          headers: { Accept: "application/json" },
        });
        if (!response.ok) throw new Error("Session expired or revoked");
        const user = await response.json();
        if (!user?.id) throw new Error("Backend did not return a verified user");
        sessionStorage.setItem("financial_os_user", JSON.stringify(user));
        if (!cancelled) setStatus("authenticated");
      } catch {
        clearSession();
        if (!cancelled) setStatus("signed-out");
      } finally {
        verificationInFlight = false;
        // Remove only after a valid session was confirmed. Invalid sessions
        // remain covered until the redirect to login occurs.
        if (!cancelled && getAccessToken()) hideSecurityCurtain();
      }
    };

    const onPageShow = (event) => {
      // pageshow fires on normal navigation and BFCache restoration. Cover
      // immediately rather than leaving previously rendered modules visible.
      showSecurityCurtain();
      verify();
    };
    const onFocus = () => verify();
    verify();
    window.addEventListener("pageshow", onPageShow);
    window.addEventListener("focus", onFocus);
    return () => {
      cancelled = true;
      window.removeEventListener("pageshow", onPageShow);
      window.removeEventListener("focus", onFocus);
      hideSecurityCurtain();
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
