// ============================================================
// FINANCIAL OS — WEALTH MANAGER
// Phase 1: Central financial cards and source-backed breakdowns.
// This component reads existing APIs; it does not write to the DB.
// ============================================================

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE_URL, apiFetch, getCurrentUserId } from "./api";
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
  LineChart,
  ArrowUpRight,
  BellRing,
  Target,
  Sparkles,
  PieChart,
  Receipt,
  WalletCards,
  CircleAlert,
} from "lucide-react";

const USER_ID = getCurrentUserId();
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
  const response = await apiFetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
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

// Navigation actions appear only where the current application has a destination.
function BreakdownAction({ children, onClick }) {
  return (
    <button className="wc-breakdown-action" type="button" onClick={onClick}>
      {children} <span aria-hidden="true">→</span>
    </button>
  );
}

function BreakdownPanel({ activeCard, data, onClose, onNavigate, onSelectCard }) {
  const [expandedLiabilityType, setExpandedLiabilityType] = useState(null);
  if (!activeCard) return null;

  const cash = numberValue(data.summary?.cash?.total_balance);
  const investments = numberValue(data.summary?.investments?.current_value);
  const receivables = numberValue(data.receivables?.total_receivable);
  const assets = cash + investments + receivables;
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
          <p className="card-label">WEALTH MANAGER / DETAILS</p>
          <h3>{titleMap[activeCard]}</h3>
        </div>
        <button className="wc-close-button" type="button" onClick={onClose}>Close details</button>
      </div>

      {activeCard === "Net Worth" && (
        <>
          <DetailRow label="Recorded assets currently available" value={money(assets)} note="Cash/account balances, investments and outstanding receivables" />
          <DetailRow label="Outstanding liabilities" value={money(liabilities)} />
          <div className="wc-total-row"><span>Estimated net worth from available records</span><strong>{money(netWorth)}</strong></div>
          <div className="wc-breakdown-actions">
            <BreakdownAction onClick={() => onSelectCard("Total Assets")}>View asset breakdown</BreakdownAction>
            <BreakdownAction onClick={() => onSelectCard("Total Liabilities")}>View liability breakdown</BreakdownAction>
          </div>
          <p className="wc-note">This is a preliminary calculation. It may exclude assets or liabilities not yet recorded in the connected modules. Historical net worth will be added after we verify the available historical records.</p>
        </>
      )}

      {activeCard === "Total Assets" && (
        <>
          <div className="wc-breakdown-category">
            <div className="wc-breakdown-category-main">
              <div><strong>Cash &amp; account balances</strong><small>Recorded cash held across your accounts</small></div>
              <strong>{money(cash)}</strong>
            </div>
            <div className="wc-breakdown-actions">
              <BreakdownAction onClick={() => onNavigate("Accounts")}>View account details</BreakdownAction>
            </div>
          </div>
          <div className="wc-breakdown-category">
            <div className="wc-breakdown-category-main">
              <div><strong>Investments</strong><small>{numberValue(data.summary?.investments?.holding_count)} recorded holdings · current value</small></div>
              <strong>{money(investments)}</strong>
            </div>
            <div className="wc-breakdown-actions">
              <BreakdownAction onClick={() => onNavigate("Portfolio")}>View portfolio</BreakdownAction>
              <BreakdownAction onClick={() => onNavigate("Holdings")}>View holdings</BreakdownAction>
            </div>
          </div>
          <div className="wc-breakdown-category">
            <div className="wc-breakdown-category-main">
              <div><strong>Outstanding receivables</strong><small>Money owed to you, net of recorded settlements</small></div>
              <strong>{money(receivables)}</strong>
            </div>
            <div className="wc-breakdown-actions">
              <BreakdownAction onClick={() => onNavigate("Transactions")}>Review receivables</BreakdownAction>
              <BreakdownAction onClick={() => onNavigate("Loans & Liabilities")}>Review loans given</BreakdownAction>
            </div>
          </div>
          <div className="wc-total-row"><span>Recorded assets included in this phase</span><strong>{money(assets)}</strong></div>
          <p className="wc-note">This breakdown includes the asset values returned by the current Financial Summary API. Separate categories such as FDs/RDs, bonds, gold, and real estate will appear only after their data sources are verified to avoid double-counting.</p>
        </>
      )}

      {activeCard === "Total Liabilities" && (
        <>
          {(() => {
            const activeLiabilities = (data.liabilities?.liabilities || [])
              .filter((item) => item.status !== "inactive" && numberValue(item.outstanding_amount) > 0);
            const grouped = new Map();
            activeLiabilities.forEach((item) => {
              const category = item.liability_type || "Other liabilities";
              if (!grouped.has(category)) grouped.set(category, []);
              grouped.get(category).push(item);
            });
            return grouped.size ? [...grouped.entries()].map(([category, items]) => {
              const total = items.reduce((sum, item) => sum + numberValue(item.outstanding_amount), 0);
              const expanded = expandedLiabilityType === category;
              return (
                <div className="wc-breakdown-category" key={category}>
                  <div className="wc-breakdown-category-main">
                    <div><strong>{category}</strong><small>{items.length} recorded {items.length === 1 ? "liability" : "liabilities"}</small></div>
                    <strong>{money(total)}</strong>
                  </div>
                  <div className="wc-breakdown-actions">
                    <BreakdownAction onClick={() => setExpandedLiabilityType(expanded ? null : category)}>
                      {expanded ? "Hide records" : "View details"}
                    </BreakdownAction>
                  </div>
                  {expanded && (
                    <div className="wc-liability-record-list">
                      {items.map((item) => (
                        <div className="wc-liability-record" key={item.id}>
                          <div><strong>{item.name || category}</strong><small>Original amount: {money(item.original_amount)} · Status: {item.status || "active"}</small>
                            {item.due_date ? <small>Due date: {item.due_date}</small> : null}
                            {item.notes ? <small>{item.notes}</small> : null}
                          </div>
                          <strong>{money(item.outstanding_amount)}</strong>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            }) : <div className="wc-empty-detail">No outstanding liabilities were returned by the existing liabilities API.</div>;
          })()}
          <div className="wc-total-row"><span>Total outstanding liabilities</span><strong>{money(liabilities)}</strong></div>
          <p className="wc-note">The current app has a liabilities API but no dedicated Loans &amp; Liabilities management page in its navigation. For now, View Details expands the recorded liability entries here; we can add a dedicated management screen later if you want. Linked loan/liability records must be counted only once.</p>
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
          <div className="wc-breakdown-actions">
            <BreakdownAction onClick={() => onNavigate("Tax")}>Open Tax Centre</BreakdownAction>
          </div>
          <p className="wc-note">The connected tax engine currently reports liability status and missing income heads. Its estimate may be provisional because salary, house-property, and business/professional income are not yet available. This page will not label a provisional calculation as a final tax demand. Open the existing Tax Centre for its full scope and limitations.</p>
        </>
      )}
    </section>
  );
}


// ============================================================
// PHASE 2 — CHART HELPERS
// SVG charts are used so this feature does not add a dependency.
// ============================================================

export default function WealthManager({ onNavigate = () => {} }) {
  const [data, setData] = useState({ summary: null, liabilities: null, taxLiability: null, receivables: null, transactions: [] });
  const [analysisPeriod, setAnalysisPeriod] = useState("12");
  const [analysisChart, setAnalysisChart] = useState("income-expense");
  // Keep the Wealth Manager estimate aligned with the user's explicit regime selection.
  const [taxRegime, setTaxRegime] = useState("new");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errors, setErrors] = useState([]);
  const [activeCard, setActiveCard] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [supportNumber, setSupportNumber] = useState(() => window.localStorage.getItem("wealth-manager-whatsapp-number") || "");
  const [showWillGuide, setShowWillGuide] = useState(false);
  const [analysisVisual, setAnalysisVisual] = useState("bar");

  const loadWealthData = useCallback(async ({ quiet = false } = {}) => {
    if (quiet) setRefreshing(true);
    else setLoading(true);
    setErrors([]);

    const requests = await Promise.allSettled([
      getJson(`/api/financial-summary/?user_id=${USER_ID}`),
      getJson(`/api/liabilities?user_id=${USER_ID}`),
      getJson(`/api/final-tax-liability/?user_id=${USER_ID}&financial_year=${FINANCIAL_YEAR}&tax_regime=${encodeURIComponent(taxRegime)}&residential_status=resident&stt_confirmed=false`),
      getJson(`/api/transactions/receivables-payables`),
      getJson(`/api/transactions/`),
    ]);

    const nextData = {
      summary: requests[0].status === "fulfilled" ? requests[0].value : null,
      liabilities: requests[1].status === "fulfilled" ? requests[1].value : null,
      taxLiability: requests[2].status === "fulfilled" ? requests[2].value : null,
      receivables: requests[3].status === "fulfilled" ? requests[3].value : null,
      transactions: requests[4].status === "fulfilled" && Array.isArray(requests[4].value) ? requests[4].value : [],
    };
    setData(nextData);

    const labels = ["Financial Summary", "Liabilities", "Tax estimate", "Receivables", "Transactions"];
    const failed = requests
      .map((result, index) => result.status === "rejected" && index < 3 ? `${labels[index]}: ${result.reason?.message || "Unable to load"}` : null)
      .filter(Boolean);
    setErrors(failed);
    setLastUpdated(new Date());
    setLoading(false);
    setRefreshing(false);
  }, [taxRegime]);

  useEffect(() => {
    loadWealthData();
    const handleTransactionChange = () => loadWealthData({ quiet: true });
    window.addEventListener("financial-os:transactions-changed", handleTransactionChange);
    return () => window.removeEventListener("financial-os:transactions-changed", handleTransactionChange);
  }, [loadWealthData]);

  const totals = useMemo(() => {
    const cash = numberValue(data.summary?.cash?.total_balance);
    const investments = numberValue(data.summary?.investments?.current_value);
    const receivables = numberValue(data.receivables?.total_receivable);
    const assets = cash + investments + receivables;
    const liabilities = numberValue(data.liabilities?.total_outstanding);
    return { cash, investments, receivables, assets, liabilities, netWorth: assets - liabilities };
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
    { title: "Total Assets", value: totals.assets, subtitle: "Cash + investments + receivables", icon: Wallet, tone: "blue" },
    { title: "Total Liabilities", value: totals.liabilities, subtitle: "Outstanding recorded balances", icon: Landmark, tone: "orange" },
    { title: "Tax Overview", value: taxAmount === undefined ? null : numberValue(taxAmount), subtitle: taxAmount === undefined ? "Estimate unavailable" : `Tax engine · FY ${FINANCIAL_YEAR}`, icon: ReceiptText, tone: "pink" },
  ];

  const attentionItems = useMemo(() => {
    const items = [];
    if (errors.length) items.push({
      tone: "warning",
      title: "Some financial data needs attention",
      detail: `${errors.length} data source${errors.length === 1 ? "" : "s"} could not be loaded. Review the message above.`,
      action: "Refresh data",
      onClick: () => loadWealthData({ quiet: true }),
    });
    if (numberValue(data.liabilities?.total_outstanding) > 0) items.push({
      tone: "orange",
      title: "Liabilities to keep in view",
      detail: `${money(data.liabilities.total_outstanding)} in outstanding recorded liabilities.`,
      action: "Review liabilities",
      destination: "Loans & Liabilities",
    });
    if (data.taxLiability) items.push({
      tone: "pink",
      title: "Tax review reminder",
      detail: `Review the tax calculation and filing obligations for FY ${FINANCIAL_YEAR}.`,
      action: "Open Tax",
      destination: "Tax",
    });
    return items.slice(0, 5);
  }, [errors, data.liabilities, data.taxLiability, loadWealthData]);

  const quickLinks = [
    { title: "Money", subtitle: "Accounts & transactions", destination: "Accounts", Icon: WalletCards, tone: "purple" },
    { title: "Invest", subtitle: "Portfolio & holdings", destination: "Portfolio", Icon: TrendingUp, tone: "green" },
    { title: "Plan", subtitle: "Goals & contributions", destination: "Goals", Icon: Target, tone: "blue" },
    { title: "Markets", subtitle: "Prices & market data", destination: "Markets", Icon: LineChart, tone: "orange" },
    { title: "AI", subtitle: "Assistant & insights", destination: "AI Assistant", Icon: Sparkles, tone: "pink" },
    { title: "Tax", subtitle: "Tax records & reports", destination: "Tax", Icon: Receipt, tone: "blue" },
  ];

  const cashShare = totals.assets > 0 ? Math.min(100, Math.max(0, (totals.cash / totals.assets) * 100)) : 0;
  const investmentShare = totals.assets > 0 ? Math.min(100, Math.max(0, (totals.investments / totals.assets) * 100)) : 0;
  const receivableShare = totals.assets > 0 ? Math.min(100, Math.max(0, (totals.receivables / totals.assets) * 100)) : 0;
  const analysisMonths = useMemo(() => {
    const count = analysisPeriod === "lifetime" ? 60 : Number(analysisPeriod);
    const now = new Date();
    const months = [];
    for (let offset = count - 1; offset >= 0; offset -= 1) {
      const date = new Date(now.getFullYear(), now.getMonth() - offset, 1);
      months.push({ key: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`, label: date.toLocaleDateString("en-IN", { month: "short", year: count > 12 ? "2-digit" : undefined }), income: 0, expenses: 0, net: 0 });
    }
    const lookup = new Map(months.map((month) => [month.key, month]));
    (data.transactions || []).forEach((tx) => {
      const dateValue = tx.transaction_date || tx.date;
      if (!dateValue) return;
      const date = new Date(dateValue);
      if (Number.isNaN(date.getTime())) return;
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
      const bucket = lookup.get(key);
      if (!bucket) return;
      const type = String(tx.transaction_type || tx.type || "").toLowerCase();
      const amount = numberValue(tx.amount);
      if (type === "income") bucket.income += amount;
      if (type === "expense") bucket.expenses += amount;
      bucket.net = bucket.income - bucket.expenses;
    });
    return months;
  }, [data.transactions, analysisPeriod]);
  const chartMax = Math.max(1, ...analysisMonths.flatMap((month) => [month.income, month.expenses, Math.abs(month.net)]));
  const liabilityRatio = totals.assets > 0 ? (totals.liabilities / totals.assets) * 100 : null;

  return (
    <div className="wealth-centre">
      <section className="wc-welcome">
        <div>
          <p className="card-label">FINANCIAL OS / WEALTH</p>
          <h2>Wealth <span>Manager</span></h2>
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

      {activeCard && <BreakdownPanel activeCard={activeCard} data={data} onClose={() => setActiveCard(null)} onNavigate={onNavigate} onSelectCard={setActiveCard} />}

      <section className="wc-wealth-analysis-grid" aria-label="Recorded wealth composition">
        <article className="glass-card wc-info-panel wc-asset-composition">
          <div className="wc-panel-heading"><div><p className="card-label">ASSET ALLOCATION</p><h3>Recorded wealth composition</h3></div><PieChart size={19} /></div>
          <p className="wc-chart-subtitle">Each amount is shown once. Select a category to open its records.</p>
          <div className="wc-wealth-mix-list">
            <button type="button" className="wc-wealth-mix-row wc-mix-clickable" onClick={() => onNavigate("Accounts")} aria-label={`Open cash and account balances: ${money(totals.cash)}`}>
              <span className="wc-wealth-mix-label"><span>Cash &amp; accounts</span><strong>{money(totals.cash)} · {cashShare.toFixed(1)}%</strong></span><span className="wc-wealth-mix-track"><span className="cash" style={{ width: `${cashShare}%` }} /></span><span className="wc-mix-action">Manage accounts →</span>
            </button>
            <button type="button" className="wc-wealth-mix-row wc-mix-clickable" onClick={() => onNavigate("Portfolio")} aria-label={`Open investments: ${money(totals.investments)}`}>
              <span className="wc-wealth-mix-label"><span>Investments</span><strong>{money(totals.investments)} · {investmentShare.toFixed(1)}%</strong></span><span className="wc-wealth-mix-track"><span className="investments" style={{ width: `${investmentShare}%` }} /></span><span className="wc-mix-action">Open portfolio →</span>
            </button>
            <button type="button" className="wc-wealth-mix-row wc-mix-clickable" onClick={() => onNavigate("Transactions")} aria-label={`Open receivables: ${money(totals.receivables)}`}>
              <span className="wc-wealth-mix-label"><span>Receivables · owed to you</span><strong>{money(totals.receivables)} · {receivableShare.toFixed(1)}%</strong></span><span className="wc-wealth-mix-track"><span className="receivables" style={{ width: `${receivableShare}%` }} /></span><span className="wc-mix-action">View receivables →</span>
            </button>
          </div>
          <div className="wc-total-row"><span>Total recorded assets</span><strong>{money(totals.assets)}</strong></div>
          <div className="wc-investment-performance"><div><span>Investment profit / loss</span><strong>{(() => { const inv = data.summary?.investments || {}; const cost = inv.invested_value ?? inv.total_invested ?? inv.invested_amount ?? inv.cost_basis; return cost === undefined || cost === null ? "Cost basis unavailable" : money(totals.investments - numberValue(cost)); })()}</strong></div><small>Calculated only when the existing summary provides a recorded investment cost basis; no profit is inferred from market value alone.</small></div>
          <p className="wc-note">Assets include cash/account balances, current investments and outstanding receivables. Loans and other liabilities are shown separately in the Total Liabilities card above, so they are not mixed into asset allocation.</p>
          <div className="wc-breakdown-actions"><BreakdownAction onClick={() => setActiveCard("Total Assets")}>Detailed asset records</BreakdownAction><BreakdownAction onClick={() => setActiveCard("Total Liabilities")}>Loans &amp; liabilities</BreakdownAction></div>
        </article>
      </section>

      <section className="glass-card wc-info-panel wc-lifetime-analysis" aria-label="Lifetime income and expense analysis">
        <div className="wc-panel-heading">
          <div><p className="card-label">LIFETIME VIEW / CASH FLOW</p><h3>Income, expenses & cash flow</h3><p className="wc-chart-subtitle">Explore available transaction history. Historical periods without recorded transactions remain zero rather than being estimated.</p></div>
          <LineChart size={19} />
        </div>
        <div className="wc-analysis-controls">
          <label>Period <select value={analysisPeriod} onChange={(event) => setAnalysisPeriod(event.target.value)} aria-label="Historical analysis period">
            <option value="1">1 month</option><option value="3">3 months</option><option value="6">6 months</option><option value="12">1 year</option><option value="36">3 years</option><option value="60">5 years</option><option value="lifetime">Lifetime (up to 5 years)</option>
          </select></label>
          <label>Data view <select value={analysisChart} onChange={(event) => setAnalysisChart(event.target.value)} aria-label="Income expense or cash flow view">
            <option value="income-expense">Income vs expenses</option><option value="net">Net cash flow</option><option value="income">Income only</option><option value="expenses">Expenses only</option>
          </select></label>
          <label>Graph style <select value={analysisVisual} onChange={(event) => setAnalysisVisual(event.target.value)} aria-label="Graph style">
            <option value="bar">Bar graph</option><option value="line">Line graph</option><option value="pie">Pie chart · asset mix</option>
          </select></label>
        </div>
        <div className="wc-analysis-summary">
          <div><span>Total income in period</span><strong>{money(analysisMonths.reduce((sum, month) => sum + month.income, 0))}</strong></div>
          <div><span>Total expenses in period</span><strong>{money(analysisMonths.reduce((sum, month) => sum + month.expenses, 0))}</strong></div>
          <div><span>Net cash flow</span><strong>{money(analysisMonths.reduce((sum, month) => sum + month.income - month.expenses, 0))}</strong></div>
        </div>
        {analysisVisual === "pie" ? (
          <div className="wc-pie-chart-wrap">
            <div className="wc-asset-pie" role="img" aria-label={`Asset mix: cash ${cashShare.toFixed(1)} percent, investments ${investmentShare.toFixed(1)} percent, receivables ${receivableShare.toFixed(1)} percent`} style={{ background: `conic-gradient(#38bdf8 0% ${cashShare}%, #a78bfa ${cashShare}% ${cashShare + investmentShare}%, #34d399 ${cashShare + investmentShare}% 100%)` }}><span>{money(totals.assets)}<small>Total assets</small></span></div>
            <div className="wc-pie-legend"><span><i className="cash" />Cash &amp; accounts <strong>{money(totals.cash)}</strong></span><span><i className="investments" />Investments <strong>{money(totals.investments)}</strong></span><span><i className="receivables" />Receivables <strong>{money(totals.receivables)}</strong></span></div>
          </div>
        ) : data.transactions.length === 0 ? <div className="wc-chart-empty">No transaction history was returned by the existing API. Add or review records in <button type="button" className="wc-inline-link" onClick={() => onNavigate("Transactions")}>Transactions</button>.</div> : (
          <div className={`wc-history-chart ${analysisVisual === "line" ? "wc-line-chart" : ""}`} role="img" aria-label={`${analysisVisual} chart for selected ${analysisChart} data`}>
            {analysisMonths.map((month) => {
              const values = analysisChart === "income-expense" ? [month.income, month.expenses] : [analysisChart === "income" ? month.income : analysisChart === "expenses" ? month.expenses : Math.abs(month.net)];
              const pointValue = analysisChart === "income" ? month.income : analysisChart === "expenses" ? month.expenses : month.net;
              const maxForView = Math.max(1, ...analysisMonths.flatMap((item) => analysisChart === "income-expense" ? [item.income, item.expenses] : [Math.abs(analysisChart === "income" ? item.income : analysisChart === "expenses" ? item.expenses : item.net)]));
              return <button type="button" className="wc-history-column" key={month.key} title={`${month.label}: income ${money(month.income)}, expenses ${money(month.expenses)}, net ${money(month.net)}`} onClick={() => onNavigate("Transactions")} aria-label={`Open transactions for ${month.label}`}>
                <span className="wc-history-bars">{values.map((value, index) => <i key={index} className={analysisChart === "net" ? (month.net >= 0 ? "net-positive" : "net-negative") : index === 0 ? "income" : "expense"} style={{ height: `${Math.max(value > 0 ? 3 : 0, Math.min(100, Math.abs(value) / maxForView * 100))}%` }} />)}</span>
                <span className="wc-line-point" style={{ bottom: `${Math.max(0, Math.min(100, (pointValue + maxForView) / (2 * maxForView) * 100))}%` }} />
                <small>{month.label}</small>
              </button>;
            })}
          </div>
        )}
        <p className="wc-note">Tap any month to open transaction records. This is a transaction-based cash-flow view, not historical net worth. Only dated income and expense transactions are included; transfers, receivables, payables and investment valuation changes are not treated as income or expense.</p>
        <div className="wc-breakdown-actions"><BreakdownAction onClick={() => onNavigate("Transactions")}>Explore transactions</BreakdownAction><BreakdownAction onClick={() => onNavigate("Categories")}>Explore categories</BreakdownAction><BreakdownAction onClick={() => onNavigate("Accounts")}>Explore accounts</BreakdownAction></div>
      </section>

        <article className="glass-card wc-info-panel wc-accent-card wc-alerts-panel">
          <div className="wc-panel-heading">
            <div><p className="card-label">ALERTS & NOTIFICATIONS</p><h3>Items needing attention</h3><p className="wc-chart-subtitle">Reminders and data-quality notices from your current financial records.</p></div>
            <BellRing size={19} />
          </div>
          {attentionItems.length ? (
            <div className="wc-alert-list">
              {attentionItems.map((item, index) => (
                <div className={`wc-alert-item ${item.tone}`} key={`${item.title}-${index}`}>
                  <span className="wc-alert-symbol">{item.tone === "warning" ? <CircleAlert size={16} /> : <BellRing size={16} />}</span>
                  <div className="wc-alert-content">
                    <strong>{item.title}</strong>
                    <p>{item.detail}</p>
                    <button type="button" onClick={() => item.destination ? onNavigate(item.destination) : item.onClick?.()}>{item.action} →</button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="wc-chart-empty">No immediate alerts from the currently loaded records.</div>
          )}
        </article>

      <section className="wc-support-grid" aria-label="Legacy planning and customer support">
        <article className="glass-card wc-info-panel"><div className="wc-panel-heading"><div><p className="card-label">ESTATE PLANNING</p><h3>Create a will</h3></div><ReceiptText size={19} /></div>
          <p className="wc-chart-subtitle">Start an organised will-planning checklist. This is preparation support, not a legally executed will.</p>
          <ul className="wc-will-checklist"><li>List assets, accounts, investments and liabilities.</li><li>Record intended beneficiaries and guardians, where applicable.</li><li>Choose an executor and seek qualified legal advice on signing and witnesses.</li></ul>
          <button type="button" className="primary-button" onClick={() => setShowWillGuide(!showWillGuide)}>{showWillGuide ? "Hide checklist" : "Start will checklist"} →</button>
          {showWillGuide && <div className="wc-will-guidance" role="status"><strong>Before you begin</strong><p>Collect asset statements, beneficiary details and your chosen executor details. Requirements vary by jurisdiction; have the final document reviewed by a qualified legal professional. Do not enter sensitive identity details into this overview.</p></div>}
        </article>
        <article className="glass-card wc-info-panel"><div className="wc-panel-heading"><div><p className="card-label">CUSTOMER SUPPORT</p><h3>WhatsApp contact</h3></div><WalletCards size={19} /></div>
          <p className="wc-chart-subtitle">Add your business WhatsApp number once on this device to enable direct contact.</p>
          <label className="wc-whatsapp-label" htmlFor="wealth-whatsapp-number">WhatsApp number with country code</label>
          <input id="wealth-whatsapp-number" className="wc-whatsapp-input" type="tel" inputMode="tel" placeholder="e.g. 919876543210" value={supportNumber} onChange={(event) => { const next = event.target.value; setSupportNumber(next); window.localStorage.setItem("wealth-manager-whatsapp-number", next); }} />
          <button type="button" className="primary-button" disabled={!/^[0-9]{8,15}$/.test(supportNumber.replace(/[^0-9]/g, ""))} onClick={() => window.open(`https://wa.me/${supportNumber.replace(/[^0-9]/g, "")}?text=${encodeURIComponent("Hello, I would like support with my wealth overview.")}`, "_blank", "noopener,noreferrer")}>Contact on WhatsApp ↗</button>
          <small className="wc-note">The number is stored in this browser only. It is not sent to the Financial OS backend.</small>
        </article>
      </section>

      {/* Cross-module navigation remains inside Wealth Manager; no separate Dashboard is created. */}
      <section className="glass-card wc-info-panel wc-accent-card wc-shortcuts-panel">
        <div className="wc-panel-heading">
          <div><p className="card-label">CROSS-MODULE SHORTCUTS</p><h3>Your financial workspace</h3><p className="wc-chart-subtitle">Jump directly to an existing module.</p></div>
          <Landmark size={19} />
        </div>
        <div className="wc-shortcut-grid">
          {quickLinks.map(({ title, subtitle, destination, Icon, tone }) => (
            <button className={`wc-shortcut-tile ${tone}`} type="button" key={title} onClick={() => onNavigate(destination)}>
              <span className="wc-shortcut-icon"><Icon size={17} /></span>
              <span><strong>{title}</strong><small>{subtitle}</small></span>
              <ArrowUpRight size={15} className="wc-shortcut-arrow" />
            </button>
          ))}
        </div>
        <p className="wc-note">Market, investment and tax details are shown only when their dedicated modules or APIs provide them. Use these shortcuts to open each module.</p>
      </section>
    </div>
  );
}
