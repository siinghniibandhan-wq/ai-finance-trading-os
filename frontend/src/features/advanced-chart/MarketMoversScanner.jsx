import React, { useCallback, useEffect, useMemo, useState } from "react";
import { loadMarketMovers } from "./api";
import { normalizeMoverRows, summarizeMoverRows } from "./marketScannerModel";
import "./market-scanner.css";

const money = (value) => new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(value);

export default function MarketMoversScanner({ type = "losers", onSelectInstrument }) {
  const isLoser = type === "losers";
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState(null);
  const [query, setQuery] = useState("");
  const [exchange, setExchange] = useState("ALL");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const next = await loadMarketMovers(type, 100);
      if (next?.status !== "success" || !Array.isArray(next?.movers)) {
        throw new Error("The REST API did not return a valid market-movers response.");
      }
      setPayload(next);
      setUpdatedAt(new Date());
    } catch (requestError) {
      setError(requestError?.message || "Market scanner data is unavailable.");
    } finally {
      setLoading(false);
    }
  }, [type]);

  useEffect(() => {
    let active = true;
    let inFlight = false;
    const request = async () => {
      if (!active || inFlight || document.visibilityState !== "visible") return;
      inFlight = true;
      setLoading(true);
      setError("");
      try {
        const next = await loadMarketMovers(type, 100);
        if (active) {
          if (next?.status !== "success" || !Array.isArray(next?.movers)) {
            throw new Error("The REST API did not return a valid market-movers response.");
          }
          setPayload(next);
          setUpdatedAt(new Date());
        }
      } catch (requestError) {
        if (active) setError(requestError?.message || "Market scanner data is unavailable.");
      } finally {
        inFlight = false;
        if (active) setLoading(false);
      }
    };
    const onVisibility = () => { if (document.visibilityState === "visible") request(); };
    request();
    const timer = window.setInterval(request, 30000);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      active = false;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [type]);

  const rows = useMemo(() => normalizeMoverRows(payload?.movers), [payload]);
  const visibleRows = useMemo(() => rows.filter((row) =>
    (exchange === "ALL" || row.exchange === exchange) &&
    (!query.trim() || row.symbol.includes(query.trim().toUpperCase()) ||
      row.name.toUpperCase().includes(query.trim().toUpperCase()))
  ), [rows, exchange, query]);
  const summary = useMemo(() => summarizeMoverRows(visibleRows), [visibleRows]);
  const maxMove = Math.max(1, ...visibleRows.map((row) => Math.abs(row.changePercent)));

  return (
    <section className="market-scanner" aria-label={isLoser ? "Loser scanner" : "Gainer scanner"}>
      <header className="market-scanner-heading">
        <div>
          <div className="market-scanner-eyebrow">LIVE REST MARKET DATA · m.STOCK</div>
          <h2>{isLoser ? "Loser Scanner" : "Gainer Scanner"}</h2>
          <p>Provider-reported {isLoser ? "decliners" : "advancers"}, ranked by percentage move. Values are not inferred.</p>
        </div>
        <button type="button" onClick={refresh} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh scanner"}
        </button>
      </header>

      <div className="market-scanner-summary">
        <div><span>VALID PROVIDER ROWS</span><strong>{summary.count}</strong></div>
        <div><span>AVERAGE CHANGE</span><strong className={isLoser ? "is-negative" : "is-positive"}>{summary.averageChangePercent === null ? "—" : `${summary.averageChangePercent > 0 ? "+" : ""}${summary.averageChangePercent.toFixed(2)}%`}</strong></div>
        <div><span>ROWS WITH VOLUME</span><strong>{summary.rowsWithVolume}</strong></div>
        <div><span>REPORTED VOLUME</span><strong>{summary.totalReportedVolume === null ? "—" : summary.totalReportedVolume.toLocaleString("en-IN")}</strong></div>
      </div>

      <div className="market-scanner-filters">
        <label>Search symbols or companies<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search scanner" /></label>
        <label>Exchange<select value={exchange} onChange={(event) => setExchange(event.target.value)}><option value="ALL">NSE + BSE</option><option value="NSE">NSE</option><option value="BSE">BSE</option></select></label>
        <span>{visibleRows.length} of {rows.length} validated rows</span>
      </div>

      {error && <div className="market-scanner-message is-error" role="alert">{error}{payload ? " · Last successful data remains visible." : ""}</div>}
      {!error && !loading && !visibleRows.length && <div className="market-scanner-message" role="status">No valid provider rows match this scanner filter.</div>}

      <div className="market-scanner-chart" role="img" aria-label={`${visibleRows.length} provider ${type} ranked by percentage change`}>
        <div className="market-scanner-chart-axis"><span>SYMBOL / EXCHANGE</span><span>CHANGE FROM PREVIOUS CLOSE (%)</span><span>LAST PRICE</span></div>
        {visibleRows.map((row) => {
          const width = Math.max(1, Math.abs(row.changePercent) / maxMove * 100);
          return (
            <button className="market-scanner-row" type="button" key={`${row.exchange}-${row.symbol}`} onClick={() => onSelectInstrument?.(row)}>
              <span className="market-scanner-instrument"><strong>{row.symbol}</strong><small>{row.exchange} · {row.name}</small></span>
              <span className="market-scanner-bar-cell">
                <span className={`market-scanner-bar ${isLoser ? "is-negative" : "is-positive"}`} style={{ width: `${width}%` }} />
                <strong className={isLoser ? "is-negative" : "is-positive"}>{row.changePercent > 0 ? "+" : ""}{row.changePercent.toFixed(2)}%</strong>
              </span>
              <span className="market-scanner-price">₹{money(row.lastPrice)}</span>
            </button>
          );
        })}
      </div>

      <footer className="market-scanner-footer">
        <span>Source: {payload?.source?.provider || "m.Stock REST API"} via Financial OS</span>
        <span>Retrieved: {updatedAt ? updatedAt.toLocaleTimeString("en-IN") : "Not yet retrieved"}</span>
        <span>Auto-refresh: 30 seconds while this view is visible</span>
      </footer>
    </section>
  );
}
