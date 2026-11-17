import React from "react";
import { buildLiveMarketView, formatMarketValue } from "./marketFlowLive";

const fmt = value => formatMarketValue(value, 2);
const compact = value => formatMarketValue(value, 0);

export default function LiveMarketFlow({ snapshot, symbol, onSymbolChange }) {
  const view = buildLiveMarketView(snapshot, symbol);
  const futures = view.futures;
  const strikes = view.strikes;
  const unavailable = view.unavailable;
  return (
    <section className="mf-live-market" aria-label={symbol + " live market flow"}>
      <div className="mf-live-market-toolbar">
        <div>
          <p className="market-flow-eyebrow">PROVIDER DATA · READ ONLY</p>
          <h2>{symbol} derivatives</h2>
        </div>
        <label className="mf-underlying-select">Underlying
          <select value={symbol} onChange={event => onSymbolChange(event.target.value)}>
            <option value="NIFTY">NIFTY</option>
            <option value="BANKNIFTY">BANKNIFTY</option>
          </select>
        </label>
      </div>
      <div className="mf-live-kpis">
        <article><small>Put / Call ratio</small><b>{view.pcr == null ? "Unavailable" : view.pcr.toFixed(2)}</b></article>
        <article><small>Max put OI · support</small><b>{view.support ? fmt(view.support.strike) : "Unavailable"}</b><small>{view.support ? compact(view.support.oi) + " OI" : "No option OI"}</small></article>
        <article><small>Max call OI · resistance</small><b>{view.resistance ? fmt(view.resistance.strike) : "Unavailable"}</b><small>{view.resistance ? compact(view.resistance.oi) + " OI" : "No option OI"}</small></article>
        <article><small>Intraday candles</small><b>Unavailable</b><small>No intraday history source</small></article>
        <article><small>Buildup</small><b>Unavailable</b><small>No reliable intraday price/OI history</small></article>
        <article><small>OI change %</small><b>Unavailable</b><small>No previous-day OI source</small></article>
      </div>
      <div className="mf-live-grid">
        <section className="mf-live-table">
          <h3>Futures contracts</h3>
          {futures.length ? <div className="mf-live-scroll"><table>
            <thead><tr><th>Contract</th><th>Expiry</th><th>Price</th><th>Open interest</th><th>Volume</th></tr></thead>
            <tbody>{futures.map((row, index) => <tr key={row.tradingsymbol || row.expiry || index}>
              <td>{row.tradingsymbol || row.symbol}</td><td>{row.expiry || "Unavailable"}</td>
              <td>{row.price == null ? "Unavailable" : "₹" + fmt(row.price)}</td>
              <td>{row.oi == null ? "Unavailable" : compact(row.oi)}</td>
              <td>{row.volume == null ? "Unavailable" : compact(row.volume)}</td>
            </tr>)}</tbody>
          </table></div> : <p className="mf-no-data">No futures contract currently has a valid price, OI and volume tick.</p>}
        </section>
        <section className="mf-live-table">
          <h3>Option open interest by strike</h3>
          {strikes.length ? <div className="mf-live-scroll"><table>
            <thead><tr><th>Strike</th><th>Call OI (CE)</th><th>Put OI (PE)</th></tr></thead>
            <tbody>{strikes.map(row => <tr key={row.strike}><td>{fmt(row.strike)}</td><td>{compact(row.ce_oi)}</td><td>{compact(row.pe_oi)}</td></tr>)}</tbody>
          </table></div> : <p className="mf-no-data">Option OI unavailable until valid option ticks arrive.</p>}
        </section>
      </div>
      <section className="mf-live-unavailable">
        <h3>Contracts unavailable</h3>
        {unavailable.length ? <ul>{unavailable.map((row, index) =>
          <li key={row.instrument_token || row.tradingsymbol || index}>
            <b>{row.tradingsymbol || "Contract"}</b> — unavailable: {row.reason || "No valid tick"}
          </li>)}</ul> : <p>None reported by the gateway for this underlying.</p>}
      </section>
      <p className="mf-disclaimer">Live figures above are provider ticks received by the gateway. Prices/OI/volume are not substituted when absent. Candles, buildup, conviction and OI change are unavailable because this feed does not supply intraday history or previous-day OI. This is market information, not a trading recommendation.</p>
    </section>
  );
}
