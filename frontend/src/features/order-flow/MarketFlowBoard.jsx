import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { loadChartHistory, loadMarketFlowSnapshot } from "../advanced-chart/api.js";
import { buildDistributionDots, buildMarketFlowBoard, filterOrderFlow, normalizeOrderFlow, normalizeSectorMovers, sortOrderFlow, buildHistoricalFlowSeries, summarizeSectorMoverSample, buildSectorFlowRows, summarizeMoverVolume, buildHistoricalCandleGeometry } from "./orderFlowModel.js";
import "./market-flow-board.css";

const fmt = (value, digits = 2) => Number.isFinite(Number(value))
  ? new Intl.NumberFormat("en-IN", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(Number(value))
  : "—";
const pct = value => (value > 0 ? "+" : "") + fmt(value) + "%";
const keyOf = row => row.exchange + ":" + row.symbol;

function Distribution({ rows, counts, retrievedAt, breadthAvailable, eyebrow = "01 / MARKET DISTRIBUTION", title = "Where the market is moving", description = "Every dot is an actual NSE/BSE mover returned by m.Stock. Counts describe this returned set, not full-exchange breadth." }) {
  const dots = useMemo(() => buildDistributionDots(rows), [rows]);
  return <section className="mfb-section mfb-distribution">
    <div className="mfb-section-head">
      <div><small>{eyebrow}</small><h2>{title}</h2>
        <p>{description}</p></div>
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

function FlowDiagram({ board, selectedKey, focusedKey, onSelect, onHover }) {
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
    <svg className="mfb-diagram" viewBox={"0 0 690 " + height} role="img" aria-label="Market price flow fanning from the market origin through a directional gate into bullish and bearish groups">
      <defs>
        <marker id="mfb-arrow-up" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7 Z" className="mfb-arrow-up"/></marker>
        <marker id="mfb-arrow-down" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7 Z" className="mfb-arrow-down"/></marker>
      </defs>
      <text x="20" y="20" className="mfb-caption">MARKET FLOW · PRICE CHANGE FROM ZERO</text>
      <line x1="20" x2="660" y1={center} y2={center} className="mfb-zero-line"/>
      <circle cx="28" cy={center} r="6" className="mfb-flow-origin"/>
      <text x="20" y={center - 14} className="mfb-zero-text">MARKET</text>
      <text x="20" y={center + 16} className="mfb-zero-text">0%</text>
      {paths.map(({ row, y, side }) => {
        const selected = keyOf(row) === selectedKey || keyOf(row) === focusedKey;
        const strength = Math.min(1, Math.abs(row.changePercent) / board.maxAbs);
        return <g key={keyOf(row)} role="button" tabIndex="0"
          aria-label={`${row.name}, ${row.symbol}, ${pct(row.changePercent)}, ${row.exchange}. Select instrument`}
          aria-pressed={keyOf(row) === selectedKey}
          className={"mfb-path " + side + (selected ? " selected" : "")}
          onMouseEnter={() => onHover(keyOf(row))} onMouseLeave={() => onHover(null)}
          onFocus={() => onHover(keyOf(row))} onBlur={() => onHover(null)}
          onClick={() => onSelect(row)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(row); } }}>
          <path d={"M 34 " + center + " C 170 " + center + ", 340 " + y + ", 570 " + y}
            markerEnd={side === "up" ? "url(#mfb-arrow-up)" : "url(#mfb-arrow-down)"}
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
      {flat.map((row, i) => <g key={keyOf(row)} role="button" tabIndex="0"
        aria-label={`${row.name}, ${row.symbol}, unchanged, ${row.exchange}. Select instrument`}
        aria-pressed={keyOf(row) === selectedKey}
        className={"mfb-flat-point" + (keyOf(row) === selectedKey ? " selected" : "")}
        onMouseEnter={() => onHover(keyOf(row))} onMouseLeave={() => onHover(null)}
        onFocus={() => onHover(keyOf(row))} onBlur={() => onHover(null)}
        onClick={() => onSelect(row)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(row); } }}>
        <circle cx={580 + (i % 3) * 7} cy={center + (Math.floor(i / 3) - 1) * 8} r="3"/><title>{row.symbol + ": unchanged"}</title></g>)}
    </svg>
    <div className="mfb-diagram-foot"><span>Movers start at the zero reference</span><span>Path positions use actual provider percentage changes</span></div>
  </div>;
}

function Side({ title, side, rows, selectedKey, focusedKey, onSelect, onHover }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? rows : rows.slice(0, 8);
  return <section className={"mfb-side " + side}>
    <div className="mfb-side-head"><h3>{title}</h3><b>{rows.length}</b></div>
    <div className="mfb-tiles">{visible.map(row => <button key={keyOf(row)} type="button"
      className={"mfb-tile " + side + (keyOf(row) === selectedKey || keyOf(row) === focusedKey ? " selected" : "")}
      onMouseEnter={() => onHover(keyOf(row))} onMouseLeave={() => onHover(null)}
      onFocus={() => onHover(keyOf(row))} onBlur={() => onHover(null)} onClick={() => onSelect(row)}>
      <span>{row.symbol}</span><strong>{pct(row.changePercent)}</strong>
      <small>₹{fmt(row.price)} · {row.exchange}</small>
      <small>Volume {row.volume === null ? "not supplied" : fmt(row.volume, 0)}</small>
    </button>)}
    {!visible.length && <p className="mfb-empty">No instruments returned on this side.</p>}</div>
    {rows.length > 8 && <button type="button" className="mfb-more" onClick={() => setExpanded(value => !value)}>{expanded ? "Show fewer" : "Show all " + rows.length}</button>}
  </section>;
}



/**
 * Connected sector-index flow. The branch is sourced from the provider's
 * sector universe; each diverging bar uses only the provider's index
 * percentage change. A missing percentage remains an explicit gap.
 */
function SectorFlowDiagram({ sectors, selectedKey, loading, onSelect }) {
  const rowHeight = 34;
  const top = 44;
  const height = Math.max(130, top + sectors.length * rowHeight + 24);
  const centerY = top + Math.max(0, sectors.length - 1) * rowHeight / 2;
  const centerX = 720;
  const maxAbs = Math.max(0.1, ...sectors.map(row => row.percentChange === null ? 0 : Math.abs(row.percentChange)));
  const halfWidth = 166;

  if (!sectors.length) {
    return <div className="mfb-sector-flow-empty" role="status">Sector universe is unavailable from the current REST response.</div>;
  }

  return <div className="mfb-sector-flow-wrap">
    <div className="mfb-sector-flow-legend">
      <span><i className="up"/> Calculated index change (LTP vs previous close)</span>
      <span><i className="down"/> Negative performance</span>
      <span>Unavailable values are not plotted</span>
    </div>
    <svg className="mfb-sector-flow" viewBox={`0 0 1000 ${height}`} role="group" aria-label="Provider sector indices connected to the market flow, ranked by calculated percentage change">
      <line x1="116" y1={centerY} x2="190" y2={centerY} className="mfb-sector-root"/>
      <line x1="190" y1={top} x2="190" y2={top + (sectors.length - 1) * rowHeight} className="mfb-sector-spine"/>
      <circle cx="116" cy={centerY} r="7" className="mfb-sector-origin"/>
      <text x="18" y={centerY - 5} className="mfb-sector-root-label">MARKET</text>
      <text x="18" y={centerY + 10} className="mfb-sector-root-sub">SECTOR FLOW</text>
      <line x1={centerX} x2={centerX} y1={top - 18} y2={top + sectors.length * rowHeight - 12} className="mfb-sector-zero"/>
      <text x={centerX} y={top - 24} textAnchor="middle" className="mfb-sector-axis-label">0%</text>
      {sectors.map((sector, index) => {
        const y = top + index * rowHeight;
        const selected = sector.key === selectedKey;
        const value = sector.percentChange;
        const barWidth = value === null ? 0 : Math.abs(value) / maxAbs * halfWidth;
        const barX = value === null ? centerX : value >= 0 ? centerX : centerX - barWidth;
        return <g key={sector.key} role="button" tabIndex="0" aria-disabled={loading} aria-pressed={selected}
          aria-label={`${sector.name}, ${value === null ? "index performance unavailable" : pct(value)}, ${sector.lastPrice === null ? "index level unavailable" : "index level " + fmt(sector.lastPrice)}. Select sector`}
          className={`mfb-sector-flow-row${selected ? " selected" : ""}`}
          onClick={() => { if (!loading) onSelect(sector.key); }}
          onKeyDown={event => {
            if (!loading && (event.key === "Enter" || event.key === " ")) {
              event.preventDefault();
              onSelect(sector.key);
            }
          }}>
          <line x1="190" y1={y} x2="222" y2={y} className="mfb-sector-branch"/>
          <rect x="222" y={y - 14} width="758" height="28" rx="5" className="mfb-sector-row-bg"/>
          <text x="238" y={y - 1} className="mfb-sector-name">{sector.name}</text>
          <text x="238" y={y + 11} className="mfb-sector-symbol">{sector.indexSymbol || "Index symbol unavailable"}{sector.lastPrice === null ? "" : ` · ${fmt(sector.lastPrice)}`}</text>
          {value !== null && <rect x={barX} y={y - 5} width={barWidth} height="10" rx="3" className={value > 0 ? "mfb-sector-bar-up" : value < 0 ? "mfb-sector-bar-down" : "mfb-sector-bar-flat"}/>}
          <text x="930" y={y + 4} textAnchor="end" className={`mfb-sector-value ${value === null ? "unavailable" : value > 0 ? "up" : value < 0 ? "down" : "flat"}`}>{value === null ? "—" : pct(value)}</text>
        </g>;
      })}
      <text x={centerX - halfWidth} y={height - 4} textAnchor="start" className="mfb-sector-axis-label">WEAKER</text>
      <text x={centerX + halfWidth} y={height - 4} textAnchor="end" className="mfb-sector-axis-label">STRONGER</text>
    </svg>
    <div className="mfb-sector-flow-foot">{loading ? "Loading selected sector constituents…" : "Select a sector branch to reveal its provider-ranked stock movers."}</div>
  </div>;
}


/** Sector node fans into the provider-ranked gainers and losers for that sector. */
function SectorConstituentDiagram({ sectorName, board, selectedKey, focusedKey, onSelect, onHover }) {
  const bullish = board.visibleBullish;
  const bearish = board.visibleBearish;
  const topStart = 48;
  const topHeight = Math.max(120, bullish.length * 32);
  const centerY = topStart + topHeight + 46;
  const bottomStart = centerY + 48;
  const bottomHeight = Math.max(120, bearish.length * 32);
  const height = bottomStart + bottomHeight + 32;
  const branches = [
    ...bullish.map((row, index) => ({ row, side: "up", y: topStart + index * 32 })),
    ...bearish.map((row, index) => ({ row, side: "down", y: bottomStart + index * 32 })),
  ];

  return <div className="mfb-constituent-flow-wrap">
    <div className="mfb-constituent-flow-head">
      <span>SELECTED SECTOR</span><strong>{sectorName}</strong>
      <small>Provider-ranked gainers and losers · {bullish.length + bearish.length} returned instruments</small>
    </div>
    {branches.length ? <svg className="mfb-constituent-flow" viewBox={`0 0 1000 ${height}`} role="group" aria-label={`${sectorName} sector index connected to its provider-ranked stock gainers and losers`}>
      <line x1="154" y1={centerY} x2="224" y2={centerY} className="mfb-constituent-root-line"/>
      <circle cx="154" cy={centerY} r="7" className="mfb-constituent-root"/>
      <text x="18" y={centerY - 5} className="mfb-constituent-root-label">SECTOR</text>
      <text x="18" y={centerY + 11} className="mfb-constituent-root-sub">INDEX NODE</text>
      <line x1="188" y1={topStart} x2="188" y2={bottomStart + Math.max(0, bearish.length - 1) * 32} className="mfb-constituent-spine"/>
      <text x="430" y={topStart - 18} className="mfb-constituent-group up">GAINERS</text>
      <text x="430" y={bottomStart - 18} className="mfb-constituent-group down">LOSERS</text>
      {branches.map(({ row, side, y }) => {
        const selected = keyOf(row) === selectedKey || keyOf(row) === focusedKey;
        return <g key={keyOf(row)} role="button" tabIndex="0"
          aria-label={`${row.name}, ${row.symbol}, ${pct(row.changePercent)}, price ${fmt(row.price)}, volume ${row.volume === null ? "unavailable" : fmt(row.volume, 0)}. Select stock`}
          aria-pressed={keyOf(row) === selectedKey}
          className={`mfb-constituent-node ${side}${selected ? " selected" : ""}`}
          onMouseEnter={() => onHover(keyOf(row))} onMouseLeave={() => onHover(null)}
          onFocus={() => onHover(keyOf(row))} onBlur={() => onHover(null)}
          onClick={() => onSelect(row)}
          onKeyDown={event => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onSelect(row);
            }
          }}>
          <line x1="188" y1={y} x2="224" y2={y} className="mfb-constituent-branch"/>
          <path d={`M 224 ${centerY} C 310 ${centerY}, 344 ${y}, 420 ${y}`} className="mfb-constituent-path"/>
          <rect x="420" y={y - 13} width="550" height="26" rx="5" className="mfb-constituent-node-bg"/>
          <text x="436" y={y + 4} className="mfb-constituent-symbol">{row.symbol}</text>
          <text x="560" y={y + 4} className="mfb-constituent-price">₹{fmt(row.price)}</text>
          <text x="690" y={y + 4} className="mfb-constituent-volume">{row.volume === null ? "Volume —" : "Vol " + fmt(row.volume, 0)}</text>
          <text x="948" y={y + 4} textAnchor="end" className="mfb-constituent-change">{pct(row.changePercent)}</text>
        </g>;
      })}
    </svg> : <p className="mfb-empty">No sector stock movers were returned by the provider.</p>}
    <div className="mfb-constituent-flow-foot">Select a stock node to connect its quote, volume and historical OHLCV chart below.</div>
  </div>;
}


