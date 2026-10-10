// ============================================================
// FINANCIAL OS — WEALTH CENTRE
// Phase 1: Central financial cards and source-backed breakdowns.
// This component reads existing APIs; it does not write to the DB.
// ============================================================

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Wallet,
  TrendingUp,
  Landmark,
  ReceiptText,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

const API_BASE_URL = "https://ai-finance-trading-os-api.onrender.com";
const USER_ID = 1;
const FINANCIAL_YEAR = "2026-27";

const money = (value) => new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
}).format(Number(value) || 0);

const numberValue = (value) => {
  const result = Number(value);
  return Number.isFinite(result) ? result : 0;
};

async function getJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    const message = await response.text().catch(() => "");
    throw new Error(message || `Request failed (${response.status})`);
  }
  return response.json();
}

function DetailRow({ label, value, note }) {
  return (
    <div className="wc-detail-row">
      <div>
        <span>{label}</span>
        {note ? <small>{note}</small> : null}
      </div>
      <strong>{value}</strong>
    </div>
  );
}

function BreakdownPanel({ activeCard, data, onClose }) {
  if (!activeCard) return null;

  const cash = numberValue(data.summary?.cash?.total_balance);
  const investments = numberValue(data.summary?.investments?.current_value);
  const assets = cash + investments;
  const liabilities = numberValue(data.liabilities?.total_outstanding);
  const netWorth = assets - liabilities;
  const tax = data.taxLiability || {};
  const taxSummary = tax.final_tax || tax.tax_summary || tax.summary || tax.tax?.summary || {};
  const taxTotal = taxSummary.total_tax_payable
    ?? taxSummary.total_tax_liability
    ?? taxSummary.total_tax
    ?? taxSummary.tax_payable
    ?? taxSummary.tax_plus_cess
    ?? taxSummary.final_tax_liability;
  const taxPaid = taxSummary.tds_paid ?? taxSummary.advance_tax_paid ?? taxSummary.tax_paid;
  const taxDue = taxSummary.net_tax_payable ?? taxSummary.remaining_tax_payable ?? taxSummary.balance_tax_payable;

  const titleMap = {
    "Net Worth": "Net worth calculation",
    "Total Assets": "Recorded asset breakdown",
    "Total Liabilities": "Outstanding liabilities",
    "Tax Overview": "Tax estimate breakdown",
  };

  return (
    <section className="wc-breakdown glass-card" aria-live="polite">
      <div className="wc-breakdown-heading">
        <div>
          <p className="card-label">WEALTH CENTRE / DETAILS</p>
          <h3>{titleMap[activeCard]}</h3>
        </div>
        <button className="wc-close-button" type="button" onClick={onClose}>Close details</button>
      </div>

      {activeCard === "Net Worth" && (
        <>
          <DetailRow label="Recorded assets currently available" value={money(assets)} note="Cash/account balances plus current investment value" />
          <DetailRow label="Outstanding liabilities" value={money(liabilities)} />
          <div className="wc-total-row"><span>Estimated net worth from available records</span><strong>{money(netWorth)}</strong></div>
          <p className="wc-note">This is a preliminary calculation. It may exclude assets or liabilities not yet recorded in the connected modules. Historical net worth will be added after we verify the available historical records.</p>
        </>
      )}

      {activeCard === "Total Assets" && (
        <>
          <DetailRow label="Cash and account balances" value={money(cash)} />
          <DetailRow label="Investments — current value" value={money(investments)} note={`${numberValue(data.summary?.investments?.holding_count)} recorded holdings`} />
          <div className="wc-total-row"><span>Recorded assets included in this phase</span><strong>{money(assets)}</strong></div>
          <p className="wc-note">This breakdown includes the asset values returned by the current Financial Summary API. We will add separate categories such as FDs/RDs, bonds, gold, real estate, and other assets only after verifying their existing data sources and preventing double-counting.</p>
        </>
      )}

      {activeCard === "Total Liabilities" && (
        <>
          {(data.liabilities?.liabilities || []).filter((item) => item.status !== "inactive" && numberValue(item.outstanding_amount) > 0).length > 0 ? (
            (data.liabilities.liabilities || [])
              .filter((item) => item.status !== "inactive" && numberValue(item.outstanding_amount) > 0)
              .map((item) => (
                <DetailRow key={item.id} label={item.name || item.liability_type || "Liability"} value={money(item.outstanding_amount)} note={item.liability_type || "Recorded liability"} />
              ))
          ) : (
            <div className="wc-empty-detail">No outstanding liabilities were returned by the existing liabilities API.</div>
          )}
          <div className="wc-total-row"><span>Total outstanding liabilities</span><strong>{money(liabilities)}</strong></div>
          <p className="wc-note">Loan-linked liability records are taken from the liabilities endpoint once each. We will verify loan/liability relationships before expanding the breakdown to additional liability types.</p>
        </>
      )}

      {activeCard === "Tax Overview" && (
        <>
          {taxTotal !== undefined ? (
            <DetailRow label="Calculated tax amount returned by the existing tax engine" value={money(taxTotal)} note="Use the tax engine's own status and scope before treating this as final tax due." />
          ) : (
            <div className="wc-empty-detail">The tax engine did not return a recognized overall tax-total field. The existing Tax Centre remains available for the full report.</div>
          )}
          {taxPaid !== undefined && <DetailRow label="Tax paid / credited (as returned)" value={money(taxPaid)} />}
          {taxDue !== undefined && <DetailRow label="Remaining tax payable (as returned)" value={money(taxDue)} />}
          <DetailRow label="Financial year" value={FINANCIAL_YEAR} />
          <p className="wc-note">The connected tax engine currently reports liability status and missing income heads. Its estimate may be provisional because salary, house-property, and business/professional income are not yet available. This page will not label a provisional calculation as a final tax demand. Open the existing Tax Centre for its full scope and limitations.</p>
        </>
      )}
    </section>
  );
}

