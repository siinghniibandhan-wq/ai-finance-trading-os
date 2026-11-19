import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { loadOptionChain, loadOptionChainMaster } from "./api";
import "./options-hub.css";

const fmt = (value, digits = 2) => Number.isFinite(Number(value))
  ? new Intl.NumberFormat("en-IN", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(Number(value))
  : "—";
const numberOrNull = value => {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
};
const expiryLabel = timestamp => new Date(Number(timestamp) * 1000).toLocaleDateString("en-IN", {
  day: "2-digit", month: "short", year: "numeric",
});

function parseMaster(data) {
  const expiryMap = data?.dctExp || {};
  const instruments = [];
  for (const group of ["OPTIDX", "OFSTK", "OPTSTK"]) {
    for (const item of Array.isArray(data?.[group]) ? data[group] : []) {
      const parts = String(item).split(",");
      const symbol = String(parts[0] || "").trim().toUpperCase();
      const token = String(parts[1] || "").trim();
      const expiryIds = parts.slice(2).filter(id => Object.prototype.hasOwnProperty.call(expiryMap, id));
      if (symbol && /^\d+$/.test(token) && expiryIds.length) {
        instruments.push({ symbol, token, group, expiryIds });
      }
    }
  }
  return { expiryMap, instruments };
}

function makeStrikeRows(contracts) {
  const byStrike = new Map();
  for (const item of Array.isArray(contracts) ? contracts : []) {
    const strike = numberOrNull(item?.strike);
    if (strike === null) continue;
    const row = byStrike.get(strike) || { strike, ce: null, pe: null };
    row[item.side === "CE" ? "ce" : "pe"] = item;
    byStrike.set(strike, row);
  }
  return [...byStrike.values()].sort((a, b) => a.strike - b.strike);
}

function calculateAnalytics(rows) {
  const callOi = rows.reduce((sum, row) => sum + (numberOrNull(row.ce?.open_interest) || 0), 0);
  const putOi = rows.reduce((sum, row) => sum + (numberOrNull(row.pe?.open_interest) || 0), 0);
  let maxPain = null;
  let minimumPayout = Infinity;
  for (const settlement of rows.map(row => row.strike)) {
    const payout = rows.reduce((sum, row) => {
      const ceOi = numberOrNull(row.ce?.open_interest) || 0;
      const peOi = numberOrNull(row.pe?.open_interest) || 0;
      return sum + ceOi * Math.max(0, settlement - row.strike)
        + peOi * Math.max(0, row.strike - settlement);
    }, 0);
    if (payout < minimumPayout) {
      minimumPayout = payout;
      maxPain = settlement;
    }
  }
  return { callOi, putOi, pcr: callOi > 0 ? putOi / callOi : null, maxPain };
}

export default function OptionsHubPage() {
  const [exchange, setExchange] = useState("NSE");
  const [master, setMaster] = useState(null);
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [selectedExpiryId, setSelectedExpiryId] = useState("");
  const [chain, setChain] = useState(null);
  const [masterLoading, setMasterLoading] = useState(true);
  const [chainLoading, setChainLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const busy = useRef(false);

  const parsed = useMemo(() => parseMaster(master?.data), [master]);
  const selectedInstrument = parsed.instruments.find(item => item.symbol === selectedSymbol) || null;
  const expiryOptions = useMemo(() => selectedInstrument
    ? selectedInstrument.expiryIds.map(id => ({ id, timestamp: parsed.expiryMap[id] }))
      .filter(item => Number.isFinite(Number(item.timestamp)))
      .sort((a, b) => Number(a.timestamp) - Number(b.timestamp))
    : [], [parsed, selectedInstrument]);
  const selectedExpiry = expiryOptions.find(item => item.id === selectedExpiryId) || expiryOptions[0] || null;
  const rows = useMemo(() => makeStrikeRows(chain?.contracts), [chain]);
  const analytics = useMemo(() => calculateAnalytics(rows), [rows]);
  const quoteCoverage = chain?.quote_count
    ? `${chain.quote_coverage || 0}/${chain.quote_count}`
    : "—";

  const loadMaster = useCallback(async () => {
    setMasterLoading(true);
    setError("");
    try {
      const result = await loadOptionChainMaster(exchange);
      const next = parseMaster(result.data);
      if (!next.instruments.length) throw new Error("The provider returned no option contracts for this exchange.");
      setMaster(result);
      const preferred = next.instruments.find(item => item.symbol === "NIFTY" && item.group === "OPTIDX") || next.instruments[0];
      setSelectedSymbol(preferred.symbol);
      setSelectedExpiryId(preferred.expiryIds[0] || "");
    } catch (err) {
      setMaster(null);
      setChain(null);
      setError(err?.message || "Option-chain master is unavailable.");
    } finally {
      setMasterLoading(false);
    }
  }, [exchange]);

  useEffect(() => { loadMaster(); }, [loadMaster, refreshKey]);

  const refreshChain = useCallback(async () => {
    if (!selectedInstrument || !selectedExpiry || busy.current) return;
    busy.current = true;
    setChainLoading(true);
    try {
      const result = await loadOptionChain({
        exchange,
        expiry: selectedExpiry.timestamp,
        token: selectedInstrument.token,
      });
      if (!Array.isArray(result.contracts)) throw new Error("The provider response did not contain option contracts.");
      setChain(result);
      setLastUpdated(result.retrieved_at || new Date().toISOString());
      setError("");
    } catch (err) {
      setError(err?.message || "Live option-chain data is unavailable.");
    } finally {
      busy.current = false;
      setChainLoading(false);
    }
  }, [exchange, selectedInstrument, selectedExpiry]);

  useEffect(() => {
    if (!selectedInstrument || !selectedExpiry) return undefined;
    refreshChain();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") refreshChain();
    }, 30000);
    return () => window.clearInterval(timer);
  }, [refreshChain, selectedInstrument, selectedExpiry]);

  const changeExchange = value => {
    setExchange(value);
    setMaster(null);
    setChain(null);
    setSelectedSymbol("");
    setSelectedExpiryId("");
  };

  return (
    <main className="options-hub-page">
      <header className="options-hub-header">
        <div>
          <small>FINANCIAL OS / MARKETS / DERIVATIVES</small>
          <h1>Options Hub</h1>
          <p>Live m.Stock option-chain snapshots through the authenticated Financial OS Gateway. Read-only; no order placement.</p>
        </div>
        <div className={`options-hub-status ${chain?.contracts?.length ? "is-live" : "is-waiting"}`}>
          {chain?.contracts?.length ? "PROVIDER DATA RECEIVED" : "AWAITING PROVIDER DATA"}
        </div>
      </header>

      <section className="options-hub-toolbar">
        <label>Exchange<select value={exchange} onChange={event => changeExchange(event.target.value)}><option value="NSE">NSE F&O</option><option value="BSE">BSE F&O</option></select></label>
        <label>Underlying<select value={selectedSymbol} onChange={event => { setSelectedSymbol(event.target.value); const item = parsed.instruments.find(x => x.symbol === event.target.value); setSelectedExpiryId(item?.expiryIds?.[0] || ""); setChain(null); }} disabled={!parsed.instruments.length}>
          {parsed.instruments.map((item, index) => <option key={item.symbol + item.group + index} value={item.symbol}>{item.symbol} · {item.group}</option>)}
        </select></label>
        <label>Expiry<select value={selectedExpiry?.id || ""} onChange={event => { setSelectedExpiryId(event.target.value); setChain(null); }} disabled={!expiryOptions.length}>
          {expiryOptions.map(item => <option key={item.id} value={item.id}>{expiryLabel(item.timestamp)}</option>)}
        </select></label>
        <button type="button" onClick={() => setRefreshKey(value => value + 1)} disabled={masterLoading || chainLoading}>Refresh master</button>
        <button type="button" onClick={refreshChain} disabled={!selectedExpiry || chainLoading}>{chainLoading ? "Refreshing…" : "Refresh chain"}</button>
      </section>

      {error && <div className="options-hub-error" role="alert">{error}</div>}
      {masterLoading && <div className="options-hub-empty">Loading provider option master…</div>}
      {!masterLoading && !master && !error && <div className="options-hub-empty">No option master is available.</div>}

      <section className="options-hub-metrics">
        <div><small>UNDERLYING</small><strong>{selectedSymbol || "—"}</strong></div>
        <div><small>EXPIRY</small><strong>{selectedExpiry ? expiryLabel(selectedExpiry.timestamp) : "—"}</strong></div>
        <div><small>CALL OI</small><strong>{rows.length ? fmt(analytics.callOi, 0) : "—"}</strong></div>
        <div><small>PUT OI</small><strong>{rows.length ? fmt(analytics.putOi, 0) : "—"}</strong></div>
        <div><small>PCR (OI)</small><strong>{analytics.pcr === null ? "—" : fmt(analytics.pcr, 2)}</strong></div>
        <div><small>MAX PAIN</small><strong>{analytics.maxPain === null ? "—" : fmt(analytics.maxPain, 2)}</strong></div>
        <div><small>LIVE LTP COVERAGE</small><strong>{quoteCoverage}</strong></div>
      </section>

      <section className="options-hub-chain">
        <div className="options-hub-chain-heading">
          <div><small>LIVE OPTION CHAIN</small><h2>{selectedSymbol || "Select underlying"} · {selectedExpiry ? expiryLabel(selectedExpiry.timestamp) : "Select expiry"}</h2></div>
          <span>{rows.length} strikes · REST refresh 30s</span>
        </div>
        {chainLoading && !rows.length && <div className="options-hub-empty">Fetching live option-chain data…</div>}
        {!chainLoading && !rows.length && !error && <div className="options-hub-empty">Select an underlying and expiry to load the chain.</div>}
        {rows.length > 0 && <div className="options-hub-table-wrap">
          <table className="options-hub-table">
            <thead><tr>
              <th colSpan="3">CALL (CE)</th><th>STRIKE</th><th colSpan="3">PUT (PE)</th>
            </tr><tr>
              <th>LTP ₹</th><th>OI</th><th>SYMBOL</th><th>PRICE</th><th>SYMBOL</th><th>OI</th><th>LTP ₹</th>
            </tr></thead>
            <tbody>{rows.map(row => <tr key={row.strike}>
              <td>{row.ce?.last_price == null ? "—" : fmt(row.ce.last_price)}</td>
              <td>{row.ce ? fmt(row.ce.open_interest, 0) : "—"}</td>
              <td>{row.ce?.tradingsymbol || "—"}</td>
              <th>{fmt(row.strike, 2)}</th>
              <td>{row.pe?.tradingsymbol || "—"}</td>
              <td>{row.pe ? fmt(row.pe.open_interest, 0) : "—"}</td>
              <td>{row.pe?.last_price == null ? "—" : fmt(row.pe.last_price)}</td>
            </tr>)}</tbody>
          </table>
        </div>}
      </section>

      <section className="options-hub-capabilities">
        <div className="options-hub-capabilities-heading"><small>DATA-QUALITY GATES</small><h2>Analytics availability</h2></div>
        <div className="options-hub-capability"><div><strong>Open-interest PCR and Max Pain</strong><span>Calculated from provider-returned CE/PE open interest and strikes.</span></div><span className={rows.length ? "options-hub-available" : "options-hub-unavailable"}>{rows.length ? "Available" : "Awaiting chain"}</span></div>
        <div className="options-hub-capability"><div><strong>Implied volatility and Greeks</strong><span>Not calculated until verified IV and contract inputs are supplied.</span></div><span className="options-hub-unavailable">Provider inputs required</span></div>
        <div className="options-hub-capability"><div><strong>Open-interest change and writer positioning</strong><span>Requires a comparable prior snapshot; no single-snapshot inference.</span></div><span className="options-hub-unavailable">History required</span></div>
      </section>

      <footer>
        Source: m.Stock Type A option-chain endpoints via Financial OS Gateway · Last snapshot: {lastUpdated ? new Date(lastUpdated).toLocaleString("en-IN") : "Not received"} · Read-only · REST only · No simulated data
      </footer>
    </main>
  );
}
