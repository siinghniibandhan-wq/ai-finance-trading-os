import React, { useMemo, useState } from "react";
import { formatMarketNumber, formatMarketTimestamp } from "./liveOrderFlowData";
import "./live-market-charts.css";

const chartTabs = [
  { id: "price", label: "Live price" },
  { id: "oi", label: "Options OI by strike" },
  { id: "activity", label: "Futures volume & OI" },
];

function EmptyChart({ children }) {
  return <div className="mf-chart-empty">{children}</div>;
}

function PriceChart({ points, contract }) {
  const [hover, setHover] = useState(null);
  const width = 1000;
  const height = 330;
  const pad = { top: 24, right: 24, bottom: 42, left: 82 };
  const values = points.map((point) => point.price);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = Math.max(max - min, Math.abs(max) * 0.0005, 0.01);
  const low = min - spread * 0.12;
  const high = max + spread * 0.12;
  const x = (index) => pad.left + (points.length < 2 ? 0.5 : index / (points.length - 1)) * (width - pad.left - pad.right);
  const y = (value) => pad.top + (high - value) / (high - low) * (height - pad.top - pad.bottom);
  const path = points.map((point, index) => (index ? "L" : "M") + x(index).toFixed(2) + "," + y(point.price).toFixed(2)).join(" ");
  const active = hover == null ? points[points.length - 1] : points[hover];
  return (
    <div className="mf-chart-canvas">
      <div className="mf-chart-readout">
        <span>{contract || "Selected futures contract"}</span>
        <strong>₹{formatMarketNumber(active?.price)}</strong>
        <small>{formatMarketTimestamp(active?.timestamp)}</small>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Live m.Stock futures price history">
        {[0, 1, 2, 3, 4].map((step) => {
          const value = high - (high - low) * step / 4;
          const yy = y(value);
          return <g key={step}><line className="mf-chart-grid" x1={pad.left} x2={width - pad.right} y1={yy} y2={yy} /><text className="mf-chart-axis" x={pad.left - 10} y={yy + 4} textAnchor="end">{formatMarketNumber(value)}</text></g>;
        })}
        {points.length > 1 && <path className="mf-price-area" d={`${path} L${x(points.length - 1)},${height - pad.bottom} L${x(0)},${height - pad.bottom} Z`} />}
        {points.length > 1 && <path className="mf-price-line" d={path} />}
        {points.map((point, index) => <circle key={point.timestamp + "-" + index} className={index === hover ? "mf-price-point is-hover" : "mf-price-point"} cx={x(index)} cy={y(point.price)} r={index === hover ? 5 : 2.5} />)}
        {active && <line className="mf-chart-crosshair" x1={x(hover ?? points.length - 1)} x2={x(hover ?? points.length - 1)} y1={pad.top} y2={height - pad.bottom} />}
        <rect x={pad.left} y={pad.top} width={width - pad.left - pad.right} height={height - pad.top - pad.bottom} fill="transparent" onPointerMove={(event) => {
          const bounds = event.currentTarget.getBoundingClientRect();
          const ratio = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width));
          setHover(Math.round(ratio * (points.length - 1)));
        }} onPointerLeave={() => setHover(null)} />
        <text className="mf-chart-axis" x={pad.left} y={height - 12}>Oldest received tick</text>
        <text className="mf-chart-axis" x={width - pad.right} y={height - 12} textAnchor="end">Latest received tick</text>
      </svg>
      <p className="mf-chart-footnote">Each point is an actual m.Stock provider tick received during this page session. No historical candles or interpolated prices are generated.</p>
    </div>
  );
}

function OpenInterestChart({ rows }) {
  const [hover, setHover] = useState(null);
  const max = Math.max(1, ...rows.flatMap((row) => [row.callOi || 0, row.putOi || 0]));
  if (!rows.length) return <EmptyChart>No fresh call/put open-interest pairs are available for this underlying and expiry.</EmptyChart>;
  return (
    <div className="mf-chart-canvas">
      <div className="mf-chart-legend"><span className="is-call">Call OI (CE)</span><span className="is-put">Put OI (PE)</span></div>
      <svg viewBox={`0 0 1000 ${Math.max(260, rows.length * 34 + 60)}`} role="img" aria-label="Live options open interest by strike">
        {rows.map((row, index) => {
          const yy = 34 + index * 34;
          const callWidth = (row.callOi || 0) / max * 360;
          const putWidth = (row.putOi || 0) / max * 360;
          return <g key={row.strike} className={hover === index ? "mf-oi-chart-row is-hover" : "mf-oi-chart-row"} onMouseEnter={() => setHover(index)} onMouseLeave={() => setHover(null)}>
            <text className="mf-chart-axis" x="500" y={yy + 14} textAnchor="middle">{formatMarketNumber(row.strike)}</text>
            <rect className="mf-oi-put-bar" x={500 - putWidth - 12} y={yy} width={putWidth} height="18" rx="3" />
            <rect className="mf-oi-call-bar" x="512" y={yy} width={callWidth} height="18" rx="3" />
            <text className="mf-chart-value" x={500 - putWidth - 20} y={yy + 13} textAnchor="end">{formatMarketNumber(row.putOi)}</text>
            <text className="mf-chart-value" x={520 + callWidth} y={yy + 13}>{formatMarketNumber(row.callOi)}</text>
          </g>;
        })}
      </svg>
      <p className="mf-chart-footnote">OI values are provider-reported contract open interest, grouped by symbol, expiry and strike.</p>
    </div>
  );
}

