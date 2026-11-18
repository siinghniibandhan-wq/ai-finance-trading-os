import React, { useEffect, useMemo, useState } from "react";
import { loadMarketOverview } from "./api";
import { normalizeMarketFlow, summarizeMarketFlow } from "./marketFlowModel";
import "./market-flow.css";

const money = (value) => new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(value);

function FlowTile({ item, direction, onSelect }) {
  return (
    <button
      type="button"
      className={`market-flow-tile is-${direction}`}
      onClick={() => onSelect?.({ symbol: item.symbol, exchange: item.exchange, name: item.name })}
      aria-label={`Open ${item.symbol} chart, ${item.changePercent.toFixed(2)} percent`}
    >
      <span className="market-flow-tile-symbol">{item.symbol}</span>
      <strong className="market-flow-tile-change">
        {item.changePercent > 0 ? "+" : ""}{item.changePercent.toFixed(2)}%
      </strong>
      <span className="market-flow-tile-price">₹{money(item.lastPrice)}</span>
      <span className="market-flow-tile-exchange">{item.exchange}</span>
    </button>
  );
}

function FlowConnections({ bullishCount, bearishCount }) {
  const upper = Math.min(Math.max(bullishCount, 1), 8);
  const lower = Math.min(Math.max(bearishCount, 1), 8);
  return (
    <svg className="market-flow-connections" viewBox="0 0 900 330" preserveAspectRatio="none" aria-hidden="true">
      {Array.from({ length: upper }, (_, index) => {
        const y = 26 + index * (112 / Math.max(upper - 1, 1));
        return <path key={`up-${index}`} d={`M 92 165 C 260 165, 290 ${y}, 470 ${y}`} className="flow-line flow-line-bullish" />;
      })}
      {Array.from({ length: lower }, (_, index) => {
        const y = 218 + index * (86 / Math.max(lower - 1, 1));
        return <path key={`down-${index}`} d={`M 92 165 C 260 165, 290 ${y}, 470 ${y}`} className="flow-line flow-line-bearish" />;
      })}
      <path d="M 0 165 H 900" className="flow-baseline" />
    </svg>
  );
}

export default function MarketFlowBoard({ onSelectInstrument }) {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState(null);

  const refresh = async () => {
    setLoading(true);
    setError("");
    try {
      const next = await loadMarketOverview();
      setPayload(next);
      setUpdatedAt(new Date());
    } catch (requestError) {
      setError(requestError?.message || "Market Flow data is unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const groups = useMemo(() => normalizeMarketFlow(payload), [payload]);
  const summary = useMemo(() => summarizeMarketFlow(groups), [groups]);
  const indices = Array.isArray(payload?.indices) ? payload.indices : [];
  const total = summary.bullish + summary.bearish + summary.unchanged;

  return (
    <section className="market-flow-board" aria-label="Market Flow workspace">
      <header className="market-flow-heading">
        <div>
          <div className="market-flow-eyebrow">MARKET-WIDE DIRECTIONAL DISTRIBUTION</div>
          <h2>Market Flow</h2>
          <p>Provider-reported market movers arranged by price direction. This view does not represent traded capital flow.</p>
        </div>
        <button type="button" className="market-flow-refresh" onClick={refresh} disabled={loading}>
          {loading ? "Loading…" : "Refresh data"}
        </button>
      </header>

      <div className="market-flow-index-strip">
        {indices.map((index) => (
          <div className="market-flow-index" key={`${index.exchange}-${index.symbol}`}>
            <span>{index.name}</span>
            <strong>{Number.isFinite(Number(index.last_price)) ? money(Number(index.last_price)) : "—"}</strong>
          </div>
        ))}
        {!indices.length && <span className="market-flow-muted">Index snapshots unavailable</span>}
      </div>

      <div className="market-flow-summary">
        <div className="flow-summary-bullish"><span>BULLISH</span><strong>{summary.bullish}</strong></div>
        <div className="flow-summary-bearish"><span>BEARISH</span><strong>{summary.bearish}</strong></div>
        <div><span>UNCHANGED</span><strong>{summary.unchanged}</strong></div>
        <div><span>PROVIDER ROWS</span><strong>{total}</strong></div>
      </div>

      {error && <div className="market-flow-message is-error" role="alert">{error}</div>}
      {!error && !loading && !total && (
        <div className="market-flow-message" role="status">No valid market-mover rows were returned by the provider. No values have been substituted.</div>
      )}

      <div className="market-flow-network">
        <div className="market-flow-side market-flow-side-bullish">
          <div className="market-flow-side-heading"><span>BULLISH LEADERS</span><strong>{groups.bullish.length}</strong></div>
          {groups.bullish.slice(0, 10).map((item) => (
            <FlowTile key={`${item.exchange}-${item.symbol}`} item={item} direction="bullish" onSelect={onSelectInstrument} />
          ))}
          {!groups.bullish.length && <p className="market-flow-empty">No verified advancing rows</p>}
        </div>

        <div className="market-flow-core">
          <FlowConnections bullishCount={groups.bullish.length} bearishCount={groups.bearish.length} />
          <div className="market-flow-core-node">
            <span>MARKET</span>
            <strong>FLOW</strong>
            <small>{total ? `${total} provider rows` : "Awaiting data"}</small>
          </div>
          <div className="market-flow-core-caption">Directional price distribution</div>
        </div>

        <div className="market-flow-side market-flow-side-bearish">
          <div className="market-flow-side-heading"><span>BEARISH LEADERS</span><strong>{groups.bearish.length}</strong></div>
          {groups.bearish.slice(0, 10).map((item) => (
            <FlowTile key={`${item.exchange}-${item.symbol}`} item={item} direction="bearish" onSelect={onSelectInstrument} />
          ))}
          {!groups.bearish.length && <p className="market-flow-empty">No verified declining rows</p>}
        </div>
      </div>

      <footer className="market-flow-footer">
        <span>Source: {payload?.data_sources?.primary || "Financial OS market overview API"}</span>
        <span>{updatedAt ? `Retrieved ${updatedAt.toLocaleTimeString("en-IN")}` : "Not yet retrieved"}</span>
        <span>Coverage: provider movers response, limited to its returned rows</span>
        {payload?.status === "partial" && <strong>Partial provider response</strong>}
      </footer>
    </section>
  );
}
