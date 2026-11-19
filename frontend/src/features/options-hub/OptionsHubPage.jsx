import React, { useEffect, useMemo, useRef, useState } from "react";
import { loadOptionsChain, loadOptionsMaster } from "./api.js";
import { buildOptionOIBars, calculateOptionsAnalytics } from "./optionsModel.js";
import "./options-hub.css";

const number = value => value === null || value === undefined || !Number.isFinite(Number(value))
  ? "—"
  : new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(Number(value));

function OptionOIProfile({ rows }) {
  const bars = useMemo(() => buildOptionOIBars(rows, 250), [rows]);
  if (!bars.length) return <p className="options-hub-muted">A complete CE/PE OI sample is not available. The OI profile is withheld.</p>;
  const height = Math.max(160, bars.length * 28 + 48);
  const center = 360;
  return <div className="options-hub-chart-scroll">
    <svg className="options-hub-oi-chart" viewBox={`0 0 720 ${height}`} role="img" aria-label="Mirrored call and put open interest by strike">
      <line x1={center} x2={center} y1="24" y2={height - 12} className="options-hub-chart-zero"/>
      <text x={center - 12} y="14" textAnchor="end" className="options-hub-chart-label">CALL OI</text>
      <text x={center + 12} y="14" className="options-hub-chart-label">PUT OI</text>
      {bars.map((row, index) => {
        const y = 30 + index * 28;
        return <g key={row.strike}>
          <rect x={center - row.callWidth} y={y} width={row.callWidth} height="15" rx="2" className="options-hub-call-bar"/>
          <rect x={center} y={y} width={row.putWidth} height="15" rx="2" className="options-hub-put-bar"/>
          <text x={center} y={y + 26} textAnchor="middle" className="options-hub-strike-label">{number(row.strike)}</text>
        </g>;
      })}
    </svg>
  </div>;
}

