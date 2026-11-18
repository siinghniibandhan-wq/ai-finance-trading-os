import React, { useMemo, useState } from "react";
import OrderFlowLiveFeed from "./OrderFlowLiveFeed";
import { mapLiveOrderFlowSnapshot } from "./liveOrderFlowData";
import "./order-flow.css";

const number = (value) => value == null
  ? "—"
  : new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(value);
const price = (value) => value == null ? "—" : "₹" + number(value);
const percent = (value) => value == null ? "—" : (value > 0 ? "+" : "") + value.toFixed(2) + "%";
const time = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
};

export default function OrderFlowPage() {
  const [snapshot, setSnapshot] = useState(null);
  const [selected, setSelected] = useState("");
  const market = useMemo(() => mapLiveOrderFlowSnapshot(snapshot), [snapshot]);
  const active = market.stocks.find((item) => item.symbol === selected) || market.stocks[0] || null;
  const positive = market.stocks.filter((item) => item.changePct > 0).length;
  const negative = market.stocks.filter((item) => item.changePct < 0).length;

  return (
    <main className="market-flow-workspace live-market-flow">
      <header className="market-flow-header">
        <div>
          <p className="market-flow-eyebrow">FINANCIAL OS · M.STOCK PROVIDER FEED</p>
          <h1>Market Flow</h1>
          <p className="market-flow-subtitle">Live NFO futures, options open interest, traded volume and provider timestamps</p>
        </div>
        <span className={"mf-provider-pill " + (market.isLive ? "is-live" : "is-offline")}>
          {market.isLive ? "● LIVE PROVIDER DATA" : "● WAITING FOR LIVE DATA"}
        </span>
      </header>

      <OrderFlowLiveFeed onSnapshot={setSnapshot} />

      <section className="mf-live-summary" aria-label="Live market summary">
        <article><small>Futures contracts</small><b>{market.futuresCount}</b></article>
        <article><small>Option contracts</small><b>{market.optionsCount}</b></article>
        <article><small>Advancing</small><b className="up">{positive}</b></article>
        <article><small>Declining</small><b className="down">{negative}</b></article>
        <article><small>Provider snapshot</small><b>{time(market.asOf)}</b></article>
      </section>

      {!market.isLive ? (
        <section className="mf-live-empty" role="status">
          <h2>No verified live market ticks received</h2>
          <p>Market Flow will populate only after the authenticated m.Stock gateway supplies fresh, instrument-matched futures or options ticks. No demo instruments, simulated prices or placeholder analytics are displayed.</p>
        </section>
      ) : (
        <>
          <section className="mf-live-contracts">
            <header><div><h2>Live futures contracts</h2><p>Prices and metrics below are read from the latest fresh m.Stock snapshot.</p></div><span>{market.futuresCount} contracts</span></header>
            <div className="mf-live-table-wrap">
              <table className="mf-live-table">
                <thead><tr><th>Underlying</th><th>Contract</th><th>Expiry</th><th>Last price</th><th>Change</th><th>Volume</th><th>Open interest</th><th>Exchange time</th></tr></thead>
                <tbody>
                  {market.stocks.map((item) => (
                    <tr key={item.instrumentToken ?? item.contract} className={active?.contract === item.contract ? "is-selected" : ""} onClick={() => setSelected(item.symbol)}>
                      <td><button type="button" className="mf-symbol-select" onClick={() => setSelected(item.symbol)}>{item.symbol}</button></td>
                      <td>{item.contract}</td>
                      <td>{item.expiry || "—"}</td>
                      <td className="mf-live-price">{price(item.price)}</td>
                      <td className={item.changePct > 0 ? "up" : item.changePct < 0 ? "down" : ""}>{percent(item.changePct)}</td>
                      <td>{number(item.volume)}</td>
                      <td>{number(item.oi)}</td>
                      <td>{time(item.exchangeTimestamp || item.receivedAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="mf-live-options">
            <header><div><h2>Live option open interest</h2><p>{active ? active.symbol + " · strike-wise call and put OI from received option ticks" : "Select an underlying"}</p></div></header>
            {active?.strikes?.length ? (
              <div className="mf-live-table-wrap">
                <table className="mf-live-table mf-option-table">
                  <thead><tr><th>Strike</th><th>Put OI</th><th>Call OI</th><th>Put / Call OI</th></tr></thead>
                  <tbody>{active.strikes.map((strike) => {
                    const max = Math.max(1, strike.put, strike.call);
                    return <tr key={strike.strike}><td>{number(strike.strike)}</td><td>{number(strike.put)}</td><td>{number(strike.call)}</td><td><span className="mf-oi-bars"><i className="put" style={{ width: (strike.put / max * 100) + "%" }} /><i className="call" style={{ width: (strike.call / max * 100) + "%" }} /></span></td></tr>;
                  })}</tbody>
                </table>
              </div>
            ) : <p className="mf-live-empty-note">No fresh option OI ticks for this underlying in the current provider snapshot.</p>}
          </section>
        </>
      )}

      <p className="mf-disclaimer">Provider values are shown only when the gateway reports a fresh stream and supplies matching instrument tokens. Missing provider fields remain blank; historical price paths, OI change, sentiment and trading signals are not inferred from a single snapshot.</p>
    </main>
  );
}
