import React, { useEffect, useState } from "react";
import { apiFetch, API_BASE_URL, friendlyErrorMessage } from "../api";

const POLL_MS = 10000;
const MAX_RETRY_MS = 60000;
const NOOP_SNAPSHOT = () => {};

function formatAge(seconds) {
  if (seconds == null) return "No tick received";
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s ago`;
}

export default function OrderFlowLiveFeed({ symbol, onSnapshot = NOOP_SNAPSHOT }) {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");
  const [retryIn, setRetryIn] = useState(POLL_MS);

  useEffect(() => {
    let active = true;
    let timer;
    let delay = POLL_MS;
    setSnapshot(null);
    onSnapshot(null);

    const poll = async () => {
      try {
        const url = new URL("/api/order-flow/snapshot", API_BASE_URL);
        if (symbol) url.searchParams.set("symbol", symbol);
        const response = await apiFetch(url.toString(), { method: "GET" });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(friendlyErrorMessage(response.status, payload));
        if (!active) return;
        setSnapshot(payload);
        onSnapshot(payload);
        setError("");
        delay = POLL_MS;
      } catch (cause) {
        if (!active) return;
        setError(cause?.message || "Live derivatives feed is unavailable.");
        setSnapshot(null);
        onSnapshot(null);
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
  }, [symbol, onSnapshot]);

  const feed = snapshot?.feed;
  const isLive = snapshot?.status === "success" && feed?.status === "fresh";

  return (
    <section className="mf-live-feed" aria-live="polite" aria-label="Live derivatives feed status">
      <div className="mf-live-feed-heading">
        <b>m.Stock derivatives feed</b>
        <span className={isLive ? "mf-feed-fresh" : "mf-feed-offline"}>
          {isLive ? "LIVE · FRESH" : feed?.status === "stale" ? "STALE · NOT LIVE" : "NOT CONNECTED"}
        </span>
      </div>
      {isLive ? (
        <p>Latest provider tick: {formatAge(feed.age_seconds)} · polling every {POLL_MS / 1000}s. Only received provider contracts are displayed.</p>
      ) : (
        <p>{error || "Waiting for a fresh authenticated m.Stock provider tick."} Retrying in {Math.round(retryIn / 1000)}s. No simulated market values are shown.</p>
      )}
    </section>
  );
}