export default function OptionsHubPage() {
  const [exchange, setExchange] = useState("NSE");
  const [master, setMaster] = useState(null);
  const [underlying, setUnderlying] = useState("");
  const [expiry, setExpiry] = useState("");
  const [chain, setChain] = useState(null);
  const [masterLoading, setMasterLoading] = useState(true);
  const [chainLoading, setChainLoading] = useState(false);
  const [masterError, setMasterError] = useState("");
  const [chainError, setChainError] = useState("");
  const masterRequest = useRef(0);
  const chainRequest = useRef(0);

  useEffect(() => {
    const requestId = ++masterRequest.current;
    setMasterLoading(true);
    setMasterError("");
    setMaster(null);
    setChain(null);
    setUnderlying("");
    setExpiry("");
    loadOptionsMaster(exchange)
      .then(payload => {
        if (requestId !== masterRequest.current) return;
        setMaster(payload);
        const first = payload?.underlyings?.[0];
        setUnderlying(first?.symbol || "");
        setExpiry(first?.expiries?.[0] || "");
      })
      .catch(error => {
        if (requestId === masterRequest.current) setMasterError(error?.message || "Options master is unavailable.");
      })
      .finally(() => {
        if (requestId === masterRequest.current) setMasterLoading(false);
      });
    return () => { masterRequest.current += 1; };
  }, [exchange]);

  useEffect(() => {
    if (!underlying || !expiry) {
      setChain(null);
      return undefined;
    }
    const requestId = ++chainRequest.current;
    setChain(null);
    setChainLoading(true);
    setChainError("");
    loadOptionsChain({ exchange, underlying, expiry })
      .then(payload => {
        if (requestId === chainRequest.current) setChain(payload);
      })
      .catch(error => {
        if (requestId === chainRequest.current) setChainError(error?.message || "Options chain is unavailable.");
      })
      .finally(() => {
        if (requestId === chainRequest.current) setChainLoading(false);
      });
    return () => { chainRequest.current += 1; };
  }, [exchange, underlying, expiry]);

  const underlyings = Array.isArray(master?.underlyings) ? master.underlyings : [];
  const selectedUnderlying = underlyings.find(item => item.symbol === underlying);
  const expiries = Array.isArray(selectedUnderlying?.expiries) ? selectedUnderlying.expiries : [];
  const analytics = useMemo(
    () => calculateOptionsAnalytics(chain?.contracts),
    [chain?.contracts],
  );
  const quoteCoverage = chain && Number(chain.quote_count) > 0
    ? `${number(chain.quote_coverage)} / ${number(chain.quote_count)}`
    : "—";

  return <main className="options-hub-page">
    <header className="options-hub-header">
      <div>
        <small>FINANCIAL OS / MARKETS / DERIVATIVES</small>
        <h1>Options Hub</h1>
        <p>Provider-backed option chain and strike-wise analysis. All data is fetched through authenticated Financial OS REST APIs.</p>
      </div>
      <span className={chain ? "options-hub-status is-connected" : "options-hub-status"}>
        {masterLoading || chainLoading ? "LOADING REST DATA" : chain ? "REST SNAPSHOT" : "DATA UNAVAILABLE"}
      </span>
    </header>

    <section className="options-hub-toolbar" aria-label="Option chain selection">
      <label>Exchange
        <select value={exchange} onChange={event => setExchange(event.target.value)}>
          <option value="NSE">NSE F&O</option>
          <option value="BSE">BSE F&O</option>
        </select>
      </label>
      <label>Underlying
        <select value={underlying} onChange={event => {
          const next = underlyings.find(item => item.symbol === event.target.value);
          setUnderlying(event.target.value);
          setExpiry(next?.expiries?.[0] || "");
        }} disabled={!underlyings.length}>
          {underlyings.map(item => <option key={item.symbol} value={item.symbol}>{item.symbol}</option>)}
        </select>
      </label>
      <label>Expiry
        <select value={expiry} onChange={event => setExpiry(event.target.value)} disabled={!expiries.length}>
          {expiries.map(value => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <span>{master?.contract_count ? `${number(master.contract_count)} contracts in Script Master` : "Instrument master not loaded"}</span>
    </section>

    {(masterError || chainError) && <section className="options-hub-error" role="alert">
      <strong>Options REST data unavailable</strong>
      <p>{masterError || chainError}</p>
      <small>The Financial OS backend is connected only to gateway routes that are actually deployed. No sample chain or synthetic values are substituted.</small>
    </section>}

    {masterLoading && <p className="options-hub-muted" role="status">Loading provider Script Master through the REST gateway…</p>}
    {!masterLoading && !masterError && !underlyings.length && <p className="options-hub-muted">The provider Script Master returned no supported option underlyings.</p>}
    {chainLoading && <p className="options-hub-muted" role="status">Loading {underlying} · {expiry} option contracts…</p>}

    {chain && <>
      <section className="options-hub-source-line">
        <span>{chain.exchange_segment} · {chain.underlying} · {chain.expiry}</span>
        <span>Quotes available: {quoteCoverage}</span>
        <span>Retrieved: {chain.retrieved_at ? new Date(chain.retrieved_at).toLocaleString("en-IN") : "not supplied"}</span>
      </section>

      <section className="options-hub-analytics">
        <div><small>PUT / CALL OI</small><strong>{analytics.pcr === null ? "Unavailable" : analytics.pcr.toFixed(2)}</strong></div>
        <div><small>CALL OPEN INTEREST</small><strong>{analytics.callOI === null ? "Unavailable" : number(analytics.callOI)}</strong></div>
        <div><small>PUT OPEN INTEREST</small><strong>{analytics.putOI === null ? "Unavailable" : number(analytics.putOI)}</strong></div>
        <div><small>MAX PAIN STRIKE</small><strong>{analytics.maxPain === null ? "Unavailable" : number(analytics.maxPain)}</strong></div>
      </section>

      {!analytics.oiComplete && <p className="options-hub-data-note" role="status">
        The current REST quote response does not provide a complete CE/PE open-interest sample for this expiry. PCR, Max Pain and the OI profile are withheld rather than estimated.
      </p>}

      <section className="options-hub-panel">
        <div className="options-hub-panel-heading">
          <div><small>STRIKE DISTRIBUTION</small><h2>Call / Put Open Interest</h2></div>
          <span>{analytics.oiComplete ? "Provider OI" : "OI unavailable"}</span>
        </div>
        <OptionOIProfile rows={analytics.rows}/>
      </section>

      <section className="options-hub-panel">
        <div className="options-hub-panel-heading">
          <div><small>CONTRACT DETAIL</small><h2>Option chain by strike</h2></div>
          <span>{analytics.rows.length} strike rows</span>
        </div>
        <div className="options-hub-table-scroll">
          <table className="options-hub-table">
            <thead><tr>
              <th colSpan="3">CALL (CE)</th><th>STRIKE</th><th colSpan="3">PUT (PE)</th>
            </tr><tr>
              <th>LTP</th><th>VOLUME</th><th>OI</th><th>PRICE</th><th>OI</th><th>VOLUME</th><th>LTP</th>
            </tr></thead>
            <tbody>
              {analytics.rows.map(row => <tr key={row.strike}>
                <td>{number(row.CE?.lastPrice)}</td><td>{number(row.CE?.volume)}</td><td>{number(row.CE?.openInterest)}</td>
                <th>{number(row.strike)}</th>
                <td>{number(row.PE?.openInterest)}</td><td>{number(row.PE?.volume)}</td><td>{number(row.PE?.lastPrice)}</td>
              </tr>)}
            </tbody>
          </table>
        </div>
      </section>
      <p className="options-hub-data-note">IV, Greeks, bid/ask, OI change and historical OI are not included unless the connected provider REST contract supplies and verifies those fields. This view is read-only and does not place orders.</p>
    </>}

    <footer>Read-only · REST API only · Provider source: m.Stock via Financial OS Gateway · No browser-held broker credentials</footer>
  </main>;
}
