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

export default function WealthManager({ onNavigate = () => {} }) {
  const [data, setData] = useState({ summary: null, liabilities: null, taxLiability: null });
  // Keep the Wealth Manager estimate aligned with the user's explicit regime selection.
  const [taxRegime, setTaxRegime] = useState("new");
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
      getJson(`/api/final-tax-liability/?user_id=${USER_ID}&financial_year=${FINANCIAL_YEAR}&tax_regime=${encodeURIComponent(taxRegime)}&residential_status=resident&stt_confirmed=false`),
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

      <section className="wc-section-grid">
        <article className="glass-card wc-info-panel">
          <div className="wc-panel-heading"><div><p className="card-label">CURRENT SNAPSHOT</p><h3>Cash & investments</h3></div><Wallet size={19} /></div>
          <DetailRow label="Cash and account balances" value={loading ? "Loading…" : money(totals.cash)} />
          <DetailRow label="Investment current value" value={loading ? "Loading…" : money(totals.investments)} />
          <div className="wc-total-row"><span>Combined recorded value</span><strong>{loading ? "Loading…" : money(totals.cash + totals.investments)}</strong></div>
          <p className="wc-note">These recorded balances feed the total-assets and asset-mix calculations. Open Accounts or Portfolio to inspect the underlying records.</p>
        </article>
        <article className="glass-card wc-info-panel">
          <div className="wc-panel-heading"><div><p className="card-label">TAX SNAPSHOT</p><h3>Tax estimate status</h3></div><ReceiptText size={19} /></div>
          <DetailRow label="Financial year" value={FINANCIAL_YEAR} />
          <label className="wc-tax-regime-control" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, margin: "12px 0", color: "inherit" }}>
            <span>Tax regime</span>
            <select
              value={taxRegime}
              onChange={(event) => setTaxRegime(event.target.value)}
              aria-label="Wealth Manager tax regime"
              style={{ maxWidth: 180, padding: "8px 10px", borderRadius: 8, background: "var(--surface, #171827)", color: "inherit", border: "1px solid rgba(148,163,184,.35)" }}
            >
              <option value="new">New Regime</option>
              <option value="old">Old Regime</option>
            </select>
          </label>
          <DetailRow label="Tax engine response" value={data.taxLiability ? "Available" : loading ? "Loading…" : "Unavailable"} />
          <DetailRow label="Tax estimate" value={taxAmount === undefined ? "Not available" : money(taxAmount)} />
          <p className="wc-note">Estimate requested using the {taxRegime === "old" ? "Old" : "New"} Regime. This amount is shown only when the existing tax engine returns a recognized total field. Review the tax calculation scope before treating it as final tax payable.</p>
          <div className="wc-tax-status"><CheckCircle2 size={15} /><span>Existing Tax Centre remains unchanged and available in the sidebar.</span></div>
        </article>
      </section>

      <section className="wc-wealth-analysis-grid" aria-label="Wealth analysis">
        <article className="glass-card wc-info-panel">
          <div className="wc-panel-heading">
            <div><p className="card-label">ASSET MIX</p><h3>Recorded wealth composition</h3></div>
            <PieChart size={19} />
          </div>
          <p className="wc-chart-subtitle">How your currently recorded assets are divided between cash and investments.</p>
          <div className="wc-wealth-mix-list">
            <div className="wc-wealth-mix-row">
              <div className="wc-wealth-mix-label"><span>Cash &amp; account balances</span><strong>{money(totals.cash)} · {cashShare.toFixed(1)}%</strong></div>
              <div className="wc-wealth-mix-track"><span className="cash" style={{ width: `${cashShare}%` }} /></div>
            </div>
            <div className="wc-wealth-mix-row">
              <div className="wc-wealth-mix-label"><span>Investments</span><strong>{money(totals.investments)} · {investmentShare.toFixed(1)}%</strong></div>
              <div className="wc-wealth-mix-track"><span className="investments" style={{ width: `${investmentShare}%` }} /></div>
            </div>
          </div>
          <div className="wc-total-row"><span>Total recorded assets</span><strong>{money(totals.assets)}</strong></div>
          <p className="wc-note">This is a current-value allocation, not historical performance. It includes only cash/account balances and investments returned by connected APIs; other assets appear only after their records are supported.</p>
        </article>

        <article className="glass-card wc-info-panel">
          <div className="wc-panel-heading">
            <div><p className="card-label">BALANCE SHEET</p><h3>Wealth position</h3></div>
            <Landmark size={19} />
          </div>
          <DetailRow label="Total recorded assets" value={loading ? "Loading…" : money(totals.assets)} />
          <DetailRow label="Outstanding liabilities" value={loading ? "Loading…" : money(totals.liabilities)} />
          <div className="wc-total-row"><span>Estimated net worth</span><strong>{loading ? "Loading…" : money(totals.netWorth)}</strong></div>
          <DetailRow label="Liabilities / assets" value={liabilityRatio === null ? "Unavailable" : `${liabilityRatio.toFixed(1)}%`} note="Based on currently recorded assets and liabilities" />
          <div className="wc-breakdown-actions">
            <BreakdownAction onClick={() => setActiveCard("Total Assets")}>Explore assets</BreakdownAction>
            <BreakdownAction onClick={() => setActiveCard("Total Liabilities")}>Explore liabilities</BreakdownAction>
            <BreakdownAction onClick={() => onNavigate("Portfolio")}>Analyse investments</BreakdownAction>
          </div>
          <p className="wc-note">Net worth is an estimate from the current connected records. It does not imply that all property, deposits, debts or other off-platform assets have been recorded.</p>
        </article>
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
