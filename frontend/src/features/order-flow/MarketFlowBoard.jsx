import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { loadChartHistory, loadMarketFlowSnapshot } from "../advanced-chart/api.js";
import { buildDistributionDots, buildMarketFlowBoard, filterOrderFlow, normalizeOrderFlow, normalizeSectorMovers, sortOrderFlow, buildHistoricalFlowSeries, summarizeSectorMoverSample, buildSectorFlowRows, summarizeMoverVolume, buildHistoricalCandleGeometry } from "./orderFlowModel.js";
import "./market-flow-board.css";

const fmt = (value, digits = 2) => Number.isFinite(Number(value))
  ? new Intl.NumberFormat("en-IN", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(Number(value))
  : "—";
const pct = value => (value > 0 ? "+" : "") + fmt(value) + "%";
const rejectionSummary = rejected => {
  const entries = Object.entries(rejected || {}).filter(([, count]) => Number(count) > 0);
  const total = entries.reduce((sum, [, count]) => sum + Number(count), 0);
  return total ? total + " provider rows rejected as invalid (" + entries.map(([reason, count]) => reason.replace(/_/g, " ") + " ×" + count).join(", ") + ")" : "";
};
const keyOf = row => row.exchange + ":" + row.symbol;

function Distribution({ rows, counts, retrievedAt, breadthAvailable, eyebrow = "01 / MARKET DISTRIBUTION", title = "Where the market is moving", description = "Every dot is an actual NSE/BSE mover returned by m.Stock. Counts describe this returned set, not full-exchange breadth." }) {
  const dots = useMemo(() => buildDistributionDots(rows), [rows]);
  return <section className="mfb-section mfb-distribution">
    <div className="mfb-section-head">
      <div><small>{eyebrow}</small><h2>{title}</h2>
        <p>{description}</p></div>
      <div className="mfb-counts"><b className="up">{counts.bullish} bullish</b><b className="down">{counts.bearish} bearish</b><b className="flat">{breadthAvailable ? counts.unchanged : "—"} flat</b></div>
    </div>
    {counts.total > 0 && <div className="mfb-breadth" role="img" aria-label={counts.bullish + " bullish and " + counts.bearish + " bearish of " + counts.total + " returned movers"}>
      <i className="up" style={{ width: counts.bullish / counts.total * 100 + "%" }}/><i className="down" style={{ width: counts.bearish / counts.total * 100 + "%" }}/>
    </div>}
    <svg viewBox="0 0 1000 84" role="img" aria-label="Provider-returned percentage changes distributed around zero">
      <line x1="40" x2="960" y1="42" y2="42" className="mfb-axis"/>
      <line x1="500" x2="500" y1="8" y2="70" className="mfb-zero"/>
      <text x="40" y="81">LOSERS</text><text x="500" y="81" textAnchor="middle">0%</text><text x="960" y="81" textAnchor="end">GAINERS</text>
      {dots.map((dot, i) => <g key={keyOf(dot) + i}><circle cx={dot.x} cy={dot.y} r="3.2" className={dot.changePercent > 0 ? "mfb-dot up" : dot.changePercent < 0 ? "mfb-dot down" : "mfb-dot flat"}/><title>{dot.symbol + " · " + pct(dot.changePercent)}</title></g>)}
    </svg>
    <div className="mfb-foot"><span>{rows.length} provider-returned instruments</span><span>Snapshot assembled: {retrievedAt || "not received"}</span></div>
  </section>;
}

function DataQuality({ title, notes }) {
  const items = (notes || []).filter(Boolean);
  if (!items.length) return null;
  return <details className="mfb-quality">
    <summary><span className="mfb-quality-dot" aria-hidden="true"/>{title}<em>{items.length} {items.length === 1 ? "note" : "notes"} · tap to view</em></summary>
    <ul>{items.map((note, index) => <li key={index}>{note}</li>)}</ul>
  </details>;
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



function VolumeParticipation({ rows, label = "MARKET" }) {
  const summary = useMemo(() => summarizeMoverVolume(rows), [rows]);
  const max = Math.max(1, summary.bullishVolume, summary.bearishVolume, summary.unchangedVolume);
  const items = [
    { key: "bullish", label: "Bullish", volume: summary.bullishVolume, count: summary.bullishCount },
    { key: "bearish", label: "Bearish", volume: summary.bearishVolume, count: summary.bearishCount },
    { key: "flat", label: "Unchanged", volume: summary.unchangedVolume, count: summary.unchangedCount },
  ];
  if (summary.positiveVolumeReported === 0) {
    return <p className="mfb-volume-warning" role="status">Volume is not reported by the provider for this {label.toLowerCase()} snapshot, so volume participation is hidden.</p>;
  }
  return <section className="mfb-volume">
    <div className="mfb-volume-head"><div><small>VOLUME PARTICIPATION / {label}</small><b>Reported volume by direction</b></div>
      <span>{summary.positiveVolumeReported} with positive volume · {summary.zeroVolumeReported} reported zero</span></div>
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


const compact = value => Number.isFinite(Number(value))
  ? new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 }).format(Number(value)) : "—";
const clip = (text, max) => { const value = String(text || ""); return value.length > max ? value.slice(0, max - 1) + "…" : value; };
const press = action => ({
  role: "button", tabIndex: 0, onClick: action,
  onKeyDown: event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); action(); } },
});

