import React, { useEffect, useState } from "react";
import { apiFetch } from "./api";
import "./trading-control.css";

/**
 * Owner-only control. Parent should render this at the top of Portfolio only
 * when the authenticated user's email matches the server-configured owner.
 * Backend authorization remains authoritative; hiding the component is not security.
 */
export default function TradingControl() {
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    setError("");
    try {
      const response = await apiFetch("/api/broker/trading-status");
      if (!response.ok) throw new Error("Unable to verify live trading status.");
      setStatus(await response.json());
    } catch {
      setStatus(null);
      setError("Status unavailable — trading state cannot be verified.");
    }
  }

  useEffect(() => { refresh(); }, []);

  async function toggle() {
    if (!status || busy) return;
    const enabled = !status.trading_enabled;
    if (enabled && !window.confirm("REAL-MONEY WARNING: Turning live trading ON allows broker orders to be submitted using real funds. Continue only if you intend to trade.")) return;
    setBusy(true);
    setError("");
    try {
      const response = await apiFetch("/api/broker/trading-toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled }),
      });
      if (!response.ok) throw new Error("The gateway did not confirm the requested state.");
      const next = await response.json();
      setStatus(next);
      if (next.trading_enabled !== enabled) throw new Error("Trading state confirmation did not match.");
    } catch {
      setError("Could not confirm the new state. Treat trading as unavailable and refresh status.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  return <section className="finos-trading-control" aria-label="Live trading control">
    <div className="finos-trading-control__heading">
      <div>
        <h3>Live Trading</h3>
        <p>Owner control · Broker orders use real money</p>
      </div>
      <span className={`finos-trading-control__status ${status?.trading_enabled ? "is-on" : "is-off"}`}>
        {status ? (status.trading_enabled ? "ON" : "OFF") : "UNVERIFIED"}
      </span>
    </div>
    <div className="finos-trading-control__actions">
      <button type="button" onClick={toggle} disabled={!status || busy} aria-pressed={Boolean(status?.trading_enabled)}>
        {busy ? "Updating…" : status?.trading_enabled ? "Turn OFF" : "Turn ON"}
      </button>
      <button type="button" className="secondary" onClick={refresh} disabled={busy}>Refresh status</button>
    </div>
    <div className="finos-trading-control__limits">
      <span>Max order value: {status?.max_order_value ?? "—"}</span>
      <span>Max order quantity: {status?.max_order_qty ?? "—"}</span>
    </div>
    {error && <p className="finos-trading-control__error" role="alert">{error}</p>}
  </section>;
}
