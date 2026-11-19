import React, { useCallback, useMemo, useState } from "react";
import { useMarketOverview } from "../../marketOverviewStore.js";
import { buildDistributionDots, buildMarketFlowBoard, normalizeOrderFlow } from "./orderFlowModel.js";
import MarketFlowPriceChart from "./MarketFlowPriceChart.jsx";
import "./market-flow-board.css";

const fmt = (value, digits = 2) => Number.isFinite(Number(value))
  ? new Intl.NumberFormat("en-IN", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(Number(value))
  : "—";
const pct = value => (value > 0 ? "+" : "") + fmt(value) + "%";
const keyOf = row => row.exchange + ":" + row.symbol;

function Distribution({ rows, counts, retrievedAt, breadthAvailable }) {
  const dots = useMemo(() => buildDistributionDots(rows), [rows]);
  return <section className="mfb-section mfb-distribution">
    <div className="mfb-section-head">
      <div><small>01 / MARKET DISTRIBUTION</small><h2>Where the market is moving</h2>
        <p>Every dot is an actual NSE/BSE mover returned by m.Stock. Counts describe this returned set, not full-exchange breadth.</p></div>
      <div className="mfb-counts"><b className="up">{counts.bullish} bullish</b><b className="down">{counts.bearish} bearish</b><b className="flat">{breadthAvailable ? counts.unchanged : "—"} flat</b></div>
    </div>
    <svg viewBox="0 0 1000 84" role="img" aria-label="Provider-returned percentage changes distributed around zero">
      <line x1="40" x2="960" y1="42" y2="42" className="mfb-axis"/>
      <line x1="500" x2="500" y1="8" y2="70" className="mfb-zero"/>
      <text x="40" y="81">LOSERS</text><text x="500" y="81" textAnchor="middle">0%</text><text x="960" y="81" textAnchor="end">GAINERS</text>
      {dots.map((dot, i) => <g key={keyOf(dot) + i}><circle cx={dot.x} cy={dot.y} r="3.2" className={dot.changePercent > 0 ? "mfb-dot up" : dot.changePercent < 0 ? "mfb-dot down" : "mfb-dot flat"}/><title>{dot.symbol + " · " + pct(dot.changePercent)}</title></g>)}
    </svg>
    <div className="mfb-foot"><span>{rows.length} provider-returned instruments</span><span>Snapshot assembled: {retrievedAt || "not received"}</span></div>
  </section>;
}

function FlowDiagram({ board, selectedKey, onSelect }) {
  const top = board.visibleBullish;
  const bottom = board.visibleBearish;
  const flat = board.unchanged.slice(0, 8);
  const gap = 30;
  const rows = Math.max(top.length, bottom.length, 3);
  const height = Math.max(410, rows * gap * 2 + 110);
  const center = height / 2;
  const paths = [
    ...top.map((row, i) => ({ row, y: center - 42 - i * gap, side: "up" })),
    ...bottom.map((row, i) => ({ row, y: center + 42 + i * gap, side: "down" })),
  ];
  return <div className="mfb-diagram-wrap">
    <svg className="mfb-diagram" viewBox={"0 0 690 " + height} role="img" aria-label="Zero-centred market flow paths converging into bullish and bearish groups">
      <text x="20" y="20" className="mfb-caption">PRICE CHANGE FROM ZERO</text>
      <line x1="20" x2="660" y1={center} y2={center} className="mfb-zero-line"/>
      <text x="20" y={center - 10} className="mfb-zero-text">0%</text>
      {paths.map(({ row, y, side }) => {
        const selected = keyOf(row) === selectedKey;
        const strength = Math.min(1, Math.abs(row.changePercent) / board.maxAbs);
        return <g key={keyOf(row)} role="button" tabIndex="0" className={"mfb-path " + side + (selected ? " selected" : "")}
          onClick={() => onSelect(row)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(row); } }}>
          <path d={"M 28 " + center + " C 170 " + center + ", 340 " + y + ", 570 " + y}
            style={{ opacity: selected ? 1 : .25 + strength * .5, strokeWidth: selected ? 3.2 : 1.1 + strength * 1.8 }}/>
          <circle cx="570" cy={y} r={selected ? 5 : 3.2}/><title>{row.symbol + ": " + pct(row.changePercent)}</title>
        </g>;
      })}
      <rect x="570" y="34" width="22" height={Math.max(40, center - 58)} rx="9" className="mfb-gate-up"/>
      <path d={"M 570 " + (center - 32) + " L 594 " + (center - 9) + " L 594 " + (center + 9) + " L 570 " + (center + 32) + " Z"} className="mfb-gate-flat"/>
      <rect x="570" y={center + 58} width="22" height={Math.max(40, center - 94)} rx="9" className="mfb-gate-down"/>
      <text x="604" y="48" className="mfb-gate-label up">BULLISH</text>
      <text x="604" y={center + 4} className="mfb-gate-label flat">FLAT</text>
      <text x="604" y={height - 28} className="mfb-gate-label down">BEARISH</text>
      {flat.map((row, i) => <g key={keyOf(row)} role="button" tabIndex="0" className={"mfb-flat-point" + (keyOf(row) === selectedKey ? " selected" : "")}
        onClick={() => onSelect(row)} onKeyDown={event => { if (event.key === "Enter") onSelect(row); }}>
        <circle cx={580 + (i % 3) * 7} cy={center + (Math.floor(i / 3) - 1) * 8} r="3"/><title>{row.symbol + ": unchanged"}</title></g>)}
    </svg>
    <div className="mfb-diagram-foot"><span>Movers start at the zero reference</span><span>Path positions use actual provider percentage changes</span></div>
  </div>;
}