function Stream({ d, width = 6, tone = "flat" }) {
  return <g className={"ms-stream " + tone}>
    <path className="ms-glow" d={d} strokeWidth={width} filter="url(#mfb-bl)"/>
    <path className="ms-wide" d={d} strokeWidth={width}/>
    <path className="ms-core" d={d}/>
  </g>;
}

/** One connected stream: market -> direction -> sectors -> sector stocks -> selected stock.
 *  Presentation only: every figure comes from props already derived from the REST snapshot. */
function StreamFlow({ rows, board, sectorFlowRows, selectedSectorKey, sectorLoading, sectorError, sectorPayload, sectorBoard,
  sectorSampleSummary, selected, selectedKey, relativeToSectorSample, historySeries, historyLoading, historyError,
  historyRange, onRangeChange, onSelectSector, onSelectStock, onOpenChart, retrievedAt }) {
  const [showAllSectors, setShowAllSectors] = useState(false);
  const volume = useMemo(() => summarizeMoverVolume(rows), [rows]);
  const sectors = Array.isArray(sectorFlowRows) ? sectorFlowRows : [];
  const rowY = index => 36 + index * 34;
  const maxAbs = Math.max(0.1, ...sectors.map(item => Math.abs(item.percentChange ?? 0)));
  const ups = sectors.map((item, index) => ({ item, index })).filter(entry => entry.item.direction === "bullish");
  const downs = sectors.map((item, index) => ({ item, index })).filter(entry => entry.item.direction === "bearish");
  const middle = list => list.length ? list.reduce((sum, entry) => sum + rowY(entry.index) + 14, 0) / list.length : null;
  const bullY = middle(ups) ?? 150, bearY = middle(downs) ?? 460, originY = (bullY + bearY) / 2;
  const GAIN_TOP = 190, LOSS_TOP = 510, CARD_STEP = 56; // card tops; captions sit 14px above, clear of the cards
  const height = Math.max(760, sectors.length * 34 + 70);
  const totalVolume = volume.bullishVolume + volume.bearishVolume;
  const bullWidth = totalVolume > 0 ? 8 + volume.bullishVolume / totalVolume * 36 : 20;
  const bearWidth = totalVolume > 0 ? 8 + volume.bearishVolume / totalVolume * 36 : 20;
  const selectedIndex = sectors.findIndex(item => item.key === selectedSectorKey);
  const sectorY = selectedIndex >= 0 ? rowY(selectedIndex) + 14 : null;
  const gainers = sectorPayload ? sectorBoard.visibleBullish.slice(0, 5) : [];
  const losers = sectorPayload ? sectorBoard.visibleBearish.slice(0, 4) : [];
  const indexQuote = sectorPayload?.sector_index;
  const indexChange = indexQuote && indexQuote.percent_change !== null && indexQuote.percent_change !== undefined
    && Number.isFinite(Number(indexQuote.percent_change)) ? Number(indexQuote.percent_change) : null;
  const rejectedSector = rejectionSummary(sectorPayload?.data_quality?.rejected_rows);
  const received = sectorPayload?.data_quality?.provider_rows_received;
  const sampleText = (sectorPayload?.data_quality?.rejected_samples || []).slice(0, 3)
    .map(row => row.symbol + " ltp " + row.ltp + " chg " + (row.change ?? "—") + " pct " + (row.percent_change ?? "—")).join(" · ");
  const noMoversText = rejectedSector ? "No usable movers: " + rejectedSector + (sampleText ? ". Examples: " + sampleText : "") + "."
    : received === 0 ? "m.Stock returned no gainers or losers for this sector right now."
      : "No ranked movers returned for this sector.";
  const volumeText = reported => reported > 0 ? "Vol " + compact(reported) : "Vol —";
  const bullShare = totalVolume > 0 ? volume.bullishVolume / totalVolume * 100 : null;
  const bearShare = totalVolume > 0 ? volume.bearishVolume / totalVolume * 100 : null;
  const compactSectors = sectors.map((item, index) => ({ item, index })).filter(entry => showAllSectors || entry.index < 8 || entry.item.key === selectedSectorKey);
  const stockTile = (row, up) => {
    const isSel = keyOf(row) === selectedKey;
    return <button type="button" key={keyOf(row)} className={"mfb-sc-stock " + (up ? "up" : "down") + (isSel ? " sel" : "")} aria-pressed={isSel} onClick={() => onSelectStock(row)}>
      <b>{row.symbol}</b><strong>{pct(row.changePercent)}</strong>
      <small>₹{fmt(row.price)} · {row.volume === null ? "Vol —" : "Vol " + compact(row.volume)}</small></button>;
  };

  return <section className="mfb-section mfb-stream" aria-label="Connected market stream">
    <div className="mfb-section-head"><div><small>02 / CONNECTED MARKET STREAM</small><h2>Market → direction → sector → stock</h2>
      <p>One flow built only from the current REST snapshot. Stream thickness at the direction gates reflects provider-reported volume of the returned movers.</p></div>
      <span className="mfb-poll">REST refresh · 30 seconds while visible</span></div>
    <div className="mfb-stream-grid">
      <div className="mfb-stream-scroll">
        <div className="mfb-stream-wide">
        <svg className="mfb-stream-svg" viewBox={"0 0 940 " + height} role="group" aria-label="Connected market stream diagram">
          <defs><filter id="mfb-bl" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="7"/></filter></defs>
          {[[20, "1 · MARKET"], [150, "2 · DIRECTION"], [330, "3 · SECTORS (" + sectors.length + ")"], [690, "4 · SECTOR STOCKS"]].map(([x, label]) =>
            <text key={label} x={x} y="16" className="ms-m ms-cap">{label}</text>)}
          <Stream d={"M78 " + originY + " C112 " + originY + " 118 " + bullY + " 150 " + bullY} width={bullWidth} tone="up"/>
          <Stream d={"M78 " + originY + " C112 " + originY + " 118 " + bearY + " 150 " + bearY} width={bearWidth} tone="down"/>
          {sectors.map((item, index) => {
            if (item.direction !== "bullish" && item.direction !== "bearish") return null;
            const up = item.direction === "bullish", gate = up ? bullY : bearY, cy = rowY(index) + 14;
            return <Stream key={"s-" + item.key} d={"M280 " + gate + " C305 " + gate + " 305 " + cy + " 330 " + cy}
              width={2 + Math.abs(item.percentChange) / maxAbs * 8} tone={up ? "up" : "down"}/>;
          })}
          <circle cx="48" cy={originY} r="28" className="ms-origin"/>
          <text x="48" y={originY + 4} textAnchor="middle" className="ms-t ms-b">ZERO</text>
          <text x="20" y={originY + 50} className="ms-t ms-b">MARKET</text>
          <text x="20" y={originY + 67} className="ms-m ms-sm">{board.counts.total} movers</text>
          <text x="20" y={originY + 82} className="ms-m ms-sm">{retrievedAt || "—"}</text>
          {[["up", "BULLISH", bullY, board.counts.bullish, volume.bullishVolume], ["down", "BEARISH", bearY, board.counts.bearish, volume.bearishVolume]].map(([tone, label, y, count, vol]) =>
            <g key={label}><rect x="150" y={y - 40} width="130" height="80" rx="14" className={"ms-gate " + tone}/>
              <text x="164" y={y - 16} className={"ms-b ms-sm " + (tone === "up" ? "ms-g" : "ms-r")}>{label}</text>
              <text x="164" y={y + 5} className="ms-t ms-b">{count} movers</text>
              <text x="164" y={y + 24} className="ms-m ms-sm">{volumeText(vol)}</text></g>)}
          {sectors.map((item, index) => {
            const y0 = rowY(index), isSel = item.key === selectedSectorKey, up = item.direction === "bullish", down = item.direction === "bearish";
            const barWidth = item.percentChange === null ? 0 : Math.abs(item.percentChange) / maxAbs * 50;
            return <g key={item.key} className={"ms-hit" + (isSel ? " sel" : "")} {...press(() => onSelectSector(item.key))}
              aria-label={item.name + " " + (item.percentChange === null ? "change unavailable" : pct(item.percentChange))} aria-pressed={isSel}>
              <rect x="330" y={y0} width="290" height="28" rx="8" className={"ms-node" + (isSel ? " sel" : "")}/>
              <text x="342" y={y0 + 19} className="ms-m ms-sm">{index + 1}</text>
              <text x="358" y={y0 + 19} className="ms-t ms-b">{clip(item.name, 20)}</text>
              <line x1="560" x2="560" y1={y0 + 5} y2={y0 + 23} className="ms-axis"/>
              {barWidth > 0 && <rect x={up ? 560 : 560 - barWidth} y={y0 + 9} width={barWidth} height="10" rx="3" className={up ? "ms-bar-up" : "ms-bar-down"}/>}
              <text x="612" y={y0 + 19} textAnchor="end" className={"ms-b ms-sm " + (up ? "ms-g" : down ? "ms-r" : "ms-m")}>{item.percentChange === null ? "—" : pct(item.percentChange)}</text></g>;
          })}
          {!sectors.length && <text x="340" y="60" className="ms-m">Sector universes were not returned by the backend.</text>}
          {sectorY !== null && sectorPayload && <>
            <Stream d={"M620 " + sectorY + " C655 " + sectorY + " 655 82 690 82"} width={12} tone="sel"/>
            {gainers.map((row, index) => <Stream key={"g-" + keyOf(row)} d={"M620 " + sectorY + " C655 " + sectorY + " 655 " + (GAIN_TOP + 24 + index * CARD_STEP) + " 690 " + (GAIN_TOP + 24 + index * CARD_STEP)} width={5} tone="up"/>)}
            {losers.map((row, index) => <Stream key={"l-" + keyOf(row)} d={"M620 " + sectorY + " C655 " + sectorY + " 655 " + (LOSS_TOP + 24 + index * CARD_STEP) + " 690 " + (LOSS_TOP + 24 + index * CARD_STEP)} width={5} tone="down"/>)}</>}
          {sectorPayload ? <g>
            <rect x="690" y="30" width="200" height="104" rx="14" className="ms-node sel"/>
            <text x="704" y="52" className="ms-t ms-b">{clip(sectorPayload.sector?.name, 22)}</text>
            <text x="704" y="72" className="ms-m ms-sm">Index {indexQuote ? fmt(indexQuote.last_price) : "—"}</text>
            <text x="704" y="90" className={"ms-b ms-sm " + (indexChange === null ? "ms-m" : indexChange >= 0 ? "ms-g" : "ms-r")}>{indexChange === null ? "Daily change unavailable" : pct(indexChange)}</text>
            <text x="704" y="108" className="ms-m ms-sm">{sectorPayload.counts?.total_returned || 0} provider-ranked movers</text>
            <text x="704" y="124" className="ms-m ms-sm">Sample median {sectorSampleSummary.medianChangePct === null ? "—" : pct(sectorSampleSummary.medianChangePct)}</text></g>
            : <g><rect x="690" y="30" width="200" height="104" rx="14" className="ms-empty"/>
              <text x="704" y="76" className="ms-m ms-sm">{sectorLoading ? "Loading sector movers…" : "Select a sector to open its stocks"}</text></g>}
          {sectorPayload && <>
            {gainers.length > 0 && <text x="690" y={GAIN_TOP - 14} className="ms-g ms-b ms-cap">GAINERS</text>}{losers.length > 0 && <text x="690" y={LOSS_TOP - 14} className="ms-r ms-b ms-cap">LOSERS</text>}
            {[...gainers.map((row, index) => ({ row, y: GAIN_TOP + index * CARD_STEP })), ...losers.map((row, index) => ({ row, y: LOSS_TOP + index * CARD_STEP }))].map(({ row, y }) => {
              const isSel = keyOf(row) === selectedKey, up = row.changePercent > 0;
              return <g key={keyOf(row)} className={"ms-hit" + (isSel ? " sel" : "")} {...press(() => onSelectStock(row))} aria-label={row.symbol + " " + pct(row.changePercent)} aria-pressed={isSel}>
                <rect x="690" y={y} width="200" height="48" rx="10" className={"ms-node" + (isSel ? " sel" : "")}/>
                <text x="704" y={y + 20} className="ms-t ms-b">{clip(row.symbol, 14)}</text>
                <text x="878" y={y + 20} textAnchor="end" className={"ms-b " + (up ? "ms-g" : "ms-r")}>{pct(row.changePercent)}</text>
                <text x="704" y={y + 38} className="ms-m ms-sm">₹{fmt(row.price)} · {row.volume === null ? "Vol —" : "Vol " + compact(row.volume)}</text></g>;
            })}
            {!gainers.length && !losers.length && <text x="690" y={GAIN_TOP + 10} className="ms-m ms-sm">{noMoversText}</text>}</>}
          {selected && sectorPayload && [...gainers.map((row, index) => ({ row, y: GAIN_TOP + index * CARD_STEP })), ...losers.map((row, index) => ({ row, y: LOSS_TOP + index * CARD_STEP }))]
            .filter(({ row }) => keyOf(row) === selectedKey).map(({ row, y }) =>
              <Stream key={"sel-" + keyOf(row)} d={"M890 " + (y + 24) + " L936 " + (y + 24)} width={6} tone="sel"/>)}
        </svg>
        </div>
        <div className="mfb-stream-compact" role="group" aria-label="Connected market stream, compact view">
          <div className="mfb-sc-origin"><small>1 · MARKET</small><strong>{board.counts.total} movers</strong><span>{retrievedAt || "—"}</span></div>
          <i className="mfb-sc-link" aria-hidden="true"/>
          <div className="mfb-sc-gates">
            {[["up", "BULLISH", board.counts.bullish, volume.bullishVolume, bullShare], ["down", "BEARISH", board.counts.bearish, volume.bearishVolume, bearShare]].map(([tone, label, count, vol, share]) =>
              <div key={label} className={"mfb-sc-gate " + tone}><small>2 · {label}</small><strong>{count} movers</strong><span>{volumeText(vol)}</span>
                {share !== null && <em><i style={{ width: share + "%" }}/></em>}</div>)}
          </div>
          <i className="mfb-sc-link" aria-hidden="true"/>
          <div className="mfb-sc-sectors"><small>3 · SECTORS ({sectors.length})</small>
            {compactSectors.map(({ item, index }) => {
              const isSel = item.key === selectedSectorKey, up = item.direction === "bullish", down = item.direction === "bearish";
              const widthPct = item.percentChange === null ? 0 : Math.abs(item.percentChange) / maxAbs * 50;
              return <button type="button" key={item.key} className={"mfb-sc-sector-row" + (isSel ? " sel" : "")} aria-pressed={isSel} onClick={() => onSelectSector(item.key)}>
                <span className="rank">{index + 1}</span><span className="nm">{item.name}</span>
                <span className="bar" aria-hidden="true">{widthPct > 0 && <i className={up ? "up" : "down"} style={up ? { left: "50%", width: widthPct + "%" } : { right: "50%", width: widthPct + "%" }}/>}</span>
                <strong className={up ? "up" : down ? "down" : "flat"}>{item.percentChange === null ? "—" : pct(item.percentChange)}</strong></button>;
            })}
            {sectors.length > 8 && <button type="button" className="mfb-sc-more" onClick={() => setShowAllSectors(value => !value)}>{showAllSectors ? "Show fewer sectors" : "Show all " + sectors.length + " sectors"}</button>}
            {!sectors.length && <p>Sector universes were not returned by the backend.</p>}
          </div>
          <i className="mfb-sc-link" aria-hidden="true"/>
          <div className="mfb-sc-sector"><small>4 · SECTOR STOCKS</small>
            {sectorPayload ? <>
              <div className="mfb-sc-head"><strong>{sectorPayload.sector?.name}</strong>
                <span>Index {indexQuote ? fmt(indexQuote.last_price) : "—"}{indexChange !== null && <b className={indexChange >= 0 ? "up" : "down"}> {pct(indexChange)}</b>}</span>
                <span>{sectorPayload.counts?.total_returned || 0} provider-ranked movers · median {sectorSampleSummary.medianChangePct === null ? "—" : pct(sectorSampleSummary.medianChangePct)}</span></div>
              {gainers.length > 0 && <><h4 className="up">Gainers</h4><div className="mfb-sc-grid">{gainers.map(row => stockTile(row, true))}</div></>}
              {losers.length > 0 && <><h4 className="down">Losers</h4><div className="mfb-sc-grid">{losers.map(row => stockTile(row, false))}</div></>}
              {!gainers.length && !losers.length && <p>{noMoversText}</p>}
            </> : <p>{sectorLoading ? "Loading sector movers…" : "Tap a sector to open its stocks."}</p>}
          </div>
        </div>
      </div>
      <aside className="mfb-stream-detail" aria-live="polite"><small>SELECTED INSTRUMENT</small>
        {sectorError && <p className="mfb-alert" role="alert">{sectorError}</p>}
        {selected ? <>
          <h3>{selected.name}</h3><span className="mfb-stream-sub">{selected.symbol} · {selected.exchange}</span>
          <div className="mfb-stream-stats">
            <div><small>LAST PRICE</small><strong>₹{fmt(selected.price)}</strong></div>
            <div><small>PRICE CHANGE</small><strong className={selected.direction}>{pct(selected.changePercent)}</strong></div>
            <div><small>VOLUME</small><strong>{selected.volume === null ? "Not supplied" : fmt(selected.volume, 0)}</strong></div>
            {relativeToSectorSample !== null && <div><small>VS SECTOR SAMPLE</small><strong className={relativeToSectorSample >= 0 ? "up" : "down"}>{pct(relativeToSectorSample)}</strong></div>}
          </div>
          <button type="button" className="mfb-stream-open" onClick={onOpenChart}>Open full chart</button>
          <HistoricalFlowPanel series={historySeries} loading={historyLoading} error={historyError} symbol={selected.symbol} range={historyRange} onRangeChange={onRangeChange}/>
        </> : <p>Click a sector, then a stock in the stream. Only provider-returned fields are shown.</p>}
      </aside>
    </div>
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
  const sectorIndexRaw = sectorPayload?.sector_index?.percent_change;
  const sectorIndexChange = sectorIndexRaw !== null && sectorIndexRaw !== undefined && Number.isFinite(Number(sectorIndexRaw)) ? Number(sectorIndexRaw) : null;
  const sectorIndexDisagrees = sectorIndexChange !== null && sectorSampleSummary.medianChangePct !== null
    && Math.abs(sectorSampleSummary.medianChangePct - sectorIndexChange) > 5;
  const unverifiedCount = useMemo(() => rows.filter(row => !row.percentVerified).length, [rows]);
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
      <div><span className={error ? "mfb-status error" : loading ? "mfb-status" : "mfb-status live"}><i className="mfb-pulse" aria-hidden="true"/>{error ? "SOURCE ERROR" : loading ? "CONNECTING" : sectorOnlyPartial ? "SECTOR DATA PARTIAL" : payload?.status === "partial" ? "PARTIAL DATA" : "REST SNAPSHOT"}</span>
        <button type="button" onClick={() => refresh(true)} disabled={loading || refreshing}>{refreshing ? "Refreshing…" : "Refresh"}</button></div>
    </header>
    <section className="mfb-index-rail">{indices.map(index => <div key={index.exchange + ":" + index.name}>
      <small>{index.name}</small><strong>{fmt(index.last_price)}</strong>
      <span>{index.exchange}{index.percent_change !== null && index.percent_change !== undefined && Number.isFinite(Number(index.percent_change)) && <b className={Number(index.percent_change) >= 0 ? "up" : "down"}>{pct(Number(index.percent_change))}</b>}</span></div>)}
      {!indices.length && <p>No index snapshots returned by the provider.</p>}</section>
    {error && <p className="mfb-alert" role="alert">{error}. Last successful data is retained; no demo feed is substituted.</p>}{coreProviderErrors.length > 0 && <p className="mfb-alert" role="status">Some market or benchmark requests failed. Available provider responses are retained; missing instruments are not estimated.</p>}
    {!loading && !rows.length && !error && <p className="mfb-alert">No valid provider movers were returned. No simulated instruments are displayed.</p>}
    <div className="mfb-overview">
    <Distribution rows={rows} counts={buildMarketFlowBoard(rows).counts} breadthAvailable={payload?.capabilities?.full_advance_decline_breadth === true} retrievedAt={retrievedAt ? new Date(retrievedAt).toLocaleTimeString("en-IN") : null}/>
    <VolumeParticipation rows={rows}/>
    </div>
    <section className="mfb-filterbar" aria-label="Filter market movers">
      <label>Search instruments<input type="search" value={searchQuery} onChange={event => setSearchQuery(event.target.value)} placeholder="Symbol or company"/></label>
      <label>Exchange<select value={exchangeFilter} onChange={event => setExchangeFilter(event.target.value)}><option value="ALL">All exchanges</option><option value="NSE">NSE</option><option value="BSE">BSE</option></select></label>
      <label>Direction<select value={directionFilter} onChange={event => setDirectionFilter(event.target.value)}><option value="all">All directions</option><option value="bullish">Bullish</option><option value="bearish">Bearish</option><option value="unchanged">Unchanged</option></select></label>
      <label>Sort by<select value={sortKey} onChange={event => setSortKey(event.target.value)}><option value="changePercent">Price change</option><option value="volume">Volume</option><option value="price">Last price</option><option value="symbol">Symbol</option></select></label>
      <button type="button" onClick={() => setSortDirection(value => value === "desc" ? "asc" : "desc")} aria-label="Toggle sort direction">{sortDirection === "desc" ? "Highest first ↓" : "Lowest first ↑"}</button>
      <span>{filteredRows.length} of {rows.length} returned movers</span>
    </section>
    <DataQuality title="Data quality" notes={[
      rejectionSummary(payload?.data_quality?.rejected_rows) && rejectionSummary(payload.data_quality.rejected_rows) + ". They are hidden, never repaired.",
      unverifiedCount > 0 && unverifiedCount + " of " + rows.length + " movers have a provider percentage that does not match their own price change. They are shown as reported.",
    ]}/>
    <StreamFlow rows={filteredRows} board={board} sectorFlowRows={sectorFlowRows} selectedSectorKey={selectedSectorKey}
      sectorLoading={sectorLoading} sectorError={sectorError} sectorPayload={sectorPayload} sectorBoard={sectorBoard}
      sectorSampleSummary={sectorSampleSummary} selected={selected} selectedKey={selectedKey} relativeToSectorSample={relativeToSectorSample}
      historySeries={historySeries} historyLoading={historyLoading} historyError={historyError} historyRange={historyRange}
      onRangeChange={setHistoryRange} onSelectSector={loadSector} onSelectStock={row => setSelectedKey(keyOf(row))}
      onOpenChart={() => onSelectInstrument?.(selected)} retrievedAt={retrievedAt ? new Date(retrievedAt).toLocaleTimeString("en-IN") : null}/>
    <section className="mfb-section mfb-flow">
      <div className="mfb-section-head"><div><small>03 / SECTOR DETAIL</small><h2>{sectorPayload?.sector?.name ? sectorPayload.sector.name + " sector detail" : "Selected sector detail"}</h2>
        <p>Index, price distribution and data notes for the sector chosen in the stream above.</p></div>
        <span className="mfb-sector-coverage" role="status">{sectorIndexPerformanceCount} of {sectorOptions.length} sector indices available</span></div>
      <div className="mfb-sectors mfb-sector-body">
        {sectorIndexErrors.length > 0 && <p className="mfb-note">Unavailable from the provider: {sectorIndexErrors.map(item => item.name || item.sector).filter(Boolean).join(", ")}.</p>}
        {!sectorIndices.length && <p className="mfb-note">Sector index quotes are not available from the current provider response. Sector stock movers remain available on selection.</p>}
        {sectorLoading && <p className="mfb-note" role="status">Loading actual {sectorOptions.find(item => item.key === selectedSectorKey)?.name || "sector"} movers…</p>}
        {sectorError && <p className="mfb-alert" role="alert">{sectorError}</p>}
        {!sectorPayload && !sectorLoading && !sectorError && <p className="mfb-note">Select a sector in the stream above to see its detail.</p>}
        {sectorPayload && <>
          {sectorPayload.sector_index && <div className="mfb-sector-index-quote"><small>{sectorPayload.sector_index.name} · INDEX LEVEL</small><strong>{fmt(sectorPayload.sector_index.last_price)}</strong>
            {sectorIndexChange !== null && <b className={sectorIndexChange >= 0 ? "up" : "down"}>{pct(sectorIndexChange)}</b>}
            <span>{sectorPayload.sector_index.previous_close ? "Previous close " + fmt(sectorPayload.sector_index.previous_close) : "Daily change unavailable from provider OHLC."}</span></div>}
          <DataQuality title="Sector data quality" notes={[
            sectorRows.some(row => !row.percentVerified) && sectorRows.filter(row => !row.percentVerified).length + " of " + sectorRows.length + " sector movers have a provider percentage that does not match their own price change. Shown as reported.",
            sectorIndexDisagrees && "Sample median " + pct(sectorSampleSummary.medianChangePct) + " is far from the sector index " + pct(sectorIndexChange) + ". The provider mover percentages may be unreliable for this sector.",
            rejectionSummary(sectorPayload.data_quality?.rejected_rows),
            sectorPayload.errors?.length > 0 && "One sector mover source did not respond. Available real results are retained.",
          ]}/>
          <Distribution eyebrow="SECTOR / PROVIDER-RANKED MOVERS" title={sectorPayload.sector?.name + " price distribution"} description="Median and directional counts describe only the returned top movers, not full-sector performance or constituent breadth." rows={sectorRows} counts={buildMarketFlowBoard(sectorRows).counts} breadthAvailable={false} retrievedAt={sectorPayload.last_updated ? new Date(sectorPayload.last_updated).toLocaleTimeString("en-IN") : null}/>
          <VolumeParticipation rows={sectorRows} label="SECTOR SAMPLE"/>
        </>}
        {!sectorOptions.length && <p className="mfb-note">Sector universes were not returned by the backend.</p>}
      </div>
    </section>
    <section className="mfb-section mfb-lists">
      <div className="mfb-section-head"><div><small>04 / ALL RETURNED MOVERS</small><h2>Bullish and bearish movers</h2>
        <p>Every market-wide mover returned by the provider that passed validation. Use the filters above to narrow this list.</p></div></div>
      <div className="mfb-sides"><Side title="Bullish" side="up" rows={board.bullish} selectedKey={selectedKey} focusedKey={focusedKey} onSelect={row => setSelectedKey(keyOf(row))} onHover={onHoverInstrument}/>
        <Side title="Bearish" side="down" rows={board.bearish} selectedKey={selectedKey} focusedKey={focusedKey} onSelect={row => setSelectedKey(keyOf(row))} onHover={onHoverInstrument}/></div>
    </section>
    <footer className="mfb-footer"><span>Source: {payload?.data_sources?.primary || "m.Stock via Financial OS Gateway"}</span>
      <span>Snapshot assembled: {retrievedAt ? new Date(retrievedAt).toLocaleString("en-IN") : "—"}</span>
      <span>Read-only · REST only · no synthetic market values</span></footer>
  </main>;
}
