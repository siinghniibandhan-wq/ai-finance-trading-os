import React, { useCallback, useEffect, useState } from "react";
import { API_BASE_URL, apiFetch, friendlyErrorMessage } from "../api";
import "./mstock-session.css";

export default function MStockSessionPanel({ onAuthenticated }) {
  const [totp, setTotp] = useState("");
  const [status, setStatus] = useState(null);
  const [localAuthenticated, setLocalAuthenticated] = useState(false);
  const [showReauthenticate, setShowReauthenticate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refreshStatus = useCallback(async () => {
    setChecking(true);
    try {
      const response = await apiFetch(new URL("/api/market-broker/status", API_BASE_URL), {
        method: "GET",
        cache: "no-store",
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(friendlyErrorMessage(response.status, payload));
      setStatus(payload);
      setLocalAuthenticated(Boolean(payload.authenticated));
      setError("");
    } catch (cause) {
      // Keep a successful login in this page's state if an older gateway
      // deployment has not yet exposed /auth/status.
      setStatus((current) => current || null);
      if (!localAuthenticated) setError(cause?.message || "Unable to check the m.Stock session.");
    } finally {
      setChecking(false);
    }
  }, [localAuthenticated]);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    setLoading(true);
    try {
      const response = await apiFetch(new URL("/api/market-broker/authenticate", API_BASE_URL), {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ totp }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(friendlyErrorMessage(response.status, payload));
      setLocalAuthenticated(true);
      setStatus((current) => ({
        ...(current || {}),
        authenticated: true,
        stream: payload.market_stream || current?.stream || {},
      }));
      setTotp("");
      setShowReauthenticate(false);
      setNotice(payload.message || "m.Stock authenticated. Market REST and Market Flow share this broker session.");
      if (onAuthenticated) onAuthenticated();
      refreshStatus();
    } catch (cause) {
      setError(cause?.message || "Unable to authenticate with m.Stock.");
    } finally {
      setLoading(false);
    }
  };

  const authenticated = Boolean(status?.authenticated || localAuthenticated);
  const stream = status?.stream || {};
  const streamLabel = stream.connected
    ? "WebSocket connected"
    : stream.running
      ? "WebSocket starting / waiting for first tick"
      : "WebSocket not connected";

  return (
    <section className="mstock-session-panel" aria-label="m.Stock broker session">
      <div className="mstock-session-copy">
        <div className="mstock-session-title">
          <span className={authenticated ? "mstock-session-dot is-connected" : "mstock-session-dot"} />
          <strong>m.Stock broker session</strong>
          <span className={authenticated ? "mstock-session-state is-connected" : "mstock-session-state"}>
            {authenticated ? "AUTHENTICATED" : "NOT AUTHENTICATED"}
          </span>
        </div>
        <p>
          One m.Stock TOTP session is shared by Market REST quotes and the Market Flow WebSocket.
          Financial OS sign-in remains separate.
        </p>
        {authenticated && (
          <small className={stream.connected ? "mstock-stream-state is-connected" : "mstock-stream-state"}>
            {streamLabel}
            {stream.last_tick_at ? ` · Last tick ${new Date(stream.last_tick_at).toLocaleTimeString("en-IN")}` : ""}
          </small>
        )}
      </div>

      {authenticated && !showReauthenticate ? (
        <div className="mstock-session-actions">
          <button type="button" className="mstock-session-secondary" onClick={refreshStatus} disabled={checking}>
            {checking ? "Checking…" : "Refresh status"}
          </button>
          <button type="button" className="mstock-session-secondary" onClick={() => setShowReauthenticate(true)}>
            Re-authenticate
          </button>
        </div>
      ) : (
        <form className="mstock-session-form" onSubmit={submit}>
          <label className="mstock-totp-field">
            <span>m.Stock TOTP</span>
            <input
              aria-label="m.Stock six-digit TOTP"
              autoComplete="one-time-code"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              minLength={6}
              value={totp}
              onChange={(event) => setTotp(event.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="6-digit code"
              required
            />
          </label>
          <button type="submit" className="mstock-session-primary" disabled={loading || totp.length !== 6}>
            {loading ? "Authenticating…" : authenticated ? "Refresh m.Stock session" : "Connect m.Stock"}
          </button>
          {authenticated && (
            <button type="button" className="mstock-session-secondary" onClick={() => setShowReauthenticate(false)}>
              Cancel
            </button>
          )}
        </form>
      )}

      {error && <p className="mstock-session-message is-error" role="alert">{error}</p>}
      {notice && <p className="mstock-session-message is-success" role="status">{notice}</p>}
    </section>
  );
}
