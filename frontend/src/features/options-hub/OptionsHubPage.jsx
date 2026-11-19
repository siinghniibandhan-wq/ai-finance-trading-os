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
const expiryLabel = value => {
  const raw = String(value || "").trim();
  let match = raw.match(/^(\d{1,2})[- ]([A-Za-z]{3})[- ](\d{4})$/);
  if (match) return `${match[1]} ${match[2].toUpperCase()} ${match[3]}`;
  match = raw.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
  if (match) return `${match[1].padStart(2, "0")}/${match[2].padStart(2, "0")}/${match[3]}`;
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? raw : parsed.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
};

function parseMaster(data) {
  const instruments = Array.isArray(data?.underlyings) ? data.underlyings
    .filter(item => item && typeof item.symbol === "string" && Array.isArray(item.expiries))
    .map(item => ({ symbol: item.symbol, expiries: item.expiries.map(String) }))
    .sort((a, b) => a.symbol.localeCompare(b.symbol)) : [];
  return { instruments };
}

function makeStrikeRows(contracts) {
  const byStrike = new Map();
  for (const item of Array.isArray(contracts) ? contracts : []) {
    const strike = numberOrNull(item?.strike);
    if (strike === null) continue;
    const row = byStrike.get(strike) || { strike, ce: null, pe: null };
    if (item.side === "CE") row.ce = item;
    if (item.side === "PE") row.pe = item;
    byStrike.set(strike, row);
  }
  return [...byStrike.values()].sort((a, b) => a.strike - b.strike);
}

function calculateAnalytics(rows) {
  const completeOi = rows.length > 0 && rows.every(row =>
    (!row.ce || numberOrNull(row.ce.open_interest) !== null) &&
    (!row.pe || numberOrNull(row.pe.open_interest) !== null)
  );
  if (!completeOi) return { available: false, callOi: null, putOi: null, pcr: null, maxPain: null };
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
    if (payout < minimumPayout) { minimumPayout = payout; maxPain = settlement; }
  }
  return { available: true, callOi, putOi, pcr: callOi > 0 ? putOi / callOi : null, maxPain };
}