function VolumeParticipation({ rows, label = "MARKET" }) {
  const summary = useMemo(() => summarizeMoverVolume(rows), [rows]);
  const max = Math.max(1, summary.bullishVolume, summary.bearishVolume, summary.unchangedVolume);
  const items = [
    { key: "bullish", label: "Bullish", volume: summary.bullishVolume, count: summary.bullishCount },
    { key: "bearish", label: "Bearish", volume: summary.bearishVolume, count: summary.bearishCount },
    { key: "flat", label: "Unchanged", volume: summary.unchangedVolume, count: summary.unchangedCount },
  ];
  return <section className="mfb-volume">
    <div className="mfb-volume-head"><div><small>VOLUME PARTICIPATION / {label}</small><b>Reported volume by direction</b></div>
      <span>{summary.positiveVolumeReported} with positive volume · {summary.zeroVolumeReported} reported zero</span></div>
    {summary.volumeReported > 0 && summary.positiveVolumeReported === 0 && <p className="mfb-volume-warning" role="status">The provider returned zero volume for every mover in this snapshot. Volume participation cannot be meaningfully ranked from these values.</p>}
    <div className="mfb-volume-bars">
      {items.map(item => <div className="mfb-volume-row" key={item.key}>
        <span>{item.label}</span><i><b className={item.key} style={{ width: item.volume / max * 100 + "%" }}/></i>
        <strong>{fmt(item.volume, 0)}</strong><small>{item.count} stocks</small>
      </div>)}
    </div>
    <p>Aggregated from returned movers only. This is not total exchange turnover or full-market participation.</p>
  </section>;
}

