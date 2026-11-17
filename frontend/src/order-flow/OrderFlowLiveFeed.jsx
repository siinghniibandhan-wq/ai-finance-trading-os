import React, { useEffect, useState } from "react";
import { apiFetch, API_BASE_URL, friendlyErrorMessage } from "../api";
import { isLiveFeed } from "./liveFeedStatus";

const POLL_MS = 10000;
const MAX_RETRY_MS = 60000;
const number = (value) => value == null || !Number.isFinite(Number(value))
  ? "—"
  : new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(Number(value));

function formatAge(seconds) {
  if (seconds == null) return "No tick received";
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s ago`;
}

export default function OrderFlowLiveFeed({ symbol }) {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");
  const [retryIn, setRetryIn] = useState(POLL_MS);
  const [lastPollSucceeded, setLastPollSucceeded] = useState(false);

  useEffect(() => {
    let active = true;
    let timer;
    let delay = POLL_MS;
    setLastPollSucceeded(false);

    const poll = async () => {
      try {
        const url = new URL("/api/order-flow/snapshot", API_BASE_URL);
        if (symbol) url.searchParams.set("symbol", symbol);
        const response = await apiFetch(url.toString(), { method: "GET" });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(friendlyErrorMessage(response.status, payload));
        if (!active) return;
        setSnapshot(payload);
        setError("");
        setLastPollSucceeded(true);
        delay = POLL_MS;
      } catch (cause) {
        if (!active) return;
        setError(cause?.message || "Live derivatives feed is unavailable.");
        setLastPollSucceeded(false);
        delay = Math.min(Math.max(POLL_MS, delay * 2), MAX_RETRY_MS);
      } finally {
        if (active) {
          setRetryIn(delay);
          timer = window.setTimeout(poll, delay);
        }
      }
    };

    poll();
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [symbol]);

  const feed = snapshot?.feed;
  const isLive = isLiveFeed(snapshot, lastPollSucceeded);
  const futures = snapshot?.futures_contracts || [];
  const options = snapshot?.option_oi_by_strike || [];
  const ticks = snapshot?.raw_ticks || [];

  return (
    <section className="mf-live-feed" aria-live="polite" aria-label="Live derivatives feed">
      <div className="mf-live-feed-heading">
        <b>m.Stock market-stream feed</b>
        <span className={isLive ? "mf-feed-fresh" : "mf-feed-offline"}>
          {isLive ? "LIVE · FRESH" : feed?.status === "stale" ? "STALE" : "NOT CONNECTED"}
        </span>
      </div>
      {isLive ? (
        <>
          <p>
            Exchange tick: {formatAge(feed.age_seconds)} · {ticks.length} decoded ticks ·
            {" "}{futures.length} mapped futures · {options.length} option strikes
          </p>
          <p>
            {snapshot.unmapped_tick_count || 0} ticks await instrument-master mapping.
            {" "}{snapshot.price_scaling || "Prices are displayed as decoded by the gateway."}
          </p>
          {futures.length > 0 && (
            <div className="mf-live-contracts">
              <h3>Live futures contracts · {symbol || "All"}</h3>
              <div className="mf-live-table-wrap">
                <table>
                  <thead><tr><th>Contract</th><th>Expiry</th><th>Price</th><th>Volume</th><th>OI</th><th>OI Δ</th></tr></thead>
                  <tbody>{futures.map((item, index) => (
                    <tr key={item.symbol + item.expiry + index}>
                      <td>{item.symbol}</td><td>{item.expiry}</td><td>{number(item.price)}</td>
                      <td>{number(item.volume)}</td><td>{number(item.oi)}</td>
                      <td>{number(item.oi_change?.change)}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
          {options.length > 0 && (
            <div className="mf-live-contracts">
              <h3>Live option open interest by strike</h3>
              <div className="mf-live-table-wrap">
                <table>
                  <thead><tr><th>Strike</th><th>CE OI</th><th>PE OI</th></tr></thead>
                  <tbody>{options.map((item) => (
                    <tr key={item.strike}><td>{number(item.strike)}</td><td>{number(item.ce_oi)}</td><td>{number(item.pe_oi)}</td></tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
          {futures.length === 0 && options.length === 0 && (
            <p>Gateway ticks are arriving, but no contracts can be mapped yet. The charts below remain labelled simulated until instrument metadata is available.</p>
          )}
        </>
      ) : (
        <p>{error || "Waiting for an authenticated provider tick."} Automatic retry in {Math.round(retryIn / 1000)}s. No live data is being claimed.</p>
      )}
    </section>
  );
}
