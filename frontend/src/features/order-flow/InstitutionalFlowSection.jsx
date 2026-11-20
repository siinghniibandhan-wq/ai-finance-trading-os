import React, { useCallback, useEffect, useState } from "react";
import { loadInstitutionalFlow } from "../advanced-chart/api";

const number = (value) => Number.isFinite(Number(value))
  ? new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(Number(value))
  : "—";

export default function InstitutionalFlowSection() {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (document.visibilityState !== "visible") return;
    try {
      const next = await loadInstitutionalFlow();
      setPayload(next);
      setError("");
    } catch (requestError) {
      setError(requestError?.message || "Institutional flow is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 15 * 60 * 1000);
    const onVisibility = () => {
      if (document.visibilityState === "visible") refresh();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [refresh]);

  const rows = Array.isArray(payload?.rows) ? payload.rows : [];
  const scale = Math.max(1, ...rows.flatMap(row => [
    Number(row.buy_value_crore) || 0,
    Number(row.sell_value_crore) || 0,
    Math.abs(Number(row.net_value_crore) || 0),
  ]));

  return (
    <section className="mfb-section mfb-institutional" aria-labelledby="mfb-institutional-title">
      <div className="mfb-section-head">
        <div>
          <small>04 / INSTITUTIONAL ACTIVITY</small>
          <h2 id="mfb-institutional-title">FII / FPI and DII flow</h2>
          <p>Daily cash-market purchases, sales and net activity reported by NSE. This is a daily report, not an intraday signal.</p>
        </div>
        <span className="mfb-poll">REST refresh · 15 minutes while visible</span>
      </div>
      {loading && !payload && <p className="mfb-note" role="status">Loading the latest NSE institutional report…</p>}
      {error && <p className="mfb-alert" role="alert">{error}{payload ? " · Showing the last successful report." : ""}</p>}
      {payload && (
        <>
          <div className="mfb-institutional-meta">
            <strong>Report date: {payload.report_date || "Not supplied"}</strong>
            <span>{payload.provisional ? "Provisional exchange data" : "Exchange status not supplied"}</span>
            <span>Values in ₹ crore</span>
          </div>
          <div className="mfb-institutional-grid">
            {["FII/FPI", "DII"].map(type => {
              const row = rows.find(item => item.investor_type === type);
              if (!row) return (
                <div className="mfb-institutional-row" key={type}>
                  <h3>{type}</h3><p className="mfb-note">No validated row returned for this category.</p>
                </div>
              );
              const net = Number(row.net_value_crore);
              return (
                <article className="mfb-institutional-row" key={type}>
                  <div className="mfb-institutional-row-head">
                    <h3>{type}</h3>
                    <strong className={net >= 0 ? "up" : "down"}>{net >= 0 ? "+" : ""}₹{number(net)} Cr net</strong>
                  </div>
                  <div className="mfb-institutional-bar-line">
                    <span>Buy</span><div className="mfb-institutional-track"><i className="buy" style={{ width: `${Math.max(0, Number(row.buy_value_crore) / scale * 100)}%` }}/></div>
                    <b>₹{number(row.buy_value_crore)}</b>
                  </div>
                  <div className="mfb-institutional-bar-line">
                    <span>Sell</span><div className="mfb-institutional-track"><i className="sell" style={{ width: `${Math.max(0, Number(row.sell_value_crore) / scale * 100)}%` }}/></div>
                    <b>₹{number(row.sell_value_crore)}</b>
                  </div>
                  <div className="mfb-institutional-net">
                    <span>Net flow</span>
                    <div className="mfb-institutional-zero"><i className={net >= 0 ? "positive" : "negative"} style={{ width: `${Math.min(50, Math.abs(net) / scale * 50)}%` }}/></div>
                    <b className={net >= 0 ? "up" : "down"}>{net >= 0 ? "+" : ""}{number(net)}</b>
                  </div>
                </article>
              );
            })}
          </div>
          <div className="mfb-institutional-foot">
            <span>Source: <a href={payload.source?.url || "https://www.nseindia.com/reports/fii-dii/"} target="_blank" rel="noreferrer">NSE India</a></span>
            <span>Retrieved {payload.retrieved_at ? new Date(payload.retrieved_at).toLocaleString("en-IN") : "—"}</span>
            <span>Daily data · not a live market feed</span>
          </div>
        </>
      )}
      {!loading && !payload && !error && <p className="mfb-note">Institutional report is not available.</p>}
    </section>
  );
}