function HistoricalFlowPanel({ series, loading, error, symbol, range, onRangeChange }) {
  const chartScrollRef = useRef(null);
  const chartWidth = Math.max(720, 48 + Math.max(0, series.length - 1) * 6);
  const geometry = useMemo(() => buildHistoricalCandleGeometry(series, chartWidth), [series, chartWidth]);
  useEffect(() => {
    const viewport = chartScrollRef.current;
    if (viewport) viewport.scrollLeft = viewport.scrollWidth;
  }, [symbol, range, series.length]);
  if (loading) return <section className="mfb-history"><small>05 / HISTORICAL PRICE FLOW</small><p>Loading verified daily candles…</p></section>;
  if (error) return <section className="mfb-history"><small>05 / HISTORICAL PRICE FLOW</small><p className="mfb-alert">{error}</p></section>;
  if (!series.length) return <section className="mfb-history"><small>05 / HISTORICAL PRICE FLOW</small><p>No historical OHLCV observations returned for {symbol}. No chart is fabricated.</p></section>;

  const latest = series[series.length - 1];
  const first = series[0];
  const periodChange = first.close > 0 ? ((latest.close - first.close) / first.close) * 100 : null;
  return <section className="mfb-history">
    <div className="mfb-history-head"><div><small>05 / HISTORICAL PRICE FLOW</small><b>{symbol} · daily candlestick chart</b></div>
      <strong className={periodChange === null ? "" : periodChange >= 0 ? "up" : "down"}>{periodChange === null ? "—" : pct(periodChange)} over selected period</strong></div>
    <div className="mfb-history-toolbar" role="group" aria-label="Historical chart range">
      <span>DAILY · REST HISTORY</span>
      <div>{[["1M",30],["3M",90],["6M",180],["1Y",365],["5Y",1825]].map(([label]) =>
        <button key={label} type="button" aria-pressed={range === label} className={range === label ? "selected" : ""} onClick={() => onRangeChange(label)}>{label}</button>
      )}</div>
    </div>
    <div className="mfb-history-ohlc"><span>O ₹{latest.open === null ? "—" : fmt(latest.open)}</span><span>H ₹{latest.high === null ? "—" : fmt(latest.high)}</span><span>L ₹{latest.low === null ? "—" : fmt(latest.low)}</span><span>C ₹{fmt(latest.close)}</span><span>V {latest.volume === null ? "—" : fmt(latest.volume, 0)}</span></div>
    <div className="mfb-history-chart-scroll" ref={chartScrollRef} tabIndex="0" role="region" aria-label={`Scrollable daily chart for ${symbol}`}>
    <svg viewBox={`0 0 ${chartWidth} 196`} style={{ width: chartWidth + "px", maxWidth: "none" }} role="img" aria-label={`Daily OHLC candlestick and volume chart for ${symbol}`}>
      <line x1="24" x2={chartWidth - 24} y1="130" y2="130" className="mfb-history-axis"/>
      <line x1="24" x2={chartWidth - 24} y1="18" y2="18" className="mfb-history-grid"/>
      {geometry.map((candle, index) => <g key={String(candle.timestamp) + index} className={`mfb-candle ${candle.direction}`}>
        <line x1={candle.x} x2={candle.x} y1={candle.highY} y2={candle.lowY} className="mfb-candle-wick"/>
        <rect x={candle.x - candle.bodyWidth / 2} y={candle.bodyTop} width={candle.bodyWidth} height={candle.bodyHeight} rx=".5" className="mfb-candle-body"/>
        {candle.volumeHeight > 0 && <rect x={candle.x - 2} y={candle.volumeY} width="4" height={candle.volumeHeight} className="mfb-candle-volume"/>}
        <title>{(Number.isFinite(Number(candle.timestamp)) ? new Date(Number(candle.timestamp) * (Number(candle.timestamp) < 100000000000 ? 1000 : 1)) : new Date(candle.timestamp)).toLocaleDateString("en-IN")} · O {fmt(candle.open)} H {fmt(candle.high)} L {fmt(candle.low)} C {fmt(candle.close)} · {candle.volume === null ? "Volume unavailable" : "Volume " + fmt(candle.volume, 0)}</title>
      </g>)}
      <text x="24" y="12" className="mfb-history-label">₹{fmt(Math.max(...series.map(row => row.high ?? row.close)))}</text>
      <text x={chartWidth - 24} y="12" textAnchor="end" className="mfb-history-label">₹{fmt(Math.min(...series.map(row => row.low ?? row.close)))}</text>
      <text x="24" y="195" className="mfb-history-label">VOLUME</text>
    </svg>
    </div>
    <div className="mfb-history-foot"><span>{geometry.length} actual daily candles</span><span>OHLC and volume from existing Market Charts REST API · no intraday data</span></div>
  </section>;
}

