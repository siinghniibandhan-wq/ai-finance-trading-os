import React, { useMemo, useState } from "react";
import MStockSessionPanel from "./MStockSessionPanel";
import OrderFlowLiveFeed from "./OrderFlowLiveFeed";
import {
  buildLiveOrderFlow,
  formatMarketNumber,
  formatMarketPercent,
  formatMarketTimestamp,
} from "./liveOrderFlowData";
import "./order-flow.css";
import "./live-order-flow.css";

function Metric({ label, value, detail }) {
  return (
    <article className="mf-live-metric">
      <small>{label}</small>
      <strong>{value}</strong>
      {detail && <span>{detail}</span>}
    </article>
  );
}

function DataTable({ title, description, columns, rows, empty }) {
  return (
    <section className="mf-live-section">
      <header>
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
        <span>{rows.length} rows</span>
      </header>
      {rows.length ? (
        <div className="mf-live-table-wrap">
          <table className="mf-live-table">
            <thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={row.key || row.contract || row.strike || index}>
                  {columns.map((column) => (
                    <td key={column.key}>{column.render ? column.render(row) : row[column.key] ?? "—"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <p className="mf-live-empty">{empty}</p>}
    </section>
  );
}

export default function OrderFlowPage() {
  const [snapshot, setSnapshot] = useState(null);
  const [symbol, setSymbol] = useState("");
  const flow = useMemo(() => buildLiveOrderFlow(snapshot, symbol), [snapshot, symbol]);
  const stream = snapshot?.stream || {};
  const feed = snapshot?.feed || {};

  const futuresRows = flow.futures.map((row) => ({
    ...row,
    key: `${row.contract}-${row.expiry}`,
  }));
  const optionRows = flow.options.map((row) => ({
    ...row,
    key: `${row.contract}-${row.expiry}`,
  }));
  const strikeRows = flow.optionOiByStrike.map((row) => ({
    ...row,
    key: String(row.strike),
  }));

  return (
    <main className="market-flow-workspace ui-flow oi-design">
      <header className="market-flow-header">
        <div>
          <p className="market-flow-eyebrow">LIVE DERIVATIVES · m.STOCK WEBSOCKET</p>
          <h1>Market Flow</h1>
          <p className="market-flow-subtitle">Verified futures ticks, options contracts and open interest from your authenticated m.Stock stream</p>
        </div>
        <span className={flow.isLive ? "mf-provider-pill is-live" : "mf-provider-pill"}>
          {flow.isLive ? "● LIVE m.Stock" : "● NOT LIVE"}
        </span>
      </header>

      <MStockSessionPanel />

      <div className="mf-live-toolbar">
        <label>
          <span>Underlying</span>
          <select value={symbol} onChange={(event) => setSymbol(event.target.value)}>
            <option value="">All subscribed F&amp;O underlyings</option>
            {flow.underlyings.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <div className="mf-live-asof">
          <small>Last provider tick</small>
          <strong>{formatMarketTimestamp(flow.asOf || feed.last_tick_at)}</strong>
        </div>
      </div>

      <OrderFlowLiveFeed symbol={symbol || undefined} onSnapshot={setSnapshot} />

      <section className="mf-live-metrics">
        <Metric label="Futures contracts" value={flow.isLive ? flow.futures.length : "—"} detail="Provider ticks with valid LTP" />
        <Metric label="Options contracts" value={flow.isLive ? flow.options.length : "—"} detail="Provider ticks with valid OI" />
        <Metric label="Underlyings" value={flow.isLive ? flow.underlyings.length : "—"} detail="Verified instrument master" />
        <Metric label="Cached gateway ticks" value={flow.isLive ? (flow.coverage.cached_ticks ?? stream.cached_instruments ?? "—") : "—"} detail={feed.age_seconds == null ? "Awaiting first tick" : `Tick age ${formatMarketNumber(feed.age_seconds)}s`} />
      </section>

      <DataTable
        title="Live futures"
        description="Latest provider-decoded futures price, volume and open interest. No estimated values are inserted."
        rows={futuresRows}
        empty="No fresh futures ticks are available. Confirm the m.Stock session and WebSocket status above."
        columns={[
          { key: "symbol", label: "Underlying" },
          { key: "contract", label: "Contract" },
          { key: "expiry", label: "Expiry" },
          { key: "price", label: "LTP", render: (row) => row.price == null ? "—" : `₹${formatMarketNumber(row.price)}` },
          { key: "changePct", label: "Change", render: (row) => formatMarketPercent(row.changePct) },
          { key: "open", label: "Open", render: (row) => formatMarketNumber(row.ohlc?.open) },
          { key: "high", label: "Day high", render: (row) => formatMarketNumber(row.ohlc?.high) },
          { key: "low", label: "Day low", render: (row) => formatMarketNumber(row.ohlc?.low) },
          { key: "close", label: "Prev close", render: (row) => formatMarketNumber(row.ohlc?.close) },
          { key: "volume", label: "Volume", render: (row) => formatMarketNumber(row.volume) },
          { key: "oi", label: "Open interest", render: (row) => formatMarketNumber(row.oi) },
          { key: "exchangeTimestamp", label: "Exchange time", render: (row) => formatMarketTimestamp(row.exchangeTimestamp || row.receivedAt) },
        ]}
      />

      <DataTable
        title="Live options contracts"
        description="Individual option contracts received through the same WebSocket session."
        rows={optionRows}
        empty="No fresh option-contract ticks are available for this selection."
        columns={[
          { key: "symbol", label: "Underlying" },
          { key: "contract", label: "Contract" },
          { key: "expiry", label: "Expiry" },
          { key: "strike", label: "Strike", render: (row) => formatMarketNumber(row.strike) },
          { key: "optionType", label: "Type" },
          { key: "price", label: "LTP", render: (row) => row.price == null ? "—" : `₹${formatMarketNumber(row.price)}` },
          { key: "changePct", label: "Change", render: (row) => formatMarketPercent(row.changePct) },
          { key: "volume", label: "Volume", render: (row) => formatMarketNumber(row.volume) },
          { key: "oi", label: "Open interest", render: (row) => formatMarketNumber(row.oi) },
        ]}
      />

      <DataTable
        title="Option open interest by strike"
        description="Call and put OI aggregated from the live option ticks. PCR and OI change are not inferred."
        rows={strikeRows}
        empty="Strike-wise OI will appear when fresh CE and PE ticks arrive."
        columns={[
          { key: "strike", label: "Strike", render: (row) => formatMarketNumber(row.strike) },
          { key: "callOi", label: "Call OI", render: (row) => formatMarketNumber(row.callOi) },
          { key: "putOi", label: "Put OI", render: (row) => formatMarketNumber(row.putOi) },
        ]}
      />

      <p className="mf-live-disclaimer">
        Only provider ticks marked fresh are displayed. No demo prices, simulated candles, synthetic percentage changes,
        estimated support/resistance, invented previous OI or fabricated conviction scores are used. Historical OI and
        OI change require a separate verified historical data source.
      </p>
    </main>
  );
}
