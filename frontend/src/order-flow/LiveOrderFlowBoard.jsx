import React, { useEffect, useMemo, useState } from "react";
import { apiFetch, API_BASE_URL, friendlyErrorMessage } from "../api";
import { mapLiveOrderFlowSnapshot } from "./liveOrderFlowData";

const POLL_MS = 10000;
const MAX_RETRY_MS = 60000;
const number = value => value == null ? "—" : new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(value);
const age = seconds => seconds == null ? "No provider tick received" : seconds < 60 ? Math.round(seconds) + "s ago" : Math.floor(seconds / 60) + "m " + Math.round(seconds % 60) + "s ago";

export default function LiveOrderFlowBoard() {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");
  const [retryIn, setRetryIn] = useState(POLL_MS);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    let active = true;
    let timer;
    let delay = POLL_MS;
    const poll = async () => {
      try {
        const url = new URL("/api/order-flow/snapshot", API_BASE_URL);
        const response = await apiFetch(url.toString(), { method: "GET" });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(friendlyErrorMessage(response.status, payload));
        const mapped = mapLiveOrderFlowSnapshot(payload);
        if (!active) return;
        setSnapshot(mapped);
        setError("");
        delay = POLL_MS;
      } catch (cause) {
        if (!active) return;
        setError(cause?.message || "Live derivatives feed is unavailable.");
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
  }, []);

  const live = snapshot?.feedStatus === "fresh";
  const query = filter.trim().toUpperCase();
  const futures = useMemo(() => (snapshot?.futures || []).filter(row =>
    !query || row.symbol.includes(query) || row.contract.toUpperCase().includes(query)
  ), [snapshot, query]);
  const options = useMemo(() => (snapshot?.options || []).filter(row =>
    !query || row.symbol.includes(query) || row.contract.toUpperCase().includes(query)
  ), [snapshot, query]);

  return (
    <main className="market-flow-workspace ui-flow oi-design mf-live-workspace">
      <header className="market-flow-header">
        <div>
          <p className="market-flow-eyebrow">MARKET INTELLIGENCE · m.STOCK</p>
          <h1>Order Flow</h1>
          <p className="market-flow-subtitle">Live exchange futures and options data from your connected market-stream gateway</p>
        </div>
        <span className={"mf-provider-pill " + (live ? "mf-feed-fresh" : "mf-feed-offline")}>
          ● {live ? "LIVE · FRESH" : snapshot?.feedStatus === "stale" ? "STALE" : "NOT CONNECTED"}
        </span>
      </header>

      <section className="mf-live-feed" aria-live="polite" aria-label="m.Stock derivatives feed status">
        <div className="mf-live-feed-heading"><b>m.Stock derivatives feed</b><span>{live ? "LIVE" : snapshot?.feedStatus === "stale" ? "STALE" : "NOT CONNECTED"}</span></div>
        <p>{error || (snapshot ? "Last provider tick: " + age(snapshot.ageSeconds) + " · " + futures.length + " futures contracts · " + options.length + " option contracts" : "Waiting for an authenticated provider tick.")}</p>
        {!live && <p>Actual market values appear here only after a verified, fresh provider tick. Automatic retry in {Math.round(retryIn / 1000)}s.</p>}
        {snapshot?.coverage && <p>Mapped ticks: {snapshot.coverage.mapped_derivative_ticks ?? "—"} · Unmapped ticks: {snapshot.coverage.unmapped_ticks ?? "—"}</p>}
      </section>

      <label className="mf-live-filter">
        <span>Filter underlying or contract</span>
        <input value={filter} onChange={event => setFilter(event.target.value)} placeholder="e.g. NIFTY, BANKNIFTY" />
      </label>

      <section className="mf-live-data-section">
        <header><h2>Futures contracts</h2><span>{futures.length} contracts</span></header>
        {futures.length ? <div className="mf-live-table-wrap"><table className="mf-live-table"><thead><tr><th>Underlying</th><th>Contract</th><th>Expiry</th><th>Last price</th><th>Volume</th><th>Open interest</th></tr></thead><tbody>{futures.map(row => <tr key={row.contract}><td>{row.symbol}</td><td>{row.contract}</td><td>{row.expiry || "—"}</td><td>{number(row.price)}</td><td>{number(row.volume)}</td><td>{number(row.oi)}</td></tr>)}</tbody></table></div> : <p className="mf-live-empty">{live ? "No futures contracts matched this filter." : "No verified live futures ticks received. Demo values are not substituted."}</p>}
      </section>

      <section className="mf-live-data-section">
        <header><h2>Options contracts</h2><span>{options.length} contracts</span></header>
        {options.length ? <div className="mf-live-table-wrap"><table className="mf-live-table"><thead><tr><th>Underlying</th><th>Contract</th><th>Expiry</th><th>Strike</th><th>Type</th><th>Last price</th><th>Volume</th><th>Open interest</th></tr></thead><tbody>{options.map(row => <tr key={row.contract}><td>{row.symbol}</td><td>{row.contract}</td><td>{row.expiry || "—"}</td><td>{number(row.strike)}</td><td>{row.optionType}</td><td>{number(row.price)}</td><td>{number(row.volume)}</td><td>{number(row.oi)}</td></tr>)}</tbody></table></div> : <p className="mf-live-empty">{live ? "No option contracts matched this filter." : "No verified live option ticks received. Demo values are not substituted."}</p>}
      </section>

      <section className="mf-live-data-section">
        <header><h2>Option open interest by strike</h2><span>{snapshot?.optionOi?.length || 0} strikes</span></header>
        {snapshot?.optionOi?.length ? <div className="mf-live-table-wrap"><table className="mf-live-table"><thead><tr><th>Strike</th><th>Call OI</th><th>Put OI</th></tr></thead><tbody>{snapshot.optionOi.map(row => <tr key={row.strike}><td>{number(row.strike)}</td><td>{number(row.ceOi)}</td><td>{number(row.peOi)}</td></tr>)}</tbody></table></div> : <p className="mf-live-empty">Option OI will appear when the provider supplies verified option ticks.</p>}
      </section>
      <p className="mf-disclaimer">Only provider-supplied values are displayed. Price change, intraday candles, previous-session OI, PCR, support/resistance and conviction are not inferred when the required source data is unavailable. This workspace is read-only and does not place orders.</p>
    </main>
  );
}