export default function MarketFlowBoard({ onSelectInstrument }) {
  const [payload, setPayload] = useState(null);
  const [retrievedAt, setRetrievedAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [selectedKey, setSelectedKey] = useState("");
  const [hoveredKey, setHoveredKey] = useState(null);
  const focusedKey = hoveredKey || selectedKey;
  const onHoverInstrument = useCallback(key => setHoveredKey(key), []);
  const [selectedSectorKey, setSelectedSectorKey] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [exchangeFilter, setExchangeFilter] = useState("ALL");
  const [directionFilter, setDirectionFilter] = useState("all");
  const [sortKey, setSortKey] = useState("changePercent");
  const [sortDirection, setSortDirection] = useState("desc");
  const [sectorPayload, setSectorPayload] = useState(null);
  const [sectorLoading, setSectorLoading] = useState(false);
  const [sectorError, setSectorError] = useState("");
  const [historySeries, setHistorySeries] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyRange, setHistoryRange] = useState("3M");
  const historyRequest = useRef(0);
  const sectorRequest = useRef(0);
  const sectorBusy = useRef(false);
  const busy = useRef(false);
  const mounted = useRef(true);
  const hasPayload = useRef(false);

  const refresh = useCallback(async (manual = false) => {
    if (busy.current || document.visibilityState !== "visible") return;
    busy.current = true;
    if (manual) setRefreshing(true);
    else if (!hasPayload.current) setLoading(true);
    try {
      const next = await loadMarketFlowSnapshot(null, true);
      if (!mounted.current) return;
      setPayload(next);
      hasPayload.current = true;
      setRetrievedAt(next?.last_updated || new Date().toISOString());
      setError("");
    } catch (requestError) {
      if (mounted.current) setError(requestError?.message || "Market data request failed.");
    } finally {
      busy.current = false;
      if (mounted.current) { setLoading(false); setRefreshing(false); }
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    refresh();
    const poll = () => { if (document.visibilityState === "visible") refresh(); };
    const timer = window.setInterval(poll, 30000);
    document.addEventListener("visibilitychange", poll);
    return () => { mounted.current = false; window.clearInterval(timer); document.removeEventListener("visibilitychange", poll); };
  }, [refresh]);

  const rows = useMemo(() => normalizeOrderFlow(payload), [payload]);
  const filteredRows = useMemo(() => sortOrderFlow(
    filterOrderFlow(rows, { query: searchQuery, exchange: exchangeFilter, direction: directionFilter }),
    sortKey,
    sortDirection,
  ), [rows, searchQuery, exchangeFilter, directionFilter, sortKey, sortDirection]);
  const board = useMemo(() => buildMarketFlowBoard(filteredRows, 12, sortKey, sortDirection), [filteredRows, sortKey, sortDirection]);
  const indices = Array.isArray(payload?.indices) ? payload.indices : [];
  const sectorOptions = Array.isArray(payload?.sector_universes) ? payload.sector_universes : [];
  const sectorIndices = Array.isArray(payload?.sector_indices) ? payload.sector_indices : [];
  const sectorIndexPerformanceCount = sectorIndices.filter(item =>
    item?.percent_change !== null && item?.percent_change !== undefined &&
    Number.isFinite(Number(item.percent_change))
  ).length;
  const providerErrors = Array.isArray(payload?.errors) ? payload.errors : [];
  const sectorIndexErrors = providerErrors.filter(item => item?.source === "m.Stock sector index quote");
  const coreProviderErrors = providerErrors.filter(item => item?.source !== "m.Stock sector index quote");
  const sectorOnlyPartial = providerErrors.length > 0 && coreProviderErrors.length === 0;
  const sectorFlowRows = useMemo(() => buildSectorFlowRows(sectorOptions, sectorIndices), [sectorOptions, sectorIndices]);
  const sectorRows = useMemo(() => normalizeSectorMovers(sectorPayload), [sectorPayload]);
  const sectorSampleSummary = useMemo(() => summarizeSectorMoverSample(sectorRows), [sectorRows]);
  const sectorBoard = useMemo(() => buildMarketFlowBoard(sectorRows, 8), [sectorRows]);
  const selected = rows.find(row => keyOf(row) === selectedKey)
    || sectorRows.find(row => keyOf(row) === selectedKey) || null;
  const selectedSectorMover = selected && sectorRows.find(row => keyOf(row) === keyOf(selected));
  const relativeToSectorSample = selectedSectorMover && sectorSampleSummary.medianChangePct !== null
    ? selectedSectorMover.changePercent - sectorSampleSummary.medianChangePct : null;

  useEffect(() => {
    if (!selected) { setHistorySeries([]); return undefined; }
    const requestId = ++historyRequest.current;
    setHistoryLoading(true);
    setHistoryError("");
    setHistorySeries([]);
    const to = new Date();
    const from = new Date(to);
    const rangeDays = { "1M": 30, "3M": 90, "6M": 180, "1Y": 365, "5Y": 1825 };
    from.setDate(from.getDate() - rangeDays[historyRange]);
    const formatDate = date => [date.getFullYear(), String(date.getMonth() + 1).padStart(2, "0"), String(date.getDate()).padStart(2, "0")].join("-");
    loadChartHistory({ symbol: selected.symbol, exchange: selected.exchange, interval: "day", from: formatDate(from), to: formatDate(to) })
      .then(result => {
        if (mounted.current && requestId === historyRequest.current) {
          setHistorySeries(buildHistoricalFlowSeries(result?.data));
        }
      })
      .catch(requestError => {
        if (mounted.current && requestId === historyRequest.current) setHistoryError(requestError?.message || "Historical chart request failed.");
      })
      .finally(() => {
        if (mounted.current && requestId === historyRequest.current) setHistoryLoading(false);
      });
    return () => { historyRequest.current += 1; };
  }, [selected?.symbol, selected?.exchange, historyRange]);

  const loadSector = useCallback(async (sectorKey) => {
    if (sectorBusy.current) return;
    sectorBusy.current = true;
    const requestId = ++sectorRequest.current;
    setSelectedKey("");
    setHoveredKey(null);
    setSelectedSectorKey(sectorKey);
    setSectorPayload(null);
    setSectorLoading(true);
    setSectorError("");
    try {
      const next = await loadMarketFlowSnapshot(sectorKey);
      if (mounted.current && requestId === sectorRequest.current) setSectorPayload(next);
    } catch (requestError) {
      if (mounted.current && requestId === sectorRequest.current) {
        setSectorError(requestError?.message || "Sector market data request failed.");
      }
    } finally {
      sectorBusy.current = false;
      if (mounted.current && requestId === sectorRequest.current) setSectorLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedSectorKey) return undefined;
    const poll = () => {
      if (document.visibilityState === "visible" && !sectorBusy.current) loadSector(selectedSectorKey);
    };
    const timer = window.setInterval(poll, 60000);
    document.addEventListener("visibilitychange", poll);
    return () => { window.clearInterval(timer); document.removeEventListener("visibilitychange", poll); };
  }, [selectedSectorKey, loadSector]);

  return <main className="market-flow-board">
    <header className="mfb-header"><div><small>FINANCIAL OS / MARKETS / CHART FLOW</small><h1>Chart Flow</h1>
      <p>Whole-market discovery from real provider-returned cash-equity movers and supported indices.</p></div>
      <div><span className={error ? "mfb-status error" : loading ? "mfb-status" : "mfb-status live"}>{error ? "SOURCE ERROR" : loading ? "CONNECTING" : sectorOnlyPartial ? "SECTOR DATA PARTIAL" : payload?.status === "partial" ? "PARTIAL DATA" : "REST SNAPSHOT"}</span>
        <button type="button" onClick={() => refresh(true)} disabled={loading || refreshing}>{refreshing ? "Refreshing…" : "Refresh"}</button></div>
    </header>
    <section className="mfb-index-rail">{indices.map(index => <div key={index.exchange + ":" + index.name}>
      <small>{index.name}</small><strong>{fmt(index.last_price)}</strong><span>{index.exchange}</span></div>)}
      {!indices.length && <p>No index snapshots returned by the provider.</p>}</section>
    {error && <p className="mfb-alert" role="alert">{error}. Last successful data is retained; no demo feed is substituted.</p>}{coreProviderErrors.length > 0 && <p className="mfb-alert" role="status">Some market or benchmark requests failed. Available provider responses are retained; missing instruments are not estimated.</p>}
    {!loading && !rows.length && !error && <p className="mfb-alert">No valid provider movers were returned. No simulated instruments are displayed.</p>}
    <Distribution rows={rows} counts={buildMarketFlowBoard(rows).counts} breadthAvailable={payload?.capabilities?.full_advance_decline_breadth === true} retrievedAt={retrievedAt ? new Date(retrievedAt).toLocaleTimeString("en-IN") : null}/>
    <VolumeParticipation rows={rows}/>
    <section className="mfb-filterbar" aria-label="Filter market movers">
      <label>Search instruments<input type="search" value={searchQuery} onChange={event => setSearchQuery(event.target.value)} placeholder="Symbol or company"/></label>
      <label>Exchange<select value={exchangeFilter} onChange={event => setExchangeFilter(event.target.value)}><option value="ALL">All exchanges</option><option value="NSE">NSE</option><option value="BSE">BSE</option></select></label>
      <label>Direction<select value={directionFilter} onChange={event => setDirectionFilter(event.target.value)}><option value="all">All directions</option><option value="bullish">Bullish</option><option value="bearish">Bearish</option><option value="unchanged">Unchanged</option></select></label>
      <label>Sort by<select value={sortKey} onChange={event => setSortKey(event.target.value)}><option value="changePercent">Price change</option><option value="volume">Volume</option><option value="price">Last price</option><option value="symbol">Symbol</option></select></label>
      <button type="button" onClick={() => setSortDirection(value => value === "desc" ? "asc" : "desc")} aria-label="Toggle sort direction">{sortDirection === "desc" ? "Highest first ↓" : "Lowest first ↑"}</button>
      <span>{filteredRows.length} of {rows.length} returned movers</span>
    </section>
    <section className="mfb-section mfb-flow">
      <div className="mfb-section-head"><div><small>02 / MARKET FLOW</small><h2>Zero-centred market flow</h2>
        <p>Actual price changes fan through the central gate into bullish and bearish instruments. This is a current snapshot, not a reconstructed intraday history.</p></div>
        <span className="mfb-poll">REST refresh · 30 seconds while visible</span></div>
      <div className="mfb-board">
        <div className="mfb-visual"><FlowDiagram board={board} selectedKey={selectedKey} focusedKey={focusedKey} onSelect={row => setSelectedKey(keyOf(row))} onHover={onHoverInstrument}/>
          <section className="mfb-sectors"><div><small>03 / SECTOR FLOW</small><b>Explore sector constituents</b>
              <span className="mfb-sector-coverage" role="status">{sectorIndexPerformanceCount} of {sectorOptions.length} sector index performance values available from REST</span></div>
            <p>Sector index change is calculated from provider LTP and OHLC previous close where both are available. Select a sector to open its actual ranked stock movers.</p>
            {sectorIndexErrors.length > 0 && <p className="mfb-alert" role="status">{sectorIndexPerformanceCount} of {sectorOptions.length} sector index performance values are available. Unavailable: {sectorIndexErrors.map(item => item.name || item.sector).filter(Boolean).join(", ") || sectorIndexErrors.length + " sector index quote(s)"}. Main market movers remain separate from this sector-index coverage.</p>}
            <SectorFlowDiagram sectors={sectorFlowRows} selectedKey={selectedSectorKey}
              loading={sectorLoading} onSelect={loadSector}/>
            {!sectorIndices.length && <p className="mfb-sector-disclaimer">Sector index quotes are not available from the current provider response. Sector stock movers remain available on selection.</p>}
            {sectorLoading && <p role="status">Loading actual {sectorOptions.find(item => item.key === selectedSectorKey)?.name || "sector"} movers…</p>}
            {sectorError && <p className="mfb-alert" role="alert">{sectorError}</p>}
            {sectorPayload && <>
              <div className="mfb-sector-result-head"><strong>{sectorPayload.sector?.name}</strong>
                <span>{sectorPayload.counts?.total_returned || 0} provider-ranked movers</span>
                <span>{sectorPayload.status === "partial" ? "Partial response" : "REST data"}</span>
                <span>Sample median {sectorSampleSummary.medianChangePct === null ? "—" : pct(sectorSampleSummary.medianChangePct)}</span></div>
              {sectorPayload.sector_index && <div className="mfb-sector-index-quote"><small>{sectorPayload.sector_index.name} · INDEX LEVEL</small><strong>{fmt(sectorPayload.sector_index.last_price)}</strong>
                {sectorPayload.sector_index.percent_change !== null && sectorPayload.sector_index.percent_change !== undefined && Number.isFinite(Number(sectorPayload.sector_index.percent_change)) && <b className={Number(sectorPayload.sector_index.percent_change) >= 0 ? "up" : "down"}>{pct(Number(sectorPayload.sector_index.percent_change))}</b>}
                <span>{sectorPayload.sector_index.previous_close ? "Previous close " + fmt(sectorPayload.sector_index.previous_close) : "Daily change unavailable from provider OHLC."}</span></div>}
              <Distribution eyebrow="SECTOR / PROVIDER-RANKED MOVERS" title={sectorPayload.sector?.name + " price distribution"} description="Actual sector-filtered gainers and losers returned by m.Stock. This is not the full sector constituent universe." rows={sectorRows} counts={buildMarketFlowBoard(sectorRows).counts} breadthAvailable={false} retrievedAt={sectorPayload.last_updated ? new Date(sectorPayload.last_updated).toLocaleTimeString("en-IN") : null}/><VolumeParticipation rows={sectorRows} label="SECTOR SAMPLE"/>
              <SectorConstituentDiagram sectorName={sectorPayload.sector?.name || "Selected sector"}
                board={sectorBoard} selectedKey={selectedKey} focusedKey={focusedKey}
                onSelect={row => setSelectedKey(keyOf(row))} onHover={onHoverInstrument}/>
              {sectorPayload.errors?.length > 0 && <p className="mfb-alert">One sector mover source did not respond. Available real results are retained.</p>}
              <p className="mfb-sector-disclaimer">Median and directional counts describe only the {sectorSampleSummary.count} returned top movers. They are not full-sector performance or constituent breadth.</p>
            </>}
            {!sectorOptions.length && <p>Sector universes were not returned by the backend.</p>}
          </section>
        </div>
        <div className="mfb-sides"><Side title="Bullish" side="up" rows={board.bullish} selectedKey={selectedKey} focusedKey={focusedKey} onSelect={row => setSelectedKey(keyOf(row))} onHover={onHoverInstrument}/>
          <Side title="Bearish" side="down" rows={board.bearish} selectedKey={selectedKey} focusedKey={focusedKey} onSelect={row => setSelectedKey(keyOf(row))} onHover={onHoverInstrument}/></div>
      </div>
    </section>
    <section className="mfb-detail"><div><small>04 / INSTRUMENT DETAIL</small><h2>{selected ? selected.name : "Select an instrument"}</h2>
      {selected && <span>{selected.symbol} · {selected.exchange}</span>}</div>
      {selected ? <div className="mfb-detail-values"><div><small>LAST PRICE</small><strong>₹{fmt(selected.price)}</strong></div>
        <div><small>PRICE CHANGE</small><strong className={selected.direction}>{pct(selected.changePercent)}</strong></div>
        <div><small>VOLUME</small><strong>{selected.volume === null ? "Not supplied" : fmt(selected.volume, 0)}</strong></div>
        {relativeToSectorSample !== null && <div><small>VS RETURNED SECTOR SAMPLE</small><strong className={relativeToSectorSample >= 0 ? "up" : "down"}>{pct(relativeToSectorSample)}</strong></div>}
        <button type="button" onClick={() => onSelectInstrument?.(selected)}>Open full chart</button></div>
        : <p>Select a flow path or tile. Only provider-returned fields are shown.</p>}
    </section>
    {selected && <HistoricalFlowPanel series={historySeries} loading={historyLoading} error={historyError} symbol={selected.symbol} range={historyRange} onRangeChange={setHistoryRange}/>}
    <footer className="mfb-footer"><span>Source: {payload?.data_sources?.primary || "m.Stock via Financial OS Gateway"}</span>
      <span>Snapshot assembled: {retrievedAt ? new Date(retrievedAt).toLocaleString("en-IN") : "—"}</span>
      <span>Read-only · REST only · no synthetic market values</span></footer>
  </main>;
}
