import React, { useEffect, useState } from "react";
import { apiFetch, API_BASE_URL, friendlyErrorMessage } from "../api";
import { isLiveFeed } from "./liveFeedStatus";
import { appendLivePricePoint } from "./livePriceHistory";

const POLL_MS = 10000;
const MAX_RETRY_MS = 60000;
const number = (value) => value == null || !Number.isFinite(Number(value))
  ? "—"
  : new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(Number(value));

function formatAge(seconds) {
  if (seconds == null) return "No exchange tick received";
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s ago`;
}

function LivePriceChart({ history }) {
  const series = [...new Set(history.flatMap(point => Object.keys(point.prices)))].slice(0, 5);
  const allValues = history.flatMap(point => Object.values(point.prices));
  if (!series.length || !allValues.length) return null;
  const minimum = Math.min(...allValues);
  const maximum = Math.max(...allValues);
  const range = Math.max(maximum - minimum, 1);
  const x = index => history.length < 2 ? 320 : 24 + (index / (history.length - 1)) * 592;
  const y = value => 142 - ((value - minimum) / range) * 116;

  return (
    <div className="mf-live-chart">
      <div className="mf-live-chart-heading">
        <b>Live futures price history</b>
        <small>Captured from exchange-timestamped provider snapshots · {history.length} points</small>
      </div>
      <svg viewBox="0 0 640 170" role="img" aria-label="Live m.Stock futures price history">
        <line x1="24" x2="616" y1="26" y2="26" />
        <line x1="24" x2="616" y1="84" y2="84" />
        <line x1="24" x2="616" y1="142" y2="142" />
        {series.map((contract, seriesIndex) => {
          const points = history
            .map((point, index) => point.prices[contract] == null ? null : `${x(index)},${y(point.prices[contract])}`)
            .filter(Boolean)
            .join(" ");
          return <polyline key={contract} points={points} className="mf-live-price-line" opacity={1 - seriesIndex * 0.12} />;
        })}
        <text x="24" y="160">{number(minimum)}</text>
        <text x="616" y="160" textAnchor="end">{number(maximum)}</text>
      </svg>
      <div className="mf-live-chart-legend">
        {series.map((contract, index) => <span key={contract} style={{ opacity: 1 - index * 0.12 }}>{contract}</span>)}
      </div>
    </div>
  );
}

export default function OrderFlowLiveFeed({ symbol }) {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");
  const [retryIn, setRetryIn] = useState(POLL_MS);
  const [lastPollSucceeded, setLastPollSucceeded] = useState(false);
  const [priceHistory, setPriceHistory] = useState([]);

  useEffect(() => {
    let active = true;
    let timer;
    let delay = POLL_MS;
    setLastPollSucceeded(false);
    setPriceHistory([]);

    const poll = async () => {
      try {
        const url = new URL("/api/order-flow/snapshot", API_BASE_URL);
        if (symbol) url.searchParams.set("symbol", symbol);
        const response = await apiFetch(url.toString(), { method: "GET" });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(friendlyErrorMessage(response.status, payload));
        if (!active) return;
        setSnapshot(payload);
        setPriceHistory(current => appendLivePricePoint(current, payload));
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
        <b>m.Stock market-stream feed · {symbol || "All underlyings"}</b>
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
            Exchange timestamp: {feed.last_tick_at ? new Date(feed.last_tick_at).toLocaleString() : "Unavailable"} ·
            {" "}{snapshot.unmapped_tick_count || 0} unmapped tokens ·
            {" "}{snapshot.price_scaling}
          </p>
          {futures.length > 0 && <LivePriceChart history={priceHistory} />}
          {futures.length > 0 && (
            <div className="mf-live-contracts">
              <h3>Live futures contracts</h3>
              <div className="mf-live-table-wrap">
                <table>
                  <thead><tr><th>Contract</th><th>Expiry</th><th>Price</th><th>Volume</th><th>Open interest</th></tr></thead>
                  <tbody>{futures.map((item, index) => (
                    <tr key={item.instrument_token || item.tradingsymbol || index}>
                      <td>{item.tradingsymbol || item.symbol}</td><td>{item.expiry}</td>
                      <td>{number(item.price)}</td><td>{number(item.volume)}</td><td>{number(item.oi)}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
              <p>OI change is not inferred: the Type-A snapshot supplies current OI, not a verified previous-session baseline.</p>
            </div>
          )}
          {options.length > 0 && (
            <div className="mf-live-contracts">
              <h3>Live option open interest by strike</h3>
              <div className="mf-live-table-wrap">
                <table>
                  <thead><tr><th>Underlying</th><th>Strike</th><th>CE OI</th><th>PE OI</th></tr></thead>
                  <tbody>{options.map((item) => (
                    <tr key={`${item.symbol || ""}-${item.strike}`}>
                      <td>{item.symbol || symbol || "—"}</td><td>{number(item.strike)}</td>
                      <td>{number(item.ce_oi)}</td><td>{number(item.pe_oi)}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
          {futures.length === 0 && options.length === 0 && (
            <p>Fresh gateway ticks are present, but no futures/options contracts matched the instrument master and selected underlying.</p>
          )}
        </>
      ) : (
        <p>
          {feed?.status === "stale"
            ? `Last exchange tick is stale (${formatAge(feed.age_seconds)}).`
            : error || "Waiting for an authenticated provider tick."}
          {" "}Automatic retry in {Math.round(retryIn / 1000)}s. No live data is being claimed.
        </p>
      )}
    </section>
  );
}
