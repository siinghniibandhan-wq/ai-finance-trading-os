import React, { useEffect, useState } from "react";
import { loadCorporateActions } from "./api";

const displayDate = value => {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
};

const money = value => Number.isFinite(Number(value))
  ? `₹${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(Number(value))}`
  : null;

export default function CorporateActionsPanel({ instrument }) {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!instrument?.symbol || !instrument?.exchange) {
      setPayload(null);
      setError("");
      setLoading(false);
      return undefined;
    }
    let current = true;
    setPayload(null);
    setError("");
    setLoading(true);
    loadCorporateActions(instrument)
      .then(result => { if (current) setPayload(result); })
      .catch(requestError => { if (current) setError(requestError?.message || "Corporate actions could not be loaded."); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [instrument?.symbol, instrument?.exchange]);

  return (
    <section className="advanced-chart-corporate" aria-labelledby="advanced-chart-corporate-title">
      <div className="advanced-chart-corporate-heading">
        <div><span>INSTRUMENT EVENTS</span><h2 id="advanced-chart-corporate-title">Dividends &amp; corporate actions</h2></div>
        {instrument && <strong>{instrument.symbol} · {instrument.exchange}</strong>}
      </div>
      {!instrument && <p>Select an instrument to view its corporate actions.</p>}
      {loading && <p role="status">Loading exchange corporate actions…</p>}
      {error && <p role="alert">{error}</p>}
      {payload?.status === "unavailable" && <p>{payload.message}</p>}
      {payload?.status === "success" && !payload.actions?.length && <p>No matching corporate actions were returned by the exchange for the available two-year window.</p>}
      {payload?.actions?.length > 0 && (
        <div className="advanced-chart-corporate-list">
          {payload.actions.map((action, index) => (
            <article key={`${action.symbol}-${action.ex_date || action.record_date || "event"}-${index}`}>
              <div className="advanced-chart-corporate-event">
                <strong>{action.purpose}</strong>
                <span>{action.event_type}</span>
                {action.dividend_per_share !== null && action.dividend_per_share !== undefined && <b>{money(action.dividend_per_share)} per share</b>}
              </div>
              <dl>
                <div><dt>Ex-date</dt><dd>{displayDate(action.ex_date)}</dd></div>
                <div><dt>Record date</dt><dd>{displayDate(action.record_date)}</dd></div>
                <div><dt>Book closure</dt><dd>{action.book_closure_start || action.book_closure_end ? `${displayDate(action.book_closure_start)} – ${displayDate(action.book_closure_end)}` : "—"}</dd></div>
              </dl>
            </article>
          ))}
        </div>
      )}
      {payload?.source?.url && <a className="advanced-chart-corporate-source" href={payload.source.url} target="_blank" rel="noreferrer">View exchange source</a>}
      <p className="advanced-chart-corporate-note">Exchange-reported dates only. Dividend amounts appear only when explicitly stated in the source purpose. No payment date is inferred.</p>
    </section>
  );
}
