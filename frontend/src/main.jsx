// ============================================================
// FINANCIAL OS — WEBSITE + DIRECT DASHBOARD ACCESS
// Authentication screens and login/session gating removed.
// ============================================================

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import LandingPage from "./LandingPage";
import "./styles.css";

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
    <RootRouter />
  </React.StrictMode>
);
