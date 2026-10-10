// ============================================================
// FINANCIAL OS - PUBLIC WEBSITE + PRIVATE APPLICATION ROUTING
// Public marketing website: /
// Existing Financial OS dashboard: /app
// ============================================================

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import LandingPage from "./LandingPage";
import "./styles.css";

function RootRouter() {
  // Keep the existing financial application intact at /app.
  // The public one-page website is the default route at /.
  const path = window.location.pathname.replace(/\/+$/, "") || "/";

  if (path === "/app" || path.startsWith("/app/")) {
    return <App />;
  }

  // Login and registration will be connected to the authentication flow
  // in the later SaaS implementation phase. For now these entry points
  // lead to the existing app so no authentication behaviour is implied.
  if (path === "/login" || path === "/register") {
    window.location.replace("/app");
    return null;
  }

  return <LandingPage />;
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RootRouter />
  </React.StrictMode>
);
