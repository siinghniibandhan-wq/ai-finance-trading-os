import React, { useEffect, useState } from "react";
import { apiFetch, API_BASE_URL, friendlyErrorMessage } from "../api";
import { getMarketFlowStatus } from "./marketFlowLive";

const POLL_MS = 10000;
const MAX_RETRY_MS = 60000;

function formatTickTime(value) {
  if (!value) return "No provider tick received";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Timestamp unavailable" : date.toLocaleString("en-IN", {
    dateStyle: "medium", timeStyle: "medium", timeZone: "Asia/Kolkata"
  }) + " IST";
}

export default function OrderFlowLiveFeed({ symbol, onSnapshot, onStatus }) {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");
  const [retryIn, setRetryIn] = useState(POLL_MS);

  useEffect(() => {
    let active = true;
    let timer;
    let delay = POLL_MS;

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
        onSnapshot?.(payload);
        const nextStatus = getMarketFlowStatus(payload);
        onStatus?.(nextStatus);
        delay = POLL_MS;
      } catch (cause) {
        if (!active) return;
        const message = cause?.message || "Live derivatives feed is unavailable.";
        setError(message);
        onStatus?.("OFFLINE");
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
  }, [symbol, onSnapshot, onStatus]);

  const status = getMarketFlowStatus(snapshot, error);
  const coverage = snapshot?.coverage || {};
  const stream = snapshot?.stream || {};
  const lastTick = snapshot?.feed?.last_tick_at || snapshot?.as_of;
  return (
    <section className="mf-live-feed" aria-live="polite" aria-label="Live derivatives feed status">
      <div className="mf-live-feed-heading">
        <b>m.Stock derivatives feed</b>
        <span className={"mf-feed-state mf-feed-" + status.toLowerCase()}>{status}</span>
      </div>
      <p>Last tick: {formatTickTime(lastTick)}</p>
      <p>Coverage: {coverage.state || "unknown"} · Stream: {stream.login_state || "not started"} · Contracts: {coverage.futures_with_data ?? 0}/{coverage.futures_planned ?? 0} futures, {coverage.options_with_data ?? 0}/{coverage.options_planned ?? 0} options</p>
      {error ? <p role="status">{error} · Retry in {Math.round(retryIn / 1000)}s</p> : null}
      {coverage.start_error ? <p role="status">Gateway start: {coverage.start_error}</p> : null}
    </section>
  );
}
