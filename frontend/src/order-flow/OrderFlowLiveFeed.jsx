import React, { useEffect, useState } from "react";
import { API_BASE_URL, getAccessToken } from "../api";

const NOOP_SNAPSHOT = () => {};
const MAX_RETRY_MS = 30000;

function formatAge(seconds) {
  if (seconds == null) return "No provider tick received";
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s ago`;
}

function websocketUrl(symbol) {
  const url = new URL("/api/order-flow/stream", API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  if (symbol) url.searchParams.set("symbol", symbol);
  return url.toString();
}

export default function OrderFlowLiveFeed({ symbol, onSnapshot = NOOP_SNAPSHOT }) {
  const [snapshot, setSnapshot] = useState(null);
  const [connection, setConnection] = useState("connecting");
  const [error, setError] = useState("");
  const [retryIn, setRetryIn] = useState(1000);

  useEffect(() => {
    let active = true;
    let socket = null;
    let retryTimer = null;
    let retryDelay = 1000;
    const token = getAccessToken();

    setSnapshot(null);
    onSnapshot(null);
    setError("");

    if (!token) {
      setConnection("unauthenticated");
      setError("Sign in to Financial OS before opening the live market stream.");
      return undefined;
    }

    const connect = () => {
      if (!active) return;
      setConnection("connecting");
      try {
        socket = new WebSocket(
          websocketUrl(symbol),
          ["financial-os", `bearer.${token}`],
        );
      } catch {
        scheduleReconnect("Unable to create the Market Flow WebSocket connection.");
        return;
      }

      socket.onopen = () => {
        if (!active) return;
        retryDelay = 1000;
        setRetryIn(retryDelay);
        setConnection("connected");
        setError("");
      };

      socket.onmessage = (event) => {
        if (!active) return;
        try {
          const payload = JSON.parse(event.data);
          setSnapshot(payload);
          onSnapshot(payload);
          if (payload.status === "success" && payload.feed?.status === "fresh") {
            setConnection("live");
            setError("");
          } else if (payload.feed?.status === "stale") {
            setConnection("stale");
            setError("The gateway has ticks, but the latest provider tick is stale.");
          } else if (payload.status === "error") {
            setConnection("connected");
            setError(payload.message || "The broker stream is waiting for authentication or provider data.");
          } else {
            setConnection("connected");
            setError("");
          }
        } catch {
          setError("The Market Flow WebSocket returned an invalid message.");
        }
      };

      socket.onerror = () => {
        if (active) setError("Market Flow WebSocket connection error.");
      };

      socket.onclose = (event) => {
        if (!active) return;
        if (event.code === 4401) {
          setConnection("unauthenticated");
          setError("Your Financial OS session is invalid or expired. Sign in again.");
          return;
        }
        if (event.code === 4400) {
          setConnection("error");
          setError("The selected underlying symbol is invalid.");
          return;
        }
        scheduleReconnect("Market Flow disconnected. Reconnecting automatically.");
      };
    };

    const scheduleReconnect = (message) => {
      if (!active) return;
      setConnection("reconnecting");
      setError(message);
      setRetryIn(retryDelay);
      window.clearTimeout(retryTimer);
      retryTimer = window.setTimeout(connect, retryDelay);
      retryDelay = Math.min(retryDelay * 2, MAX_RETRY_MS);
    };

    connect();

    return () => {
      active = false;
      window.clearTimeout(retryTimer);
      if (socket) {
        socket.onclose = null;
        socket.close(1000, "Market Flow view closed");
      }
    };
  }, [symbol, onSnapshot]);

  const feed = snapshot?.feed;
  const isLive = snapshot?.status === "success" && feed?.status === "fresh";
  const statusLabel = isLive
    ? "LIVE · FRESH"
    : connection === "stale" || feed?.status === "stale"
      ? "STALE"
      : connection === "unauthenticated"
        ? "AUTH REQUIRED"
        : connection === "reconnecting"
          ? "RECONNECTING"
          : connection === "error"
            ? "ERROR"
            : "WAITING FOR LIVE TICKS";

  return (
    <section className="mf-live-feed" aria-live="polite" aria-label="Live derivatives WebSocket status">
      <div className="mf-live-feed-heading">
        <b>m.Stock Market Flow WebSocket</b>
        <span className={isLive ? "mf-feed-fresh" : "mf-feed-offline"}>{statusLabel}</span>
      </div>
      {isLive ? (
        <>
          <p>Last provider tick: {formatAge(feed.age_seconds)} · {snapshot.futures_contracts?.length || 0} futures contracts · {snapshot.option_contracts?.length || 0} option contracts</p>
          <p>Gateway stream: {snapshot.stream?.socket_connected ? "socket connected" : "socket disconnected"} · {snapshot.stream?.cached_instruments || 0} cached instruments</p>
        </>
      ) : (
        <p>{error || "Waiting for an authenticated m.Stock provider tick."}{connection === "reconnecting" ? ` Retry in ${Math.ceil(retryIn / 1000)}s.` : ""} No simulated values are substituted.</p>
      )}
    </section>
  );
}
