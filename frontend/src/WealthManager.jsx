// ============================================================
// FINANCIAL OS — WEALTH MANAGER
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
  LineChart,
  BarChart3,
  AreaChart,
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
          <p className="card-label">WEALTH MANAGER / DETAILS</p>
          <h3>{titleMap[activeCard]}</h3>
        </div>
        <button className="wc-close-button" type="button" onClick={onClose}>Close details</button>
      </div>

      {activeCard === "Net Worth" && (
        <>
          <DetailRow label="Recorded assets currently available" value={money(assets)} note="Cash/account balances plus current investment value" />
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

const PERIODS = [
  { key: "1M", months: 1, label: "1 month" },
  { key: "3M", months: 3, label: "3 months" },
  { key: "6M", months: 6, label: "6 months" },
  { key: "1Y", months: 12, label: "1 year" },
  { key: "2Y", months: 24, label: "2 years" },
  { key: "3Y", months: 36, label: "3 years" },
  { key: "5Y", months: 60, label: "5 years" },
];

const CHART_TYPES = [
  { key: "line", label: "Line", Icon: LineChart },
  { key: "bar", label: "Bar", Icon: BarChart3 },
  { key: "area", label: "Area", Icon: AreaChart },
];

const dateKey = (date) => {
  const d = new Date(date);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

const monthStart = (date) => new Date(date.getFullYear(), date.getMonth(), 1);
const addMonths = (date, count) => new Date(date.getFullYear(), date.getMonth() + count, 1);
const monthLabel = (key, short = true) => {
  const [year, month] = key.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("en-IN", {
    month: short ? "short" : "long",
    year: "2-digit",
  });
};

function WealthChart({ points, type, series, height = 220, emptyText }) {
  const width = 720;
  const pad = { top: 18, right: 14, bottom: 38, left: 52 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const values = points.flatMap((p) => series.map((s) => numberValue(p[s.key])));
  const maxValue = Math.max(1, ...values, 0);
  const minValue = Math.min(0, ...values);
  const range = Math.max(1, maxValue - minValue);
  const x = (i) => pad.left + (points.length <= 1 ? plotW / 2 : (i / (points.length - 1)) * plotW);
  const y = (v) => pad.top + ((maxValue - numberValue(v)) / range) * plotH;
  const barStep = plotW / Math.max(points.length, 1);
  const barW = Math.max(3, Math.min(24, barStep * (series.length > 1 ? 0.27 : 0.55)));
  const grid = [0, 0.25, 0.5, 0.75, 1];
  const shownLabels = points.length <= 6
    ? points.map((p, i) => i)
    : [0, Math.floor((points.length - 1) / 3), Math.floor(2 * (points.length - 1) / 3), points.length - 1];

  if (!points.length) return <div className="wc-chart-empty">{emptyText || "No recorded data for this period."}</div>;

  return (
    <div className="wc-chart-scroll">
      <svg className="wc-chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Financial trend chart">
        {grid.map((fraction) => {
          const val = maxValue - fraction * range;
          const yy = pad.top + fraction * plotH;
          return <g key={fraction}>
            <line x1={pad.left} y1={yy} x2={width - pad.right} y2={yy} stroke="rgba(226,232,240,.10)" strokeDasharray="3 4" />
            <text x={pad.left - 8} y={yy + 4} textAnchor="end" fill="rgba(226,232,240,.5)" fontSize="10">{Math.abs(val) >= 100000 ? `${(val / 100000).toFixed(1)}L` : Math.abs(val) >= 1000 ? `${(val / 1000).toFixed(1)}k` : Math.round(val)}</text>
          </g>;
        })}
        {type === "bar" && points.map((point, i) => series.map((s, si) => {
          const v = numberValue(point[s.key]);
          const baseline = y(0);
          const yy = y(v);
          const h = Math.max(1, Math.abs(baseline - yy));
          const xx = pad.left + i * barStep + barStep / 2 - (series.length * barW) / 2 + si * barW;
          return <rect key={`${i}-${s.key}`} x={xx} y={Math.min(yy, baseline)} width={barW - 2} height={h} rx="2" fill={s.color} opacity=".88">
            <title>{`${point.label}: ${s.label} ${money(v)}`}</title>
          </rect>;
        }))}
        {(type === "line" || type === "area") && series.map((s) => {
          const coords = points.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)} ${y(p[s.key])}`).join(" ");
          const areaPath = `${coords} L ${x(points.length - 1)} ${y(0)} L ${x(0)} ${y(0)} Z`;
          return <g key={s.key}>
            {type === "area" && <path d={areaPath} fill={s.color} opacity=".13" />}
            <path d={coords} fill="none" stroke={s.color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
            {points.length <= 18 && points.map((p, i) => <circle key={i} cx={x(i)} cy={y(p[s.key])} r="3" fill={s.color}><title>{`${p.label}: ${s.label} ${money(p[s.key])}`}</title></circle>)}
          </g>;
        })}
        {shownLabels.map((i) => <text key={i} x={x(i)} y={height - 12} textAnchor="middle" fill="rgba(226,232,240,.58)" fontSize="10">{points[i]?.label}</text>)}
      </svg>
    </div>
  );
}

function ChartControls({ period, setPeriod, chartType, setChartType }) {
  return <div className="wc-chart-controls">
    <div className="wc-periods" aria-label="Chart period">
      {PERIODS.map((p) => <button key={p.key} type="button" className={period === p.key ? "active" : ""} onClick={() => setPeriod(p.key)}>{p.key}</button>)}
    </div>
    <div className="wc-chart-types" aria-label="Chart type">
      {CHART_TYPES.map(({ key, label, Icon }) => <button key={key} type="button" className={chartType === key ? "active" : ""} onClick={() => setChartType(key)} aria-pressed={chartType === key}><Icon size={14} /> <span>{label}</span></button>)}
    </div>
  </div>;
}

function ChartLegend({ series }) {
  return <div className="wc-chart-legend">{series.map((s) => <span key={s.key}><i style={{ background: s.color }} />{s.label}</span>)}</div>;
}

export default function WealthManager({ onNavigate = () => {} }) {
  const [data, setData] = useState({ summary: null, liabilities: null, taxLiability: null });
  const [goals, setGoals] = useState([]);
  const [goalsLoading, setGoalsLoading] = useState(true);
  const [goalsError, setGoalsError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errors, setErrors] = useState([]);
  const [activeCard, setActiveCard] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cashPeriod, setCashPeriod] = useState("6M");
  const [flowPeriod, setFlowPeriod] = useState("6M");
  const [cashChartType, setCashChartType] = useState("line");
  const [flowChartType, setFlowChartType] = useState("bar");
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");

  const loadWealthData = useCallback(async ({ quiet = false } = {}) => {
    if (quiet) setRefreshing(true);
    else setLoading(true);
    setErrors([]);

    const requests = await Promise.allSettled([
      getJson(`/api/financial-summary/?user_id=${USER_ID}`),
      getJson(`/api/liabilities?user_id=${USER_ID}`),
      getJson(`/api/final-tax-liability/?user_id=${USER_ID}&financial_year=${FINANCIAL_YEAR}&tax_regime=new&residential_status=resident&stt_confirmed=false`),
      getJson(`/api/transactions/?user_id=${USER_ID}`),
      getJson(`/api/categories/?user_id=${USER_ID}`),
      getJson(`/api/goals/?user_id=${USER_ID}`),
    ]);

    const nextData = {
      summary: requests[0].status === "fulfilled" ? requests[0].value : null,
      liabilities: requests[1].status === "fulfilled" ? requests[1].value : null,
      taxLiability: requests[2].status === "fulfilled" ? requests[2].value : null,
    };
    setTransactions(requests[3].status === "fulfilled" && Array.isArray(requests[3].value) ? requests[3].value : []);
    setCategories(requests[4].status === "fulfilled" && Array.isArray(requests[4].value) ? requests[4].value : []); 
    const goalsPayload = requests[5].status === "fulfilled" ? requests[5].value : null;
    setGoals(goalsPayload && Array.isArray(goalsPayload.goals) ? goalsPayload.goals : []);
    setGoalsLoading(false);
    setGoalsError(requests[5].status === "rejected" ? (requests[5].reason?.message || "Goals could not be loaded.") : "");
    setHistoryError(requests[3].status === "rejected" ? "Transaction history could not be loaded. Check the Transactions API." : "");
    setHistoryLoading(false);
    setData(nextData);

    const labels = ["Financial Summary", "Liabilities", "Tax estimate", "Transactions", "Categories", "Financial goals"];
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

  const categoryById = useMemo(() => new Map(categories.map((c) => [Number(c.id), String(c.name || "").toLowerCase()])), [categories]);
  const loanDisbursementIds = useMemo(() => new Set(categories.filter((c) => String(c.name || "").toLowerCase().trim() === "loan disbursement").map((c) => Number(c.id))), [categories]);
  const currentDate = new Date();
  const selectedCashMonths = PERIODS.find((p) => p.key === cashPeriod)?.months || 6;
  const selectedFlowMonths = PERIODS.find((p) => p.key === flowPeriod)?.months || 6;
  const cashPoints = useMemo(() => {
    const end = monthStart(currentDate);
    const start = addMonths(end, -(selectedCashMonths - 1));
    const points = [];
    for (let i = 0; i < selectedCashMonths; i += 1) {
      const date = addMonths(start, i);
      const key = dateKey(date);
      const endOfMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0);
      let balance = totals.cash;
      // Reverse recorded balance effects after each historical month-end.
      // This is an estimate if transaction history is incomplete.
      transactions.forEach((tx) => {
        const txDate = new Date(`${tx.transaction_date}T00:00:00`);
        if (txDate > endOfMonth) {
          const amount = numberValue(tx.amount);
          const type = String(tx.transaction_type || "").toLowerCase();
          if (["income", "refund", "interest", "dividend"].includes(type)) balance -= amount;
          else if (["expense", "withdrawal", "tax", "loan_repayment"].includes(type)) balance += amount;
        }
      });
      points.push({ key, label: monthLabel(key, true), balance });
    }
    return points;
  }, [transactions, totals.cash, selectedCashMonths]);
  const flowPoints = useMemo(() => {
    const end = monthStart(currentDate);
    const start = addMonths(end, -(selectedFlowMonths - 1));
    const points = [];
    for (let i = 0; i < selectedFlowMonths; i += 1) {
      const date = addMonths(start, i);
      const key = dateKey(date);
      let income = 0;
      let expense = 0;
      transactions.forEach((tx) => {
        if (dateKey(new Date(`${tx.transaction_date}T00:00:00`)) !== key) return;
        const type = String(tx.transaction_type || "").toLowerCase();
        const amount = numberValue(tx.amount);
        if (type === "income" && !loanDisbursementIds.has(Number(tx.category_id))) income += amount;
        if (type === "expense") expense += amount;
      });
      points.push({ key, label: monthLabel(key, true), income, expense, net: income - expense });
    }
    return points;
  }, [transactions, selectedFlowMonths, loanDisbursementIds]);
  const flowTotals = useMemo(() => flowPoints.reduce((acc, p) => ({
    income: acc.income + p.income,
    expense: acc.expense + p.expense,
    net: acc.net + p.net,
  }), { income: 0, expense: 0, net: 0 }), [flowPoints]);
  // Phase 4: summarize existing saved goals without creating or changing goal records.
  const activeGoals = useMemo(
    () => goals.filter((goal) => String(goal.status || "active").toLowerCase() === "active"),
    [goals]
  );
  const goalTotals = useMemo(() => activeGoals.reduce((acc, goal) => ({
    target: acc.target + numberValue(goal.target_amount),
    saved: acc.saved + numberValue(goal.current_amount),
    remaining: acc.remaining + Math.max(0, numberValue(goal.target_amount) - numberValue(goal.current_amount)),
  }), { target: 0, saved: 0, remaining: 0 }), [activeGoals]);
  const overallGoalProgress = goalTotals.target > 0
    ? Math.min(100, (goalTotals.saved / goalTotals.target) * 100)
    : 0;

  // Phase 3: category-level income and expense breakdowns for the selected flow period.
  // Amounts use only the transaction types already classified as income/expense by this page.
  const categoryBreakdowns = useMemo(() => {
    const income = new Map();
    const expense = new Map();
    const end = monthStart(new Date());
    const start = addMonths(end, -(selectedFlowMonths - 1));
    transactions.forEach((tx) => {
      const txDate = new Date(`${tx.transaction_date}T00:00:00`);
      if (Number.isNaN(txDate.getTime()) || txDate < start || txDate >= addMonths(end, 1)) return;
      const type = String(tx.transaction_type || "").toLowerCase();
      const amount = numberValue(tx.amount);
      const categoryName = categories.find((c) => Number(c.id) === Number(tx.category_id))?.name
        || tx.category_name
        || "Uncategorized";
      if (type === "income" && !loanDisbursementIds.has(Number(tx.category_id))) {
        income.set(categoryName, (income.get(categoryName) || 0) + amount);
      } else if (type === "expense") {
        expense.set(categoryName, (expense.get(categoryName) || 0) + amount);
      }
    });
    const toRows = (map) => [...map.entries()]
      .map(([name, amount]) => ({ name, amount }))
      .sort((a, b) => b.amount - a.amount);
    return { income: toRows(income), expense: toRows(expense) };
  }, [transactions, categories, selectedFlowMonths, loanDisbursementIds]);

  const cashSeries = [{ key: "balance", label: "Cash balance", color: "#a78bfa" }];
  const flowSeries = flowChartType === "line"
    ? [{ key: "net", label: "Net cash flow", color: "#a78bfa" }]
    : [{ key: "income", label: "Income", color: "#34d399" }, { key: "expense", label: "Expenses", color: "#fb7185" }];

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

      <section className="wc-chart-grid">
        <article className="glass-card wc-chart-panel">
          <div className="wc-panel-heading">
            <div><p className="card-label">CASH POSITION</p><h3>Cash balance over time</h3><p className="wc-chart-subtitle">Estimated historical month-end balances reconstructed from current balances and recorded transactions.</p></div>
            <Wallet size={19} />
          </div>
          <ChartControls period={cashPeriod} setPeriod={setCashPeriod} chartType={cashChartType} setChartType={setCashChartType} />
          <div className="wc-chart-stat"><span>Latest recorded cash balance</span><strong>{money(totals.cash)}</strong></div>
          <ChartLegend series={cashSeries} />
          {historyLoading ? <div className="wc-chart-empty">Loading transaction history…</div> : historyError ? <div className="wc-chart-empty">{historyError}</div> : <WealthChart points={cashPoints} type={cashChartType} series={cashSeries} emptyText="No account history is available for this period." />}
          <p className="wc-note">Important: the current database does not store monthly balance snapshots. Historical values are reconstructed from available transactions and may be incomplete if transactions were not recorded consistently or account opening balances changed.</p>
        </article>

        <article className="glass-card wc-chart-panel">
          <div className="wc-panel-heading">
            <div><p className="card-label">CASH FLOW</p><h3>Income vs expenses</h3><p className="wc-chart-subtitle">Monthly transaction-based cash flow, excluding loan-disbursement income categories.</p></div>
            <TrendingUp size={19} />
          </div>
          <ChartControls period={flowPeriod} setPeriod={setFlowPeriod} chartType={flowChartType} setChartType={setFlowChartType} />
          <div className="wc-flow-stats">
            <div><span>Income</span><strong>{money(flowTotals.income)}</strong></div>
            <div><span>Expenses</span><strong>{money(flowTotals.expense)}</strong></div>
            <div><span>Net flow</span><strong className={flowTotals.net >= 0 ? "positive" : "negative"}>{money(flowTotals.net)}</strong></div>
          </div>
          <ChartLegend series={flowSeries} />
          {historyLoading ? <div className="wc-chart-empty">Loading transaction history…</div> : historyError ? <div className="wc-chart-empty">{historyError}</div> : <WealthChart points={flowPoints} type={flowChartType} series={flowSeries} emptyText="No income or expense transactions are recorded for this period." />}
          <p className="wc-note">Only transaction types classified as income and expense are included, matching the existing Financial Summary convention. Refunds, interest, dividends, taxes, repayments, and other types are not reclassified as income/expense here.</p>
        </article>
      </section>

      {/* Phase 3: category breakdowns, using the same selected period as Cash Flow. */}
      <section className="wc-breakdown-grid">
        <article className="glass-card wc-info-panel">
          <div className="wc-panel-heading">
            <div><p className="card-label">INCOME ANALYSIS</p><h3>Income by category</h3></div>
            <TrendingUp size={19} />
          </div>
          <p className="wc-chart-subtitle">Recorded income categories for the selected Cash Flow period ({flowPeriod}). Loan-disbursement categories are excluded.</p>
          {categoryBreakdowns.income.length ? categoryBreakdowns.income.slice(0, 8).map((row) => (
            <div className="wc-category-row" key={row.name}>
              <div className="wc-category-label"><span>{row.name}</span><strong>{money(row.amount)}</strong></div>
              <div className="wc-category-track"><span className="income" style={{ width: `${Math.max(2, (row.amount / Math.max(1, categoryBreakdowns.income[0].amount)) * 100)}%` }} /></div>
            </div>
          )) : <div className="wc-chart-empty">No classified income transactions are recorded for this period.</div>}
        </article>

        <article className="glass-card wc-info-panel">
          <div className="wc-panel-heading">
            <div><p className="card-label">EXPENSE ANALYSIS</p><h3>Expenses by category</h3></div>
            <ReceiptText size={19} />
          </div>
          <p className="wc-chart-subtitle">Recorded expense categories for the selected Cash Flow period ({flowPeriod}).</p>
          {categoryBreakdowns.expense.length ? categoryBreakdowns.expense.slice(0, 8).map((row) => (
            <div className="wc-category-row" key={row.name}>
              <div className="wc-category-label"><span>{row.name}</span><strong>{money(row.amount)}</strong></div>
              <div className="wc-category-track"><span className="expense" style={{ width: `${Math.max(2, (row.amount / Math.max(1, categoryBreakdowns.expense[0].amount)) * 100)}%` }} /></div>
            </div>
          )) : <div className="wc-chart-empty">No classified expense transactions are recorded for this period.</div>}
        </article>
      </section>

      {/* Phase 4: Financial Goals summary reads the existing Goals API only. */}
      <section className="wc-goals-section glass-card">
        <div className="wc-panel-heading">
          <div>
            <p className="card-label">FINANCIAL PLANNING</p>
            <h3>Financial Goals</h3>
            <p className="wc-chart-subtitle">Progress from your existing saved goals. This overview does not create or modify goals.</p>
          </div>
          <TrendingUp size={19} />
        </div>

        {goalsLoading ? (
          <div className="wc-chart-empty">Loading financial goals…</div>
        ) : goalsError ? (
          <div className="wc-chart-empty">Goals could not be loaded: {goalsError}</div>
        ) : activeGoals.length === 0 ? (
          <div className="wc-chart-empty">No active financial goals found. Create a goal in the existing Goals module to see its progress here.</div>
        ) : (
          <>
            <div className="wc-goal-summary-grid">
              <div><span>Active goals</span><strong>{activeGoals.length}</strong></div>
              <div><span>Total target</span><strong>{money(goalTotals.target)}</strong></div>
              <div><span>Saved toward goals</span><strong>{money(goalTotals.saved)}</strong></div>
              <div><span>Remaining</span><strong>{money(goalTotals.remaining)}</strong></div>
            </div>
            <div className="wc-goal-overall">
              <div className="wc-goal-overall-label"><span>Combined progress</span><strong>{overallGoalProgress.toFixed(1)}%</strong></div>
              <div className="wc-goal-track"><span style={{ width: `${overallGoalProgress}%` }} /></div>
            </div>
            <div className="wc-goal-list">
              {activeGoals.map((goal) => {
                const target = numberValue(goal.target_amount);
                const saved = numberValue(goal.current_amount);
                const remaining = Math.max(0, target - saved);
                const progress = target > 0 ? Math.min(100, (saved / target) * 100) : 0;
                return (
                  <article className="wc-goal-card" key={goal.id}>
                    <div className="wc-goal-card-heading">
                      <div><span className="wc-goal-category">{goal.category || "Other"}</span><h4>{goal.name || "Untitled goal"}</h4></div>
                      <strong>{progress.toFixed(0)}%</strong>
                    </div>
                    <div className="wc-goal-track"><span style={{ width: `${progress}%` }} /></div>
                    <div className="wc-goal-amounts">
                      <span>Saved <strong>{money(saved)}</strong></span>
                      <span>Target <strong>{money(target)}</strong></span>
                      <span>Remaining <strong>{money(remaining)}</strong></span>
                    </div>
                    {goal.target_date ? <p className="wc-goal-date">Target date: {goal.target_date}</p> : null}
                    {numberValue(goal.monthly_contribution) > 0 ? <p className="wc-goal-date">Planned monthly contribution: {money(goal.monthly_contribution)}</p> : null}
                  </article>
                );
              })}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