export default function WealthManager() {
  const [data, setData] = useState({ summary: null, liabilities: null, taxLiability: null });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errors, setErrors] = useState([]);
  const [activeCard, setActiveCard] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadWealthData = useCallback(async ({ quiet = false } = {}) => {
    if (quiet) setRefreshing(true);
    else setLoading(true);
    setErrors([]);

    const requests = await Promise.allSettled([
      getJson(`/api/financial-summary/?user_id=${USER_ID}`),
      getJson(`/api/liabilities?user_id=${USER_ID}`),
      getJson(`/api/final-tax-liability/?user_id=${USER_ID}&financial_year=${FINANCIAL_YEAR}&tax_regime=new&residential_status=resident&stt_confirmed=false`),
    ]);

    const nextData = {
      summary: requests[0].status === "fulfilled" ? requests[0].value : null,
      liabilities: requests[1].status === "fulfilled" ? requests[1].value : null,
      taxLiability: requests[2].status === "fulfilled" ? requests[2].value : null,
    };
    setData(nextData);

    const labels = ["Financial Summary", "Liabilities", "Tax estimate"];
    const failed = requests
      .map((result, index) => result.status === "rejected" ? `${labels[index]}: ${result.reason?.message || "Unable to load"}` : null)
      .filter(Boolean);
    setErrors(failed);
    setLastUpdated(new Date());
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    loadWealthData();
    const handleTransactionChange = () => loadWealthData({ quiet: true });
    window.addEventListener("financial-os:transactions-changed", handleTransactionChange);
    return () => window.removeEventListener("financial-os:transactions-changed", handleTransactionChange);
  }, [loadWealthData]);

  const totals = useMemo(() => {
    const cash = numberValue(data.summary?.cash?.total_balance);
    const investments = numberValue(data.summary?.investments?.current_value);
    const assets = cash + investments;
    const liabilities = numberValue(data.liabilities?.total_outstanding);
    return { cash, investments, assets, liabilities, netWorth: assets - liabilities };
  }, [data]);

  const tax = data.taxLiability || {};
  const taxSummary = tax.final_tax || tax.tax_summary || tax.summary || tax.tax?.summary || {};
  const taxAmount = taxSummary.total_tax_payable
    ?? taxSummary.total_tax_liability
    ?? taxSummary.total_tax
    ?? taxSummary.tax_payable
    ?? taxSummary.tax_plus_cess
    ?? taxSummary.final_tax_liability;

  const cards = [
    { title: "Net Worth", value: totals.netWorth, subtitle: "Assets minus liabilities", icon: TrendingUp, tone: "purple" },
    { title: "Total Assets", value: totals.assets, subtitle: "Cash + recorded investments", icon: Wallet, tone: "blue" },
    { title: "Total Liabilities", value: totals.liabilities, subtitle: "Outstanding recorded balances", icon: Landmark, tone: "orange" },
    { title: "Tax Overview", value: taxAmount === undefined ? null : numberValue(taxAmount), subtitle: taxAmount === undefined ? "Estimate unavailable" : `Tax engine · FY ${FINANCIAL_YEAR}`, icon: ReceiptText, tone: "pink" },
  ];

  return (
    <div className="wealth-centre">
      <section className="wc-welcome">
        <div>
          <p className="card-label">FINANCIAL OS / WEALTH</p>
          <h2>Wealth <span>Centre</span></h2>
          <p>Your central view of recorded wealth, liabilities, and tax information.</p>
          <small>{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}` : "Connecting to financial data…"}</small>
        </div>
        <button className="primary-button" type="button" onClick={() => loadWealthData({ quiet: true })} disabled={loading || refreshing}>
          <RefreshCw size={15} className={refreshing ? "wc-spin" : ""} /> {refreshing ? "Refreshing…" : "Refresh data"}
        </button>
      </section>

      {errors.length > 0 && (
        <div className="wc-error" role="alert">
          <AlertCircle size={18} />
          <div><strong>Some information could not be loaded.</strong><ul>{errors.map((error) => <li key={error}>{error}</li>)}</ul></div>
        </div>
      )}

      <section className="wc-primary-grid" aria-label="Primary financial summary">
        {cards.map((card) => {
          const Icon = card.icon;
          const selected = activeCard === card.title;
          return (
            <button
              key={card.title}
              type="button"
              className={`wc-primary-card wc-${card.tone} ${selected ? "selected" : ""}`}
              onClick={() => setActiveCard(selected ? null : card.title)}
              aria-expanded={selected}
            >
              <span className="wc-card-top"><span className="wc-card-icon"><Icon size={20} /></span>{selected ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</span>
              <span className="wc-card-label">{card.title}</span>
              <strong className="wc-card-value">{loading ? "Loading…" : card.value === null ? "Unavailable" : money(card.value)}</strong>
              <span className="wc-card-subtitle">{card.subtitle}</span>
              <span className="wc-card-action">{selected ? "Hide breakdown" : "View breakdown"} →</span>
            </button>
          );
        })}
      </section>

      {activeCard && <BreakdownPanel activeCard={activeCard} data={data} onClose={() => setActiveCard(null)} />}

      <section className="wc-section-grid">
        <article className="glass-card wc-info-panel">
          <div className="wc-panel-heading"><div><p className="card-label">CURRENT SNAPSHOT</p><h3>Cash & investments</h3></div><Wallet size={19} /></div>
          <DetailRow label="Cash and account balances" value={loading ? "Loading…" : money(totals.cash)} />
          <DetailRow label="Investment current value" value={loading ? "Loading…" : money(totals.investments)} />
          <div className="wc-total-row"><span>Combined recorded value</span><strong>{loading ? "Loading…" : money(totals.cash + totals.investments)}</strong></div>
          <p className="wc-note">This is a current snapshot, not historical cash position. Historical charting will be added after we verify transaction-history coverage.</p>
        </article>
        <article className="glass-card wc-info-panel">
          <div className="wc-panel-heading"><div><p className="card-label">TAX SNAPSHOT</p><h3>Tax estimate status</h3></div><ReceiptText size={19} /></div>
          <DetailRow label="Financial year" value={FINANCIAL_YEAR} />
          <DetailRow label="Tax engine response" value={data.taxLiability ? "Available" : loading ? "Loading…" : "Unavailable"} />
          <DetailRow label="Tax estimate" value={taxAmount === undefined ? "Not available" : money(taxAmount)} />
          <p className="wc-note">This amount is shown only when the existing tax engine returns a recognized total field. Review the tax calculation scope before treating it as final tax payable.</p>
          <div className="wc-tax-status"><CheckCircle2 size={15} /><span>Existing Tax Centre remains unchanged and available in the sidebar.</span></div>
        </article>
      </section>

      <section className="glass-card wc-next-phase">
        <div><p className="card-label">NEXT BUILD PHASE</p><h3>Cash Position & Cash Flow charts</h3><p>Next we'll add the 1M, 3M, 6M, 1Y, 2Y, 3Y and 5Y filters plus selectable Line, Bar and Area charts, using verified source data rather than fabricated history.</p></div>
        <span>Phase 2</span>
      </section>
    </div>
  );
}