function Side({ title, side, rows, selectedKey, onSelect }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? rows : rows.slice(0, 8);
  return <section className={"mfb-side " + side}>
    <div className="mfb-side-head"><h3>{title}</h3><b>{rows.length}</b></div>
    <div className="mfb-tiles">{visible.map(row => <button key={keyOf(row)} type="button"
      className={"mfb-tile " + side + (keyOf(row) === selectedKey ? " selected" : "")} onClick={() => onSelect(row)}>
      <span>{row.symbol}</span><strong>{pct(row.changePercent)}</strong>
      <small>₹{fmt(row.price)} · {row.exchange}</small>
      <small>Volume {row.volume === null ? "not supplied" : fmt(row.volume, 0)}</small>
    </button>)}
    {!visible.length && <p className="mfb-empty">No instruments returned on this side.</p>}</div>
    {rows.length > 8 && <button type="button" className="mfb-more" onClick={() => setExpanded(value => !value)}>{expanded ? "Show fewer" : "Show all " + rows.length}</button>}
  </section>;
}

export default function MarketFlowBoard({ onSelectInstrument }) {
  // Market and Order Flow subscribe to the same app-wide snapshot and refresh lifecycle.
  const { data: payload, loading, error, refresh } = useMarketOverview();
  const [refreshing, setRefreshing] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);
  const retrievedAt = payload?.last_updated || null;
  const refreshManually = useCallback(async () => {
    setRefreshing(true);
    try { await refresh(); } catch { /* The shared store retains the last successful snapshot. */ }
    finally { setRefreshing(false); }
  }, [refresh]);

  const rows = useMemo(() => normalizeOrderFlow(payload), [payload]);
  const board = useMemo(() => buildMarketFlowBoard(rows), [rows]);
  const indices = Array.isArray(payload?.indices) ? payload.indices : [];
  const selected = rows.find(row => keyOf(row) === selectedKey) || null;
  const sectors = useMemo(() => {
    const groups = new Map();
    rows.forEach(row => { if (row.sector) groups.set(row.sector, [...(groups.get(row.sector) || []), row.changePercent]); });
    return [...groups.entries()].map(([name, values]) => ({
      name, median: [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)],
      up: values.filter(value => value > 0).length, flat: values.filter(value => value === 0).length, down: values.filter(value => value < 0).length,
    })).sort((a, b) => b.median - a.median);
  }, [rows]);

  return <main className="market-flow-board">
    <header className="mfb-header"><div><small>FINANCIAL OS / MARKETS / ORDER FLOW</small><h1>Chart Flow</h1>
      <p>Whole-market discovery from real provider-returned cash-equity movers and supported indices.</p></div>
      <div><span className={error ? "mfb-status error" : loading ? "mfb-status" : "mfb-status live"}>{error ? "SOURCE ERROR" : loading ? "CONNECTING" : payload?.status === "partial" ? "PARTIAL DATA" : "REST SNAPSHOT"}</span>
        <button type="button" onClick={refreshManually} disabled={loading || refreshing}>{refreshing ? "Refreshing…" : "Refresh"}</button></div>
    </header>
    <section className="mfb-index-rail">{indices.map(index => <div key={index.exchange + ":" + index.name}>
      <small>{index.name}</small><strong>{fmt(index.last_price)}</strong><span>{index.exchange}</span></div>)}
      {!indices.length && <p>No index snapshots returned by the provider.</p>}</section>
    {error && <p className="mfb-alert" role="alert">{error}. Last successful data is retained; no demo feed is substituted.</p>}{payload?.status === "partial" && <p className="mfb-alert" role="status">Some provider requests failed. The board contains only the successful real responses; missing instruments are not filled with estimates.</p>}
    {!loading && !rows.length && !error && <p className="mfb-alert">No valid provider movers were returned. No simulated instruments are displayed.</p>}
    <Distribution rows={rows} counts={board.counts} breadthAvailable={payload?.capabilities?.full_advance_decline_breadth === true} retrievedAt={retrievedAt ? new Date(retrievedAt).toLocaleTimeString("en-IN") : null}/>
    <section className="mfb-section mfb-flow">
      <div className="mfb-section-head"><div><small>02 / MARKET FLOW</small><h2>Zero-centred market flow</h2>
        <p>Actual price changes fan through the central gate into bullish and bearish instruments. This is a current snapshot, not a reconstructed intraday history.</p></div>
        <span className="mfb-poll">Shared Market feed · 30-second refresh</span></div>
      <div className="mfb-board">
        <div className="mfb-visual"><FlowDiagram board={board} selectedKey={selectedKey} onSelect={row => setSelectedKey(keyOf(row))}/>
          <section className="mfb-sectors"><div><small>03 / SECTOR FLOW</small><b>Sector participation</b></div>
            {sectors.length ? sectors.map(sector => <div className="mfb-sector" key={sector.name}>
              <span>{sector.name}</span><strong className={sector.median >= 0 ? "up" : "down"}>{pct(sector.median)}</strong>
              <i><b className="up" style={{ width: (sector.up / (sector.up + sector.flat + sector.down) * 100) + "%" }}/><b className="flat" style={{ width: (sector.flat / (sector.up + sector.flat + sector.down) * 100) + "%" }}/><b className="down" style={{ width: (sector.down / (sector.up + sector.flat + sector.down) * 100) + "%" }}/></i>
            </div>) : <p>Sector classifications are not included in the current Market Overview REST response. Sector performance is withheld rather than guessed.</p>}
          </section>
        </div>
        <div className="mfb-sides"><Side title="Bullish" side="up" rows={board.bullish} selectedKey={selectedKey} onSelect={row => setSelectedKey(keyOf(row))}/>
          <Side title="Bearish" side="down" rows={board.bearish} selectedKey={selectedKey} onSelect={row => setSelectedKey(keyOf(row))}/></div>
      </div>
    </section>
    <section className="mfb-detail"><div><small>04 / INSTRUMENT DETAIL</small><h2>{selected ? selected.name : "Select an instrument"}</h2>
      {selected && <span>{selected.symbol} · {selected.exchange}</span>}</div>
      {selected ? <div className="mfb-detail-values"><div><small>LAST PRICE</small><strong>₹{fmt(selected.price)}</strong></div>
        <div><small>PRICE CHANGE</small><strong className={selected.direction}>{pct(selected.changePercent)}</strong></div>
        <div><small>VOLUME</small><strong>{selected.volume === null ? "Not supplied" : fmt(selected.volume, 0)}</strong></div>
        <button type="button" onClick={() => onSelectInstrument?.(selected)}>Open full chart</button></div>
        : <p>Select a flow path or tile. Only provider-returned fields are shown.</p>}
    </section>
    <MarketFlowPriceChart instrument={selected} />
    <footer className="mfb-footer"><span>Source: {payload?.data_sources?.primary || "m.Stock via Financial OS Gateway"}</span>
      <span>Snapshot assembled: {retrievedAt ? new Date(retrievedAt).toLocaleString("en-IN") : "—"}</span>
      <span>Read-only · REST only · no synthetic market values</span></footer>
  </main>;
}
