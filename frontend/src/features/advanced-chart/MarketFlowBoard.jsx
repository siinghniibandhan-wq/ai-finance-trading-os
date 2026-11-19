import React, { useMemo, useState } from "react";
import { useMarketOverview } from "../../marketOverviewStore.js";
import { buildMarketFlowDiagram, normalizeMarketFlow } from "./marketFlowModel";
import "./market-flow.css";

const money = (value) => new Intl.NumberFormat("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
const pct = (value) => `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;

function InstrumentNode({ item, side, selected, onSelect }) {
  return <button type="button" className={`mf-instrument-node is-${side}${selected ? " is-selected" : ""}`} onClick={() => onSelect(item)} aria-pressed={selected}>
    <span className="mf-node-symbol">{item.symbol}</span>
    <strong>{pct(item.changePercent)}</strong>
    <small>₹{money(item.lastPrice)} · {item.exchange}</small>
  </button>;
}

export default function MarketFlowBoard({ onSelectInstrument }) {
  // This legacy Advanced Chart surface shares the exact same app-wide feed as Market and Chart Flow.
  const { data: payload, loading, error, refresh } = useMarketOverview();
  const [selected, setSelected] = useState(null);
  const groups = useMemo(() => normalizeMarketFlow(payload), [payload]);
  const all = useMemo(() => [...groups.bullish, ...groups.bearish, ...groups.unchanged], [groups]);
  const diagram = useMemo(() => buildMarketFlowDiagram(groups, { width: 1200, height: 700 }), [groups]);
  const indices = Array.isArray(payload?.indices) ? payload.indices : [];
  const selectedItem = selected ? all.find((item) => item.symbol === selected.symbol && item.exchange === selected.exchange) || selected : null;
  const sourceName = payload?.data_sources?.primary || "m.Stock via Financial OS REST API";
  const hasRows = all.length > 0;
  const retrievedAt = payload?.last_updated || null;

  return <section className="mf-orderflow" aria-label="Order Flow live market visualisation">
    <header className="mf-orderflow-header">
      <div className="mf-brand-lockup"><span className="mf-brand-mark"/><div><div className="mf-eyebrow">FINANCIAL OS · LIVE MARKET DATA</div><h2>Order Flow</h2></div></div>
      <div className="mf-header-controls"><span className={`mf-live-state${loading ? " is-loading" : hasRows ? " is-live" : " is-unavailable"}`}>{loading ? "FETCHING REST DATA" : hasRows ? "PROVIDER DATA RECEIVED" : "DATA UNAVAILABLE"}</span><button type="button" onClick={() => void refresh()} disabled={loading}>↻ Refresh</button></div>
    </header>
    <div className="mf-market-strip">
      {indices.map((index) => <div className="mf-index-quote" key={`${index.exchange}-${index.symbol}`}><span>{index.name}</span><strong>{Number.isFinite(Number(index.last_price)) ? money(Number(index.last_price)) : "—"}</strong></div>)}
      {!indices.length && <span className="mf-no-index">Index quotes not returned by provider</span>}
      <span className="mf-universe-count">{all.length} returned movers</span>
    </div>
    {error && <div className="mf-data-alert" role="alert">{error}. Last successful snapshot remains visible; no simulated values are displayed.</div>}
    {!error && !loading && !hasRows && <div className="mf-data-alert" role="status">The provider returned no valid market movers. The flow board is intentionally empty; no demo data is substituted.</div>}
    <div className="mf-flow-layout">
      <section className="mf-flow-canvas" aria-label="Connected bullish and bearish market flow">
        <div className="mf-canvas-heading"><span>MARKET-WIDE PRICE DISTRIBUTION</span><span>Provider-reported percentage change</span></div>
        <svg className="mf-flow-svg" viewBox="0 0 1200 700" preserveAspectRatio="none" aria-hidden="true">
          <path d={`M 0 ${diagram.zeroY} H 1200`} className="mf-zero-line"/>
          {diagram.connections.map((connection) => <path key={`${connection.exchange}-${connection.symbol}`} d={connection.path} className={`mf-flow-path is-${connection.side}`} vectorEffect="non-scaling-stroke" />)}
        </svg>
        <div className="mf-zero-label">0.00%</div>
        <div className="mf-flow-gate"><span>MARKET</span><strong>FLOW</strong><small>{all.length ? `${all.length} provider rows` : "Awaiting provider data"}</small></div>
        <div className="mf-flow-groups">
          <div className="mf-flow-group mf-flow-group-bull"><div className="mf-flow-group-title"><span>BULLISH</span><strong>{groups.bullish.length}</strong></div><div className="mf-node-grid">{groups.bullish.map((item) => <InstrumentNode key={`${item.exchange}-${item.symbol}`} item={item} side="bullish" selected={selectedItem?.symbol === item.symbol && selectedItem?.exchange === item.exchange} onSelect={setSelected}/>)}</div></div>
          <div className="mf-flow-group mf-flow-group-bear"><div className="mf-flow-group-title"><span>BEARISH</span><strong>{groups.bearish.length}</strong></div><div className="mf-node-grid">{groups.bearish.map((item) => <InstrumentNode key={`${item.exchange}-${item.symbol}`} item={item} side="bearish" selected={selectedItem?.symbol === item.symbol && selectedItem?.exchange === item.exchange} onSelect={setSelected}/>)}</div></div>
        </div>
      </section>
      <aside className="mf-instrument-detail" aria-live="polite">
        <div className="mf-detail-kicker">SELECTED INSTRUMENT</div>
        {selectedItem ? <>
          <div className="mf-detail-title"><div><h3>{selectedItem.symbol}</h3><span>{selectedItem.name} · {selectedItem.exchange}</span></div><button type="button" onClick={() => onSelectInstrument?.({ symbol: selectedItem.symbol, exchange: selectedItem.exchange, name: selectedItem.name })}>Open chart ↗</button></div>
          <div className={`mf-detail-change ${selectedItem.changePercent >= 0 ? "is-up" : "is-down"}`}>{pct(selectedItem.changePercent)}</div>
          <div className="mf-detail-price">₹{money(selectedItem.lastPrice)}</div>
          <div className="mf-detail-stats"><div><span>VOLUME</span><strong>{selectedItem.volume == null ? "Not supplied" : new Intl.NumberFormat("en-IN").format(selectedItem.volume)}</strong></div><div><span>EXCHANGE</span><strong>{selectedItem.exchange}</strong></div></div>
        </> : <div className="mf-detail-empty">Select an instrument from the flow network to inspect its provider-reported values.</div>}
        <div className="mf-capability-block"><strong>Futures OI / option-chain analytics</strong><span>Not supplied by the currently connected m.Stock Type A REST contract. No OI curves, strike profiles or build-up labels are fabricated.</span></div>
      </aside>
    </div>
    <footer className="mf-orderflow-footer"><span>Source: {sourceName}</span><span>{retrievedAt ? `Snapshot ${new Date(retrievedAt).toLocaleTimeString("en-IN")}` : "Snapshot not yet received"}</span><span>Coverage: returned gainers and losers only; not full F&O breadth</span>{payload?.status === "partial" && <strong>PARTIAL PROVIDER RESPONSE</strong>}</footer>
  </section>;
}
