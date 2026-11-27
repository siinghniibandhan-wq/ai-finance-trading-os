import React, { useEffect } from "react";
import { API_BASE_URL, saveSession } from "./api";

// Landing spot after Google / GitHub sign-in. The server puts the session token in the
// part of the address after "#". We read it once, remove it from the address bar,
// confirm it with the server, then open the app.
// Captured at load time so a repeated render cannot lose it.
const CAPTURED_HASH = typeof window !== "undefined" ? window.location.hash : "";
let started = false;

function backToLogin(reason) {
  window.location.replace(`/login?social_error=${encodeURIComponent(reason)}`);
}

export default function SocialCallback() {
  useEffect(() => {
    if (started) return;
    started = true;
    try { window.history.replaceState({}, "", window.location.pathname); } catch { /* ignore */ }

    const token = new URLSearchParams(CAPTURED_HASH.replace(/^#/, "")).get("access_token");
    if (!token) { backToLogin("invalid_state"); return; }

    fetch(`${API_BASE_URL}/api/auth/me`, {
      cache: "no-store",
      headers: { Accept: "application/json", Authorization: `Bearer ${token}` },
    })
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error("rejected"))))
      .then((user) => {
        saveSession({ access_token: token, user });
        window.location.replace("/app");
      })
      .catch(() => backToLogin("provider_error"));
  }, []);

  return (
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "var(--th-page)", color: "var(--th-text)", fontFamily: "system-ui, sans-serif" }}>
      Signing you in…
    </main>
  );
}