function ActivityChart({ futures }) {
  const [metric, setMetric] = useState("volume");
  const rows = futures.filter((row) => row[metric] != null && row[metric] >= 0);
  const max = Math.max(1, ...rows.map((row) => row[metric]));
  if (!rows.length) return <EmptyChart>No provider-reported futures {metric === "volume" ? "volume" : "open interest"} values are available.</EmptyChart>;
  return (
    <div className="mf-chart-canvas">
      <div className="mf-chart-controls" role="group" aria-label="Futures activity metric">
        <button type="button" className={metric === "volume" ? "active" : ""} onClick={() => setMetric("volume")}>Traded volume</button>
        <button type="button" className={metric === "oi" ? "active" : ""} onClick={() => setMetric("oi")}>Open interest</button>
      </div>
      <div className="mf-activity-bars">
        {rows.map((row) => <div className="mf-activity-row" key={row.contract}>
          <span title={row.contract}>{row.contract || row.symbol}</span>
          <div><i style={{ width: (row[metric] / max * 100) + "%" }} /></div>
          <b>{formatMarketNumber(row[metric])}</b>
        </div>)}
      </div>
      <p className="mf-chart-footnote">Only values explicitly supplied by the m.Stock provider are plotted. Missing volume/OI is not treated as zero.</p>
    </div>
  );
}

export default function LiveMarketCharts({ flow, history, symbol }) {
  const [activeTab, setActiveTab] = useState("price");
  const [windowSize, setWindowSize] = useState("session");
  const selected = flow.futures.find((row) => row.symbol === symbol) || flow.futures[0] || null;
  const pricePoints = useMemo(() => {
    const contract = selected?.contract;
    const filtered = (history || []).filter((point) => point.symbol === selected?.symbol && (!contract || point.contract === contract));
    const cutoff = windowSize === "session" ? 0 : Date.now() - Number(windowSize) * 60 * 1000;
    return filtered.filter((point) => !cutoff || new Date(point.timestamp).getTime() >= cutoff);
  }, [history, selected?.symbol, selected?.contract, windowSize]);
  const strikes = flow.optionOiByStrike.filter((row) => !symbol || row.symbol === symbol);
  const expiry = strikes[0]?.expiry;
  const strikeRows = strikes.filter((row) => !expiry || row.expiry === expiry).sort((a, b) => a.strike - b.strike);
  return (
    <section className="mf-live-charts" aria-label="Live market charts">
      <header className="mf-live-charts-header">
        <div><p>LIVE CHARTING WORKSPACE</p><h2>Market charts</h2><small>Charts are driven by authenticated provider ticks only</small></div>
        {activeTab === "price" && <label>Window <select value={windowSize} onChange={(event) => setWindowSize(event.target.value)}><option value="1">1 minute</option><option value="5">5 minutes</option><option value="15">15 minutes</option><option value="session">This session</option></select></label>}
      </header>
      <nav className="mf-live-chart-tabs" aria-label="Chart type">
        {chartTabs.map((tab) => <button type="button" key={tab.id} className={activeTab === tab.id ? "active" : ""} aria-pressed={activeTab === tab.id} onClick={() => setActiveTab(tab.id)}>{tab.label}</button>)}
      </nav>
      {activeTab === "price" && (pricePoints.length ? <PriceChart points={pricePoints} contract={selected?.contract} /> : <EmptyChart>Waiting for fresh m.Stock futures ticks. The live price chart will begin plotting after provider ticks arrive; no demo or historical placeholder series is shown.</EmptyChart>)}
      {activeTab === "oi" && <OpenInterestChart rows={strikeRows} />}
      {activeTab === "activity" && <ActivityChart futures={flow.futures} />}
    </section>
  );
}
