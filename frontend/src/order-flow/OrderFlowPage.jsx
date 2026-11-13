import React, { useEffect, useMemo, useState } from "react";
import "./order-flow.css";
import { toSpotChangeRows } from "./marketFlowData";

const API_BASE = (import.meta.env.VITE_MARKET_FLOW_API_BASE || "").replace(/\/$/, "");

async function readJson(path, signal) {
  const response = await fetch(`${API_BASE}${path}`, { signal, headers: { Accept: "application/json" } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body?.error || `Order Flow service returned ${response.status}`);
  return body;
}

export default function OrderFlowPage() {
  const [status, setStatus] = useState(null);
  const [market, setMarket] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [symbol, setSymbol] = useState("NIFTY");

  useEffect(() => {
    if (!API_BASE) {
      setError("Order Flow data service is not configured. Set VITE_MARKET_FLOW_API_BASE to the authenticated Order Flow service URL.");
      setLoading(false);
      return undefined;
    }
    const controller = new AbortController();
    let active = true;
    const load = async () => {
      try {
        const [nextStatus, nextMarket] = await Promise.all([
          readJson("/api/status", controller.signal),
          readJson("/api/market", controller.signal),
        ]);
        if (!active) return;
        setStatus(nextStatus);
        setMarket(nextMarket);
        setError("");
      } catch (e) {
        if (active && e.name !== "AbortError") setError(e.message || "Unable to load Order Flow data.");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    const timer = window.setInterval(load, 60000);
    return () => { active = false; controller.abort(); window.clearInterval(timer); };
  }, []);

  const rows = useMemo(() => {
    return toSpotChangeRows(market?.series);
  }, [market]);

  const selected = rows.find((row) => row.symbol === symbol) || rows[0] || null;
  const bullish = rows.filter((row) => row.change >= 0);
  const bearish = rows.filter((row) => row.change < 0);

  return (
    <main className="market-flow-workspace" aria-labelledby="market-flow-title">
      <header className="market-flow-header">
        <div>
          <p className="market-flow-eyebrow">MARKET INTELLIGENCE</p>
          <h1 id="market-flow-title">Order Flow</h1>
          <p className="market-flow-subtitle">Spot breadth from the Order Flow market feed</p>
        </div>
        <div className="market-flow-status">
          <span className={status?.ready ? "market-flow-dot is-ready" : "market-flow-dot"} />
          {loading ? "Connecting…" : status?.provider?.label || "Service unavailable"}
        </div>
      </header>

      {error && <div className="market-flow-alert" role="alert">{error}</div>}
      {!API_BASE && <div className="market-flow-empty"><strong>Data service required</strong><span>This workspace is isolated from your existing Markets and investment workflows. Configure the Order Flow service before displaying market signals.</span></div>}

      {API_BASE && <>
        <section className="market-flow-summary">
          <article><span>UNDERLYINGS</span><strong>{rows.length || "—"}</strong></article>
          <article><span>BULLISH</span><strong className="is-bullish">{bullish.length || "—"}</strong></article>
          <article><span>BEARISH</span><strong className="is-bearish">{bearish.length || "—"}</strong></article>
          <article><span>LAST SCAN</span><strong>{market?.t ? new Date(market.t).toLocaleTimeString("en-IN") : "—"}</strong></article>
        </section>
        <section className="market-flow-board">
          <div className="market-flow-board-head">
            <div><h2>Spot breadth</h2><p>Spot change from the previous close · futures and OI board integration in progress</p></div>
            <label>Instrument <select value={selected?.symbol || symbol} onChange={(e) => setSymbol(e.target.value)}>{rows.map((row) => <option key={row.symbol} value={row.symbol}>{row.symbol}</option>)}</select></label>
          </div>
          <div className="market-flow-columns">
            <div className="market-flow-list"><h3 className="is-bullish">Bullish <span>{bullish.length}</span></h3>{bullish.slice(0, 20).map((row) => <button key={row.symbol} onClick={() => setSymbol(row.symbol)} className={selected?.symbol === row.symbol ? "is-selected" : ""}><span>{row.symbol}</span><strong>+{row.change.toFixed(2)}%</strong></button>)}</div>
            <div className="market-flow-list"><h3 className="is-bearish">Bearish <span>{bearish.length}</span></h3>{bearish.slice(0, 20).map((row) => <button key={row.symbol} onClick={() => setSymbol(row.symbol)} className={selected?.symbol === row.symbol ? "is-selected" : ""}><span>{row.symbol}</span><strong>{row.change.toFixed(2)}%</strong></button>)}</div>
          </div>
          {selected && <div className="market-flow-selection"><span>Selected underlying</span><strong>{selected.symbol}</strong><b className={selected.change >= 0 ? "is-bullish" : "is-bearish"}>{selected.change > 0 ? "+" : ""}{selected.change.toFixed(2)}%</b></div>}
        </section>
        <p className="market-flow-footnote">{status?.provider?.label || "Order Flow provider"} · This interim view uses spot prices only; it is not a futures/OI signal. Verify provider mode before using any market data.</p>
      </>}
    </main>
  );
}
