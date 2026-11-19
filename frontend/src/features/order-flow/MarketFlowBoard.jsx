import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { loadChartHistory, loadMarketFlowSnapshot } from "../advanced-chart/api.js";
import { buildDistributionDots, buildMarketFlowBoard, filterOrderFlow, normalizeOrderFlow, normalizeSectorMovers, sortOrderFlow, buildHistoricalFlowSeries, summarizeSectorMoverSample, rankSectorIndices } from "./orderFlowModel.js";
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
        return <g key={keyOf(row)} role="button" tabIndex="0" className={"mfb-path " + side + (selected ? " selected" : "")}
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
      {flat.map((row, i) => <g key={keyOf(row)} role="button" tabIndex="0" className={"mfb-flat-point" + (keyOf(row) === selectedKey ? " selected" : "")}
        onClick={() => onSelect(row)} onKeyDown={event => { if (event.key === "Enter") onSelect(row); }}>
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


function HistoricalFlowPanel({ series, loading, error, symbol }) {
  if (loading) return <section className="mfb-history"><small>05 / HISTORICAL PRICE FLOW</small><p>Loading verified historical candles…</p></section>;
  if (error) return <section className="mfb-history"><small>05 / HISTORICAL PRICE FLOW</small><p className="mfb-alert">{error}</p></section>;
  if (!series.length) return <section className="mfb-history"><small>05 / HISTORICAL PRICE FLOW</small><p>No historical OHLCV observations returned for {symbol}. No chart is fabricated.</p></section>;

  const values = series.map(row => row.relativeChange);
  const min = Math.min(0, ...values);
  const max = Math.max(0, ...values);
  const range = Math.max(0.01, max - min);
  const points = series.map((row, index) => {
    const x = 24 + (series.length === 1 ? 0 : index / (series.length - 1) * 672);
    const y = 112 - ((row.relativeChange - min) / range) * 88;
    return `${x},${y}`;
  }).join(" ");
  const latest = series[series.length - 1];
  const volumes = series.map(row => row.volume).filter(value => value !== null);
  const maxVolume = Math.max(1, ...volumes);
  return <section className="mfb-history">
    <div className="mfb-history-head"><div><small>05 / HISTORICAL PRICE FLOW</small><b>{symbol} · daily candles</b></div>
      <strong className={latest.relativeChange >= 0 ? "up" : "down"}>{pct(latest.relativeChange)} since first candle</strong></div>
    <div className="mfb-history-ohlc"><span>O ₹{latest.open === null ? "—" : fmt(latest.open)}</span><span>H ₹{latest.high === null ? "—" : fmt(latest.high)}</span><span>L ₹{latest.low === null ? "—" : fmt(latest.low)}</span><span>C ₹{fmt(latest.close)}</span></div>
    <svg viewBox="0 0 720 172" role="img" aria-label={`Historical relative price movement and actual volume for ${symbol}`}>
      <line x1="24" x2="696" y1="112" y2="112" className="mfb-history-axis"/>
      <polyline points={points} className="mfb-history-line" fill="none"/>
      {series.map((row, index) => {
        const x = 24 + (series.length === 1 ? 0 : index / (series.length - 1) * 672);
        const height = row.volume === null ? 0 : row.volume / maxVolume * 30;
        return <g key={String(row.timestamp) + index}>
          <rect x={x - 2} y={158 - height} width="4" height={height} className="mfb-history-volume"/>
          <title>{(Number.isFinite(Number(row.timestamp)) ? new Date(Number(row.timestamp) * (Number(row.timestamp) < 100000000000 ? 1000 : 1)) : new Date(row.timestamp)).toLocaleDateString("en-IN")} · ₹{fmt(row.close)} · {row.volume === null ? "Volume unavailable" : "Volume " + fmt(row.volume, 0)}</title>
        </g>;
      })}
      <text x="24" y="12" className="mfb-history-label">{pct(min)}</text>
      <text x="696" y="12" textAnchor="end" className="mfb-history-label">{pct(max)}</text>
      <text x="24" y="170" className="mfb-history-label">VOLUME</text>
    </svg>
    <div className="mfb-history-foot"><span>{series.length} actual candles</span><span>Close-based relative change · volume shown only when supplied</span></div>
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
  const sectorIndexByKey = useMemo(() => new Map(sectorIndices.map(item => [item.key, item])), [sectorIndices]);
  const rankedSectorOptions = useMemo(() => rankSectorIndices(sectorOptions, sectorIndices), [sectorOptions, sectorIndices]);
  const sectorIndexMaxAbs = Math.max(0.1, ...sectorIndices.map(item => Math.abs(Number(item.percent_change) || 0)));
  const sectorRows = useMemo(() => normalizeSectorMovers(sectorPayload), [sectorPayload]);
  const sectorSampleSummary = useMemo(() => summarizeSectorMoverSample(sectorRows), [sectorRows]);
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
    from.setDate(from.getDate() - 45);
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
  }, [selected?.symbol, selected?.exchange]);

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
    <header className="mfb-header"><div><small>FINANCIAL OS / MARKETS / ORDER FLOW</small><h1>Chart Flow</h1>
      <p>Whole-market discovery from real provider-returned cash-equity movers and supported indices.</p></div>
      <div><span className={error ? "mfb-status error" : loading ? "mfb-status" : "mfb-status live"}>{error ? "SOURCE ERROR" : loading ? "CONNECTING" : payload?.status === "partial" ? "PARTIAL DATA" : "REST SNAPSHOT"}</span>
        <button type="button" onClick={() => refresh(true)} disabled={loading || refreshing}>{refreshing ? "Refreshing…" : "Refresh"}</button></div>
    </header>
    <section className="mfb-index-rail">{indices.map(index => <div key={index.exchange + ":" + index.name}>
      <small>{index.name}</small><strong>{fmt(index.last_price)}</strong><span>{index.exchange}</span></div>)}
      {!indices.length && <p>No index snapshots returned by the provider.</p>}</section>
    {error && <p className="mfb-alert" role="alert">{error}. Last successful data is retained; no demo feed is substituted.</p>}{payload?.status === "partial" && <p className="mfb-alert" role="status">Some provider requests failed. The board contains only the successful real responses; missing instruments are not filled with estimates.</p>}
    {!loading && !rows.length && !error && <p className="mfb-alert">No valid provider movers were returned. No simulated instruments are displayed.</p>}
    <Distribution rows={rows} counts={buildMarketFlowBoard(rows).counts} breadthAvailable={payload?.capabilities?.full_advance_decline_breadth === true} retrievedAt={retrievedAt ? new Date(retrievedAt).toLocaleTimeString("en-IN") : null}/>
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
          <section className="mfb-sectors"><div><small>03 / SECTOR FLOW</small><b>Explore sector constituents</b></div>
            <p>Sector index performance uses provider OHLC previous-close data where available. Select a sector to open its actual ranked stock movers.</p>
            <div className="mfb-sector-selector" role="group" aria-label="Compare and select sectors">
              {rankedSectorOptions.map(sector => {
                const quote = sectorIndexByKey.get(sector.key);
                const change = quote?.percent_change !== null && quote?.percent_change !== undefined && Number.isFinite(Number(quote.percent_change)) ? Number(quote.percent_change) : null;
                const barWidth = change === null ? 0 : Math.min(50, Math.abs(change) / sectorIndexMaxAbs * 50);
                return <button key={sector.key} type="button"
                  className={selectedSectorKey === sector.key ? "selected" : ""}
                  aria-pressed={selectedSectorKey === sector.key}
                  onClick={() => loadSector(sector.key)} disabled={sectorLoading}>
                  <span>{sector.name}</span>
                  <strong className={change === null ? "flat" : change >= 0 ? "up" : "down"}>{change === null ? "—" : pct(change)}</strong>
                  <small>{quote?.last_price ? "Index " + fmt(quote.last_price) : "Index quote unavailable"}</small>
                  <i className="mfb-sector-track"><b className={change === null ? "flat" : change >= 0 ? "up" : "down"} style={{ width: barWidth + "%" }}/></i>
                </button>;
              })}
            </div>
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
              <Distribution eyebrow="SECTOR / PROVIDER-RANKED MOVERS" title={sectorPayload.sector?.name + " price distribution"} description="Actual sector-filtered gainers and losers returned by m.Stock. This is not the full sector constituent universe." rows={sectorRows} counts={buildMarketFlowBoard(sectorRows).counts} breadthAvailable={false} retrievedAt={sectorPayload.last_updated ? new Date(sectorPayload.last_updated).toLocaleTimeString("en-IN") : null}/>
              <div className="mfb-sector-movers">
                <Side title="Sector gainers" side="up" rows={sectorRows.filter(row => row.direction === "bullish")}
                  selectedKey={selectedKey} focusedKey={focusedKey} onSelect={row => setSelectedKey(keyOf(row))} onHover={onHoverInstrument}/>
                <Side title="Sector losers" side="down" rows={sectorRows.filter(row => row.direction === "bearish")}
                  selectedKey={selectedKey} focusedKey={focusedKey} onSelect={row => setSelectedKey(keyOf(row))} onHover={onHoverInstrument}/>
              </div>
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
    {selected && <HistoricalFlowPanel series={historySeries} loading={historyLoading} error={historyError} symbol={selected.symbol}/>}
    <footer className="mfb-footer"><span>Source: {payload?.data_sources?.primary || "m.Stock via Financial OS Gateway"}</span>
      <span>Snapshot assembled: {retrievedAt ? new Date(retrievedAt).toLocaleString("en-IN") : "—"}</span>
      <span>Read-only · REST only · no synthetic market values</span></footer>
  </main>;
}