export default function OptionsHubPage() {
  const [exchange, setExchange] = useState("NSE");
  const [master, setMaster] = useState(null);
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [selectedExpiry, setSelectedExpiry] = useState("");
  const [chain, setChain] = useState(null);
  const [masterLoading, setMasterLoading] = useState(true);
  const [chainLoading, setChainLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const busy = useRef(false);

  const parsed = useMemo(() => parseMaster(master?.data), [master]);
  const selectedInstrument = parsed.instruments.find(item => item.symbol === selectedSymbol) || null;
  const expiryOptions = selectedInstrument?.expiries || [];
  const rows = useMemo(() => makeStrikeRows(chain?.contracts), [chain]);
  const analytics = useMemo(() => calculateAnalytics(rows), [rows]);
  const quoteCoverage = chain?.quote_count
    ? `${chain.quote_coverage || 0}/${chain.quote_count}`
    : "—";

  const loadMaster = useCallback(async () => {
    setMasterLoading(true);
    setError("");
    setChain(null);
    try {
      const result = await loadOptionChainMaster(exchange);
      const next = parseMaster(result);
      if (!next.instruments.length) throw new Error("The provider instrument master contains no option contracts for this exchange.");
      setMaster(result);
      const preferred = next.instruments.find(item => item.symbol === "NIFTY") || next.instruments[0];
      setSelectedSymbol(preferred.symbol);
      setSelectedExpiry(preferred.expiries[0] || "");
    } catch (err) {
      setMaster(null);
      setSelectedSymbol("");
      setSelectedExpiry("");
      setError(err?.message || "Option instrument master is unavailable.");
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
      const result = await loadOptionChain({ exchange, expiry: selectedExpiry, underlying: selectedSymbol });
      if (!Array.isArray(result.contracts)) throw new Error("The provider response did not contain option contracts.");
      setChain(result);
      setLastUpdated(result.retrieved_at || new Date().toISOString());
      setError("");
    } catch (err) {
      setError(err?.message || "Live options quotes are unavailable.");
    } finally {
      busy.current = false;
      setChainLoading(false);
    }
  }, [exchange, selectedExpiry, selectedInstrument, selectedSymbol]);

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
    setSelectedExpiry("");
  };

  return (
    <main className="options-hub-page">
      <header className="options-hub-header">
        <div>
          <small>FINANCIAL OS / MARKETS / DERIVATIVES</small>
          <h1>Options Hub</h1>
          <p>Live option contracts and LTP snapshots from the m.Stock Script Master and batch REST quote API. Read-only; no order placement.</p>
        </div>
        <div className={`options-hub-status ${chain?.contracts?.length ? "is-live" : "is-waiting"}`}>
          {chain?.contracts?.length ? "PROVIDER DATA RECEIVED" : "AWAITING PROVIDER DATA"}
        </div>
      </header>

      <section className="options-hub-toolbar">
        <label>Exchange<select value={exchange} onChange={event => changeExchange(event.target.value)}><option value="NSE">NSE F&O</option><option value="BSE">BSE F&O</option></select></label>
        <label>Underlying<select value={selectedSymbol} onChange={event => { setSelectedSymbol(event.target.value); const item = parsed.instruments.find(x => x.symbol === event.target.value); setSelectedExpiry(item?.expiries?.[0] || ""); setChain(null); }} disabled={!parsed.instruments.length}>
          {parsed.instruments.map(item => <option key={item.symbol} value={item.symbol}>{item.symbol}</option>)}
        </select></label>
        <label>Expiry<select value={selectedExpiry} onChange={event => { setSelectedExpiry(event.target.value); setChain(null); }} disabled={!expiryOptions.length}>
          {expiryOptions.map(item => <option key={item} value={item}>{expiryLabel(item)}</option>)}
        </select></label>
        <button type="button" onClick={() => setRefreshKey(value => value + 1)} disabled={masterLoading || chainLoading}>Refresh master</button>
        <button type="button" onClick={refreshChain} disabled={!selectedExpiry || chainLoading}>{chainLoading ? "Refreshing…" : "Refresh quotes"}</button>
      </section>

      {error && <div className="options-hub-error" role="alert">{error}</div>}
      {masterLoading && <div className="options-hub-empty">Loading m.Stock instrument master…</div>}
      {!masterLoading && !master && !error && <div className="options-hub-empty">No option master is available.</div>}

      <section className="options-hub-metrics">
        <div><small>UNDERLYING</small><strong>{selectedSymbol || "—"}</strong></div>
        <div><small>EXPIRY</small><strong>{selectedExpiry ? expiryLabel(selectedExpiry) : "—"}</strong></div>
        <div><small>CALL OI</small><strong>{analytics.available ? fmt(analytics.callOi, 0) : "Not supplied"}</strong></div>
        <div><small>PUT OI</small><strong>{analytics.available ? fmt(analytics.putOi, 0) : "Not supplied"}</strong></div>
        <div><small>PCR (OI)</small><strong>{analytics.pcr === null ? "—" : fmt(analytics.pcr, 2)}</strong></div>
        <div><small>MAX PAIN</small><strong>{analytics.maxPain === null ? "—" : fmt(analytics.maxPain, 2)}</strong></div>
        <div><small>LIVE LTP COVERAGE</small><strong>{quoteCoverage}</strong></div>
      </section>

      <section className="options-hub-chain">
        <div className="options-hub-chain-heading">
          <div><small>LIVE OPTION CONTRACTS</small><h2>{selectedSymbol || "Select underlying"} · {selectedExpiry ? expiryLabel(selectedExpiry) : "Select expiry"}</h2></div>
          <span>{rows.length} strikes · REST refresh 30s</span>
        </div>
        {chainLoading && !rows.length && <div className="options-hub-empty">Fetching live option quotes…</div>}
        {!chainLoading && !rows.length && !error && <div className="options-hub-empty">Select an underlying and expiry to load contracts.</div>}
        {rows.length > 0 && <div className="options-hub-table-wrap">
          <table className="options-hub-table">
            <thead><tr><th colSpan="3">CALL (CE)</th><th>STRIKE</th><th colSpan="3">PUT (PE)</th></tr>
              <tr><th>LTP ₹</th><th>OI</th><th>SYMBOL</th><th>PRICE</th><th>SYMBOL</th><th>OI</th><th>LTP ₹</th></tr></thead>
            <tbody>{rows.map(row => <tr key={row.strike}>
              <td>{row.ce?.last_price == null ? "—" : fmt(row.ce.last_price)}</td>
              <td>{row.ce?.open_interest == null ? "—" : fmt(row.ce.open_interest, 0)}</td>
              <td>{row.ce?.tradingsymbol || "—"}</td>
              <th>{fmt(row.strike, 2)}</th>
              <td>{row.pe?.tradingsymbol || "—"}</td>
              <td>{row.pe?.open_interest == null ? "—" : fmt(row.pe.open_interest, 0)}</td>
              <td>{row.pe?.last_price == null ? "—" : fmt(row.pe.last_price)}</td>
            </tr>)}</tbody>
          </table>
        </div>}
      </section>

      <section className="options-hub-capabilities">
        <div className="options-hub-capabilities-heading"><small>DATA-QUALITY GATES</small><h2>Analytics availability</h2></div>
        <div className="options-hub-capability"><div><strong>Option contract strikes and live LTP</strong><span>Provider Script Master contracts enriched from batch REST quotes.</span></div><span className={rows.length ? "options-hub-available" : "options-hub-unavailable"}>{rows.length ? "Available" : "Awaiting quotes"}</span></div>
        <div className="options-hub-capability"><div><strong>Open interest, PCR and Max Pain</strong><span>Only available when the connected REST quote contract supplies complete OI for the selected expiry.</span></div><span className={analytics.available ? "options-hub-available" : "options-hub-unavailable"}>{analytics.available ? "Available" : "OI not supplied"}</span></div>
        <div className="options-hub-capability"><div><strong>Implied volatility and Greeks</strong><span>Not calculated until verified IV and underlying/contract inputs are supplied.</span></div><span className="options-hub-unavailable">Provider inputs required</span></div>
        <div className="options-hub-capability"><div><strong>Open-interest change and writer positioning</strong><span>Requires comparable prior snapshots; no single-snapshot inference.</span></div><span className="options-hub-unavailable">History required</span></div>
      </section>

      <footer>
        Source: m.Stock Script Master + batched Type A REST LTP via Financial OS Gateway · Last snapshot: {lastUpdated ? new Date(lastUpdated).toLocaleString("en-IN") : "Not received"} · Read-only · REST only · No simulated data
      </footer>
    </main>
  );
}
