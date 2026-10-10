// ============================================================
// FINANCIAL OS
// MAIN APPLICATION
// ============================================================

import React, { useEffect, useState } from "react";
import WealthManager from "./WealthManager";
import LoanManagement from "./LoanManagement";

import {
  LayoutDashboard,
  WalletCards,
  ArrowLeftRight,
  PieChart,
  Receipt,
  TrendingUp,
  BarChart3,
  Target,
  Sparkles,
  Settings,
  Bell,
  Search,
  Menu,
  X,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
  Landmark,
  CreditCard,
  CircleDollarSign,
  Trash2
} from "lucide-react";

// ============================================================
// NAVIGATION
// ============================================================

const navigation = [
  {
    section: "Overview",
    items: [
      // Dashboard is intentionally hidden from the sidebar for Option A.
      // Its component and route remain in this file so it can be restored later.
      {
        name: "Wealth Manager",
        icon: Landmark
      }
    ]
  },

  {
    section: "Money",
    items: [
      {
        name: "Accounts",
        icon: WalletCards
      },
      {
        name: "Transactions",
        icon: ArrowLeftRight
      },
      {
        name: "Loans & Liabilities",
        icon: Landmark
      },
      {
  name: "Budget",
  icon: PieChart
},
{
  name: "Categories",
  icon: CircleDollarSign
},
{
  name: "Bills",
  icon: Receipt
}
    ]
  },

  {
    section: "Invest",
    items: [
      {
        name: "Portfolio",
        icon: TrendingUp
      },
      {
        name: "Holdings",
        icon: BarChart3
      },
      {
        name: "Investment Transactions",
        icon: ArrowLeftRight
      }
    ]
  },

  {
    section: "Markets",
    items: [{ name: "Markets", icon: TrendingUp }]
  },

  {
    section: "Plan",
    items: [
      {
        name: "Goals",
        icon: Target
      }
    ]
  },

  // ============================================================
  // AI SECTION
  // ============================================================
  {
    section: "AI",
    items: [
      {
        name: "AI Assistant",
        icon: Sparkles
      }
    ]
  },

  // ============================================================
  // TAX SECTION
  // ============================================================
  {
    section: "Tax",
    items: [
      {
        name: "Tax",
        icon: Receipt
      }
    ]
  },

  // ============================================================
  // PLAYGROUND SECTION
  // ============================================================
  {
    section: "Playground",
    items: [
      {
        name: "Playground",
        icon: Sparkles
      }
    ]
  }
];

// ============================================================
// MAIN APP
// ============================================================

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [activePage, setActivePage] = useState("Wealth Manager");

  // ----------------------------------------------------------
  // NAVIGATION HANDLER
  // ----------------------------------------------------------

  const handleNavigation = (page) => {
    setActivePage(page);
    setSidebarOpen(false);
  };

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (
    <div className="app-shell">

      {/* =====================================================
          MOBILE OVERLAY
      ===================================================== */}

      {sidebarOpen && (
        <div
          className="mobile-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* =====================================================
          SIDEBAR
      ===================================================== */}

      <aside
        className={`sidebar ${
          sidebarOpen ? "sidebar-open" : ""
        }`}
      >

        {/* BRAND */}

        <div className="brand">

          <div className="brand-icon">
            <CircleDollarSign size={24} />
          </div>

          <div className="brand-text">
            <strong>Financial OS</strong>
            <span>Your Financial Command Center</span>
          </div>

          <button
            className="mobile-close"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>

        </div>

        {/* NAVIGATION */}

        <div className="navigation">

          {navigation.map((group) => (

            <div
              className="navigation-group"
              key={group.section}
            >

              <div className="navigation-title">
                {group.section}
              </div>

              {group.items.map((item) => {

                const Icon = item.icon;

                const active =
                  activePage === item.name;

                return (
                  <button
                    key={item.name}
                    className={`navigation-item ${
                      active ? "active" : ""
                    }`}
                    onClick={() =>
                      handleNavigation(item.name)
                    }
                  >

                    <Icon size={19} />

                    <span>
                      {item.name}
                    </span>

                  </button>
                );
              })}

            </div>
          ))}

        </div>

        {/* SIDEBAR FOOTER */}

        <div className="sidebar-footer">

          <button
            className="navigation-item"
            onClick={() =>
              handleNavigation("Settings")
            }
          >
            <Settings size={19} />
            <span>Settings</span>
          </button>

        </div>

      </aside>

      {/* =====================================================
          MAIN AREA
      ===================================================== */}

      <main className="main-area">

        {/* ===================================================
            TOP BAR
        =================================================== */}

        <header className="topbar">

          <div className="topbar-left">

            <button
              className="menu-button"
              onClick={() =>
                setSidebarOpen(true)
              }
            >
              <Menu size={22} />
            </button>

            <div className="page-title">

              <span className="eyebrow">
                FINANCIAL OS
              </span>

              <h1>
                {activePage}
              </h1>

            </div>

          </div>

          <div className="topbar-actions">

            <button className="icon-button">
              <Search size={19} />
            </button>

            <button className="icon-button">
              <Bell size={19} />
            </button>

            <div className="profile">

              <div className="profile-avatar">
                NS
              </div>

              <div className="profile-info">
                <strong>User</strong>
                <span>Personal</span>
              </div>

            </div>

          </div>

        </header>

        {/* ===================================================
            CONTENT
        =================================================== */}

        <section className="content">
          
{activePage === "Dashboard" ? (
  <Dashboard />
) : activePage === "Wealth Manager" ? (
  <WealthManager onNavigate={handleNavigation} />
) : activePage === "Accounts" ? (
  <Accounts />
) : activePage === "Transactions" ? (
  <Transactions />
) : activePage === "Budget" ? (
  <Budget />
) : activePage === "Categories" ? (
  <Category />
) : activePage === "Bills" ? (
  <Bills />
) : activePage === "Portfolio" ? (
  <Portfolio />
) : activePage === "Holdings" ? (
  <Holdings />
 ) : activePage === "Loans & Liabilities" ? (
   <LoanManagement />
 ) : activePage === "Investment Transactions" ? (
   <InvestmentTransactions />
) : activePage === "Markets" ? (
   <MarketsPage />
) : activePage === "Tax" ? (
   <TaxPage />
) : activePage === "Goals" ? (
   <PlanPage />
) : (
   <PlaceholderPage
    title={activePage}
/>
)}
        

        </section>

      </main>

    </div>
  );
}

// ============================================================
// DASHBOARD
// ============================================================

function Dashboard() {
  // Dashboard uses real API data; missing module data is shown as unavailable.
  const [dashboardData, setDashboardData] = useState(null);
  const [goalsData, setGoalsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const API_BASE_URL = "https://ai-finance-trading-os-api.onrender.com";
  const USER_ID = 1;


  const loadDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const [dashboardResponse, goalsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/dashboard/summary?user_id=${USER_ID}`, { cache: "no-store" }),
        fetch(`${API_BASE_URL}/api/goals/?user_id=${USER_ID}`, { cache: "no-store" }).catch(() => null),
      ]);
      if (!dashboardResponse.ok) {
        throw new Error(`Dashboard API error: ${dashboardResponse.status}`);
      }
      const data = await dashboardResponse.json();
      setDashboardData(data);
      if (goalsResponse?.ok) {
        const goalPayload = await goalsResponse.json();
        setGoalsData(Array.isArray(goalPayload.goals) ? goalPayload.goals : []);
      } else {
        setGoalsData([]);
      }
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Dashboard API error:", err);
      setError("Unable to load the latest financial data. Please retry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();

    // Refresh dashboard totals whenever a transaction is created, edited, or deleted.
    const handleTransactionChange = () => loadDashboard();
    window.addEventListener("financial-os:transactions-changed", handleTransactionChange);
    return () => window.removeEventListener("financial-os:transactions-changed", handleTransactionChange);
  }, []);

  const formatCurrency = (value) => new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0,
  }).format(Number(value) || 0);

  const summary = dashboardData?.summary || {};
  const trend = dashboardData?.monthly_trend || [];
  const breakdown = dashboardData?.expense_breakdown || [];
  const alerts = dashboardData?.alerts || [];
  const recentTransactions = dashboardData?.recent_transactions || [];
  const totalBalance = Number(summary.total_balance || 0);
  const totalIncome = Number(summary.total_income || 0);
  const totalExpense = Number(summary.total_expense || 0);
  const netCashFlow = Number(summary.net_cash_flow || 0);
  const avgIncome = Number(summary.average_monthly_income || 0);
  const avgExpense = Number(summary.average_monthly_expense || 0);
  const monthlySavings = avgIncome - avgExpense;
  const savingsRate = avgIncome > 0 ? (monthlySavings / avgIncome) * 100 : 0;
  const activeGoals = goalsData.filter(g => (g.status || "active").toLowerCase() === "active");
  const goalsTarget = activeGoals.reduce((sum, g) => sum + Number(g.target_amount || 0), 0);
  const goalsCurrent = activeGoals.reduce((sum, g) => sum + Number(g.current_amount || 0), 0);

  const goTo = (page) => {
    // The parent app exposes page navigation through the existing sidebar.
    const buttons = Array.from(document.querySelectorAll(".navigation-item"));
    const target = buttons.find(button => button.textContent.trim().includes(page));
    if (target) target.click();
  };

  const notificationItems = [
    ...alerts.map((alert, index) => ({
      key: `budget-${index}`, severity: alert.severity || "warning",
      title: alert.title || "Budget alert", message: alert.message || "Review your category spending.",
    })),
    {
      key: "tax-review", severity: "info", title: "Tax records review",
      message: "Review income, interest, dividends and capital-gains records periodically. This is a general reminder, not a filing-deadline alert.",
    },
    ...(activeGoals.length === 0 ? [{
      key: "goal-reminder", severity: "info", title: "Set a financial goal",
      message: "Create a goal in Plan → Goals to track a target amount, date and monthly contribution.",
    }] : []),
    ...(summary.transaction_count === 0 ? [{
      key: "transactions", severity: "warning", title: "No transactions recorded",
      message: "Add transactions to make cash-flow charts and savings estimates more useful.",
    }] : []),
  ];

  const maxTrend = Math.max(1, ...trend.flatMap(item => [Number(item.income || 0), Number(item.expenses || 0)]));
  const maxCategory = Math.max(1, ...breakdown.map(item => Number(item.amount || 0)));

  return (
    <div className="dashboard dashboard-overview">
      <section className="welcome-section">
        <div>
          <p className="welcome-label">FINANCIAL COMMAND CENTRE</p>
          <h2>Your financial <br /><span>overview.</span></h2>
          <p className="welcome-description">
            A concise view of Money, Investments, Planning, Markets, AI and Tax—using available recorded data.
          </p>
          <p style={{fontSize: "12px", opacity: .7, marginTop: 8}}>
            {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString("en-IN", {hour:"2-digit", minute:"2-digit"})}` : "Loading overview…"}
          </p>
        </div>
        <button className="primary-button" onClick={loadDashboard} disabled={loading}>
          {loading ? "Refreshing…" : "↻ Refresh overview"}
        </button>
      </section>

      {error && <div className="glass-card" role="alert">
        <strong>{error}</strong> <button className="small-button" onClick={loadDashboard}>Retry</button>
      </div>}

      {/* MONEY: high-level metrics; the dashboard intentionally avoids transaction-level detail. */}
      <section className="metrics-grid">
        <MetricCard title="Cash Balance" value={loading ? "Loading…" : formatCurrency(totalBalance)} change={`${summary.account_count || 0} active accounts`} positive icon={Wallet} />
        <MetricCard title="Total Income" value={loading ? "Loading…" : formatCurrency(totalIncome)} change="All recorded income" positive icon={TrendingUp} />
        <MetricCard title="Total Expenses" value={loading ? "Loading…" : formatCurrency(totalExpense)} change="All recorded expenses" positive={false} icon={CreditCard} />
        <MetricCard title="Net Cash Flow" value={loading ? "Loading…" : formatCurrency(netCashFlow)} change={netCashFlow >= 0 ? "Positive" : "Negative"} positive={netCashFlow >= 0} icon={CircleDollarSign} />
        <MetricCard title="Avg. Monthly Income" value={loading ? "Loading…" : formatCurrency(avgIncome)} change="Last 90 days ÷ 3" positive icon={ArrowUpRight} />
        <MetricCard title="Avg. Monthly Expenses" value={loading ? "Loading…" : formatCurrency(avgExpense)} change="Last 90 days ÷ 3" positive={false} icon={ArrowDownRight} />
        <MetricCard title="Estimated Monthly Savings" value={loading ? "Loading…" : formatCurrency(monthlySavings)} change="Income minus expenses" positive={monthlySavings >= 0} icon={WalletCards} />
        <MetricCard title="Savings Rate" value={loading ? "Loading…" : `${savingsRate.toFixed(1)}%`} change={avgIncome > 0 ? "90-day average" : "Add income records"} positive={savingsRate >= 0} icon={PieChart} />
      </section>

      {/* Cash-flow graph: real monthly values from dated transactions. */}
      <section className="dashboard-grid">
        <div className="glass-card large-card">
          <div className="card-header">
            <div><p className="card-label">MONEY • CASH FLOW</p><h3>Income vs Expenses</h3></div>
            <span className="small-button">Last 6 calendar months</span>
          </div>
          {trend.length === 0 ? <div className="empty-chart">No dated transaction data available yet.</div> : (
            <div className="overview-chart" role="img" aria-label="Monthly income and expense comparison">
              <div className="chart-legend"><span><i className="legend-income"/> Income</span><span><i className="legend-expense"/> Expenses</span></div>
              <div className="trend-columns">
                {trend.map(item => (
                  <div className="trend-column" key={item.month}>
                    <div className="trend-bars">
                      <div className="trend-bar income-bar" title={`Income ${formatCurrency(item.income)}`} style={{height:`${Math.max(2, Number(item.income || 0) / maxTrend * 100)}%`}}/>
                      <div className="trend-bar expense-bar" title={`Expenses ${formatCurrency(item.expenses)}`} style={{height:`${Math.max(2, Number(item.expenses || 0) / maxTrend * 100)}%`}}/>
                    </div>
                    <span>{new Date(`${item.month}-01T12:00:00`).toLocaleDateString("en-IN",{month:"short"})}</span>
                  </div>
                ))}
              </div>
              <div className="chart-footnote">Bars are based on recorded transactions; a zero-height value is shown minimally for visibility.</div>
            </div>
          )}
        </div>

        <div className="glass-card">
          <div className="card-header"><div><p className="card-label">MONEY • SPENDING</p><h3>Expense categories</h3></div></div>
          {breakdown.length === 0 ? <div className="empty-chart">No expense categories recorded for this month.</div> : (
            <div className="category-chart">
              {breakdown.map((item, index) => (
                <div className="category-row" key={`${item.category}-${index}`}>
                  <div className="category-row-label"><span>{item.category}</span><strong>{formatCurrency(item.amount)}</strong></div>
                  <div className="category-track"><div className="category-fill" style={{width:`${Math.min(100, Number(item.amount || 0) / maxCategory * 100)}%`}}/></div>
                </div>
              ))}
              <p className="chart-footnote">Current-month expenses; largest categories shown first.</p>
            </div>
          )}
        </div>
      </section>

      {/* Cross-module overview cards: click through to each module for full detail. */}
      <section className="glass-card module-overview-card">
        <div className="card-header"><div><p className="card-label">ALL MODULES</p><h3>Financial OS overview</h3></div></div>
        <div className="module-overview-grid">
          {[
            {name:"Money", detail:`${summary.account_count || 0} active accounts`, icon:WalletCards, page:"Accounts"},
            {name:"Investments", detail:"Open portfolio and holdings", icon:TrendingUp, page:"Portfolio"},
            {name:"Plan & Goals", detail:activeGoals.length ? `${activeGoals.length} active goals • ${formatCurrency(goalsCurrent)} saved of ${formatCurrency(goalsTarget)}` : "No active goals yet", icon:Target, page:"Goals"},
            {name:"Markets", detail:"Open market data and instruments", icon:BarChart3, page:"Markets"},
            {name:"AI Assistant", detail:"Open financial assistant", icon:Sparkles, page:"AI Assistant"},
            {name:"Tax", detail:"Review tax records and reports", icon:Receipt, page:"Tax"},
          ].map(module => {
            const Icon = module.icon;
            return <button className="module-overview-tile" key={module.name} onClick={() => goTo(module.page)}>
              <span className="module-tile-icon"><Icon size={19}/></span>
              <span><strong>{module.name}</strong><small>{module.detail}</small></span>
              <ArrowUpRight size={16}/>
            </button>;
          })}
        </div>
      </section>

      {/* Alerts and notifications from actual budget data plus clearly-labelled reminders. */}
      <section className="dashboard-grid">
        <div className="glass-card notifications-card">
          <div className="card-header"><div><p className="card-label">ATTENTION</p><h3>Alerts & Notifications</h3></div><span className="notification-count">{notificationItems.length}</span></div>
          {notificationItems.length === 0 ? <div className="empty-chart">You're all caught up. No active alerts were returned.</div> : (
            <div className="notification-list">
              {notificationItems.map(item => <div className={`notification-item severity-${item.severity}`} key={item.key}>
                <span className="notification-dot"/>
                <div><strong>{item.title}</strong><p>{item.message}</p></div>
              </div>)}
            </div>
          )}
        </div>

        <div className="glass-card goals-summary-card">
          <div className="card-header"><div><p className="card-label">PLAN • PROGRESS</p><h3>Goal progress</h3></div><button className="small-button" onClick={() => goTo("Goals")}>Open Plan</button></div>
          {activeGoals.length === 0 ? <div className="empty-chart"><p>No saved active goals found.</p><button className="primary-button" onClick={() => goTo("Goals")}>Create a goal</button></div> : activeGoals.slice(0,4).map(goal => {
            const target = Number(goal.target_amount || 0);
            const current = Number(goal.current_amount || 0);
            const progress = target > 0 ? Math.min(100, current / target * 100) : 0;
            return <div className="goal-summary-row" key={goal.id}>
              <div className="category-row-label"><span>{goal.name}</span><strong>{progress.toFixed(0)}%</strong></div>
              <div className="category-track"><div className="category-fill goal-fill" style={{width:`${progress}%`}}/></div>
              <small>{formatCurrency(current)} of {formatCurrency(target)}</small>
            </div>;
          })}
        </div>
      </section>

      {/* AI summary is explicitly a module link until real AI insights are connected. */}
      <section className="glass-card ai-card">
        <div className="card-header"><div className="ai-title"><div className="ai-icon"><Sparkles size={19}/></div><div><p className="card-label">AI • INSIGHTS</p><h3>Financial Assistant</h3></div></div></div>
        <p className="welcome-description">AI-generated recommendations are not shown here until a working AI analysis endpoint is connected. Open the assistant to explore available features.</p>
        <button className="primary-button" onClick={() => goTo("AI Assistant")}><Sparkles size={17}/> Open AI Assistant</button>
      </section>

      <section className="glass-card health-card">
        <div className="card-header"><div><p className="card-label">RECENT ACTIVITY</p><h3>Recent Transactions</h3></div><span className="score">{summary.transaction_count || 0}</span></div>
        {recentTransactions.length === 0 ? <div className="health-footer"><span>No transactions available.</span></div> : recentTransactions.map(transaction => (
          <div key={transaction.id} className="health-footer">
            <span>{transaction.description || "Transaction"} • {transaction.transaction_date}</span>
            <strong>{transaction.transaction_type === "expense" ? "-" : "+"}{formatCurrency(transaction.amount)}</strong>
          </div>
        ))}
      </section>
    </div>
  );
}

// ============================================================
// METRIC CARD
// ============================================================

function MetricCard({
  title,
  value,
  change,
  positive,
  icon: Icon
}) {

  return (
    <div className="glass-card metric-card">

      <div className="metric-top">

        <div className="metric-icon">
          <Icon size={20} />
        </div>

        <span
          className={`metric-change ${
            positive ? "positive" : "negative"
          }`}
        >
          {positive ? (
            <ArrowUpRight size={14} />
          ) : (
            <ArrowDownRight size={14} />
          )}

          {change}
        </span>

      </div>

      <p className="metric-label">
        {title}
      </p>

      <h3 className="metric-value">
        {value}
      </h3>

    </div>
  );
}

// ============================================================
// TAX SECTION ERROR BOUNDARY
// Keeps a rendering error in one Tax tab from blanking the whole app.
// ============================================================

class TaxSectionErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorMessage: "" };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error("Tax section rendering error:", error, info);
    this.setState({ errorMessage: error?.message || String(error || "Unknown rendering error") });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          style={{
            padding: "18px",
            borderRadius: "14px",
            border: "1px solid rgba(239,68,68,0.3)",
            background: "rgba(239,68,68,0.08)",
            color: "#fca5a5",
            lineHeight: 1.7,
          }}
        >
          <strong>This Tax section could not be displayed.</strong>
          <p style={{ margin: "8px 0 12px" }}>
            The rest of Financial OS is protected. Refresh the page or choose another Tax tab.
            {this.state.errorMessage ? ` Details: ${this.state.errorMessage}` : "Try again or select another Tax tab."}
          </p>
          <button
            type="button"
            className="secondary-button"
            onClick={() => this.setState({ hasError: false, errorMessage: "" })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ============================================================
// TAX CENTRE
// Six sections powered by the existing read-only tax APIs.
// ============================================================

function TaxPage() {
  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";
  const USER_ID = 1;

  const [section, setSection] = useState("Overview");
  const [financialYear, setFinancialYear] = useState("2026-27");
  const [taxRegime, setTaxRegime] = useState("new");
  const [sttConfirmed, setSttConfirmed] = useState(false);
  const [taxData, setTaxData] = useState(null);
  const [incomeData, setIncomeData] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const sections = [
    "Overview",
    "Income",
    "Capital Gains",
    "Deductions",
    "Tax Calculation",
    "Tax Report",
  ];

  // Safely format API values. React cannot render arbitrary objects as text.
  const safeText = (value, fallback = "—") => {
    if (value === null || value === undefined || value === "") return fallback;
    if (["string", "number", "boolean"].includes(typeof value)) return String(value);
    if (Array.isArray(value)) return value.map((item) => safeText(item, "")).filter(Boolean).join(", ") || fallback;
    // If an API field unexpectedly contains an object, show a useful scalar field.
    if (typeof value === "object") {
      const candidate = value.name ?? value.label ?? value.value ?? value.symbol;
      if (candidate !== undefined && candidate !== value) return safeText(candidate, fallback);
      return fallback;
    }
    return fallback;
  };

  const formatCurrency = (value) => {
    const numericValue = Number(value ?? 0);
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number.isFinite(numericValue) ? numericValue : 0);
  };

  const readApi = async (path) => {
    const response = await fetch(`${API_BASE_URL}${path}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(
        data?.detail || data?.message || `Tax API returned ${response.status}`
      );
    }
    return data;
  };

  // Load only existing, read-only endpoints. The tax page does not write to the DB.
  const loadTaxData = async () => {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const [capitalTax, taxableIncome] = await Promise.all([
        readApi(
          `/api/tax-calculation/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&stt_confirmed=${sttConfirmed}`
        ),
        readApi(
          `/api/final-taxable-income/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&tax_regime=${encodeURIComponent(taxRegime)}`
        ),
      ]);
      setTaxData(capitalTax);
      setIncomeData(taxableIncome);
      setNotice("Tax data refreshed from the existing read-only engines.");

      // This report endpoint is optional: show report content only if deployed.
      try {
        const report = await readApi(
          `/api/itr-ready-tax-report/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&tax_regime=${encodeURIComponent(taxRegime)}`
        );
        setReportData(report);
      } catch (reportError) {
        setReportData(null);
        console.info("ITR report endpoint is not available yet:", reportError);
      }
    } catch (err) {
      console.error("Tax Centre load error:", err);
      setError(err?.message || "Unable to load tax data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTaxData();
    // Reload is triggered by the user after changing filters.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cardStyle = {
    border: "1px solid rgba(255,255,255,0.09)",
    borderRadius: "16px",
    padding: "18px",
    background: "linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.025))",
    minWidth: 0,
  };
  const labelStyle = {
    color: "rgba(255,255,255,0.48)",
    fontSize: "10px",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    marginBottom: "8px",
  };
  const valueStyle = { fontSize: "21px", fontWeight: 800, overflowWrap: "anywhere" };
  const panelStyle = {
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: "16px",
    padding: "18px",
    background: "rgba(255,255,255,0.025)",
  };
  const tableCellStyle = {
    padding: "11px 10px",
    borderBottom: "1px solid rgba(255,255,255,0.07)",
    textAlign: "left",
    fontSize: "12px",
    verticalAlign: "top",
  };
  const capitalGains = taxData?.capital_gains || {};
  const tax = taxData?.tax || {};
  const taxSummary = tax?.summary || {};
  const taxable = incomeData?.taxable_income || {};
  const otherSources = incomeData?.other_sources || {};
  const lossSetoff = incomeData?.capital_loss_setoff || {};
  const deductions = incomeData?.deductions || {};
  const exemptIncome = incomeData?.exempt_income || {};
  // Ignore malformed/null API rows so one bad record cannot crash the Tax Centre.
  const rawGainRows = Array.isArray(taxData?.realised_transactions)
    ? taxData.realised_transactions
    : Array.isArray(taxData?.classified_transactions)
    ? taxData.classified_transactions
    : [];
  const gainRows = rawGainRows.filter(
    (row) => row && typeof row === "object" && !Array.isArray(row)
  );

  const renderOverview = () => (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "14px" }}>
        <div style={cardStyle}><div style={labelStyle}>Indicative capital-gains tax + cess</div><div style={valueStyle}>{formatCurrency(taxSummary.tax_plus_cess)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>Special-rate calculation only</div></div>
        <div style={cardStyle}><div style={labelStyle}>Provisional taxable income</div><div style={valueStyle}>{formatCurrency(taxable.provisional_taxable_income)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>{taxable.status || "Not yet classified"}</div></div>
        <div style={cardStyle}><div style={labelStyle}>STCG gain</div><div style={valueStyle}>{formatCurrency(capitalGains.stcg)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>STT confirmation: {sttConfirmed ? "Confirmed" : "Not confirmed"}</div></div>
        <div style={cardStyle}><div style={labelStyle}>LTCG gain</div><div style={valueStyle}>{formatCurrency(capitalGains.ltcg)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>Section 112A treatment shown by engine</div></div>
      </div>
      <div style={panelStyle}>
        <h3 style={{ marginTop: 0 }}>Tax readiness</h3>
        <p style={{ color: "rgba(255,255,255,0.62)", lineHeight: 1.7, fontSize: "13px" }}>
          This page combines the current capital-gains calculation and provisional taxable-income framework. It is not a complete ITR filing or a final tax demand. Salary, house-property and business/professional income may remain unavailable until their source data is added.
        </p>
        <button className="secondary-button" type="button" onClick={() => setSection("Tax Report")}>Open Tax Report</button>
      </div>
    </>
  );

  const renderIncome = () => (
    <div style={panelStyle}>
      <h3 style={{ marginTop: 0 }}>Income aggregation</h3>
      <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "12px", lineHeight: 1.6 }}>Amounts are taken from the existing final taxable-income engine. Missing income heads are shown as unavailable rather than assumed to be zero.</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "12px" }}>
        {[
          ["Other-source income", otherSources.income],
          ["Interest", otherSources.interest],
          ["Dividend", otherSources.dividend],
          ["Other-source total", otherSources.total],
          ["Capital gains after set-off", incomeData?.capital_gains?.total_after_setoff],
          ["Available gross income", taxable.available_gross_income],
        ].map(([label, value]) => <div key={label} style={cardStyle}><div style={labelStyle}>{label}</div><div style={{ fontSize: "18px", fontWeight: 750 }}>{value == null ? "Unavailable" : formatCurrency(value)}</div></div>)}
      </div>
      <div style={{ marginTop: "16px", color: "rgba(255,255,255,0.55)", fontSize: "12px" }}>Salary, house-property and business/profession income must not be treated as zero if the engine marks those heads unavailable.</div>
    </div>
  );

  const renderCapitalGains = () => (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
        <div style={cardStyle}><div style={labelStyle}>STCG</div><div style={valueStyle}>{formatCurrency(capitalGains.stcg)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>LTCG</div><div style={valueStyle}>{formatCurrency(capitalGains.ltcg)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Unclassified gains</div><div style={valueStyle}>{formatCurrency(capitalGains.unclassified)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Capital-gains tax + cess</div><div style={valueStyle}>{formatCurrency(taxSummary.tax_plus_cess)}</div></div>
      </div>
      <div style={panelStyle}>
        <h3 style={{ marginTop: 0 }}>Realised transaction details</h3>
        {gainRows.length === 0 ? <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "13px" }}>No realised transaction rows were returned for this financial year.</p> : <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse" }}><thead><tr>{["Investment", "Date", "Asset class", "Classification", "Realised gain/loss"].map(x => <th key={x} style={{ ...tableCellStyle, color: "rgba(255,255,255,0.55)" }}>{x}</th>)}</tr></thead><tbody>{gainRows.map((row, index) => <tr key={row.id || `${row.investment_id || "gain"}-${index}`}><td style={tableCellStyle}>{safeText(row.name ?? row.symbol ?? row.investment_name, `Investment ${safeText(row.investment_id, "")}`)}</td><td style={tableCellStyle}>{safeText(row.transaction_date ?? row.sell_date ?? row.date)}</td><td style={tableCellStyle}>{safeText(row.asset_class)}</td><td style={tableCellStyle}>{safeText(row.capital_gain_classification ?? row.classification)}</td><td style={tableCellStyle}>{formatCurrency(row.realised_gain_loss ?? row.gain_loss)}</td></tr>)}</tbody></table></div>}
      </div>
    </>
  );

  const renderDeductions = () => (
    <div style={panelStyle}>
      <h3 style={{ marginTop: 0 }}>Deductions and exempt income</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "12px" }}>
        <div style={cardStyle}><div style={labelStyle}>Verified deductions</div><div style={valueStyle}>{formatCurrency(deductions.verified_amount)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>{deductions.status || "Status unavailable"}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Verified exempt income</div><div style={valueStyle}>{formatCurrency(exemptIncome.verified_amount)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>{exemptIncome.status || "Status unavailable"}</div></div>
      </div>
      <p style={{ color: "rgba(255,255,255,0.62)", fontSize: "13px", lineHeight: 1.7, marginBottom: 0 }}>
        The current engine may report no verified claims because a dedicated verified-claims ledger is not available. These figures are not a request to claim deductions; enter and verify supporting data through the relevant backend module before relying on them.
      </p>
    </div>
  );

  const renderTaxCalculation = () => (
    <>
      <div style={panelStyle}>
        <h3 style={{ marginTop: 0 }}>Calculation settings</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", alignItems: "end" }}>
          <label style={{ display: "grid", gap: "7px", fontSize: "12px", color: "rgba(255,255,255,0.65)" }}>Financial year<select value={financialYear} onChange={e => setFinancialYear(e.target.value)} style={{ padding: "11px", borderRadius: "10px", background: "#151525", color: "white", border: "1px solid rgba(255,255,255,0.12)" }}><option value="2025-26">2025-26</option><option value="2026-27">2026-27</option></select></label>
          <label style={{ display: "grid", gap: "7px", fontSize: "12px", color: "rgba(255,255,255,0.65)" }}>Tax regime framework<select value={taxRegime} onChange={e => setTaxRegime(e.target.value)} style={{ padding: "11px", borderRadius: "10px", background: "#151525", color: "white", border: "1px solid rgba(255,255,255,0.12)" }}><option value="new">New regime</option><option value="old">Old regime</option></select></label>
          <label style={{ display: "flex", alignItems: "center", gap: "9px", fontSize: "12px", color: "rgba(255,255,255,0.65)", minHeight: "42px" }}><input type="checkbox" checked={sttConfirmed} onChange={e => setSttConfirmed(e.target.checked)} /> Confirm applicable STT condition for STCG</label>
          <button type="button" className="primary-button" onClick={loadTaxData} disabled={loading}>{loading ? "Calculating..." : "Refresh / Calculate"}</button>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
        <div style={cardStyle}><div style={labelStyle}>STCG tax</div><div style={valueStyle}>{formatCurrency(tax?.stcg?.tax)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>{tax?.stcg?.status || "Awaiting calculation"}</div></div>
        <div style={cardStyle}><div style={labelStyle}>LTCG tax</div><div style={valueStyle}>{formatCurrency(tax?.ltcg?.tax)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>Taxable gain: {formatCurrency(tax?.ltcg?.taxable_gain)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Base tax</div><div style={valueStyle}>{formatCurrency(taxSummary.base_tax)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Health & education cess</div><div style={valueStyle}>{formatCurrency(taxSummary.health_education_cess)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Total calculated tax + cess</div><div style={valueStyle}>{formatCurrency(taxSummary.tax_plus_cess)}</div></div>
      </div>
      <div style={{ ...panelStyle, color: "rgba(255,255,255,0.6)", fontSize: "12px", lineHeight: 1.7 }}>This tax-calculation endpoint estimates tax on qualifying realised capital gains only. It does not calculate complete ITR liability, slab-rate tax, surcharge, rebate or all deductions. The selected tax regime is used by the provisional taxable-income endpoint and does not convert this special-rate calculation into a complete tax assessment.</div>
    </>
  );

  const renderReport = () => (
    <div style={panelStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
        <div><h3 style={{ margin: "0 0 6px" }}>ITR readiness report</h3><p style={{ color: "rgba(255,255,255,0.5)", fontSize: "12px", margin: 0 }}>Financial year {financialYear} · {taxRegime === "new" ? "New" : "Old"} regime framework</p></div>
        <button className="secondary-button" type="button" onClick={loadTaxData} disabled={loading}>{loading ? "Refreshing..." : "Refresh report"}</button>
      </div>
      {reportData && (() => {
        // Safely read the report sections returned by the API.
        const reportPeriod = reportData.period || {};
        const taxpayer = reportData.taxpayer || {};
        const reportIncome = reportData.income || {};
        const reportGains = reportData.capital_gains || {};
        const reportSales = Array.isArray(reportGains.sales) ? reportGains.sales : [];
        const incomeHeads = [
          ["Salary", reportIncome.salary],
          ["House property", reportIncome.house_property],
          ["Business / profession", reportIncome.business_or_profession],
          ["Other sources", reportIncome.other_sources],
        ];
        const smallLabel = { color: "rgba(255,255,255,0.5)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "6px" };
        const reportValue = { fontSize: "16px", fontWeight: 750, overflowWrap: "anywhere" };
        const safeAmount = (value) => value == null || value === "" ? "Unavailable" : formatCurrency(value);
        return <div style={{ display: "grid", gap: "14px", marginTop: "18px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(135px, 1fr))", gap: "10px" }}>
            <div style={cardStyle}><div style={smallLabel}>Report status</div><div style={reportValue}>{String(reportData.status || "Unknown")}</div><div style={{ color: "rgba(134,239,172,0.9)", fontSize: "11px", marginTop: "6px" }}>{reportData.read_only ? "Read-only report" : "Review report"}</div></div>
            <div style={cardStyle}><div style={smallLabel}>Financial year</div><div style={reportValue}>{reportData.financial_year || financialYear}</div></div>
            <div style={cardStyle}><div style={smallLabel}>Assessment year</div><div style={reportValue}>{reportData.assessment_year || "Unavailable"}</div></div>
            <div style={cardStyle}><div style={smallLabel}>Tax regime</div><div style={reportValue}>{taxpayer.regime === "old" ? "Old regime" : taxpayer.regime === "new" ? "New regime" : taxRegime === "new" ? "New regime" : "Old regime"}</div></div>
          </div>
          <div style={panelStyle}>
            <h4 style={{ margin: "0 0 12px" }}>Return period</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "12px" }}>
              <div><div style={smallLabel}>Start date</div><div>{reportPeriod.start_date || "Unavailable"}</div></div>
              <div><div style={smallLabel}>End date</div><div>{reportPeriod.end_date || "Unavailable"}</div></div>
              <div><div style={smallLabel}>Taxpayer type</div><div>{taxpayer.taxpayer_type || "Unavailable"}</div></div>
              <div><div style={smallLabel}>STT confirmed</div><div>{taxpayer.stt_confirmed == null ? "Unavailable" : taxpayer.stt_confirmed ? "Yes" : "No"}</div></div>
            </div>
          </div>
          <div style={panelStyle}>
            <h4 style={{ margin: "0 0 12px" }}>Income information</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))", gap: "10px" }}>
              {incomeHeads.map(([label, item]) => <div key={label} style={cardStyle}><div style={smallLabel}>{label}</div><div style={reportValue}>{safeAmount(item?.amount)}</div><div style={{ color: "rgba(255,255,255,0.55)", fontSize: "11px", marginTop: "6px" }}>{item?.available === true ? "Available" : item?.available === false ? "Source data unavailable" : "Status unavailable"}</div></div>)}
            </div>
            <div style={{ marginTop: "12px", color: "rgba(255,255,255,0.6)", fontSize: "12px" }}>Other sources total: <strong>{safeAmount(reportIncome.other_sources?.total)}</strong></div>
          </div>
          <div style={panelStyle}>
            <h4 style={{ margin: "0 0 12px" }}>Capital gains summary</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))", gap: "10px" }}>
              {[["STCG before set-off", reportGains.stcg_before_setoff], ["LTCG before set-off", reportGains.ltcg_before_setoff], ["STCG after set-off", reportGains.stcg_after_setoff], ["LTCG after set-off", reportGains.ltcg_after_setoff], ["Unclassified gain", reportGains.unclassified_gain]].map(([label, value]) => <div key={label} style={cardStyle}><div style={smallLabel}>{label}</div><div style={reportValue}>{safeAmount(value)}</div></div>)}
            </div>
            <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "12px", marginBottom: 0 }}>Sales reported: {Number(reportGains.sales_count ?? reportSales.length)}</p>
            {reportSales.length > 0 && <div style={{ overflowX: "auto", marginTop: "12px" }}><table style={{ width: "100%", borderCollapse: "collapse", minWidth: "460px" }}><thead><tr>{["Investment", "Sale date", "Quantity", "Gain", "Class"].map(label => <th key={label} style={{ ...tableCellStyle, color: "rgba(255,255,255,0.55)" }}>{label}</th>)}</tr></thead><tbody>{reportSales.map((sale, index) => <tr key={sale.sale_transaction_id || `${sale.investment_id || "sale"}-${index}`}><td style={tableCellStyle}>{sale.name || sale.symbol || `Investment ${sale.investment_id ?? ""}`}</td><td style={tableCellStyle}>{sale.sale_date || "—"}</td><td style={tableCellStyle}>{sale.quantity ?? "—"}</td><td style={tableCellStyle}>{safeAmount(sale.gain)}</td><td style={tableCellStyle}>{sale.classification || "—"}</td></tr>)}</tbody></table></div>}
          </div>
          <details style={{ ...panelStyle, color: "rgba(255,255,255,0.65)" }}><summary style={{ cursor: "pointer", fontWeight: 700 }}>Advanced: view raw report data</summary><pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontSize: "11px", lineHeight: 1.5, marginTop: "12px" }}>{JSON.stringify(reportData, null, 2)}</pre></details>
        </div>;
      })()}
      {!reportData && <div style={{ marginTop: "18px", padding: "14px", borderRadius: "12px", background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)", color: "#fcd34d", fontSize: "12px", lineHeight: 1.7 }}>The ITR report endpoint did not return data. Check that the report route is deployed and review the API error. The provisional income summary below is still available when its endpoint succeeds.</div>}
      <div style={{ marginTop: "18px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
        <div style={cardStyle}><div style={labelStyle}>Provisional taxable income</div><div style={valueStyle}>{formatCurrency(taxable.provisional_taxable_income)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Verified deductions</div><div style={valueStyle}>{formatCurrency(deductions.verified_amount)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Indicative capital-gains tax + cess</div><div style={valueStyle}>{formatCurrency(taxSummary.tax_plus_cess)}</div></div>
      </div>
      <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "12px", lineHeight: 1.7, marginBottom: 0 }}>This is a review aid, not a filed return or tax-professional certification. Verify income heads, deductions, tax regime, realised transactions and applicable law before filing.</p>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
      {/* Tax Centre header */}
      <section style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "14px", flexWrap: "wrap" }}>
        <div><p className="card-label">FINANCIAL OS / TAX</p><h2 style={{ margin: "4px 0 6px", fontSize: "28px", fontWeight: 800 }}>Tax Centre</h2><p style={{ margin: 0, color: "rgba(255,255,255,0.55)", fontSize: "13px" }}>Income, capital gains, deductions and tax-report readiness in one place.</p></div>
        <button className="secondary-button" type="button" onClick={loadTaxData} disabled={loading}>{loading ? "Loading..." : "Refresh tax data"}</button>
      </section>

      {/* Financial year and regime quick selectors */}
      <section style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
        <span style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px" }}>FINANCIAL YEAR</span>
        <strong>{financialYear}</strong><span style={{ color: "rgba(255,255,255,0.3)" }}>•</span><span style={{ color: "rgba(255,255,255,0.6)", fontSize: "12px" }}>{taxRegime === "new" ? "New regime framework" : "Old regime framework"}</span>
      </section>

      {/* Six section tabs */}
      <nav aria-label="Tax sections" style={{ display: "flex", gap: "8px", flexWrap: "wrap", paddingBottom: "4px" }}>
        {sections.map((item) => <button key={item} type="button" onClick={() => setSection(item)} className={section === item ? "primary-button" : "secondary-button"} style={{ padding: "10px 13px", fontSize: "12px" }}>{item}</button>)}
      </nav>

      {error && <div style={{ padding: "13px 15px", borderRadius: "12px", border: "1px solid rgba(239,68,68,0.25)", background: "rgba(239,68,68,0.08)", color: "#fca5a5", fontSize: "13px" }}>{error}</div>}
      {notice && !error && <div style={{ color: "#86efac", fontSize: "12px" }}>{notice}</div>}
      {loading && !taxData && <div className="glass-card" style={{ padding: "18px" }}>Loading tax data from the Financial OS API...</div>}

      <TaxSectionErrorBoundary key={section}>
        {section === "Overview" && renderOverview()}
        {section === "Income" && renderIncome()}
        {section === "Capital Gains" && renderCapitalGains()}
        {section === "Deductions" && renderDeductions()}
        {section === "Tax Calculation" && renderTaxCalculation()}
        {section === "Tax Report" && renderReport()}
      </TaxSectionErrorBoundary>

      <style>{`
        @media (max-width: 600px) {
          .tax-centre-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}

// ============================================================
// MARKETS WORKSPACE — existing read-only m.Stock/AWS APIs
// ============================================================
function MarketsPage() {
  const API = "https://ai-finance-trading-os-api.onrender.com";
  const [overview, setOverview] = useState(null);
  const [busy, setBusy] = useState(true);
  const [overviewError, setOverviewError] = useState("");
  const [query, setQuery] = useState("RELIANCE");
  const [exchange, setExchange] = useState("NSE");
  const [results, setResults] = useState([]);
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [quote, setQuote] = useState(null);
  const [quoteBusy, setQuoteBusy] = useState(false);
  const [quoteError, setQuoteError] = useState("");
  const [updated, setUpdated] = useState("");
  // Historical chart state — uses the existing read-only backend route.
  const [chartSymbol, setChartSymbol] = useState("RELIANCE");
  const [chartExchange, setChartExchange] = useState("NSE");
  const [chartRange, setChartRange] = useState("1M");
  const [chartData, setChartData] = useState([]);
  const [chartInfo, setChartInfo] = useState(null);
  const [chartBusy, setChartBusy] = useState(false);
  const [chartError, setChartError] = useState("");

  const card = { padding: "16px", borderRadius: "15px", border: "1px solid rgba(255,255,255,0.09)", background: "linear-gradient(135deg, rgba(255,255,255,0.065), rgba(255,255,255,0.02))", minWidth: 0 };
  const muted = { color: "rgba(255,255,255,0.55)", fontSize: "12px", lineHeight: 1.6 };
  const input = { width: "100%", boxSizing: "border-box", padding: "11px 12px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.12)", background: "#151525", color: "white", fontSize: "13px" };
  const money = (value) => {
    if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return "—";
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(Number(value));
  };

  const refresh = async () => {
    setBusy(true); setOverviewError("");
    try {
      const response = await fetch(`${API}/api/market-overview/`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Market overview returned ${response.status}`);
      setOverview(data); setUpdated(new Date().toLocaleString("en-IN"));
      if (data?.status === "error") setOverviewError("Market provider returned no usable data. Check the gateway.");
      else if (Array.isArray(data?.errors) && data.errors.length) setOverviewError("Some market sources are unavailable; available results are shown.");
    } catch (e) { setOverviewError(e?.message || "Unable to load market overview."); }
    finally { setBusy(false); }
  };
  useEffect(() => { refresh(); }, []);

  const search = async (event) => {
    event.preventDefault();
    if (!query.trim()) { setSearchError("Enter a company name or symbol."); return; }
    setSearchBusy(true); setSearchError(""); setResults([]); setQuote(null); setQuoteError("");
    try {
      const response = await fetch(`${API}/api/market-search/?query=${encodeURIComponent(query.trim())}&exchange=${encodeURIComponent(exchange)}&limit=20`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Search returned ${response.status}`);
      const rows = Array.isArray(data?.results) ? data.results : [];
      setResults(rows); if (!rows.length) setSearchError("No matching instruments returned.");
    } catch (e) { setSearchError(e?.message || "Market search failed."); }
    finally { setSearchBusy(false); }
  };
  const getQuote = async (symbol) => {
    if (!symbol) return;
    setQuoteBusy(true); setQuoteError(""); setQuote(null);
    try {
      const response = await fetch(`${API}/api/market-quote/?symbol=${encodeURIComponent(symbol)}`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Quote returned ${response.status}`);
      setQuote(data);
    } catch (e) { setQuoteError(e?.message || "Quote unavailable."); }
    finally { setQuoteBusy(false); }
  };

  // Fetch historical daily candles from the existing Market Charts API.
  const loadChart = async (symbol = chartSymbol, marketExchange = chartExchange, range = chartRange) => {
    if (!symbol) { setChartError("Choose a stock before loading its chart."); return; }
    const daysByRange = { "1M": 30, "3M": 90, "6M": 180, "1Y": 365 };
    const toDate = new Date();
    const fromDate = new Date(toDate);
    fromDate.setDate(fromDate.getDate() - (daysByRange[range] || 30));
    const isoDate = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    setChartBusy(true); setChartError(""); setChartData([]); setChartInfo(null);
    try {
      const url = `${API}/api/market-charts/?symbol=${encodeURIComponent(symbol)}&exchange=${encodeURIComponent(marketExchange)}&interval=day&from=${isoDate(fromDate)}&to=${isoDate(toDate)}`;
      const response = await fetch(url);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Historical data returned ${response.status}`);
      const rows = Array.isArray(data?.data) ? data.data : [];
      const validRows = rows.map((row) => ({ ...row, close: Number(row.close) })).filter((row) => Number.isFinite(row.close) && row.close > 0);
      setChartData(validRows); setChartInfo(data?.chart || null);
      if (!validRows.length) setChartError("The historical-data API responded, but no usable daily prices were returned for this period.");
    } catch (e) {
      setChartError(e?.message || "Unable to load historical prices. Check the market gateway and symbol.");
    } finally { setChartBusy(false); }
  };

  const chooseChart = (symbol, marketExchange) => {
    setChartSymbol(symbol || "RELIANCE"); setChartExchange(marketExchange || "NSE");
    loadChart(symbol || "RELIANCE", marketExchange || "NSE", chartRange);
  };

  const indices = Array.isArray(overview?.indices) ? overview.indices : [];
  const movers = overview?.market_movers || {};
  const gainers = Array.isArray(movers.gainers) ? movers.gainers : [];
  const losers = Array.isArray(movers.losers) ? movers.losers : [];
  return <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
    <section style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap" }}><div><p className="card-label">FINANCIAL OS / MARKETS</p><h2 style={{ margin: "4px 0 6px", fontSize: "28px", fontWeight: 800 }}>Market Workspace</h2><p style={{ ...muted, margin: 0 }}>Indian market overview, stock search and quotes.</p></div><button className="secondary-button" type="button" onClick={refresh} disabled={busy}>{busy ? "Refreshing..." : "Refresh market data"}</button></section>
    <p style={{ ...muted, margin: 0 }}>Existing m.Stock gateway via Financial OS API · Read-only · No database writes{updated ? ` · Updated ${updated}` : ""}</p>
    {overviewError && <div role="status" style={{ padding: "12px 14px", borderRadius: "12px", color: "#fcd34d", background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)", fontSize: "12px" }}>{overviewError}</div>}
    <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
      {busy && !indices.length ? <div style={card}>Loading market indices...</div> : indices.length ? indices.map((row, i) => <div key={`${row.name || row.symbol || "index"}-${i}`} style={card}><div style={muted}>{row.name || row.symbol || "Index"}</div><div style={{ fontSize: "23px", fontWeight: 800, marginTop: "7px" }}>{row.last_price == null || !Number.isFinite(Number(row.last_price)) ? "Unavailable" : Number(row.last_price).toLocaleString("en-IN", { maximumFractionDigits: 2 })}</div><div style={{ ...muted, marginTop: "6px" }}>{row.exchange || "Exchange"} · {row.status || "Latest available"}</div></div>) : <div style={card}><strong>Indices unavailable</strong><p style={muted}>Refresh later or check the market gateway.</p></div>}
      <div style={card}><div style={muted}>Gainers returned</div><div style={{ fontSize: "23px", fontWeight: 800, marginTop: "7px" }}>{gainers.length}</div></div><div style={card}><div style={muted}>Losers returned</div><div style={{ fontSize: "23px", fontWeight: 800, marginTop: "7px" }}>{losers.length}</div></div>
    </section>
    <section style={card}><h3 style={{ margin: "0 0 5px" }}>Find a stock or instrument</h3><p style={{ ...muted, marginTop: 0 }}>Search the existing instrument master, then request a quote for a result.</p><form onSubmit={search} style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 100px auto", gap: "9px", alignItems: "center" }}><input aria-label="Company name or symbol" style={input} value={query} onChange={e => setQuery(e.target.value)} placeholder="Company or symbol"/><select aria-label="Exchange" style={input} value={exchange} onChange={e => setExchange(e.target.value)}><option value="NSE">NSE</option><option value="BSE">BSE</option></select><button className="primary-button" type="submit" disabled={searchBusy}>{searchBusy ? "Searching..." : "Search"}</button></form>
      {searchError && <p role="status" style={{ color: "#fca5a5", fontSize: "12px" }}>{searchError}</p>}
      {results.map((row, i) => <div key={`${row.exchange || exchange}-${row.symbol || row.instrument_token || i}`} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", padding: "12px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", flexWrap: "wrap" }}><div><strong>{row.symbol || "Unknown symbol"}</strong><div style={muted}>{row.name || "Company name unavailable"} · {row.exchange || exchange}</div></div><div style={{ display: "flex", gap: "10px", alignItems: "center" }}><strong style={{ fontSize: "12px" }}>{money(row.last_price)}</strong><button type="button" className="secondary-button" onClick={() => getQuote(row.symbol)}>Get quote</button><button type="button" className="secondary-button" onClick={() => chooseChart(row.symbol, row.exchange || exchange)}>Chart</button></div></div>)}
    </section>
    {(quote || quoteBusy || quoteError) && <section style={card}><h3 style={{ marginTop: 0 }}>Latest quote</h3>{quoteBusy && <p style={muted}>Fetching quote...</p>}{quoteError && <p role="status" style={{ color: "#fca5a5", fontSize: "12px" }}>{quoteError}</p>}{quote && <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap" }}><div><div style={muted}>{quote.symbol} · {quote.source?.provider || "Market provider"}</div><div style={{ fontSize: "28px", fontWeight: 850, marginTop: "5px" }}>{money(quote.quote?.last_price)}</div></div><div style={muted}>Updated: {quote.last_updated ? new Date(quote.last_updated).toLocaleString("en-IN") : "Timestamp unavailable"}</div></div>}</section>}
    {/* Historical price chart — read-only, powered by /api/market-charts/ */}
    <section style={card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
        <div><h3 style={{ margin: "0 0 4px" }}>Historical price chart</h3><p style={{ ...muted, margin: 0 }}>{chartInfo ? `${chartInfo.symbol || chartSymbol} · ${chartInfo.exchange || chartExchange} · Daily close` : "Choose a stock and period to load daily closing prices."}</p></div>
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>{["1M", "3M", "6M", "1Y"].map((range) => <button key={range} type="button" className={chartRange === range ? "primary-button" : "secondary-button"} style={{ padding: "8px 10px", fontSize: "11px" }} onClick={() => { setChartRange(range); loadChart(chartSymbol, chartExchange, range); }}>{range}</button>)}</div>
      </div>
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "12px" }}><input aria-label="Chart stock symbol" style={{ ...input, maxWidth: "220px" }} value={chartSymbol} onChange={(e) => setChartSymbol(e.target.value.toUpperCase())} placeholder="e.g. RELIANCE"/><select aria-label="Chart exchange" style={{ ...input, width: "100px" }} value={chartExchange} onChange={(e) => setChartExchange(e.target.value)}><option value="NSE">NSE</option><option value="BSE">BSE</option></select><button type="button" className="secondary-button" disabled={chartBusy} onClick={() => loadChart()}>{chartBusy ? "Loading chart..." : "Load chart"}</button></div>
      {chartError && <p role="status" style={{ color: "#fcd34d", fontSize: "12px", lineHeight: 1.6, marginBottom: 0 }}>{chartError}</p>}
      {chartBusy && <p style={muted}>Requesting historical prices from the existing market API...</p>}
      {!chartBusy && chartData.length > 1 && (() => {
        const values = chartData.map((row) => row.close);
        const min = Math.min(...values); const max = Math.max(...values); const span = max - min || 1;
        const width = 720; const height = 240; const pad = 18;
        const points = values.map((value, i) => `${pad + i * (width - pad * 2) / Math.max(values.length - 1, 1)},${height - pad - ((value - min) / span) * (height - pad * 2)}`).join(" ");
        const first = values[0]; const last = values[values.length - 1]; const change = last - first; const percent = first ? (change / first) * 100 : 0;
        return <div style={{ marginTop: "14px" }}><div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap", marginBottom: "8px" }}><div><div style={muted}>Latest close</div><strong style={{ fontSize: "22px" }}>{money(last)}</strong></div><div style={{ textAlign: "right" }}><div style={muted}>Change over period</div><strong style={{ color: change >= 0 ? "#86efac" : "#fca5a5" }}>{change >= 0 ? "+" : ""}{money(change)} ({percent >= 0 ? "+" : ""}{percent.toFixed(2)}%)</strong></div></div><div style={{ width: "100%", overflow: "hidden" }}><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${chartSymbol} historical daily closing-price chart`} style={{ display: "block", width: "100%", minHeight: "150px" }}><line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="rgba(255,255,255,0.18)" strokeWidth="1"/><line x1={pad} y1={height/2} x2={width-pad} y2={height/2} stroke="rgba(255,255,255,0.08)" strokeWidth="1"/><polyline points={points} fill="none" stroke="#c084fc" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round"/></svg></div><div style={{ display: "flex", justifyContent: "space-between", ...muted }}><span>{String(chartData[0].timestamp || "").slice(0, 10)}</span><span>{chartData.length} daily records</span><span>{String(chartData[chartData.length - 1].timestamp || "").slice(0, 10)}</span></div></div>;
      })()}
      {!chartBusy && !chartError && chartData.length === 1 && <p style={muted}>Only one historical price was returned; at least two points are needed to draw a chart.</p>}
      {!chartBusy && !chartData.length && !chartError && <p style={muted}>No chart loaded yet. Select a period and tap Load chart.</p>}
      <p style={{ ...muted, marginBottom: 0, marginTop: "12px" }}>Historical prices may be delayed or unavailable. This chart uses daily closing prices and is for research only; it does not place trades.</p>
    </section>
    <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "14px" }}>{[{ title: "Top gainers", rows: gainers }, { title: "Top losers", rows: losers }].map(group => <div key={group.title} style={card}><h3 style={{ margin: "0 0 12px" }}>{group.title}</h3>{!group.rows.length ? <p style={muted}>No rows returned by the provider.</p> : group.rows.slice(0, 8).map((row, i) => <div key={`${row.symbol || "item"}-${i}`} style={{ display: "flex", justifyContent: "space-between", gap: "12px", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.06)" }}><div><strong style={{ fontSize: "12px" }}>{row.symbol || row.name || "Instrument"}</strong><div style={muted}>{row.name || row.exchange || ""}</div></div><div style={{ textAlign: "right", whiteSpace: "nowrap" }}><div style={{ fontSize: "12px", fontWeight: 700 }}>{money(row.ltp)}</div><div style={{ color: Number(row.percent_change) < 0 ? "#fca5a5" : "#86efac", fontSize: "11px" }}>{row.percent_change == null ? "Change unavailable" : `${row.percent_change}%`}</div></div></div>)}</div>)}</section>
    <p style={{ ...muted, margin: 0 }}>Data may be delayed or unavailable when the provider or exchange is closed. Verify quotes with your broker before making investment decisions. This workspace does not place trades.</p>
  </div>;
}

// ============================================================
// PLAN / GOALS
// PHASE 1: ACTIVATE THE PLAN PAGE USING THE EXISTING API
// This page is read-only for now; it does not change accounts
// or transactions and does not pretend goals are persisted.
// ============================================================

function PlanPage() {
  // Persistent financial goals API. Keep USER_ID consistent with existing app.
  const API_BASE_URL = "https://ai-finance-trading-os-api.onrender.com";
  const USER_ID = 1;
  const categories = ["Emergency Fund", "Savings", "House", "Car", "Education", "Financial Independence", "Retirement", "Major Purchase", "Other"];
  const [goals, setGoals] = useState([]);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editingId, setEditingId] = useState(null);
  const emptyForm = { name: "", category: "Emergency Fund", target_amount: "100000", current_amount: "0", target_date: "", monthly_contribution: "5000", notes: "", status: "active" };
  const [form, setForm] = useState(emptyForm);

  const money = (value) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Number(value || 0));
  const card = { padding: "18px", borderRadius: "16px", border: "1px solid rgba(255,255,255,0.10)", background: "rgba(255,255,255,0.035)", minWidth: 0 };
  const muted = { color: "rgba(255,255,255,0.62)", fontSize: "12px", lineHeight: 1.6 };
  const field = { width: "100%", boxSizing: "border-box", padding: "11px 12px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.14)", background: "rgba(5,10,22,0.75)", color: "inherit", marginTop: "7px" };

  const loadGoals = async () => {
    const response = await fetch(`${API_BASE_URL}/api/goals/?user_id=${USER_ID}`);
    if (!response.ok) throw new Error(`Goals API returned ${response.status}`);
    const data = await response.json();
    if (data.status !== "success") throw new Error("Could not load saved goals.");
    setGoals(data.goals || []);
  };
  const loadPlan = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/financial-plan/?user_id=${USER_ID}`);
      if (response.ok) { const data = await response.json(); if (data.status === "success") setPlan(data); }
    } catch (e) { console.warn("Planning assumptions unavailable", e); }
  };
  const refreshAll = async () => {
    setLoading(true); setError("");
    try { await Promise.all([loadGoals(), loadPlan()]); }
    catch (e) { console.error(e); setError(`${e.message}. Check that the backend goals route is deployed and the database table was created.`); }
    finally { setLoading(false); }
  };
  useEffect(() => { refreshAll(); }, []);

  const updateForm = (key, value) => setForm(prev => ({ ...prev, [key]: value }));
  const resetForm = () => { setForm({ ...emptyForm, monthly_contribution: String(Math.max(0, Number(plan?.investment_planning?.monthly_contribution_capacity || 5000))) }); setEditingId(null); };
  const submitGoal = async (event) => {
    event.preventDefault(); setSaving(true); setError(""); setSuccess("");
    if (!form.name.trim()) { setError("Enter a goal name."); setSaving(false); return; }
    if (!(Number(form.target_amount) > 0)) { setError("Target amount must be greater than zero."); setSaving(false); return; }
    const payload = { user_id: USER_ID, name: form.name.trim(), category: form.category, target_amount: Number(form.target_amount), current_amount: Number(form.current_amount || 0), target_date: form.target_date || null, monthly_contribution: Number(form.monthly_contribution || 0), notes: form.notes.trim() || null, status: form.status };
    try {
      const response = await fetch(`${API_BASE_URL}/api/goals/${editingId ? `${editingId}` : ""}`, { method: editingId ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Save failed (${response.status})`);
      await loadGoals(); resetForm(); setSuccess(editingId ? "Goal updated successfully." : "Goal saved successfully. It will remain available after refresh.");
    } catch (e) { setError(e.message || "Could not save goal."); }
    finally { setSaving(false); }
  };
  const editGoal = (goal) => { setEditingId(goal.id); setForm({ name: goal.name, category: goal.category || "Other", target_amount: String(goal.target_amount), current_amount: String(goal.current_amount), target_date: goal.target_date || "", monthly_contribution: String(goal.monthly_contribution || 0), notes: goal.notes || "", status: goal.status || "active" }); setSuccess(""); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const removeGoal = async (goal) => {
    if (!window.confirm(`Delete goal “${goal.name}”? This will not change any account balance or transaction.`)) return;
    setError(""); setSuccess("");
    try { const response = await fetch(`${API_BASE_URL}/api/goals/${goal.id}?user_id=${USER_ID}`, { method: "DELETE" }); const data = await response.json().catch(() => ({})); if (!response.ok) throw new Error(data.detail || `Delete failed (${response.status})`); setGoals(prev => prev.filter(g => g.id !== goal.id)); if (editingId === goal.id) resetForm(); setSuccess("Goal deleted."); }
    catch (e) { setError(e.message || "Could not delete goal."); }
  };

  const totalTarget = goals.filter(g => g.status === "active").reduce((sum, g) => sum + Number(g.target_amount || 0), 0);
  const totalSaved = goals.filter(g => g.status === "active").reduce((sum, g) => sum + Number(g.current_amount || 0), 0);
  const totalMonthly = goals.filter(g => g.status === "active").reduce((sum, g) => sum + Number(g.monthly_contribution || 0), 0);
  const remaining = Math.max(0, Number(form.target_amount || 0) - Number(form.current_amount || 0));
  const monthly = Math.max(0, Number(form.monthly_contribution || 0));
  const monthsNeeded = monthly > 0 ? Math.ceil(remaining / monthly) : null;
  const dateObj = form.target_date ? new Date(`${form.target_date}T00:00:00`) : null;
  const monthsAvailable = dateObj && !Number.isNaN(dateObj.getTime()) ? Math.max(0, (dateObj.getFullYear() - new Date().getFullYear()) * 12 + dateObj.getMonth() - new Date().getMonth()) : null;
  const requiredMonthly = monthsAvailable > 0 ? remaining / monthsAvailable : (remaining === 0 ? 0 : null);
  const progress = Number(form.target_amount) > 0 ? Math.min(100, Number(form.current_amount || 0) / Number(form.target_amount) * 100) : 0;

  return <div style={{ display: "grid", gap: "18px" }}>
    <section style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "14px", flexWrap: "wrap" }}>
      <div><p className="card-label">FINANCIAL OS · PLAN</p><h2 style={{ margin: "6px 0" }}>Plan & Goals</h2><p style={{ ...muted, maxWidth: "680px", fontSize: "13px" }}>Create and save goals, track progress, and calculate the contribution required to reach your target. Goals are stored separately and do not change account balances.</p></div>
      <button type="button" onClick={refreshAll} disabled={loading} className="secondary-button">{loading ? "Refreshing…" : "Refresh goals"}</button>
    </section>
    {error && <div role="alert" style={{ ...card, borderColor: "rgba(248,113,113,.45)", color: "#fca5a5" }}>{error}</div>}
    {success && <div role="status" style={{ ...card, borderColor: "rgba(74,222,128,.35)", color: "#86efac" }}>{success}</div>}

    <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "12px" }}>
      {[{ label: "Active goals", value: goals.filter(g => g.status === "active").length }, { label: "Total target amount", value: money(totalTarget) }, { label: "Saved / allocated", value: money(totalSaved) }, { label: "Planned monthly total", value: money(totalMonthly) }].map(item => <div key={item.label} style={card}><div style={muted}>{item.label}</div><div style={{ fontSize: "clamp(21px,3vw,28px)", fontWeight: 800, marginTop: "8px" }}>{item.value}</div></div>)}
    </section>

    <section style={card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap" }}><div><h3 style={{ margin: "0 0 5px" }}>{editingId ? "Edit financial goal" : "Create a financial goal"}</h3><p style={muted}>Your goals are saved to the backend. Enter an amount you have actually saved or allocated; this form does not move money.</p></div>{editingId && <button type="button" className="secondary-button" onClick={resetForm}>Cancel edit</button>}</div>
      <form onSubmit={submitGoal} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))", gap: "14px", marginTop: "14px" }}>
        <label style={muted}>Goal name *<input required maxLength={150} value={form.name} onChange={e => updateForm("name", e.target.value)} style={field} placeholder="e.g. Emergency fund" /></label>
        <label style={muted}>Category<select value={form.category} onChange={e => updateForm("category", e.target.value)} style={field}>{categories.map(c => <option key={c}>{c}</option>)}</select></label>
        <label style={muted}>Target amount (₹) *<input required type="number" min="1" step="0.01" value={form.target_amount} onChange={e => updateForm("target_amount", e.target.value)} style={field} /></label>
        <label style={muted}>Already saved / allocated (₹)<input type="number" min="0" step="0.01" value={form.current_amount} onChange={e => updateForm("current_amount", e.target.value)} style={field} /></label>
        <label style={muted}>Target date<input type="date" min={new Date().toISOString().slice(0,10)} value={form.target_date} onChange={e => updateForm("target_date", e.target.value)} style={field} /></label>
        <label style={muted}>Monthly contribution (₹)<input type="number" min="0" step="0.01" value={form.monthly_contribution} onChange={e => updateForm("monthly_contribution", e.target.value)} style={field} /></label>
        <label style={muted}>Status<select value={form.status} onChange={e => updateForm("status", e.target.value)} style={field}><option value="active">Active</option><option value="paused">Paused</option><option value="completed">Completed</option></select></label>
        <label style={{ ...muted, gridColumn: "1 / -1" }}>Notes (optional)<textarea rows="2" value={form.notes} onChange={e => updateForm("notes", e.target.value)} style={{ ...field, resize: "vertical" }} placeholder="Any details about this goal" /></label>
        <div style={{ gridColumn: "1 / -1", display: "flex", gap: "10px", flexWrap: "wrap" }}><button type="submit" disabled={saving} className="primary-button">{saving ? "Saving…" : editingId ? "Save changes" : "Save goal"}</button><button type="button" className="secondary-button" onClick={resetForm}>Clear form</button></div>
      </form>
    </section>

    <section style={card}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center", flexWrap: "wrap" }}><h3 style={{ margin: 0 }}>My saved goals</h3><span style={muted}>{goals.length} saved</span></div>
      {loading ? <p style={muted}>Loading saved goals…</p> : goals.length === 0 ? <div style={{ marginTop: "14px", padding: "18px", borderRadius: "12px", background: "rgba(255,255,255,.025)", border: "1px dashed rgba(255,255,255,.14)" }}><strong>No saved goals yet</strong><p style={muted}>Use the form above to create your first goal. Suggested categories include Emergency Fund, House, Car, Education, Retirement and Financial Independence.</p><button type="button" className="primary-button" onClick={() => { updateForm("name", "Emergency Fund"); updateForm("category", "Emergency Fund"); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Start with an emergency fund</button></div> : <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: "12px", marginTop: "14px" }}>{goals.map(goal => { const pct = Math.min(100, Number(goal.progress_percent || 0)); return <article key={goal.id} style={{ ...card, padding: "15px" }}><div style={{ display: "flex", justifyContent: "space-between", gap: "10px", alignItems: "flex-start" }}><div><span style={{ ...muted, textTransform: "uppercase", letterSpacing: ".06em" }}>{goal.category} · {goal.status}</span><h4 style={{ margin: "7px 0" }}>{goal.name}</h4></div><Target size={19} /></div><div style={{ fontSize: "22px", fontWeight: 800 }}>{money(goal.current_amount)} <span style={{ ...muted, fontWeight: 400 }}>of {money(goal.target_amount)}</span></div><div style={{ display: "flex", justifyContent: "space-between", ...muted, margin: "10px 0 6px" }}><span>Progress</span><strong>{pct.toFixed(1)}%</strong></div><div style={{ height: "8px", background: "rgba(255,255,255,.10)", borderRadius: "99px", overflow: "hidden" }}><div style={{ width: `${pct}%`, height: "100%", background: "linear-gradient(90deg,#a855f7,#ec4899)" }} /></div><div style={{ ...muted, marginTop: "10px" }}>Remaining: {money(goal.remaining_amount)}<br/>Monthly contribution: {money(goal.monthly_contribution)}<br/>Target date: {goal.target_date || "Not set"}</div>{goal.notes && <p style={muted}>{goal.notes}</p>}<div style={{ display: "flex", gap: "8px", marginTop: "12px" }}><button type="button" className="secondary-button" onClick={() => editGoal(goal)}>Edit</button><button type="button" className="secondary-button" onClick={() => removeGoal(goal)}>Delete</button></div></article>; })}</div>}
    </section>

    <section style={card}>
      <p className="card-label">PLANNING TOOL</p><h3 style={{ margin: "5px 0 8px" }}>Contribution calculator</h3><p style={muted}>The calculator uses the same inputs as the goal form and assumes no interest or investment return.</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "12px", marginTop: "14px" }}>
        {[{label:"Amount remaining",value:money(remaining)},{label:"Required monthly contribution",value:requiredMonthly === null ? "Set target date" : money(requiredMonthly)},{label:"Estimated time at planned amount",value:remaining === 0 ? "Goal reached" : monthsNeeded === null ? "Enter contribution" : `${monthsNeeded} months`}].map(x => <div key={x.label} style={{ ...card, padding: "14px" }}><div style={muted}>{x.label}</div><div style={{ fontSize: "clamp(18px,3vw,25px)", fontWeight: 800, marginTop: "7px" }}>{x.value}</div></div>)}
      </div><div style={{ marginTop: "14px" }}><div style={{ display: "flex", justifyContent: "space-between", ...muted, marginBottom: "7px" }}><span>Current goal progress (form values)</span><strong>{progress.toFixed(1)}%</strong></div><div style={{ height: "8px", background: "rgba(255,255,255,.10)", borderRadius: "99px", overflow: "hidden" }}><div style={{ width: `${progress}%`, height: "100%", background: "linear-gradient(90deg,#a855f7,#ec4899)" }} /></div></div>
      <p style={{ ...muted, marginBottom: 0, marginTop: "12px" }}>{plan?.investment_planning?.monthly_contribution_capacity != null ? `The existing planning API estimates monthly contribution capacity at ${money(plan.investment_planning.monthly_contribution_capacity)}. This is a suggestion, not a saved allocation.` : "Planning assumptions are unavailable; goal calculations still work from your inputs."} Goal records do not change your bank or investment balances.</p>
    </section>
  </div>;
}

// ============================================================
// PLACEHOLDER PAGE
// ============================================================

function PlaceholderPage({ title }) {

  return (
    <div className="placeholder-page">

      <div className="glass-card placeholder-card">

        <div className="placeholder-icon">
          <Sparkles size={30} />
        </div>

        <p className="card-label">
          FINANCIAL OS
        </p>

        <h2>
          {title}
        </h2>

        <p>
          This module is ready for development.
          We will connect it to the Financial OS
          engine in the next stages.
        </p>

      </div>

    </div>
  );
}

// ============================================================
// INVESTMENT TRANSACTIONS
// READ-ONLY INVESTMENT TRANSACTION CONSOLE
// ============================================================
// BUY / SELL creation remains ONLY in Portfolio.
// Money -> Transactions remains completely separate.
// This page is for history, tracking, filtering and sorting.
// ============================================================

function InvestmentTransactions() {

  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";

  const USER_ID = 1;

  // ----------------------------------------------------------
  // STATE
  // ----------------------------------------------------------

  const [transactions, setTransactions] =
    useState([]);

  const [investments, setInvestments] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [filters, setFilters] =
    useState({
      instrumentType: "All",
      instrumentName: "All",
      transactionType: "All",
      sort: "date_desc",
    });

  // ----------------------------------------------------------
  // LOAD INVESTMENT TRANSACTIONS
  // ----------------------------------------------------------

  const loadInvestmentTransactions = async () => {

    try {

      setLoading(true);
      setError("");

      const [
        transactionResponse,
        investmentResponse,
      ] = await Promise.all([
        fetch(
          `${API_BASE_URL}/api/investment-transactions/?user_id=${USER_ID}`
        ),
        fetch(
          `${API_BASE_URL}/api/investments/?user_id=${USER_ID}`
        ),
      ]);

      const transactionData =
        await transactionResponse.json();

      const investmentData =
        await investmentResponse.json();

      if (!transactionResponse.ok) {
        throw new Error(
          transactionData?.detail ||
            "Unable to load investment transactions."
        );
      }

      if (!investmentResponse.ok) {
        throw new Error(
          investmentData?.detail ||
            "Unable to load investments."
        );
      }

      const investmentList =
        Array.isArray(investmentData)
          ? investmentData
          : [];

      const investmentMap =
        new Map(
          investmentList.map(
            (investment) => [
              Number(investment.id),
              investment,
            ]
          )
        );

      const enrichedTransactions =
        (
          Array.isArray(transactionData)
            ? transactionData
            : []
        ).map((transaction) => {

          const investment =
            investmentMap.get(
              Number(transaction.investment_id)
            );

          return {
            ...transaction,
            instrument_name:
              investment?.name ||
              "Unknown Investment",
            instrument_type:
              investment?.investment_type ||
              "Other",
            symbol:
              investment?.symbol ||
              "—",
            broker:
              investment?.broker ||
              "—",
          };

        });

      setInvestments(
        investmentList
      );

      setTransactions(
        enrichedTransactions
      );

    } catch (err) {

      console.error(
        "Investment transaction console error:",
        err
      );

      setError(
        err?.message ||
          "Unable to load investment transactions."
      );

    } finally {

      setLoading(false);

    }

  };

  // ----------------------------------------------------------
  // TRANSACTION MANAGEMENT: EDIT AND VOID
  // ----------------------------------------------------------

  const editInvestmentTransaction = async (transaction) => {
    if (transaction.status && transaction.status !== "ACTIVE") {
      alert("Only active transactions can be edited.");
      return;
    }
    const quantity = window.prompt("Correct quantity:", String(transaction.quantity));
    if (quantity === null) return;
    const price = window.prompt("Correct price per unit:", String(transaction.price));
    if (price === null) return;
    const fees = window.prompt("Correct fees:", String(transaction.fees ?? 0));
    if (fees === null) return;
    const transactionDate = window.prompt("Transaction date (YYYY-MM-DD):", String(transaction.transaction_date).slice(0, 10));
    if (transactionDate === null) return;
    const notes = window.prompt("Notes (optional):", transaction.notes ?? "");
    if (notes === null) return;
    if (!(Number(quantity) > 0) || !(Number(price) > 0) || Number(fees) < 0 || !/^\d{4}-\d{2}-\d{2}$/.test(transactionDate)) {
      alert("Please enter a valid quantity, price, fees and date.");
      return;
    }
    const response = await fetch(`${API_BASE_URL}/api/investment-transactions/${transaction.id}?user_id=${USER_ID}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transaction_type: transaction.transaction_type, quantity, price, fees, transaction_date: transactionDate, notes }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      alert(result?.detail || "Unable to edit transaction.");
      return;
    }
    await loadInvestmentTransactions();
    alert("Transaction updated. Holdings will be recalculated from active transactions.");
  };

  const voidInvestmentTransaction = async (transaction) => {
    if (transaction.status && transaction.status !== "ACTIVE") {
      alert("This transaction is already inactive.");
      return;
    }
    const reason = window.prompt(`Reason for voiding transaction #${transaction.id}:`);
    if (reason === null) return;
    if (reason.trim().length < 3) {
      alert("Please provide a reason of at least 3 characters.");
      return;
    }
    if (!window.confirm(`Void transaction #${transaction.id}? It will be excluded from active calculations, but its audit record will be preserved.`)) return;
    const response = await fetch(`${API_BASE_URL}/api/investment-transactions/${transaction.id}/void?user_id=${USER_ID}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      alert(result?.detail || "Unable to void transaction.");
      return;
    }
    await loadInvestmentTransactions();
    alert("Transaction voided. Its audit history has been preserved.");
  };

  useEffect(() => {
    loadInvestmentTransactions();
  }, []);

  // ----------------------------------------------------------
  // FILTER OPTIONS
  // ----------------------------------------------------------

  const instrumentTypes = [
    "All",
    ...Array.from(
      new Set(
        investments
          .map(
            (investment) =>
              investment.investment_type
          )
          .filter(Boolean)
      )
    ).sort(),
  ];

  const instrumentNames = [
    "All",
    ...Array.from(
      new Set(
        investments
          .map(
            (investment) =>
              investment.name
          )
          .filter(Boolean)
      )
    ).sort(),
  ];

  // ----------------------------------------------------------
  // FILTER + SORT
  // ----------------------------------------------------------

  const filteredTransactions =
    transactions
      .filter((transaction) => {

        if (
          filters.instrumentType !== "All" &&
          transaction.instrument_type !==
            filters.instrumentType
        ) {
          return false;
        }

        if (
          filters.instrumentName !== "All" &&
          transaction.instrument_name !==
            filters.instrumentName
        ) {
          return false;
        }

        if (
          filters.transactionType !== "All" &&
          transaction.transaction_type !==
            filters.transactionType
        ) {
          return false;
        }

        return true;

      })
      .sort((a, b) => {

        if (filters.sort === "date_asc") {
          return (
            new Date(a.transaction_date) -
            new Date(b.transaction_date)
          );
        }

        if (filters.sort === "name_asc") {
          return String(
            a.instrument_name
          ).localeCompare(
            String(b.instrument_name)
          );
        }

        if (filters.sort === "type_asc") {
          return String(
            a.instrument_type
          ).localeCompare(
            String(b.instrument_type)
          );
        }

        return (
          new Date(b.transaction_date) -
          new Date(a.transaction_date)
        );

      });

  const buyCount =
    transactions.filter(
      (transaction) =>
        transaction.transaction_type === "BUY"
    ).length;

  const sellCount =
    transactions.filter(
      (transaction) =>
        transaction.transaction_type === "SELL"
    ).length;

  const formatCurrency = (value) =>
    new Intl.NumberFormat(
      "en-IN",
      {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }
    ).format(
      Number(value || 0)
    );

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "22px",
      }}
    >

      {/* HEADER */}

      <section
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >

        <div>

          <p className="card-label">
            INVEST
          </p>

          <h2
            style={{
              margin: "4px 0 6px",
              fontSize: "28px",
              fontWeight: 800,
            }}
          >
            Investment transactions.
          </h2>

          <p
            style={{
              margin: 0,
              color:
                "rgba(255,255,255,0.55)",
              fontSize: "13px",
              lineHeight: 1.6,
            }}
          >
            View and track investment
            transaction history.
            New transactions are created
            from Portfolio.
          </p>

        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={
            loadInvestmentTransactions
          }
          disabled={loading}
          style={{
            opacity: loading ? 0.6 : 1,
            cursor: loading
              ? "wait"
              : "pointer",
          }}
        >
          {loading
            ? "Refreshing..."
            : "Refresh"}
        </button>

      </section>


      {/* SUMMARY */}

      <section
        className="investment-transaction-summary-grid"
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(4, minmax(0, 1fr))",
          gap: "14px",
        }}
      >

        <MetricCard
          title="Investment Transactions"
          value={
            loading
              ? "Loading..."
              : String(
                  transactions.length
                )
          }
          change="Total activity"
          positive
          icon={Receipt}
        />

        <MetricCard
          title="BUY"
          value={
            loading
              ? "Loading..."
              : String(buyCount)
          }
          change="Purchase activity"
          positive
          icon={ArrowUpRight}
        />

        <MetricCard
          title="Voided"
          value={loading ? "Loading..." : String(transactions.filter((transaction) => transaction.status === "VOIDED").length)}
          change="Excluded from active calculations"
          positive={false}
          icon={Receipt}
        />

        <MetricCard
          title="SELL"
          value={
            loading
              ? "Loading..."
              : String(sellCount)
          }
          change="Sale activity"
          positive={false}
          icon={ArrowDownRight}
        />

      </section>


      {/* FILTERS */}

      <section className="glass-card">

        <div className="card-header">

          <div>

            <p className="card-label">
              FILTERS
            </p>

            <h3>
              Investment activity
            </h3>

          </div>

        </div>

        <div
          className="investment-transaction-filter-grid"
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(4, minmax(0, 1fr))",
            gap: "12px",
            marginTop: "16px",
          }}
        >

          <select
            value={
              filters.instrumentType
            }
            onChange={(event) =>
              setFilters({
                ...filters,
                instrumentType:
                  event.target.value,
              })
            }
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "11px 12px",
              borderRadius: "10px",
              border:
                "1px solid rgba(255,255,255,0.10)",
              background: "#151525",
              color: "#ffffff",
              fontSize: "12px",
              outline: "none",
            }}
          >
            {instrumentTypes.map(
              (type) => (
                <option
                  key={type}
                  value={type}
                >
                  {type === "All"
                    ? "All Instrument Types"
                    : type}
                </option>
              )
            )}
          </select>


          <select
            value={
              filters.instrumentName
            }
            onChange={(event) =>
              setFilters({
                ...filters,
                instrumentName:
                  event.target.value,
              })
            }
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "11px 12px",
              borderRadius: "10px",
              border:
                "1px solid rgba(255,255,255,0.10)",
              background: "#151525",
              color: "#ffffff",
              fontSize: "12px",
              outline: "none",
            }}
          >
            {instrumentNames.map(
              (name) => (
                <option
                  key={name}
                  value={name}
                >
                  {name === "All"
                    ? "All Instruments"
                    : name}
                </option>
              )
            )}
          </select>


          <select
            value={
              filters.transactionType
            }
            onChange={(event) =>
              setFilters({
                ...filters,
                transactionType:
                  event.target.value,
              })
            }
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "11px 12px",
              borderRadius: "10px",
              border:
                "1px solid rgba(255,255,255,0.10)",
              background: "#151525",
              color: "#ffffff",
              fontSize: "12px",
              outline: "none",
            }}
          >
            <option value="All">
              All Transactions
            </option>
            <option value="BUY">
              BUY
            </option>
            <option value="SELL">
              SELL
            </option>
          </select>


          <select
            value={filters.sort}
            onChange={(event) =>
              setFilters({
                ...filters,
                sort: event.target.value,
              })
            }
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "11px 12px",
              borderRadius: "10px",
              border:
                "1px solid rgba(255,255,255,0.10)",
              background: "#151525",
              color: "#ffffff",
              fontSize: "12px",
              outline: "none",
            }}
          >
            <option value="date_desc">
              Newest First
            </option>
            <option value="date_asc">
              Oldest First
            </option>
            <option value="name_asc">
              Instrument Name
            </option>
            <option value="type_asc">
              Instrument Type
            </option>
          </select>

        </div>

      </section>


      {/* TRANSACTION HISTORY */}

      <section className="glass-card">

        <div className="card-header">

          <div>

            <p className="card-label">
              TRANSACTION HISTORY
            </p>

            <h3>
              Investment activity
            </h3>

          </div>

          <span className="score">
            {filteredTransactions.length}
          </span>

        </div>


        {loading && (

          <div className="empty-chart">

            <strong>
              Loading investment transactions...
            </strong>

          </div>

        )}


        {!loading && error && (

          <div
            style={{
              marginTop: "16px",
              padding: "14px",
              borderRadius: "12px",
              background:
                "rgba(239,68,68,0.10)",
              border:
                "1px solid rgba(239,68,68,0.20)",
              color: "#fca5a5",
              fontSize: "13px",
            }}
          >
            {error}
          </div>

        )}


        {!loading &&
          !error &&
          filteredTransactions.length === 0 && (

            <div className="empty-chart">

              <div className="chart-icon">
                <Receipt size={28} />
              </div>

              <strong>
                No investment transactions found
              </strong>

              <span>
                Investment transactions will
                appear here after they are
                created from Portfolio.
              </span>

            </div>

          )}


        {!loading &&
          !error &&
          filteredTransactions.length > 0 && (

            <div
              className="investment-transaction-list"
              style={{
                display: "grid",
                gap: "10px",
                marginTop: "18px",
              }}
            >

              {filteredTransactions.map(
                (transaction) => {

                  const value =
                    Number(
                      transaction.quantity || 0
                    ) *
                    Number(
                      transaction.price || 0
                    );

                  const isBuy =
                    transaction.transaction_type ===
                    "BUY";

                  return (

                    <div
                      key={transaction.id}
                      className="investment-transaction-row"
                      style={{
                        display: "grid",
                        gap: "14px",
                        alignItems: "center",
                        padding: "16px",
                        borderRadius: "16px",
                        background:
                          "linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03))",
                        border:
                          "1px solid rgba(255,255,255,0.08)",
                      }}
                    >

                      {/* INSTRUMENT */}

                      <div
                        style={{
                          minWidth: 0,
                        }}
                      >

                        <strong>
                          {
                            transaction.instrument_name
                          }
                        </strong>

                        <div
                          style={{
                            marginTop: "5px",
                            fontSize: "11px",
                            color:
                              "rgba(255,255,255,0.45)",
                            whiteSpace:
                              "nowrap",
                            overflow:
                              "hidden",
                            textOverflow:
                              "ellipsis",
                          }}
                        >
                          {
                            transaction.instrument_type
                          }
                          {" • "}
                          {
                            transaction.symbol
                          }
                          {" • "}
                          Broker:{" "}
                          {
                            transaction.broker
                          }
                        </div>

                      </div>


                      {/* CENTER COLUMN: DATE, STATUS, AND ACTIONS */}

                      <div className="investment-transaction-date-column">

                        <div
                          style={{
                            fontSize: "10px",
                            color:
                              "rgba(255,255,255,0.38)",
                            textTransform:
                              "uppercase",
                            letterSpacing:
                              "0.06em",
                          }}
                        >
                          Date
                        </div>

                        <div
                          style={{
                            marginTop: "5px",
                            fontSize: "12px",
                          }}
                        >
                          {
                            transaction.transaction_date
                          }
                        </div>

                      </div>


                      {/* TYPE */}

                      <div>

                        <div
                          style={{
                            fontSize: "10px",
                            color:
                              "rgba(255,255,255,0.38)",
                            textTransform:
                              "uppercase",
                            letterSpacing:
                              "0.06em",
                          }}
                        >
                          Type
                        </div>

                        <strong
                          style={{
                            display:
                              "inline-block",
                            marginTop: "5px",
                            color:
                              isBuy
                                ? "#86efac"
                                : "#fca5a5",
                          }}
                        >
                          {
                            transaction.transaction_type
                          }
                        </strong>

                      </div>


                      {/* VALUE */}

                      <div>

                        <div
                          style={{
                            fontSize: "10px",
                            color:
                              "rgba(255,255,255,0.38)",
                            textTransform:
                              "uppercase",
                            letterSpacing:
                              "0.06em",
                          }}
                        >
                          Value
                        </div>

                        <div
                          style={{
                            marginTop: "5px",
                            fontSize: "12px",
                            fontWeight: 700,
                          }}
                        >
                          {formatCurrency(
                            value
                          )}
                        </div>

                        <div
                          style={{
                            marginTop: "4px",
                            fontSize: "10px",
                            color:
                              "rgba(255,255,255,0.42)",
                          }}
                        >
                          Qty{" "}
                          {
                            transaction.quantity
                          }
                          {" @ "}
                          {formatCurrency(
                            transaction.price
                          )}
                        </div>

                      </div>

                      {/* STATUS AND ACTIONS */}
                      <div className="investment-transaction-actions" style={{ display: "flex", flexDirection: "column", gap: "8px", alignItems: "flex-start", minWidth: 0 }}>
                        <span style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", padding: "4px 8px", borderRadius: "999px", background: transaction.status === "VOIDED" ? "rgba(248,113,113,0.14)" : "rgba(134,239,172,0.12)", color: transaction.status === "VOIDED" ? "#fca5a5" : "#86efac" }}>
                          {transaction.status || "ACTIVE"}
                        </span>
                        {(transaction.status || "ACTIVE") === "ACTIVE" && <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                          <button type="button" className="secondary-button" onClick={() => editInvestmentTransaction(transaction)} style={{ padding: "6px 9px", fontSize: "11px" }}>Edit</button>
                          <button type="button" className="secondary-button" onClick={() => voidInvestmentTransaction(transaction)} style={{ padding: "6px 9px", fontSize: "11px", color: "#fca5a5" }}>Void</button>
                        </div>}
                        {transaction.status === "VOIDED" && transaction.void_reason && <small style={{ color: "rgba(255,255,255,0.5)" }}>Reason: {transaction.void_reason}</small>}
                      </div>

                    </div>

                  );

                }
              )}

            </div>

          )}

      </section>


      {/* RESPONSIVE DESIGN */}

      <style>
        {`
          .investment-transaction-summary-grid {
            width: 100%;
          }

          .investment-transaction-list,
          .investment-transaction-row {
            width: 100%;
            min-width: 0;
            box-sizing: border-box;
          }

          /* Desktop: instrument details | centered date/actions | right-aligned type */
          .investment-transaction-row {
            grid-template-columns: minmax(0, 1.35fr) minmax(145px, 0.9fr) minmax(80px, 0.55fr) !important;
            min-height: 112px;
          }

          .investment-transaction-row > div {
            min-width: 0;
            overflow-wrap: anywhere;
          }

          .investment-transaction-row > div:nth-child(2) {
            justify-self: center;
            text-align: center;
            align-self: center;
          }

          /* Value remains available as a compact detail within the first column. */
          .investment-transaction-row > div:nth-child(3) {
            grid-column: 1;
            margin-top: -5px;
            align-self: start;
          }
          .investment-transaction-row > div:nth-child(1) { grid-column: 1; }
          .investment-transaction-row > div:nth-child(2) { grid-column: 2; }
          .investment-transaction-row > div:nth-child(3) { grid-row: 2; }
          .investment-transaction-row > div:nth-child(4) { grid-column: 3; grid-row: 1 / span 2; }

          .investment-transaction-row > div:nth-child(4) {
            justify-self: end;
            align-self: center;
            text-align: center;
            min-width: 68px;
          }

          .investment-transaction-actions {
            align-items: center !important;
            margin-top: 9px;
          }

          .investment-transaction-actions button {
            min-height: 34px;
            white-space: nowrap;
          }

          @media (max-width: 900px) {
            .investment-transaction-summary-grid {
              grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }
            .investment-transaction-filter-grid {
              grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }
            .investment-transaction-row {
              grid-template-columns: minmax(0, 1.2fr) minmax(125px, 0.9fr) minmax(65px, 0.5fr) !important;
              padding: 14px !important;
              gap: 10px !important;
            }
          }

          @media (max-width: 600px) {
            .investment-transaction-summary-grid {
              grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
              gap: 10px !important;
            }
            .investment-transaction-summary-grid > * { min-width: 0; }
            .investment-transaction-filter-grid {
              grid-template-columns: 1fr !important;
            }
            .investment-transaction-row {
              grid-template-columns: minmax(0, 1fr) minmax(92px, 0.55fr) !important;
              padding: 14px !important;
              gap: 12px !important;
              border-radius: 14px !important;
              min-height: 0;
            }
            .investment-transaction-row > div:nth-child(1) {
              grid-column: 1;
              grid-row: 1;
            }
            .investment-transaction-row > div:nth-child(2) {
              grid-column: 1 / -1;
              grid-row: 3;
              justify-self: stretch;
              text-align: center;
              padding: 10px 8px 0;
              border-top: 1px solid rgba(255,255,255,0.08);
            }
            .investment-transaction-row > div:nth-child(3) {
              grid-column: 1;
              grid-row: 2;
              margin-top: 0;
            }
            .investment-transaction-row > div:nth-child(4) {
              grid-column: 2;
              grid-row: 1 / span 2;
              justify-self: end;
              align-self: center;
              text-align: center;
              min-width: 70px;
            }
            .investment-transaction-actions {
              flex-direction: row !important;
              justify-content: center;
              align-items: center !important;
              flex-wrap: wrap;
              padding-top: 8px;
            }
            .investment-transaction-actions button {
              flex: 0 1 auto;
              min-height: 36px;
              font-size: 12px !important;
            }
          }
        `}
      </style>

    </div>
  );
}



// ============================================================
// HOLDINGS
// CONSOLIDATED CURRENT OWNERSHIP VIEW
// ============================================================
// Portfolio = individual investment records.
// Holdings = consolidated securities currently owned.
//
// Stage 4:
// - Reads the Holdings API.
// - Shows consolidated quantity and valuation.
// - Shows weighted-average cost basis.
// - Shows realised P&L from completed SELL transactions.
// - Shows unrealised P&L on the remaining holding.
// - Shows total P&L = realised + unrealised.
// - Shows broker breakdown.
// - Allows drill-down into underlying Portfolio records.
// - Does NOT create or modify investments/transactions.
// ============================================================

function Holdings() {
  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";

  const USER_ID = 1;

  const [holdings, setHoldings] = useState([]);
  const [summary, setSummary] = useState({});
  const [investments, setInvestments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [expandedSymbol, setExpandedSymbol] = useState(null);

  // ----------------------------------------------------------
  // FORMATTERS
  // ----------------------------------------------------------

  const formatCurrency = (value) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value || 0));

  const formatNumber = (value) =>
    new Intl.NumberFormat("en-IN", {
      maximumFractionDigits: 4,
    }).format(Number(value || 0));

  const formatPercent = (value) =>
    `${Number(value || 0).toFixed(2)}%`;

  const pnlColor = (value) =>
    Number(value || 0) >= 0
      ? "#86efac"
      : "#fca5a5";

  // ----------------------------------------------------------
  // LOAD HOLDINGS + PORTFOLIO RECORDS
  // ----------------------------------------------------------

  const loadHoldings = async () => {
    try {
      setLoading(true);
      setError("");

      const [holdingsResponse, investmentsResponse] =
        await Promise.all([
          fetch(
            `${API_BASE_URL}/api/holdings/?user_id=${USER_ID}`
          ),
          fetch(
            `${API_BASE_URL}/api/investments/?user_id=${USER_ID}`
          ),
        ]);

      const holdingsData =
        await holdingsResponse.json();

      const investmentsData =
        await investmentsResponse.json();

      if (!holdingsResponse.ok) {
        throw new Error(
          holdingsData?.detail ||
            holdingsData?.message ||
            "Unable to load holdings."
        );
      }

      if (!investmentsResponse.ok) {
        throw new Error(
          investmentsData?.detail ||
            "Unable to load portfolio records."
        );
      }

      setHoldings(
        Array.isArray(holdingsData?.holdings)
          ? holdingsData.holdings
          : Array.isArray(holdingsData)
          ? holdingsData
          : []
      );

      setSummary(
        holdingsData?.summary || {}
      );

      setInvestments(
        Array.isArray(investmentsData)
          ? investmentsData
          : []
      );
    } catch (err) {
      console.error(
        "Holdings API error:",
        err
      );

      setError(
        err?.message ||
          "Unable to load holdings."
      );

      setHoldings([]);
      setSummary({});
      setInvestments([]);
    } finally {
      setLoading(false);
    }
  };

  // ----------------------------------------------------------
  // REFRESH MARKET PRICES THEN RELOAD HOLDINGS
  // ----------------------------------------------------------

  const refreshHoldings = async () => {
    try {
      setRefreshing(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/investments/refresh?user_id=${USER_ID}`,
        {
          method: "POST",
          headers: {
            Accept: "application/json",
          },
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to refresh market prices."
        );
      }

      await loadHoldings();
    } catch (err) {
      console.error(
        "Holdings market refresh error:",
        err
      );

      setError(
        err?.message ||
          "Unable to refresh market prices."
      );
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadHoldings();
  }, []);

  // ----------------------------------------------------------
  // HELPERS
  // ----------------------------------------------------------

  const getUnderlyingInvestments = (holding) => {
    const ids = new Set(
      (holding?.investment_ids || []).map(Number)
    );

    return investments.filter((investment) =>
      ids.has(Number(investment.id))
    );
  };

  const totalRealisedPnl = Number(
    summary?.total_realised_gain_loss || 0
  );

  const totalUnrealisedPnl = Number(
    summary?.total_unrealised_gain_loss || 0
  );

  const totalPnl = Number(
    summary?.total_gain_loss ??
      totalRealisedPnl +
        totalUnrealisedPnl
  );

  const totalPnlReturn = Number(
    summary?.total_return_percent || 0
  );

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "22px",
      }}
    >
      {/* HEADER */}

      <section
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p className="card-label">
            INVEST
          </p>

          <h2
            style={{
              margin: "4px 0 6px",
              fontSize: "28px",
              fontWeight: 800,
            }}
          >
            Holdings.
          </h2>

          <p
            style={{
              margin: 0,
              color:
                "rgba(255,255,255,0.55)",
              fontSize: "13px",
              lineHeight: 1.6,
            }}
          >
            See what you currently own,
            including realised and unrealised
            investment performance.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: "10px",
            flexWrap: "wrap",
          }}
        >
          <button
            type="button"
            className="secondary-button"
            onClick={loadHoldings}
            disabled={
              loading || refreshing
            }
          >
            {loading
              ? "Loading..."
              : "Refresh Data"}
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={refreshHoldings}
            disabled={refreshing}
          >
            {refreshing
              ? "Updating Prices..."
              : "Refresh Market Prices"}
          </button>
        </div>
      </section>

      {/* ERROR */}

      {error && (
        <div
          className="glass-card"
          style={{
            padding: "14px 16px",
            border:
              "1px solid rgba(239,68,68,0.25)",
            color: "#fca5a5",
            fontSize: "13px",
          }}
        >
          {error}
        </div>
      )}

      {/* STAGE 4 SUMMARY */}

      <section
        className="holdings-summary-grid"
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(6, minmax(0, 1fr))",
          gap: "14px",
          width: "100%",
        }}
      >
        <MetricCard
          title="Holdings"
          value={
            loading
              ? "Loading..."
              : String(
                  summary?.holding_count ??
                    holdings.length
                )
          }
          change="Current positions"
          positive
          icon={BarChart3}
        />

        <MetricCard
          title="Cost Basis"
          value={
            loading
              ? "Loading..."
              : formatCurrency(
                  summary?.total_cost_basis
                )
          }
          change="Remaining invested cost"
          positive
          icon={Wallet}
        />

        <MetricCard
          title="Current Value"
          value={
            loading
              ? "Loading..."
              : formatCurrency(
                  summary?.total_current_value
                )
          }
          change="Current market value"
          positive
          icon={TrendingUp}
        />

        <MetricCard
          title="Realised P&L"
          value={
            loading
              ? "Loading..."
              : formatCurrency(
                  totalRealisedPnl
                )
          }
          change={
            loading
              ? "Loading..."
              : formatPercent(
                  summary?.total_realised_return_percent
                )
          }
          positive={
            totalRealisedPnl >= 0
          }
          icon={
            totalRealisedPnl >= 0
              ? ArrowUpRight
              : ArrowDownRight
          }
        />

        <MetricCard
          title="Unrealised P&L"
          value={
            loading
              ? "Loading..."
              : formatCurrency(
                  totalUnrealisedPnl
                )
          }
          change={
            loading
              ? "Loading..."
              : formatPercent(
                  summary?.total_unrealised_return_percent
                )
          }
          positive={
            totalUnrealisedPnl >= 0
          }
          icon={
            totalUnrealisedPnl >= 0
              ? ArrowUpRight
              : ArrowDownRight
          }
        />

        <MetricCard
          title="Total P&L"
          value={
            loading
              ? "Loading..."
              : formatCurrency(totalPnl)
          }
          change={
            loading
              ? "Loading..."
              : formatPercent(totalPnlReturn)
          }
          positive={totalPnl >= 0}
          icon={
            totalPnl >= 0
              ? ArrowUpRight
              : ArrowDownRight
          }
        />
      </section>

      {/* HOLDINGS LIST */}

      <section className="glass-card">
        <div className="card-header">
          <div>
            <p className="card-label">
              CURRENT OWNERSHIP
            </p>

            <h3>
              Consolidated Holdings
            </h3>
          </div>

          <span className="score">
            {holdings.length}
          </span>
        </div>

        {loading ? (
          <div
            className="empty-chart"
            style={{ marginTop: "18px" }}
          >
            <strong>
              Loading holdings...
            </strong>
          </div>
        ) : holdings.length === 0 ? (
          <div
            className="empty-chart"
            style={{ marginTop: "18px" }}
          >
            <div className="chart-icon">
              <BarChart3 size={28} />
            </div>

            <strong>
              No active holdings found
            </strong>

            <span>
              Holdings will appear here after
              Portfolio positions and transactions
              are available.
            </span>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gap: "12px",
              marginTop: "18px",
            }}
          >
            {holdings.map(
              (holding, index) => {
                const realisedPnl = Number(
                  holding.realised_gain_loss ||
                    0
                );

                const unrealisedPnl =
                  Number(
                    holding.unrealised_gain_loss ||
                      0
                  );

                const holdingTotalPnl =
                  Number(
                    holding.total_gain_loss ??
                      realisedPnl +
                        unrealisedPnl
                  );

                const underlying =
                  getUnderlyingInvestments(
                    holding
                  );

                const holdingKey =
                  holding.symbol ||
                  `holding-${index}`;

                const expanded =
                  expandedSymbol ===
                  holdingKey;

                return (
                  <div
                    key={holdingKey}
                    style={{
                      border:
                        "1px solid rgba(255,255,255,0.08)",
                      borderRadius: "16px",
                      padding: "16px",
                      background:
                        "linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.025))",
                    }}
                  >
                    {/* MAIN HOLDING */}

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns:
                          "minmax(190px, 2fr) repeat(8, minmax(90px, 1fr)) auto",
                        gap: "14px",
                        alignItems: "center",
                      }}
                      className="holdings-row"
                    >
                      <div
                        style={{
                          minWidth: 0,
                        }}
                      >
                        <strong
                          style={{
                            fontSize: "14px",
                          }}
                        >
                          {holding.name ||
                            "Unknown"}
                        </strong>

                        <div
                          style={{
                            marginTop: "5px",
                            fontSize: "11px",
                            color:
                              "rgba(255,255,255,0.45)",
                            whiteSpace:
                              "nowrap",
                            overflow:
                              "hidden",
                            textOverflow:
                              "ellipsis",
                          }}
                        >
                          {holding.investment_type ||
                            "Other"}
                          {" • "}
                          {holding.symbol ||
                            "No symbol"}
                          {" • "}
                          {holding.investment_count ||
                            0}
                          {" position(s)"}
                        </div>
                      </div>

                      <div>
                        <div className="card-label">
                          QTY
                        </div>
                        <strong>
                          {formatNumber(
                            holding.quantity_held
                          )}
                        </strong>
                      </div>

                      <div>
                        <div className="card-label">
                          AVG COST
                        </div>
                        <strong>
                          {formatCurrency(
                            holding.average_cost
                          )}
                        </strong>
                      </div>

                      <div>
                        <div className="card-label">
                          PRICE
                        </div>
                        <strong>
                          {formatCurrency(
                            holding.current_price
                          )}
                        </strong>
                      </div>

                      <div>
                        <div className="card-label">
                          COST BASIS
                        </div>
                        <strong>
                          {formatCurrency(
                            holding.cost_basis
                          )}
                        </strong>
                      </div>

                      <div>
                        <div className="card-label">
                          VALUE
                        </div>
                        <strong>
                          {formatCurrency(
                            holding.current_value
                          )}
                        </strong>
                      </div>

                      <div>
                        <div className="card-label">
                          REALISED
                        </div>
                        <strong
                          style={{
                            color:
                              pnlColor(
                                realisedPnl
                              ),
                          }}
                        >
                          {formatCurrency(
                            realisedPnl
                          )}
                        </strong>
                        <div
                          style={{
                            marginTop: "3px",
                            fontSize: "10px",
                            color:
                              pnlColor(
                                realisedPnl
                              ),
                          }}
                        >
                          {formatPercent(
                            holding.realised_return_percent
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="card-label">
                          UNREALISED
                        </div>
                        <strong
                          style={{
                            color:
                              pnlColor(
                                unrealisedPnl
                              ),
                          }}
                        >
                          {formatCurrency(
                            unrealisedPnl
                          )}
                        </strong>
                        <div
                          style={{
                            marginTop: "3px",
                            fontSize: "10px",
                            color:
                              pnlColor(
                                unrealisedPnl
                              ),
                          }}
                        >
                          {formatPercent(
                            holding.unrealised_return_percent
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="card-label">
                          TOTAL P&L
                        </div>
                        <strong
                          style={{
                            color:
                              pnlColor(
                                holdingTotalPnl
                              ),
                          }}
                        >
                          {formatCurrency(
                            holdingTotalPnl
                          )}
                        </strong>
                        <div
                          style={{
                            marginTop: "3px",
                            fontSize: "10px",
                            color:
                              pnlColor(
                                holdingTotalPnl
                              ),
                          }}
                        >
                          {formatPercent(
                            holding.total_return_percent
                          )}
                        </div>
                      </div>

                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() =>
                          setExpandedSymbol(
                            expanded
                              ? null
                              : holdingKey
                          )
                        }
                        style={{
                          whiteSpace:
                            "nowrap",
                        }}
                      >
                        {expanded
                          ? "Hide"
                          : "View"}
                      </button>
                    </div>

                    {/* DRILL-DOWN */}

                    {expanded && (
                      <div
                        style={{
                          marginTop: "16px",
                          paddingTop: "16px",
                          borderTop:
                            "1px solid rgba(255,255,255,0.08)",
                          display: "grid",
                          gridTemplateColumns:
                            "repeat(2, minmax(0, 1fr))",
                          gap: "14px",
                        }}
                        className="holdings-detail-grid"
                      >
                        {/* PERFORMANCE DETAIL */}

                        <div
                          style={{
                            padding: "14px",
                            borderRadius: "14px",
                            background:
                              "rgba(255,255,255,0.035)",
                            border:
                              "1px solid rgba(255,255,255,0.06)",
                          }}
                        >
                          <p className="card-label">
                            PERFORMANCE
                          </p>

                          <div
                            style={{
                              display: "grid",
                              gap: "10px",
                              marginTop: "10px",
                            }}
                          >
                            {[
                              [
                                "Realised P&L",
                                formatCurrency(
                                  realisedPnl
                                ),
                                pnlColor(
                                  realisedPnl
                                ),
                              ],
                              [
                                "Unrealised P&L",
                                formatCurrency(
                                  unrealisedPnl
                                ),
                                pnlColor(
                                  unrealisedPnl
                                ),
                              ],
                              [
                                "Total P&L",
                                formatCurrency(
                                  holdingTotalPnl
                                ),
                                pnlColor(
                                  holdingTotalPnl
                                ),
                              ],
                              [
                                "Remaining cost basis",
                                formatCurrency(
                                  holding.cost_basis
                                ),
                                undefined,
                              ],
                              [
                                "Sell proceeds",
                                formatCurrency(
                                  holding.sell_proceeds
                                ),
                                undefined,
                              ],
                              [
                                "Fees",
                                formatCurrency(
                                  holding.total_fees
                                ),
                                undefined,
                              ],
                            ].map(
                              (
                                [label, value, color]
                              ) => (
                                <div
                                  key={label}
                                  style={{
                                    display:
                                      "flex",
                                    justifyContent:
                                      "space-between",
                                    gap: "12px",
                                    fontSize:
                                      "12px",
                                  }}
                                >
                                  <span>
                                    {label}
                                  </span>
                                  <strong
                                    style={{
                                      color,
                                    }}
                                  >
                                    {value}
                                  </strong>
                                </div>
                              )
                            )}
                          </div>
                        </div>

                        {/* BROKER BREAKDOWN */}

                        <div
                          style={{
                            padding: "14px",
                            borderRadius: "14px",
                            background:
                              "rgba(255,255,255,0.035)",
                            border:
                              "1px solid rgba(255,255,255,0.06)",
                          }}
                        >
                          <p className="card-label">
                            BROKER BREAKDOWN
                          </p>

                          {(
                            holding.broker_breakdown ||
                            []
                          ).length === 0 ? (
                            <p
                              style={{
                                color:
                                  "rgba(255,255,255,0.45)",
                                fontSize:
                                  "12px",
                              }}
                            >
                              No broker information
                              available.
                            </p>
                          ) : (
                            <div
                              style={{
                                display:
                                  "grid",
                                gap: "9px",
                                marginTop:
                                  "10px",
                              }}
                            >
                              {(
                                holding.broker_breakdown ||
                                []
                              ).map(
                                (
                                  brokerItem
                                ) => (
                                  <div
                                    key={
                                      brokerItem.broker
                                    }
                                    style={{
                                      display:
                                        "flex",
                                      justifyContent:
                                        "space-between",
                                      gap: "12px",
                                      fontSize:
                                        "12px",
                                    }}
                                  >
                                    <span>
                                      {
                                        brokerItem.broker
                                      }
                                    </span>
                                    <strong>
                                      {formatNumber(
                                        brokerItem.quantity
                                      )}
                                    </strong>
                                  </div>
                                )
                              )}
                            </div>
                          )}
                        </div>

                        {/* UNDERLYING PORTFOLIO RECORDS */}

                        <div
                          style={{
                            padding: "14px",
                            borderRadius: "14px",
                            background:
                              "rgba(255,255,255,0.035)",
                            border:
                              "1px solid rgba(255,255,255,0.06)",
                            gridColumn:
                              "1 / -1",
                          }}
                        >
                          <p className="card-label">
                            PORTFOLIO POSITIONS
                          </p>

                          {underlying.length ===
                          0 ? (
                            <p
                              style={{
                                color:
                                  "rgba(255,255,255,0.45)",
                                fontSize:
                                  "12px",
                              }}
                            >
                              No underlying
                              Portfolio records
                              found.
                            </p>
                          ) : (
                            <div
                              style={{
                                display:
                                  "grid",
                                gap: "9px",
                                marginTop:
                                  "10px",
                              }}
                            >
                              {underlying.map(
                                (
                                  investment
                                ) => (
                                  <div
                                    key={
                                      investment.id
                                    }
                                    style={{
                                      display:
                                        "grid",
                                      gridTemplateColumns:
                                        "1fr auto",
                                      gap: "10px",
                                      fontSize:
                                        "12px",
                                    }}
                                  >
                                    <div>
                                      <strong>
                                        {investment.name ||
                                          "Investment"}
                                      </strong>

                                      <div
                                        style={{
                                          marginTop:
                                            "3px",
                                          color:
                                            "rgba(255,255,255,0.42)",
                                          fontSize:
                                            "10px",
                                        }}
                                      >
                                        ID #
                                        {
                                          investment.id
                                        }
                                        {" • "}
                                        {investment.broker ||
                                          "Unspecified broker"}
                                        {" • "}
                                        {investment.symbol ||
                                          "No symbol"}
                                      </div>
                                    </div>

                                    <div
                                      style={{
                                        textAlign:
                                          "right",
                                      }}
                                    >
                                      {formatNumber(
                                        investment.quantity
                                      )}

                                      <div
                                        style={{
                                          marginTop:
                                            "3px",
                                          color:
                                            "rgba(255,255,255,0.42)",
                                          fontSize:
                                            "10px",
                                        }}
                                      >
                                        Portfolio
                                      </div>
                                    </div>
                                  </div>
                                )
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              }
            )}
          </div>
        )}
      </section>

      {/* RESPONSIVE DESIGN */}

      <style>
        {`
          .holdings-summary-grid {
            width: 100%;
          }

          .holdings-row {
            min-width: 0;
          }

          @media (max-width: 1300px) {
            .holdings-row {
              grid-template-columns:
                repeat(5, minmax(0, 1fr)) !important;
            }
          }

          @media (max-width: 1100px) {
            .holdings-row {
              grid-template-columns:
                repeat(4, minmax(0, 1fr)) !important;
            }

            .holdings-detail-grid {
              grid-template-columns:
                1fr !important;
            }
          }

          @media (max-width: 900px) {
            .holdings-summary-grid {
              grid-template-columns:
                repeat(2, minmax(0, 1fr)) !important;
            }

            .holdings-row {
              grid-template-columns:
                repeat(2, minmax(0, 1fr)) !important;
            }
          }

          @media (max-width: 600px) {
            .holdings-summary-grid {
              grid-template-columns:
                1fr !important;
            }

            .holdings-row {
              grid-template-columns:
                1fr !important;
            }

            .holdings-detail-grid {
              grid-template-columns:
                1fr !important;
            }
          }
        `}
      </style>
    </div>
  );
}

// ============================================================
// PORTFOLIO
// ============================================================

function Portfolio() {

  // Shared muted text style used by Portfolio and the investment form.
  // Keep this local to Portfolio so it does not depend on MarketsPage state.
  const muted = { color: "rgba(255,255,255,0.55)", fontSize: "12px", lineHeight: 1.6 };
  
  // ----------------------------------------------------------
  // ADD INVESTMENT FORM STATE
  // ----------------------------------------------------------

  const [showInvestmentForm, setShowInvestmentForm] =
    useState(false);
  const [editingInvestmentId, setEditingInvestmentId] =
  useState(null);

  const [investmentForm, setInvestmentForm] = useState({
    name: "",
    investment_type: "Stocks",
    symbol: "",
    quantity: "",
    buy_price: "",
    current_price: "",
    buy_date: "",
    broker: "",
    fees: "",
    notes: "",
  });
  // Searchable instrument picker state. Uses the existing read-only market-search API.
  const [instrumentQuery, setInstrumentQuery] = useState("");
  const [instrumentResults, setInstrumentResults] = useState([]);
  const [instrumentSearchBusy, setInstrumentSearchBusy] = useState(false);
  const [instrumentSearchError, setInstrumentSearchError] = useState("");
  const [brokerChoice, setBrokerChoice] = useState("");
  const [customBroker, setCustomBroker] = useState("");

  // Reset every add/edit field so the two form modes never leak into each other.
  const resetInvestmentForm = () => {
    setInvestmentForm({ name: "", investment_type: "Stocks", symbol: "", quantity: "", buy_price: "", current_price: "", buy_date: "", broker: "", fees: "", notes: "" });
    setInstrumentQuery("");
    setInstrumentResults([]);
    setInstrumentSearchError("");
    setInstrumentSearchBusy(false);
    setBrokerChoice("");
    setCustomBroker("");
    setEditingInvestmentId(null);
  };

  // Search the correct instrument catalogue for the selected asset category.
  // Stocks/ETFs keep using the existing market-search API; Mutual Funds use AMFI.
  const searchInvestmentInstruments = async (value) => {
    setInstrumentQuery(value);
    setInstrumentSearchError("");
    if (!value.trim()) { setInstrumentResults([]); return; }
    setInstrumentSearchBusy(true);
    try {
      const isMutualFund = investmentForm.investment_type === "Mutual Funds";
      const endpoint = isMutualFund
        ? `https://ai-finance-trading-os-api.onrender.com/api/mutual-funds/search/?query=${encodeURIComponent(value.trim())}&limit=12`
        : `https://ai-finance-trading-os-api.onrender.com/api/market-search/?query=${encodeURIComponent(value.trim())}&exchange=NSE&limit=12`;
      const response = await fetch(endpoint);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : `Instrument search failed (${response.status})`;
        throw new Error(detail);
      }
      const safeResults = Array.isArray(data?.results)
        ? data.results.filter((item) => item && typeof item === "object").map((item) => {
            const symbol = typeof item.symbol === "string"
              ? item.symbol
              : (typeof item.scheme_code === "string" ? item.scheme_code : (typeof item.tradingsymbol === "string" ? item.tradingsymbol : ""));
            // AMFI mutual-fund results use the human-readable scheme name, while
            // scheme code remains the unique identifier for the selected variant.
            const name = isMutualFund
              ? (typeof item.scheme_name === "string" && item.scheme_name.trim()
                  ? item.scheme_name.trim()
                  : (typeof item.name === "string" && item.name.trim()
                      ? item.name.trim()
                      : String(symbol || "Mutual Fund Scheme")))
              : (typeof item.name === "string"
                  ? item.name
                  : (typeof item.scheme_name === "string" ? item.scheme_name : (typeof item.company_name === "string" ? item.company_name : String(symbol || "Instrument"))));
            return {
              ...item,
              name,
              symbol,
              exchange: typeof item.exchange === "string" ? item.exchange : (isMutualFund ? "AMFI" : "NSE"),
            };
          })
        : [];
      setInstrumentResults(safeResults);
      // Only show the empty-state message when the latest response has no results.
      setInstrumentSearchError(safeResults.length ? "" : (isMutualFund ? "No matching mutual fund schemes found." : "No matching market instruments found."));
    } catch (error) {
      setInstrumentResults([]);
      setInstrumentSearchError(error?.message || "Instrument search is unavailable.");
    } finally { setInstrumentSearchBusy(false); }
  };

  const selectInvestmentInstrument = (instrument) => {
    const symbol = instrument?.tradingsymbol || instrument?.symbol || "";
    const name = instrument?.name || instrument?.company_name || symbol;
    setInvestmentForm((previous) => ({
      ...previous,
      name,
      symbol,
      investment_type: previous.investment_type === "Mutual Funds" ? previous.investment_type : "Stocks",
      current_price: instrument?.last_price != null && Number(instrument.last_price) > 0 ? String(instrument.last_price) : previous.current_price,
    }));
    setInstrumentQuery(`${name}${symbol ? ` (${symbol})` : ""}`);
    setInstrumentResults([]);
  };

  // ----------------------------------------------------------
  // INVESTMENT DATA
  // ----------------------------------------------------------

  const [investments, setInvestments] = useState([]);
// ----------------------------------------------------------
// MARKET PRICE REFRESH STATE
// ----------------------------------------------------------

const [refreshingPrices, setRefreshingPrices] =
  useState(false);

const [refreshMessage, setRefreshMessage] =
  useState("");
  
// ============================================================
// INVESTMENT BUY / SELL TRANSACTION STATE
// ============================================================

const [transactionModal, setTransactionModal] =
  useState(null);

const [transactionType, setTransactionType] =
  useState("BUY");

const [transactionForm, setTransactionForm] =
  useState({
    quantity: "",
    price: "",
    fees: "",
    transaction_date:
      new Date().toISOString().split("T")[0],
    notes: "",
  });

const [investmentTransactions, setInvestmentTransactions] =
  useState([]);

const [transactionLoading, setTransactionLoading] =
  useState(false);

const [transactionHistoryLoading, setTransactionHistoryLoading] =
  useState(false);

const [transactionMessage, setTransactionMessage] =
  useState("");
  const loadInvestments = async () => {
    try {
      const response = await fetch(
        "https://ai-finance-trading-os-api.onrender.com/api/investments/?user_id=1"
      );

      if (!response.ok) {
        throw new Error(
          `Investments API error: ${response.status}`
        );
      }

      const data = await response.json();

      setInvestments(
        Array.isArray(data) ? data : []
      );

    } catch (error) {
      console.error(
        "Load investments error:",
        error
      );
    }
  };

  // Remove one selected investment record only. The backend refuses to
  // remove records that have linked BUY/SELL transactions.
  const handleDeleteInvestment = async (investment) => {
    const details = [
      investment?.name || "Investment",
      investment?.broker ? `Broker: ${investment.broker}` : null,
      investment?.quantity != null ? `Quantity: ${investment.quantity}` : null,
      investment?.id != null ? `Record ID: ${investment.id}` : null,
    ].filter(Boolean).join("\n");

    const confirmed = window.confirm(
      `Remove this investment record?\n\n${details}\n\nOnly this record will be targeted. Other records for the same instrument will remain. This will not create a SELL transaction.`
    );
    if (!confirmed) return;

    try {
      const response = await fetch(
        `https://ai-finance-trading-os-api.onrender.com/api/investments/${encodeURIComponent(investment.id)}?user_id=1`,
        { method: "DELETE", headers: { Accept: "application/json" } }
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || `Unable to remove investment (${response.status}).`);
      }
      await loadInvestments();
      setRefreshMessage(`Investment record ${investment.id} removed. Other records were not changed.`);
    } catch (error) {
      window.alert(error?.message || "Unable to remove this investment record.");
    }
  };
  
// ----------------------------------------------------------
// REFRESH MARKET PRICES
// ----------------------------------------------------------
//
// Portfolio
//     ↓
// Investments API
//     ↓
// m.Stock Market API
//     ↓
// Current prices updated
//
// ----------------------------------------------------------

const refreshMarketPrices = async () => {

  try {

    setRefreshingPrices(true);
    setRefreshMessage("");

    const response = await fetch(
      "https://ai-finance-trading-os-api.onrender.com/api/investments/refresh?user_id=1",
      {
        method: "POST",
        headers: {
          "Accept": "application/json",
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          "Unable to refresh market prices."
      );
    }

    // Reload portfolio after prices are updated
    await loadInvestments();

    const refreshedCount =
      data?.refreshed_count || 0;

    const failedCount =
      data?.failed_count || 0;

    if (failedCount > 0) {

      setRefreshMessage(
        `${refreshedCount} investment(s) updated. ${failedCount} could not be updated.`
      );

    } else {

      setRefreshMessage(
        `${refreshedCount} investment(s) updated successfully.`
      );
    }

  } catch (error) {

    console.error(
      "Market price refresh error:",
      error
    );

    setRefreshMessage(
      error?.message ||
        "Unable to refresh market prices."
    );

  } finally {

    setRefreshingPrices(false);
  }
};
  
// ----------------------------------------------------------
// EDIT INVESTMENT
// ----------------------------------------------------------

const handleEditInvestment = (investment) => {
  setInstrumentQuery("");
  setInstrumentResults([]);
  setInstrumentSearchError("");
  const standardBrokers = ["Zerodha", "Groww", "Upstox", "Angel One", "ICICI Direct", "HDFC Securities", "Kotak Securities", "m.Stock"];
  setBrokerChoice(standardBrokers.includes(investment.broker) ? investment.broker : (investment.broker ? "Other" : ""));
  setCustomBroker(standardBrokers.includes(investment.broker) ? "" : (investment.broker || ""));
  setInvestmentForm({
    name: investment.name || "",
    investment_type:
      investment.investment_type || "Stocks",
    symbol: investment.symbol || "",
    quantity: investment.quantity || "",
    buy_price: investment.buy_price || "",
    current_price: investment.current_price || "",
    buy_date: investment.buy_date || "",
    broker: investment.broker || "",
    fees: investment.fees || "",
    notes: investment.notes || "",
  });

  setEditingInvestmentId(investment.id);
  setShowInvestmentForm(true);
};

// ============================================================
// LOAD INVESTMENT TRANSACTIONS
// ============================================================

const loadInvestmentTransactions = async (
  investmentId
) => {

  try {

    setTransactionHistoryLoading(true);
    setTransactionMessage("");

    const response = await fetch(
      `https://ai-finance-trading-os-api.onrender.com/api/investment-transactions/?user_id=1&investment_id=${investmentId}`
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          "Unable to load investment transactions."
      );
    }

    setInvestmentTransactions(
      Array.isArray(data)
        ? data
        : []
    );

  } catch (error) {

    console.error(
      "Investment transaction history error:",
      error
    );

    setTransactionMessage(
      error?.message ||
        "Unable to load transactions."
    );

  } finally {

    setTransactionHistoryLoading(false);

  }

};


// ============================================================
// OPEN BUY / SELL MODAL
// ============================================================

const openInvestmentTransaction = (
  investment,
  type
) => {

  setTransactionType(type);

  setTransactionModal({
    investment,
    mode: "form",
  });

  setTransactionForm({
    quantity: "",
    price:
      investment.current_price ??
      investment.buy_price ??
      "",
    fees: "",
    transaction_date:
      new Date().toISOString().split("T")[0],
    notes: "",
  });

  setInvestmentTransactions([]);
  setTransactionMessage("");

};


// ============================================================
// OPEN TRANSACTION HISTORY
// ============================================================

const openInvestmentTransactions = async (
  investment
) => {

  setTransactionModal({
    investment,
    mode: "history",
  });

  setTransactionType("BUY");

  setTransactionMessage("");

  await loadInvestmentTransactions(
    investment.id
  );

};


// ============================================================
// CLOSE TRANSACTION MODAL
// ============================================================

const closeInvestmentTransactionModal = () => {

  setTransactionModal(null);

  setInvestmentTransactions([]);

  setTransactionMessage("");

};


// ============================================================
// SUBMIT BUY / SELL TRANSACTION
// ============================================================

const handleInvestmentTransactionSubmit =
  async () => {

    if (!transactionModal?.investment) {
      return;
    }

    const investment =
      transactionModal.investment;

    try {

      setTransactionLoading(true);
      setTransactionMessage("");

      // ------------------------------------------------------
      // VALIDATION
      // ------------------------------------------------------

      if (
        !transactionForm.quantity ||
        Number(transactionForm.quantity) <= 0
      ) {

        setTransactionMessage(
          "Please enter a valid quantity."
        );

        return;

      }

      if (
        !transactionForm.price ||
        Number(transactionForm.price) <= 0
      ) {

        setTransactionMessage(
          "Please enter a valid price."
        );

        return;

      }

      if (!transactionForm.transaction_date) {

        setTransactionMessage(
          "Please select a transaction date."
        );

        return;

      }

      // ------------------------------------------------------
      // TRANSACTION PAYLOAD
      // ------------------------------------------------------

      const payload = {

        user_id: 1,

        investment_id:
          investment.id,

        transaction_type:
          transactionType,

        quantity:
          Number(
            transactionForm.quantity
          ),

        price:
          Number(
            transactionForm.price
          ),

        fees:
          Number(
            transactionForm.fees || 0
          ),

        transaction_date:
          transactionForm.transaction_date,

        notes:
          transactionForm.notes.trim() ||
          null,

      };

      // ------------------------------------------------------
      // CREATE TRANSACTION
      // ------------------------------------------------------

      const response = await fetch(
        "https://ai-finance-trading-os-api.onrender.com/api/investment-transactions/",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify(payload),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {

        throw new Error(
          data?.detail ||
            `Unable to create ${transactionType} transaction.`
        );

      }

      // ------------------------------------------------------
      // SUCCESS
      // ------------------------------------------------------

      setTransactionMessage(
        `${transactionType} transaction created successfully.`
      );

      // Refresh transaction history
      await loadInvestmentTransactions(
        investment.id
      );

      // Refresh investment data
      await loadInvestments();

      // Reset quantity/fees/notes
      setTransactionForm({
        quantity: "",
        price:
          investment.current_price ??
          investment.buy_price ??
          "",
        fees: "",
        transaction_date:
          new Date().toISOString().split("T")[0],
        notes: "",
      });

      // Switch to transaction history
      setTransactionModal({
        investment,
        mode: "history",
      });

    } catch (error) {

      console.error(
        "Investment transaction error:",
        error
      );

      setTransactionMessage(
        error?.message ||
          `Unable to create ${transactionType} transaction.`
      );

    } finally {

      setTransactionLoading(false);

    }

  };
  
  useEffect(() => {
    loadInvestments();
  }, []);
  
  // ----------------------------------------------------------
  // INVESTMENT FORM FIELD STYLE
  // ----------------------------------------------------------

  const investmentFieldStyle = {
    width: "100%",
    boxSizing: "border-box",
    padding: "11px 12px",
    borderRadius: "10px",
    border: "1px solid rgba(255,255,255,0.10)",
    background: "rgba(255,255,255,0.05)",
    color: "#ffffff",
    fontSize: "12px",
    outline: "none",
  };


  // ==========================================================
  // SAVE INVESTMENT + CREATE INITIAL BUY TRANSACTION
  // ==========================================================

  const handleInvestmentSubmit = async () => {
    try {
      // --------------------------------------------------------
      // VALIDATION
      // --------------------------------------------------------

      if (!investmentForm.name.trim()) {
        alert("Please enter an investment name.");
        return;
      }

      if (
        !investmentForm.quantity ||
        Number(investmentForm.quantity) <= 0
      ) {
        alert("Please enter a valid quantity.");
        return;
      }

      if (
        !investmentForm.buy_price ||
        Number(investmentForm.buy_price) <= 0
      ) {
        alert("Please enter a valid buy price.");
        return;
      }

      if (!investmentForm.buy_date) {
        alert("Please select a buy date.");
        return;
      }

      if (!investmentForm.broker.trim()) {
        alert("Please select or enter a broker before saving.");
        return;
      }
      if (!editingInvestmentId && (!investmentForm.name.trim() || !investmentForm.symbol.trim())) {
        alert("Please search for and select an instrument from the results before adding an investment.");
        return;
      }

      // --------------------------------------------------------
      // INVESTMENT PAYLOAD
      // --------------------------------------------------------

      const payload = {
        user_id: 1,

        name:
          investmentForm.name.trim(),

        investment_type:
          investmentForm.investment_type,

        symbol:
          investmentForm.symbol.trim() || null,

        quantity:
          Number(investmentForm.quantity),

        buy_price:
          Number(investmentForm.buy_price),

        current_price:
          Number(
            investmentForm.current_price ||
            investmentForm.buy_price
          ),

        buy_date:
          investmentForm.buy_date,

        broker:
          investmentForm.broker.trim() || null,

        fees:
          Number(investmentForm.fees || 0),

        notes:
          investmentForm.notes.trim() || null,
      };

      // --------------------------------------------------------
      // CREATE / UPDATE INVESTMENT
      // --------------------------------------------------------

      const url = editingInvestmentId
        ? `https://ai-finance-trading-os-api.onrender.com/api/investments/${editingInvestmentId}`
        : "https://ai-finance-trading-os-api.onrender.com/api/investments/";

      const response = await fetch(
        url,
        {
          method: editingInvestmentId
            ? "PUT"
            : "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to save investment."
        );
      }

      // --------------------------------------------------------
      // CREATE INITIAL BUY TRANSACTION
      //
      // IMPORTANT:
      // Only CREATE mode creates a BUY transaction.
      //
      // Editing an existing investment does NOT create
      // another BUY transaction.
      // --------------------------------------------------------

      if (!editingInvestmentId) {

        const transactionPayload = {
          user_id: 1,

          investment_id:
            data.id,

          transaction_type:
            "BUY",

          quantity:
            Number(investmentForm.quantity),

          price:
            Number(investmentForm.buy_price),

          fees:
            Number(investmentForm.fees || 0),

          transaction_date:
            investmentForm.buy_date,

          notes:
            investmentForm.notes.trim() ||
            "Initial BUY transaction",
        };

        const transactionResponse =
          await fetch(
            "https://ai-finance-trading-os-api.onrender.com/api/investment-transactions/",
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify(
                  transactionPayload
                ),
            }
          );

        const transactionData =
          await transactionResponse.json();

        // ------------------------------------------------------
        // TRANSACTION FAILED
        // ------------------------------------------------------

        if (!transactionResponse.ok) {

          // Try to remove the newly created
          // investment so we don't leave an
          // incomplete investment record.

          try {
            await fetch(
              `https://ai-finance-trading-os-api.onrender.com/api/investments/${data.id}`,
              {
                method: "DELETE",
              }
            );
          } catch (rollbackError) {
            console.error(
              "Investment rollback failed:",
              rollbackError
            );
          }

          throw new Error(
            transactionData?.detail ||
              "Investment created, but BUY transaction failed."
          );
        }
      }

      // --------------------------------------------------------
      // RESET FORM
      // --------------------------------------------------------

      const wasEditing = Boolean(editingInvestmentId);
      resetInvestmentForm();

      // --------------------------------------------------------
      // CLOSE FORM
      // --------------------------------------------------------

      setShowInvestmentForm(false);
      setEditingInvestmentId(null);

      // --------------------------------------------------------
      // RELOAD INVESTMENTS
      // --------------------------------------------------------

      await loadInvestments();

      // --------------------------------------------------------
      // SUCCESS MESSAGE
      // --------------------------------------------------------

      alert(
        wasEditing
          ? "Investment updated successfully."
          : "Investment and BUY transaction created successfully."
      );

    } catch (err) {

      console.error(
        "Save investment error:",
        err
      );

      alert(
        err?.message ||
          "Unable to save investment."
      );
    }
  };


  
  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(value || 0);
  };

// ============================================================
// ASSET ALLOCATION
// ============================================================

const assetAllocation = investments.reduce((allocation, investment) => {
  const type = investment.investment_type || "Other";

  const value =
  Number(investment.quantity || 0) *
  Number(
    investment.current_price ??
      investment.buy_price ??
      0
  );

  allocation[type] = (allocation[type] || 0) + value;

  return allocation;
}, {});

const totalInvested = Object.values(assetAllocation).reduce(
  (total, value) => total + value,
  0
);

// ============================================================
// PORTFOLIO SUMMARY CALCULATIONS
// ============================================================

const investedAmount = investments.reduce(
  (total, investment) =>
    total +
    Number(investment.quantity || 0) *
      Number(investment.buy_price || 0),
  0
);

const portfolioValue = investments.reduce(
  (total, investment) =>
    total +
    Number(investment.quantity || 0) *
      Number(
        investment.current_price ??
          investment.buy_price ??
          0
      ),
  0
);

const totalGainLoss =
  portfolioValue - investedAmount;

const overallReturn =
  investedAmount > 0
    ? (
        (totalGainLoss / investedAmount) *
        100
      ).toFixed(2) + "%"
    : "0.00%";

const summaryCards = [
  {
    label: "PORTFOLIO VALUE",
    value: formatCurrency(portfolioValue),
    change: "Current market value",
  },
  {
    label: "INVESTED AMOUNT",
    value: formatCurrency(investedAmount),
    change: "Total capital invested",
  },
  {
    label: "TOTAL GAIN / LOSS",
    value: formatCurrency(totalGainLoss),
    change: "Unrealised + realised",
  },
  {
    label: "OVERALL RETURN",
    value: overallReturn,
    change: "Portfolio return",
  },
];
 
    return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "22px",
      }}
    >

      {/* =====================================================
          HEADER
      ===================================================== */}

      <section
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >

        <div>
          <p className="card-label">
            INVESTMENTS
          </p>

          <h2
            style={{
              margin: "4px 0 6px",
              fontSize: "28px",
              fontWeight: 800,
            }}
          >
            Your portfolio.
          </h2>

          <p
            style={{
              margin: 0,
              color: "rgba(255,255,255,0.55)",
              fontSize: "13px",
            }}
          >
            Track your investments, returns and asset allocation.
          </p>
        </div>

       {/* =====================================================
    PORTFOLIO ACTIONS
===================================================== */}

<div
  style={{
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
  }}
>

  {/* REFRESH MARKET PRICES */}

  <button
    type="button"
    className="secondary-button"
    onClick={refreshMarketPrices}
    disabled={refreshingPrices}
    style={{
      opacity: refreshingPrices ? 0.6 : 1,
      cursor: refreshingPrices
        ? "wait"
        : "pointer",
    }}
  >
    <TrendingUp size={16} />

    {refreshingPrices
      ? "Refreshing..."
      : "Refresh Prices"}
  </button>

  {/* ADD INVESTMENT */}

  <button
    type="button"
    className="primary-button"
    onClick={() => {
      resetInvestmentForm();
      setShowInvestmentForm(true);
    }}
  >
    <Plus size={16} />
    Add Investment
  </button>

</div>
      </section>


            {/* =====================================================
          ADD INVESTMENT FORM
      ===================================================== */}

      {showInvestmentForm && (
        <div
          className="glass-card"
          style={{
            padding: "20px",
          }}
        >

          <div className="card-header">

            <div>
              <p className="card-label">
                INVESTMENTS
              </p>

              <h3>
  {editingInvestmentId
    ? "Edit Investment"
    : "Add Investment"}
</h3>
              
            </div>

          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "14px",
            }}
          >

            {/* ADD mode requires a canonical search result; EDIT mode edits the existing record directly. */}
            {editingInvestmentId ? (
              <div style={{ gridColumn: "1 / -1" }}>
                <label style={{ display: "block", marginBottom: "6px", color: "rgba(255,255,255,0.65)", fontSize: "12px" }}>Investment Instrument</label>
                <input type="text" value={investmentForm.name} onChange={(event) => setInvestmentForm((previous) => ({ ...previous, name: event.target.value }))} required style={investmentFieldStyle} />
                <div style={{ ...muted, marginTop: "5px" }}>Editing the existing investment. Instrument search is only required when adding a new investment.</div>
              </div>
            ) : (
              <div style={{ gridColumn: "1 / -1", position: "relative" }}>
                <label style={{ display: "block", marginBottom: "6px", color: "rgba(255,255,255,0.65)", fontSize: "12px" }}>Investment Instrument (required)</label>
                <input type="text" autoComplete="off" placeholder={investmentForm.investment_type === "Mutual Funds" ? "Search mutual fund scheme, e.g. HDFC Flexi Cap" : "Search instrument name or symbol, e.g. HDFC Bank"} value={instrumentQuery || investmentForm.name} onChange={(event) => searchInvestmentInstruments(event.target.value)} style={investmentFieldStyle} />
                {instrumentSearchBusy && <div style={{ ...muted, marginTop: "5px" }}>{investmentForm.investment_type === "Mutual Funds" ? "Searching mutual fund schemes…" : "Searching NSE instruments…"}</div>}
                {instrumentSearchError && <div role="alert" style={{ color: "#fca5a5", fontSize: "12px", marginTop: "5px" }}>{instrumentSearchError}</div>}
                {instrumentResults.length > 0 && <div style={{ position: "absolute", zIndex: 20, top: "100%", left: 0, right: 0, maxHeight: "240px", overflowY: "auto", background: "#17172a", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "10px", boxShadow: "0 12px 30px rgba(0,0,0,0.4)" }}>
                  {instrumentResults.map((instrument, index) => {
                    // Show both plan and option because they identify distinct AMFI schemes.
                    const displayName = instrument.scheme_name || instrument.name || instrument.company_name || instrument.tradingsymbol || instrument.symbol;
                    const isMutualFund = investmentForm.investment_type === "Mutual Funds";
                    const planSource = `${instrument.plan_type || ""} ${instrument.plan || ""} ${displayName}`;
                    const planMatch = isMutualFund && /\bdirect(?:\s+plan)?\b/i.test(planSource)
                      ? "Direct Plan"
                      : (isMutualFund && /\bregular(?:\s+plan)?\b/i.test(planSource) ? "Regular Plan" : "");
                    const optionSource = `${instrument.option_type || ""} ${instrument.option || ""} ${instrument.scheme_option || ""}`;
                    const optionMatch = isMutualFund && /\bidcw\b/i.test(optionSource)
                      ? "IDCW"
                      : (isMutualFund && /\bgrowth\b/i.test(optionSource) ? "Growth" : (isMutualFund && /\bbonus\b/i.test(optionSource) ? "Bonus" : ""));
                    return <button key={`${instrument.scheme_code || instrument.instrument_token || instrument.tradingsymbol || instrument.symbol}-${index}`} type="button" onClick={() => selectInvestmentInstrument({ ...instrument, name: isMutualFund ? `${displayName}${planMatch ? ` - ${planMatch}` : ""}${optionMatch ? ` - ${optionMatch}` : ""}` : displayName })} style={{ display: "block", width: "100%", padding: "10px 12px", textAlign: "left", color: "white", background: "transparent", border: 0, borderBottom: "1px solid rgba(255,255,255,0.07)", cursor: "pointer" }}>
                      <strong>{displayName}</strong>{planMatch && <span style={{ display: "inline-block", marginLeft: "8px", padding: "2px 6px", borderRadius: "5px", background: planMatch === "Direct Plan" ? "rgba(34,197,94,0.15)" : "rgba(245,158,11,0.15)", color: planMatch === "Direct Plan" ? "#86efac" : "#fcd34d", fontSize: "10px", fontWeight: 700 }}>{planMatch}</span>}{optionMatch && <span style={{ display: "inline-block", marginLeft: "6px", padding: "2px 6px", borderRadius: "5px", background: "rgba(99,102,241,0.18)", color: "#c4b5fd", fontSize: "10px", fontWeight: 700 }}>{optionMatch}</span>}<div style={{ color: "rgba(255,255,255,0.55)", marginTop: "4px", fontSize: "11px" }}>{instrument.scheme_code ? `Scheme Code: ${instrument.scheme_code}` : (instrument.tradingsymbol || instrument.symbol)} · {instrument.exchange || (isMutualFund ? "AMFI" : "NSE")}</div>
                    </button>;
                  })}
                </div>}
                {investmentForm.name && investmentForm.symbol && <div style={{ ...muted, marginTop: "5px" }}>Selected: {investmentForm.name} · {investmentForm.symbol}</div>}
              </div>
            )}

            {/* INVESTMENT TYPE */}

            <select
              value={investmentForm.investment_type}
              onChange={(event) => {
                const nextType = event.target.value;
                setInvestmentForm((previous) => ({
                  ...previous,
                  investment_type: nextType,
                  name: "",
                  symbol: "",
                  current_price: "",
                }));
                setInstrumentQuery("");
                setInstrumentResults([]);
                setInstrumentSearchError("");
              }}
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "10px",
                border:
                  "1px solid rgba(255,255,255,0.10)",
                background:
                  "rgba(255,255,255,0.05)",
                color: "#ffffff",
                fontSize: "12px",
                outline: "none",
              }}
            >
              <option value="Stocks">
                Stocks
              </option>

              <option value="Mutual Funds">
                Mutual Funds
              </option>

              <option value="ETFs">
                ETFs
              </option>

              <option value="Gold">
                Gold
              </option>

              <option value="Bonds">
                Bonds
              </option>

              <option value="NPS">
                NPS
              </option>

              <option value="Fixed Deposits">
                Fixed Deposits
              </option>

              <option value="Other">
                Other
              </option>
            </select>


            {/* Symbol is selected in Add mode and editable in Edit mode. */}
            <input
              type="text"
              placeholder={editingInvestmentId ? "Symbol" : "Select an instrument above to populate symbol"}
              value={investmentForm.symbol}
              readOnly={!editingInvestmentId}
              required={!editingInvestmentId}
              onChange={(event) => setInvestmentForm((previous) => ({ ...previous, symbol: event.target.value }))}
              style={{ width: "100%", boxSizing: "border-box", padding: "11px 12px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.10)", background: "rgba(255,255,255,0.03)", color: "#ffffff", fontSize: "12px", outline: "none" }}
            />

            {/* QUANTITY */}

            <input
              type="number"
              placeholder="Quantity"
              value={investmentForm.quantity}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  quantity: event.target.value,
                })
              }
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "10px",
                border:
                  "1px solid rgba(255,255,255,0.10)",
                background:
                  "rgba(255,255,255,0.05)",
                color: "#ffffff",
                fontSize: "12px",
                outline: "none",
              }}
            />


            {/* BUY PRICE */}

            <input
              type="number"
              placeholder="Buy price"
              value={investmentForm.buy_price}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  buy_price: event.target.value,
                })
              }
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "10px",
                border:
                  "1px solid rgba(255,255,255,0.10)",
                background:
                  "rgba(255,255,255,0.05)",
                color: "#ffffff",
                fontSize: "12px",
                outline: "none",
              }}
            />

           {/* CURRENT PRICE - EDIT ONLY */}
{editingInvestmentId && (
  <div>
    <label
      style={{
        display: "block",
        marginBottom: "6px",
        fontSize: "11px",
        color: "rgba(255,255,255,0.60)",
      }}
    >
      Current Price
    </label>

    <input
      type="number"
      step="0.01"
      placeholder="Current market price"
      value={investmentForm.current_price}
      onChange={(event) =>
        setInvestmentForm({
          ...investmentForm,
          current_price: event.target.value,
        })
      }
      style={investmentFieldStyle}
    />
  </div>
)} 

            {/* BUY DATE */}

            <input
              type="date"
              value={investmentForm.buy_date}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  buy_date: event.target.value,
                })
              }
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "10px",
                border:
                  "1px solid rgba(255,255,255,0.10)",
                background:
                  "rgba(255,255,255,0.05)",
                color: "#ffffff",
                fontSize: "12px",
                outline: "none",
                colorScheme: "dark",
              }}
            />


            {/* BROKER — mandatory dropdown, with explicit custom broker option */}
            <div>
              <label style={{ display: "block", marginBottom: "6px", color: "rgba(255,255,255,0.65)", fontSize: "12px" }}>Broker / Platform (required)</label>
              <select
                value={brokerChoice || (investmentForm.broker && !["Zerodha", "Groww", "Upstox", "Angel One", "ICICI Direct", "HDFC Securities", "Kotak Securities", "m.Stock", "Other"].includes(investmentForm.broker) ? "Other" : investmentForm.broker)}
                onChange={(event) => {
                  const value = event.target.value;
                  setBrokerChoice(value);
                  setCustomBroker(value === "Other" ? (customBroker || "") : "");
                  setInvestmentForm((previous) => ({ ...previous, broker: value === "Other" ? "" : value }));
                }}
                required
                style={{ width: "100%", boxSizing: "border-box", padding: "11px 12px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.10)", background: "#151525", color: "#ffffff", fontSize: "12px" }}
              >
                <option value="">Select broker…</option>
                <option value="Zerodha">Zerodha</option><option value="Groww">Groww</option><option value="Upstox">Upstox</option><option value="Angel One">Angel One</option><option value="ICICI Direct">ICICI Direct</option><option value="HDFC Securities">HDFC Securities</option><option value="Kotak Securities">Kotak Securities</option><option value="m.Stock">m.Stock (Mirae Asset)</option><option value="Other">Other (enter broker)</option>
              </select>
              {brokerChoice === "Other" && <input type="text" placeholder="Enter broker name (required)" value={customBroker} onChange={(event) => { setCustomBroker(event.target.value); setInvestmentForm((previous) => ({ ...previous, broker: event.target.value })); }} required style={{ width: "100%", boxSizing: "border-box", marginTop: "8px", padding: "11px 12px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.10)", background: "rgba(255,255,255,0.05)", color: "#ffffff", fontSize: "12px" }} />}
            </div>

            {/* FEES */}

            <input
              type="number"
              placeholder="Fees"
              value={investmentForm.fees}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  fees: event.target.value,
                })
              }
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "10px",
                border:
                  "1px solid rgba(255,255,255,0.10)",
                background:
                  "rgba(255,255,255,0.05)",
                color: "#ffffff",
                fontSize: "12px",
                outline: "none",
              }}
            />


            {/* NOTES */}

            <textarea
              placeholder="Notes"
              value={investmentForm.notes}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  notes: event.target.value,
                })
              }
              style={{
                width: "100%",
                boxSizing: "border-box",
                gridColumn: "1 / -1",
                minHeight: "90px",
                padding: "11px 12px",
                borderRadius: "10px",
                border:
                  "1px solid rgba(255,255,255,0.10)",
                background:
                  "rgba(255,255,255,0.05)",
                color: "#ffffff",
                fontSize: "12px",
                outline: "none",
                resize: "vertical",
              }}
            />

          </div>


          {/* ACTION BUTTONS */}

          <div
            style={{
              display: "flex",
              gap: "10px",
              marginTop: "18px",
            }}
          >

            <button
              type="button"
              className="primary-button"
              onClick={handleInvestmentSubmit}
            >
              {editingInvestmentId
  ? "Update Investment"
  : "Save Investment"}
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setShowInvestmentForm(false);
                resetInvestmentForm();
              }}
            >
              Cancel
            </button>

          </div>

        </div>
      )}     
              
    {/* =====================================================
    PORTFOLIO SUMMARY CARD RESPONSIVE STYLE
===================================================== */}

<style>
{`
  .portfolio-summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    width: 100%;
  }

  .portfolio-summary-value {
    font-size: 20px;
    font-weight: 800;
    color: #ffffff;
    white-space: nowrap;
  }

  @media (max-width: 768px) {
    .portfolio-summary-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .portfolio-summary-value {
      font-size: 17px;
    }
  }
`}
</style>        

      {/* =====================================================
          SUMMARY CARDS
      ===================================================== */}

      <div className="portfolio-summary-grid">

        {summaryCards.map((card) => (
          <div
  key={card.label}
  className="glass-card"
  style={{
    padding: "18px",
    minHeight: "105px",
    minWidth: 0,
    boxSizing: "border-box",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
  }}
>

            <div
              style={{
                fontSize: "10px",
                color: "rgba(255,255,255,0.42)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: "8px",
              }}
            >
              {card.label}
            </div>

            <div className="portfolio-summary-value">
  {card.value}
</div>

            <div
              style={{
                marginTop: "6px",
                fontSize: "11px",
                color: "rgba(255,255,255,0.42)",
              }}
            >
              {card.change}
            </div>

          </div>
        ))}

      </div>


      {/* =====================================================
          PERFORMANCE + ALLOCATION
      ===================================================== */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "minmax(0, 1.5fr) minmax(280px, 1fr)",
          gap: "16px",
        }}
      >

        {/* PERFORMANCE */}

        <div
          className="glass-card"
          style={{
            padding: "20px",
            minHeight: "280px",
          }}
        >

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: "10px",
              flexWrap: "wrap",
            }}
          >

            <div>
              <div
                style={{
                  fontSize: "15px",
                  fontWeight: 800,
                }}
              >
                Portfolio Performance
              </div>

              <div
                style={{
                  marginTop: "4px",
                  fontSize: "11px",
                  color: "rgba(255,255,255,0.45)",
                }}
              >
                Track portfolio growth over time
              </div>
            </div>

            <div
              style={{
                display: "flex",
                gap: "5px",
              }}
            >
              {["1M", "3M", "6M", "1Y", "3Y"].map(
                (period, index) => (
                  <span
                    key={period}
                    style={{
                      padding: "5px 8px",
                      borderRadius: "8px",
                      fontSize: "10px",
                      background:
                        index === 3
                          ? "rgba(168,85,247,0.18)"
                          : "rgba(255,255,255,0.04)",
                      border:
                        "1px solid rgba(255,255,255,0.08)",
                      color:
                        index === 3
                          ? "#d8b4fe"
                          : "rgba(255,255,255,0.50)",
                    }}
                  >
                    {period}
                  </span>
                )
              )}
            </div>

          </div>

          <div
            style={{
              height: "180px",
              marginTop: "24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: "14px",
              border:
                "1px dashed rgba(255,255,255,0.10)",
              background:
                "rgba(255,255,255,0.02)",
            }}
          >

        <div
  style={{
    width: "100%",
    textAlign: "center",
  }}
>
  <div
    style={{
      fontSize: "12px",
      color: "rgba(255,255,255,0.45)",
      marginBottom: "8px",
    }}
  >
    CURRENT PORTFOLIO PERFORMANCE
  </div>

  <div
    style={{
      fontSize: "24px",
      fontWeight: 800,
      marginBottom: "6px",
    }}
  >
    {formatCurrency(portfolioValue)}
  </div>

  <div
    style={{
      fontSize: "12px",
      color: "rgba(255,255,255,0.45)",
    }}
  >
    Current portfolio value
  </div>

  <div
    style={{
      marginTop: "12px",
      fontSize: "12px",
      fontWeight: 700,
    }}
  >
    Return: {overallReturn}
  </div>
</div>    

          </div>

        </div>


        {/* ASSET ALLOCATION */}

        <div
          className="glass-card"
          style={{
            padding: "20px",
            minHeight: "280px",
          }}
        >

          <div
            style={{
              fontSize: "15px",
              fontWeight: 800,
            }}
          >
            Asset Allocation
          </div>

          <div
            style={{
              marginTop: "4px",
              fontSize: "11px",
              color: "rgba(255,255,255,0.45)",
            }}
          >
            Where your investment money is allocated
          </div>

          <div
            style={{
              height: "190px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >

            <div
              style={{
                width: "130px",
                height: "130px",
                borderRadius: "50%",
                border:
                  "18px solid rgba(168,85,247,0.10)",
                boxShadow:
                  "0 0 0 1px rgba(255,255,255,0.05)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <div
                style={{
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontSize: "20px",
                    fontWeight: 800,
                  }}
                >
                {totalInvested > 0 ? "100%" : "0%"}
                </div>

                <div
                  style={{
                    fontSize: "9px",
                    color: "rgba(255,255,255,0.40)",
                    textTransform: "uppercase",
                  }}
                >
                  Invested
                </div>
              </div>
            </div>

          </div>

          <div
  style={{
    marginTop: "4px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  }}
>
  {Object.entries(assetAllocation).map(
    ([type, value]) => {
      const percentage =
        totalInvested > 0
          ? (value / totalInvested) * 100
          : 0;

      return (
        <div
          key={type}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "11px",
          }}
        >
          <span
            style={{
              color: "rgba(255,255,255,0.65)",
            }}
          >
            {type}
          </span>

          <span
            style={{
              fontWeight: 700,
            }}
          >
            {percentage.toFixed(1)}%
          </span>
        </div>
      );
    }
  )}
</div>

        </div>

      </div>


      {/* =====================================================
          HOLDINGS PREVIEW
      ===================================================== */}

      <div
        className="glass-card"
        style={{
          padding: "20px",
        }}
      >

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
            marginBottom: "16px",
          }}
        >

          <div>
            <div
              style={{
                fontSize: "15px",
                fontWeight: 800,
              }}
            >
              Holdings
            </div>

            <div
              style={{
                marginTop: "4px",
                fontSize: "11px",
                color: "rgba(255,255,255,0.45)",
              }}
            >
              Your current investments
            </div>
          </div>

          <span
            style={{
              padding: "5px 9px",
              borderRadius: "999px",
              fontSize: "10px",
              color: "rgba(255,255,255,0.55)",
              background:
                "rgba(255,255,255,0.05)",
              border:
                "1px solid rgba(255,255,255,0.08)",
            }}
          >
            {investments.length} Holdings
          </span>

        </div>

        <div
  style={{
    minHeight: "120px",
    borderRadius: "14px",
    background:
      "rgba(255,255,255,0.02)",
    border:
      "1px solid rgba(255,255,255,0.06)",
    padding: "14px",
  }}
>

  {investments.length === 0 ? (

    <div
      style={{
        minHeight: "90px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
      }}
    >
      <div>

        <Wallet
          size={26}
          style={{
            opacity: 0.45,
            marginBottom: "7px",
          }}
        />

        <div
          style={{
            fontSize: "13px",
            fontWeight: 700,
          }}
        >
          No holdings yet
        </div>

        <div
          style={{
            marginTop: "4px",
            fontSize: "11px",
            color:
              "rgba(255,255,255,0.40)",
          }}
        >
          Your investments will appear here.
        </div>

      </div>
    </div>

  ) : (

    investments.map((investment) => {

      const investedAmount =
        Number(investment.quantity || 0) *
        Number(investment.buy_price || 0);
      const currentValue =
  Number(investment.quantity || 0) *
  Number(
    investment.current_price ??
      investment.buy_price ??
      0
  );

const gainLoss =
  currentValue - investedAmount;

const holdingReturn =
  investedAmount > 0
    ? (
        (gainLoss / investedAmount) *
        100
      ).toFixed(2) + "%"
    : "0.00%";

      return (
        <div
          key={investment.id}
          style={{
            display: "grid",
            gridTemplateColumns:
              "minmax(0, 1fr) auto",
            gap: "12px",
            alignItems: "center",
            padding: "14px",
            borderRadius: "12px",
            background:
              "rgba(255,255,255,0.04)",
            border:
              "1px solid rgba(255,255,255,0.08)",
            marginBottom: "8px",
          }}
        >

          <div>

            <div
              style={{
                fontSize: "14px",
                fontWeight: 800,
              }}
            >
              {investment.name}
            </div>

            <div
              style={{
                marginTop: "4px",
                fontSize: "11px",
                color:
                  "rgba(255,255,255,0.45)",
              }}
            >
              {investment.investment_type}
              {investment.symbol
                ? ` • ${investment.symbol}`
                : ""}
            </div>

            <div
              style={{
                marginTop: "6px",
                fontSize: "11px",
                color:
                  "rgba(255,255,255,0.55)",
              }}
            >
              Qty: {investment.quantity}
              {" • "}
              Buy Price:{" "}
              {formatCurrency(
                investment.buy_price
              )}
            </div>

          </div>

      <div
  style={{
    textAlign: "right",
  }}
>
  {/* INVESTED AMOUNT */}
  <div
    style={{
      fontSize: "14px",
      fontWeight: 800,
    }}
  >
    {formatCurrency(investedAmount)}
  </div>

  <div
    style={{
      marginTop: "4px",
      fontSize: "10px",
      color: "rgba(255,255,255,0.40)",
    }}
  >
    Invested
  </div>

  {/* CURRENT VALUE */}
  <div
    style={{
      marginTop: "8px",
      fontSize: "13px",
      fontWeight: 800,
    }}
  >
    {formatCurrency(currentValue)}
  </div>

  <div
    style={{
      marginTop: "4px",
      fontSize: "10px",
      color: "rgba(255,255,255,0.40)",
    }}
  >
    Current Value
  </div>

  {/* GAIN / LOSS */}
  <div
    style={{
      marginTop: "8px",
      fontSize: "12px",
      fontWeight: 700,
    }}
  >
    {formatCurrency(gainLoss)}
  </div>

  <div
    style={{
      marginTop: "4px",
      fontSize: "10px",
      color: "rgba(255,255,255,0.40)",
    }}
  >
    Gain / Loss
  </div>

  {/* RETURN */}
  <div
    style={{
      marginTop: "8px",
      fontSize: "11px",
      fontWeight: 700,
    }}
  >
    Return: {holdingReturn}
  </div>
{/* =====================================================
    INVESTMENT ACTION BUTTONS
===================================================== */}

<div
  style={{
    display: "grid",
    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
    gap: "6px",
    marginTop: "10px",
  }}
>

  {/* BUY */}
  <button
    type="button"
    className="small-button"
    style={{
      cursor: "pointer",
      color: "#86efac",
    }}
    onClick={() =>
      openInvestmentTransaction(
        investment,
        "BUY"
      )
    }
  >
    BUY
  </button>

  {/* SELL */}
  <button
    type="button"
    className="small-button"
    style={{
      cursor: "pointer",
      color: "#fca5a5",
    }}
    onClick={() =>
      openInvestmentTransaction(
        investment,
        "SELL"
      )
    }
  >
    SELL
  </button>

  {/* HISTORY */}
  <button
    type="button"
    className="small-button"
    style={{
      cursor: "pointer",
    }}
    onClick={() =>
      openInvestmentTransactions(
        investment
      )
    }
  >
    History
  </button>

</div>

{/* EDIT BUTTON */}
<button
  type="button"
  className="small-button"
  style={{
    marginTop: "6px",
    cursor: "pointer",
  }}
  onClick={() =>
    handleEditInvestment(investment)
  }
>
  Edit
</button>

{/* Remove only this record; the backend checks transaction history. */}
<button
  type="button"
  aria-label={`Remove ${investment.name || "investment"} record ${investment.id}`}
  title="Remove this investment record"
  className="small-button"
  style={{
    marginTop: "6px",
    marginLeft: "6px",
    cursor: "pointer",
    color: "#fca5a5",
    minWidth: "34px",
    padding: "6px 9px",
  }}
  onClick={() => handleDeleteInvestment(investment)}
>
  <Trash2 size={14} aria-hidden="true" />
</button>

</div>  

        </div>
      );
    })

  )}

</div>
         </div>

  {/* =====================================================
      STEP 3 — BUY / SELL TRANSACTION MODAL
  ===================================================== */}

  {transactionModal && (

    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "18px",
        background: "rgba(0,0,0,0.72)",
        backdropFilter: "blur(8px)",
      }}
      onClick={closeInvestmentTransactionModal}
    >

      <div
        className="glass-card"
        style={{
          width: "100%",
          maxWidth: "560px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "22px",
        }}
        onClick={(event) =>
          event.stopPropagation()
        }
      >

        {/* MODAL HEADER */}

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
            marginBottom: "18px",
          }}
        >

          <div>

            <p className="card-label">
              INVESTMENT TRANSACTION
            </p>

            <h3
              style={{
                margin: "4px 0 0",
              }}
            >
              {transactionModal.investment.name}
            </h3>

            <div
              style={{
                marginTop: "4px",
                fontSize: "11px",
                color: "rgba(255,255,255,0.45)",
              }}
            >
              {transactionModal.investment.symbol ||
                transactionModal.investment.investment_type}
            </div>

          </div>

          <button
            type="button"
            className="icon-button"
            onClick={closeInvestmentTransactionModal}
          >
            <X size={18} />
          </button>

        </div>


        {/* BUY / SELL / HISTORY */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(3, minmax(0, 1fr))",
            gap: "8px",
            marginBottom: "18px",
          }}
        >

          <button
            type="button"
            className="small-button"
            style={{
              padding: "10px",
              color:
                transactionType === "BUY"
                  ? "#86efac"
                  : "rgba(255,255,255,0.55)",
            }}
            onClick={() => {
              setTransactionType("BUY");
              setTransactionModal({
                ...transactionModal,
                mode: "form",
              });
              setTransactionMessage("");
            }}
          >
            BUY
          </button>


          <button
            type="button"
            className="small-button"
            style={{
              padding: "10px",
              color:
                transactionType === "SELL"
                  ? "#fca5a5"
                  : "rgba(255,255,255,0.55)",
            }}
            onClick={() => {
              setTransactionType("SELL");
              setTransactionModal({
                ...transactionModal,
                mode: "form",
              });
              setTransactionMessage("");
            }}
          >
            SELL
          </button>


          <button
            type="button"
            className="small-button"
            style={{
              padding: "10px",
            }}
            onClick={async () => {

              setTransactionModal({
                ...transactionModal,
                mode: "history",
              });

              await loadInvestmentTransactions(
                transactionModal.investment.id
              );

            }}
          >
            History
          </button>

        </div>


        {/* =================================================
            BUY / SELL FORM
        ================================================= */}

        {transactionModal.mode === "form" && (

          <div>

            <div
              style={{
                padding: "12px",
                borderRadius: "12px",
                marginBottom: "16px",
                background:
                  transactionType === "BUY"
                    ? "rgba(34,197,94,0.08)"
                    : "rgba(239,68,68,0.08)",
              }}
            >

              <div
                style={{
                  fontSize: "12px",
                  fontWeight: 800,
                }}
              >
                {transactionType === "BUY"
                  ? "Buy Investment"
                  : "Sell Investment"}
              </div>

              <div
                style={{
                  marginTop: "4px",
                  fontSize: "10px",
                  color:
                    "rgba(255,255,255,0.45)",
                }}
              >
                Record this transaction in your
                permanent investment ledger.
              </div>

            </div>


            {/* QUANTITY */}

            <label
              style={{
                display: "block",
                marginBottom: "6px",
                fontSize: "11px",
                color:
                  "rgba(255,255,255,0.55)",
              }}
            >
              Quantity
            </label>

            <input
              type="number"
              min="0"
              step="any"
              value={transactionForm.quantity}
              onChange={(event) =>
                setTransactionForm((previous) => ({
                  ...previous,
                  quantity:
                    event.target.value,
                }))
              }
              placeholder="Enter quantity"
              style={investmentFieldStyle}
            />


            {/* PRICE */}

            <label
              style={{
                display: "block",
                marginTop: "12px",
                marginBottom: "6px",
                fontSize: "11px",
                color:
                  "rgba(255,255,255,0.55)",
              }}
            >
              Price
            </label>

            <input
              type="number"
              min="0"
              step="any"
              value={transactionForm.price}
              onChange={(event) =>
                setTransactionForm((previous) => ({
                  ...previous,
                  price:
                    event.target.value,
                }))
              }
              placeholder="Enter price"
              style={investmentFieldStyle}
            />


            {/* FEES */}

            <label
              style={{
                display: "block",
                marginTop: "12px",
                marginBottom: "6px",
                fontSize: "11px",
                color:
                  "rgba(255,255,255,0.55)",
              }}
            >
              Fees
            </label>

            <input
              type="number"
              min="0"
              step="any"
              value={transactionForm.fees}
              onChange={(event) =>
                setTransactionForm((previous) => ({
                  ...previous,
                  fees:
                    event.target.value,
                }))
              }
              placeholder="0"
              style={investmentFieldStyle}
            />


            {/* TRANSACTION DATE */}

            <label
              style={{
                display: "block",
                marginTop: "12px",
                marginBottom: "6px",
                fontSize: "11px",
                color:
                  "rgba(255,255,255,0.55)",
              }}
            >
              Transaction Date
            </label>

            <input
              type="date"
              value={
                transactionForm.transaction_date
              }
              onChange={(event) =>
                setTransactionForm((previous) => ({
                  ...previous,
                  transaction_date:
                    event.target.value,
                }))
              }
              style={{
                ...investmentFieldStyle,
                colorScheme: "dark",
              }}
            />


            {/* NOTES */}

            <label
              style={{
                display: "block",
                marginTop: "12px",
                marginBottom: "6px",
                fontSize: "11px",
                color:
                  "rgba(255,255,255,0.55)",
              }}
            >
              Notes
            </label>

            <textarea
              rows={3}
              value={transactionForm.notes}
              onChange={(event) =>
                setTransactionForm((previous) => ({
                  ...previous,
                  notes:
                    event.target.value,
                }))
              }
              placeholder="Optional notes"
              style={{
                ...investmentFieldStyle,
                resize: "vertical",
              }}
            />


            {/* MESSAGE */}

            {transactionMessage && (

              <div
                style={{
                  marginTop: "12px",
                  padding: "10px",
                  borderRadius: "10px",
                  background:
                    "rgba(255,255,255,0.05)",
                  fontSize: "11px",
                }}
              >
                {transactionMessage}
              </div>

            )}


            {/* SUBMIT */}

            <button
              type="button"
              className="primary-button"
              style={{
                width: "100%",
                justifyContent: "center",
                marginTop: "16px",
              }}
              disabled={transactionLoading}
              onClick={
                handleInvestmentTransactionSubmit
              }
            >
              {transactionLoading
                ? "Saving..."
                : `Confirm ${transactionType}`}
            </button>

          </div>

        )}


        {/* =================================================
            TRANSACTION HISTORY
        ================================================= */}

        {transactionModal.mode === "history" && (

          <div>

            <div
              style={{
                marginBottom: "12px",
                fontSize: "13px",
                fontWeight: 800,
              }}
            >
              Transaction History
            </div>

            {transactionHistoryLoading ? (

              <div
                style={{
                  padding: "30px 10px",
                  textAlign: "center",
                  fontSize: "12px",
                  color:
                    "rgba(255,255,255,0.45)",
                }}
              >
                Loading transactions...
              </div>

            ) : investmentTransactions.length ===
              0 ? (

              <div
                style={{
                  padding: "30px 10px",
                  textAlign: "center",
                  fontSize: "12px",
                  color:
                    "rgba(255,255,255,0.45)",
                }}
              >
                No transactions yet.
              </div>

            ) : (

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                }}
              >

                {investmentTransactions.map(
                  (transaction) => (

                    <div
                      key={transaction.id}
                      style={{
                        padding: "12px",
                        borderRadius: "12px",
                        background:
                          "rgba(255,255,255,0.04)",
                        border:
                          "1px solid rgba(255,255,255,0.08)",
                      }}
                    >

                      <div
                        style={{
                          display: "flex",
                          justifyContent:
                            "space-between",
                          gap: "10px",
                        }}
                      >

                        <div>

                          <div
                            style={{
                              fontSize: "12px",
                              fontWeight: 800,
                              color:
                                transaction.transaction_type ===
                                "BUY"
                                  ? "#86efac"
                                  : "#fca5a5",
                            }}
                          >
                            {transaction.transaction_type}
                          </div>

                          <div
                            style={{
                              marginTop: "4px",
                              fontSize: "10px",
                              color:
                                "rgba(255,255,255,0.45)",
                            }}
                          >
                            {transaction.transaction_date}
                          </div>

                        </div>


                        <div
                          style={{
                            textAlign: "right",
                          }}
                        >

                          <div
                            style={{
                              fontSize: "12px",
                              fontWeight: 800,
                            }}
                          >
                            {transaction.quantity}
                            {" × "}
                            {formatCurrency(
                              transaction.price
                            )}
                          </div>

                          <div
                            style={{
                              marginTop: "4px",
                              fontSize: "10px",
                              color:
                                "rgba(255,255,255,0.45)",
                            }}
                          >
                            Fees:{" "}
                            {formatCurrency(
                              transaction.fees
                            )}
                          </div>

                        </div>

                      </div>


                      {transaction.notes && (

                        <div
                          style={{
                            marginTop: "8px",
                            fontSize: "10px",
                            color:
                              "rgba(255,255,255,0.45)",
                          }}
                        >
                          {transaction.notes}
                        </div>

                      )}

                    </div>

                  )
                )}

              </div>

            )}

          </div>

        )}

      </div>

    </div>

  )}

    </div>
      
  );
              }         

// ============================================================
// ACCOUNTS
// ============================================================

function Accounts() {

  // ----------------------------------------------------------
  // STATE
  // ----------------------------------------------------------

  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ----------------------------------------------------------
  // ACCOUNT FORM STATE
  // ----------------------------------------------------------

  const [showAccountForm, setShowAccountForm] = useState(false);
  const [accountSaving, setAccountSaving] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [accountToDelete, setAccountToDelete] = useState(null);
  const [accountDeleting, setAccountDeleting] = useState(false);
  const [accountStatusSaving, setAccountStatusSaving] = useState(false);
  const [accountForm, setAccountForm] = useState({
    name: "",
    account_type: "bank",
    institution: "",
    account_number: "",
    currency: "INR",
    balance: "",
  });

  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";

  const USER_ID = 1;

  // ----------------------------------------------------------
  // LOAD ACCOUNTS
  // ----------------------------------------------------------

  useEffect(() => {

    const loadAccounts = async () => {

      try {

        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_BASE_URL}/api/accounts/?user_id=${USER_ID}`
        );

        if (!response.ok) {
          throw new Error(
            `Accounts API error: ${response.status}`
          );
        }

        const data = await response.json();

        setAccounts(data);

      } catch (err) {

        console.error("Accounts API error:", err);

        setError(
          "Unable to load accounts."
        );

      } finally {

        setLoading(false);

      }
    };

    loadAccounts();

  }, []);


// ----------------------------------------------------------
// SAVE ACCOUNT
// CREATE / UPDATE
// ----------------------------------------------------------

const handleAccountSubmit = async () => {

  try {

    setError("");

    if (!accountForm.name.trim()) {
      setError("Please enter an account name.");
      return;
    }

    if (!accountForm.institution.trim()) {
      setError("Please enter the institution name.");
      return;
    }

    if (
      accountForm.balance === "" ||
      Number(accountForm.balance) < 0
    ) {
      setError("Please enter a valid opening balance.");
      return;
    }

    setAccountSaving(true);

    const isEditing = Boolean(editingAccount);

    const payload = isEditing
      ? {
          name: accountForm.name.trim(),
          account_type: accountForm.account_type,
          institution: accountForm.institution.trim(),
          account_number:
            accountForm.account_number.trim(),
          currency: accountForm.currency,
          balance: Number(accountForm.balance),
        }
      : {
          user_id: USER_ID,
          name: accountForm.name.trim(),
          account_type: accountForm.account_type,
          institution: accountForm.institution.trim(),
          account_number:
            accountForm.account_number.trim(),
          currency: accountForm.currency,
          balance: Number(accountForm.balance),
        };

    const response = await fetch(
      isEditing
        ? `${API_BASE_URL}/api/accounts/${editingAccount.id}`
        : `${API_BASE_URL}/api/accounts/`,
      {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          (isEditing
            ? "Unable to update account."
            : "Unable to create account.")
      );
    }

    setAccounts((previous) =>
      isEditing
        ? previous.map((account) =>
            account.id === data.id
              ? data
              : account
          )
        : [data, ...previous]
    );

    setAccountForm({
      name: "",
      account_type: "bank",
      institution: "",
      account_number: "",
      currency: "INR",
      balance: "",
    });

    setEditingAccount(null);
    setShowAccountForm(false);

  } catch (err) {

    console.error(
      "Save account error:",
      err
    );

    setError(
      err?.message ||
        "Unable to save account."
    );

  } finally {

    setAccountSaving(false);

  }

};

// ----------------------------------------------------------
// TOGGLE ACCOUNT STATUS
// ACTIVE / INACTIVE
// ----------------------------------------------------------

const handleToggleAccountStatus = async (account) => {

  try {

    setAccountStatusSaving(true);
    setError("");

    const response = await fetch(
      `${API_BASE_URL}/api/accounts/${account.id}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          is_active: !account.is_active,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          "Unable to update account status."
      );
    }

    setAccounts((previous) =>
      previous.map((item) =>
        item.id === data.id
          ? data
          : item
      )
    );

  } catch (err) {

    console.error(
      "Account status error:",
      err
    );

    setError(
      err?.message ||
        "Unable to update account status."
    );

  } finally {

    setAccountStatusSaving(false);

  }

};
  
// ----------------------------------------------------------
// EDIT ACCOUNT — LOAD ACCOUNT INTO FORM
// ----------------------------------------------------------

const handleEditAccount = (account) => {
  setEditingAccount(account);

  setAccountForm({
    name: account.name || "",
    account_type: account.account_type || "bank",
    institution: account.institution || "",
    account_number: account.account_number || "",
    currency: account.currency || "INR",
    balance: account.balance ?? "",
  });

  setShowAccountForm(true);
  setError("");
};
  
// ----------------------------------------------------------
// DELETE ACCOUNT
// ----------------------------------------------------------

const deleteAccount = async () => {
  if (!accountToDelete) {
    return;
  }

  setAccountDeleting(true);
  setError("");

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/accounts/${accountToDelete.id}`,
      {
        method: "DELETE",
      }
    );

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          data?.message ||
          "Unable to delete account."
      );
    }

    setAccountToDelete(null);

    await loadAccounts();

    setMessage("Account deleted successfully.");
  } catch (err) {
    console.error("Delete account error:", err);

    setError(
      err?.message ||
        "Unable to delete account."
    );
  } finally {
    setAccountDeleting(false);
  }
};
  
  // ----------------------------------------------------------
  // FORMAT CURRENCY
  // ----------------------------------------------------------

  const formatCurrency = (value) => {

    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(value || 0);

  };

  // ----------------------------------------------------------
  // TOTAL BALANCE
  // ----------------------------------------------------------

  const totalBalance = accounts.reduce(
    (total, account) =>
      total + Number(account.balance || 0),
    0
  );

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (

    <div className="dashboard">

      {/* ====================================================
          HEADER
      ==================================================== */}

      <section className="welcome-section">

        <div>

          <p className="welcome-label">
            MONEY
          </p>

          <h2>
            Your <span>accounts.</span>
          </h2>

          <p className="welcome-description">
            Manage your bank accounts, cards and
            other financial accounts in one place.
          </p>

        </div>

        <button
  className="primary-button"
  onClick={() => setShowAccountForm(true)}
>
  <Plus size={18} />
  Add Account
</button>

      </section>


      {/* ====================================================
          SUMMARY
      ==================================================== */}

      <section className="metrics-grid">

        <MetricCard
          title="Total Balance"
          value={
            loading
              ? "Loading..."
              : formatCurrency(totalBalance)
          }
          change={`${accounts.length} account${
            accounts.length === 1 ? "" : "s"
          }`}
          positive
          icon={Wallet}
        />

        <MetricCard
          title="Active Accounts"
          value={
            loading
              ? "Loading..."
              : String(
    accounts.filter(
      (account) => account.is_active
    ).length
  )
          }
          change="Connected"
          positive
          icon={Landmark}
        />

      </section>


      {/* ====================================================
          ERROR
      ==================================================== */}

      {error && (

        <div className="glass-card">

          <strong>
            {error}
          </strong>

        </div>

      )}


      {/* ====================================================
          ACCOUNT LIST
      ==================================================== */}

      <section className="glass-card">

        <div className="card-header">

          <div>

            <p className="card-label">
              YOUR ACCOUNTS
            </p>

            <h3>
              Connected Accounts
            </h3>

          </div>

          <span className="score">
            {accounts.length}
          </span>

        </div>


        {/* --------------------------------------------------
            LOADING
        -------------------------------------------------- */}

        {loading && (

          <div className="empty-chart">

            <strong>
              Loading accounts...
            </strong>

          </div>

        )}


        {/* --------------------------------------------------
            EMPTY
        -------------------------------------------------- */}

        {!loading && accounts.length === 0 && (

          <div className="empty-chart">

            <div className="chart-icon">
              <Wallet size={28} />
            </div>

            <strong>
              No accounts found
            </strong>

            <span>
              Add your first financial account
              to get started.
            </span>

          </div>

        )}


{/* --------------------------------------------------
    ACCOUNT CARDS
-------------------------------------------------- */}

{!loading && accounts.length > 0 && (

  <div
    style={{
      display: "grid",
      gap: "14px",
      marginTop: "20px",
    }}
  >

    {accounts.map((account) => (

      <div
        key={account.id}
        style={{
          display: "grid",
gridTemplateColumns: "minmax(0, 1fr) minmax(120px, 1fr) 90px",
alignItems: "center",
columnGap: "20px",
          padding: "20px",
          borderRadius: "18px",
          background:
            "linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03))",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow:
            "0 12px 30px rgba(0,0,0,0.18)",
          minHeight: "90px",
        }}
      >

        {/* ACCOUNT INFORMATION */}

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "15px",
            minWidth: 0,
          }}
        >

          {/* ACCOUNT ICON */}

          <div
            style={{
              width: "48px",
              height: "48px",
              minWidth: "48px",
              borderRadius: "14px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background:
                "linear-gradient(135deg, rgba(168,85,247,0.30), rgba(236,72,153,0.20))",
              border:
                "1px solid rgba(255,255,255,0.10)",
            }}
          >
            <Landmark size={21} />
          </div>

          {/* DETAILS */}

          <div
            style={{
              minWidth: 0,
            }}
          >

            <div
              style={{
                fontSize: "15px",
                fontWeight: 700,
                color: "#ffffff",
                marginBottom: "5px",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {account.name}
            </div>

            <div
              style={{
                fontSize: "12px",
                color: "rgba(255,255,255,0.60)",
                textTransform: "capitalize",
              }}
            >
              {account.institution ||
                "Financial Account"}
              {" • "}
              {account.type}
            </div>

            {account.account_number && (

              <div
                style={{
                  fontSize: "11px",
                  color: "rgba(255,255,255,0.40)",
                  marginTop: "4px",
                }}
              >
                {account.account_number}
              </div>

            )}

            <div
  style={{
    display: "flex",
    alignItems: "center",
    gap: "5px",
    marginTop: "6px",
    fontSize: "10px",
    color: account.is_active
      ? "#4ade80"
      : "#f87171",
  }}
>
  <span
    style={{
      width: "6px",
      height: "6px",
      borderRadius: "50%",
      background: account.is_active
        ? "#4ade80"
        : "#f87171",
    }}
  />

  {account.is_active ? "Active" : "Inactive"}
</div>
          </div>

        </div>


        {/* BALANCE */}

        <div
          style={{
            textAlign: "center",
            minWidth: "110px",
          }}
        >

          <div
            style={{
              fontSize: "10px",
              color: "rgba(255,255,255,0.45)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              marginBottom: "5px",
            }}
          >
            Balance
          </div>

          <div
            style={{
              fontSize: "17px",
              fontWeight: 800,
              color: "#ffffff",
              whiteSpace: "nowrap",
            }}
          >
            {formatCurrency(account.balance)}
          </div>

        </div>


{/* ACCOUNT ACTIONS */}
<div
  style={{
    display: "flex",
    flexDirection: "column",
    gap: "7px",
    alignItems: "stretch",
  }}
>

          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              handleEditAccount(account)
            }
            style={{
              width: "100%",
              padding: "7px 12px",
              fontSize: "11px",
            }}
          >
            Edit
          </button>

                        <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  handleToggleAccountStatus(account)
                }
                disabled={accountStatusSaving}
                style={{
                  width: "100%",
                  padding: "7px 12px",
                  fontSize: "11px",
                  color: account.is_active
                    ? "#fbbf24"
                    : "#4ade80",
                  borderColor: account.is_active
                    ? "rgba(251,191,36,0.25)"
                    : "rgba(74,222,128,0.25)",
                }}
              >
                {account.is_active
                  ? "Deactivate"
                  : "Activate"}
              </button>
          
          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              setAccountToDelete(account)
            }
            disabled={accountDeleting}
            style={{
  width: "100%",
  padding: "7px 12px",
  fontSize: "11px",
  color: "#fb7185",
  borderColor: "rgba(251,113,133,0.25)",
}}
          >
            Delete
          </button>

        </div>
      </div>

    ))}

    </div>

)}

        {/* ==================================================
            ADD ACCOUNT FORM
        ================================================== */}

        {showAccountForm && (

          <div
            className="glass-card"
            style={{
              marginTop: "20px",
            }}
          >

            <div className="card-header">

              <div>
                <p className="card-label">
                  MONEY
                </p>

                <h3>
                  Add Account
                </h3>
              </div>

            </div>

            <div
              style={{
                display: "grid",
                gap: "14px",
              }}
            >

              <input
                type="text"
                placeholder="Account name"
                value={accountForm.name}
                onChange={(event) =>
                  setAccountForm({
                    ...accountForm,
                    name: event.target.value,
                  })
                }
              />

              <select
                value={accountForm.account_type}
                onChange={(event) =>
                  setAccountForm({
                    ...accountForm,
                    account_type: event.target.value,
                  })
                }
              >
                <option value="bank">
                  Bank
                </option>

                <option value="credit_card">
                  Credit Card
                </option>

                <option value="cash">
                  Cash
                </option>

                <option value="investment">
                  Investment
                </option>

                <option value="other">
                  Other
                </option>
              </select>

              <input
                type="text"
                placeholder="Institution / Bank name"
                value={accountForm.institution}
                onChange={(event) =>
                  setAccountForm({
                    ...accountForm,
                    institution: event.target.value,
                  })
                }
              />

              <input
                type="text"
                placeholder="Account number"
                value={accountForm.account_number}
                onChange={(event) =>
                  setAccountForm({
                    ...accountForm,
                    account_number: event.target.value,
                  })
                }
              />

              <input
                type="number"
                placeholder="Opening balance"
                value={accountForm.balance}
                onChange={(event) =>
                  setAccountForm({
                    ...accountForm,
                    balance: event.target.value,
                  })
                }
              />

              <div
                style={{
                  display: "flex",
                  gap: "10px",
                  marginTop: "8px",
                }}
              >

                <button
                  type="button"
                  className="primary-button"
                  onClick={handleAccountSubmit}
                  disabled={accountSaving}
                >
                  {accountSaving
                    ? "Saving..."
                    : "Save Account"}
                </button>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    setShowAccountForm(false)
                  }
                  disabled={accountSaving}
                >
                  Cancel
                </button>

              </div>

            </div>

          </div>

        )}
        
      {/* ACCOUNT DELETE CONFIRMATION MODAL */}
      {accountToDelete && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.65)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            padding: "20px",
          }}
        >
          <div
            className="glass-card"
            style={{
              width: "100%",
              maxWidth: "420px",
              padding: "24px",
            }}
          >
            <div className="card-header">
              <div>
                <p className="card-label">
                  ACCOUNT
                </p>

                <h3>
                  Delete Account
                </h3>
              </div>
            </div>

            <p
              style={{
                color: "rgba(255,255,255,0.70)",
                lineHeight: 1.6,
                marginTop: "16px",
              }}
            >
              Are you sure you want to delete{" "}
              <strong style={{ color: "#ffffff" }}>
                {accountToDelete.name}
              </strong>
              ?
            </p>

            <p
              style={{
                color: "rgba(255,255,255,0.50)",
                fontSize: "13px",
                marginTop: "8px",
              }}
            >
              This action cannot be undone.
            </p>

            <div
              style={{
                display: "flex",
                gap: "10px",
                marginTop: "20px",
                justifyContent: "flex-end",
              }}
            >
              <button
                type="button"
                className="secondary-button"
                onClick={() => setAccountToDelete(null)}
                disabled={accountDeleting}
              >
                Cancel
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={deleteAccount}
                disabled={accountDeleting}
                style={{
                  color: "#fb7185",
                  borderColor: "rgba(251,113,133,0.25)",
                }}
              >
                {accountDeleting
                  ? "Deleting..."
                  : "Delete Account"}
              </button>
            </div>
          </div>
        </div>
      )}
        
      </section>

    </div>
    
    );
}


// ============================================================
// BUDGET
// ============================================================

function Budget() {

  // ----------------------------------------------------------
  // STATE
  // ----------------------------------------------------------

  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [transactions, setTransactions] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [budgetToDelete, setBudgetToDelete] = useState(null);
  const [budgetDeleting, setBudgetDeleting] = useState(false);
  const [formData, setFormData] = useState({
    month: new Date().toISOString().slice(0, 7),
    category_id: "",
    amount: "",
  });

  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";

  const USER_ID = 1;

  // ----------------------------------------------------------
  // LOAD BUDGETS
  // ----------------------------------------------------------

  async function loadBudgets() {

    try {

      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/budgets/?user_id=${USER_ID}`
      );

      if (!response.ok) {
        throw new Error("Unable to load budgets.");
      }

      const data = await response.json();

      setBudgets(
        Array.isArray(data) ? data : []
      );

    } catch (err) {

      console.error("Budget API error:", err);

      setError(
        err?.message || "Unable to load budgets."
      );

    } finally {

      setLoading(false);

    }
  }

// ----------------------------------------------------------
// LOAD TRANSACTIONS
// ----------------------------------------------------------

async function loadTransactions() {

  try {

    const response = await fetch(
      `${API_BASE_URL}/api/transactions/?user_id=${USER_ID}`
    );

    if (!response.ok) {
      throw new Error("Unable to load transactions.");
    }

    const data = await response.json();

    setTransactions(
      Array.isArray(data) ? data : []
    );

  } catch (err) {

    console.error(
      "Budget transaction API error:",
      err
    );

    setError(
      err?.message ||
      "Unable to load transactions."
    );

  }
}
  
  // ----------------------------------------------------------
  // LOAD CATEGORIES
  // ----------------------------------------------------------

  async function loadCategories() {

    try {

      const response = await fetch(
        `${API_BASE_URL}/api/categories/?user_id=${USER_ID}`
      );

      if (!response.ok) {
        throw new Error("Unable to load categories.");
      }

      const data = await response.json();

      setCategories(
        Array.isArray(data) ? data : []
      );

    } catch (err) {

      console.error("Category API error:", err);

      setError(
        err?.message || "Unable to load categories."
      );

    }
  }

  // ----------------------------------------------------------
  // LOAD DATA WHEN BUDGET OPENS
  // ----------------------------------------------------------

  useEffect(() => {

    loadBudgets();
    loadCategories();
    loadTransactions();

  }, []);

  // ----------------------------------------------------------
  // OPEN ADD BUDGET FORM
  // ----------------------------------------------------------

  function openBudgetForm() {

    setFormData({
      month: new Date().toISOString().slice(0, 7),
      category_id: "",
      amount: "",
    });

    setMessage("");
    setError("");
    setEditingBudget(null);
    setShowForm(true);

  }

// ----------------------------------------------------------
// OPEN EDIT BUDGET FORM
// ----------------------------------------------------------

function openEditBudgetForm(budget) {

  setEditingBudget(budget);

  setFormData({
    month: budget.month || "",
    category_id: String(budget.category_id || ""),
    amount: budget.amount ?? "",
  });

  setMessage("");
  setError("");
  setShowForm(true);

}
  
  // ----------------------------------------------------------
  // FORM CHANGE
  // ----------------------------------------------------------

  function updateForm(field, value) {

    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));

  }

  // ----------------------------------------------------------
  // SAVE BUDGET
  // ----------------------------------------------------------

  async function saveBudget(event) {

    event.preventDefault();

    setMessage("");
    setError("");

    if (!formData.month) {
      setError("Please select a month.");
      return;
    }

    if (!formData.category_id) {
      setError("Please select a category.");
      return;
    }

    if (!formData.amount || Number(formData.amount) <= 0) {
      setError("Please enter a valid budget amount.");
      return;
    }

    try {

      setSaving(true);

      const response = await fetch(
  editingBudget
    ? `${API_BASE_URL}/api/budgets/${editingBudget.id}`
    : `${API_BASE_URL}/api/budgets/`,
  {
    method: editingBudget ? "PUT" : "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: USER_ID,
            month: formData.month,
            category_id: Number(formData.category_id),
            amount: Number(formData.amount),
          }),
        }
      );

      if (!response.ok) {

        const errorData =
          await response.json().catch(() => null);

        throw new Error(
          errorData?.detail ||
          "Unable to save budget."
        );

      }

      setMessage("Budget saved successfully.");

      setShowForm(false);

      setFormData({
        month: new Date().toISOString().slice(0, 7),
        category_id: "",
        amount: "",
      });

      await loadBudgets();

    } catch (err) {

      console.error("Save budget error:", err);

      setError(
        err?.message || "Unable to save budget."
      );

    } finally {

      setSaving(false);

    }
  }

// ----------------------------------------------------------
// DELETE BUDGET
// ----------------------------------------------------------

async function deleteBudget() {
  if (!budgetToDelete) {
    return;
  }

  setBudgetDeleting(true);
  setError("");

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/budgets/${budgetToDelete.id}`,
      {
        method: "DELETE",
      }
    );

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          data?.message ||
          "Unable to delete budget."
      );
    }

    setBudgetToDelete(null);

    await loadBudgets();

    setMessage("Budget deleted successfully.");
  } catch (err) {
    console.error("Delete budget error:", err);

    setError(
      err?.message ||
        "Unable to delete budget."
    );
  } finally {
    setBudgetDeleting(false);
  }
}
  
// ----------------------------------------------------------
// CALCULATE ACTUAL SPENDING
// ----------------------------------------------------------

function getActualSpending(categoryId, month) {

  return transactions
    .filter((transaction) => {

      const transactionMonth =
        transaction.transaction_date
          ? String(transaction.transaction_date).slice(0, 7)
          : "";

      const isExpense =
        transaction.transaction_type === "expense" ||
        transaction.transaction_type === "withdrawal" ||
        transaction.transaction_type === "tax" ||
        transaction.transaction_type === "loan_repayment";

      return (
        transactionMonth === month &&
        Number(transaction.category_id) === Number(categoryId) &&
        isExpense
      );

    })
    .reduce(
      (total, transaction) =>
        total + Number(transaction.amount || 0),
      0
    );
}
  
  // ----------------------------------------------------------
  // FORMAT CURRENCY
  // ----------------------------------------------------------

  function formatCurrency(value) {

    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value || 0));

  }

  // ----------------------------------------------------------
  // GET CATEGORY NAME
  // ----------------------------------------------------------

  function getCategoryName(categoryId) {

    const category = categories.find(
      (item) =>
        Number(item.id) === Number(categoryId)
    );

    return category?.name || "Category";

  }

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (

    <div className="dashboard">

      {/* ====================================================
          HEADER
      ==================================================== */}

      <section className="welcome-section">

        <div>

          <p className="welcome-label">
            MONEY
          </p>

          <h2>
            Your <span>budget.</span>
          </h2>

          <p className="welcome-description">
            Plan your monthly spending and stay
            within your financial limits.
          </p>

        </div>

        <button
          className="primary-button"
          onClick={openBudgetForm}
        >
          <Plus size={18} />
          Add Budget
        </button>

      </section>


      {/* ====================================================
          MESSAGE
      ==================================================== */}

      {message && (

        <div className="glass-card">

          <strong>
            {message}
          </strong>

        </div>

      )}


      {/* ====================================================
          ERROR
      ==================================================== */}

      {error && (

        <div className="glass-card">

          <strong>
            {error}
          </strong>

        </div>

      )}


      {/* ====================================================
          BUDGET LIST
      ==================================================== */}

      <section className="glass-card">

        <div className="card-header">

          <div>

            <p className="card-label">
              MONTHLY BUDGET
            </p>

            <h3>
              Budget Plans
            </h3>

          </div>

          <span className="score">
            {budgets.length}
          </span>

        </div>


        {/* --------------------------------------------------
            LOADING
        -------------------------------------------------- */}

        {loading && (

          <div className="empty-chart">

            <strong>
              Loading budgets...
            </strong>

          </div>

        )}


        {/* --------------------------------------------------
            EMPTY
        -------------------------------------------------- */}

        {!loading && budgets.length === 0 && (

          <div className="empty-chart">

            <div className="chart-icon">
              <PieChart size={28} />
            </div>

            <strong>
              No budgets created yet.
            </strong>

            <span>
              Create your first monthly budget
              to start controlling your spending.
            </span>

            <button
              className="secondary-button"
              onClick={openBudgetForm}
            >
              Add Budget
            </button>

          </div>

        )}


{/* ====================================================
    BUDGET CARDS
==================================================== */}

{!loading && budgets.length > 0 && (

  <div
    style={{
      display: "grid",
      gridTemplateColumns:
        "repeat(auto-fit, minmax(280px, 1fr))",
      gap: "16px",
      marginTop: "20px",
    }}
  >

    {budgets.map((budget) => (

      <div
        key={budget.id}
        style={{
          position: "relative",
          overflow: "hidden",
          padding: "20px",
          borderRadius: "20px",
          background:
            "linear-gradient(145deg, rgba(112,72,255,0.18), rgba(244,91,105,0.08), rgba(255,255,255,0.04))",
          border:
            "1px solid rgba(255,255,255,0.10)",
          boxShadow:
            "0 12px 35px rgba(0,0,0,0.18)",
        }}
      >

        {/* ---------------------------------------------
            DECORATIVE GLOW
        --------------------------------------------- */}

        <div
          style={{
            position: "absolute",
            width: "100px",
            height: "100px",
            borderRadius: "50%",
            background:
              "rgba(112,72,255,0.16)",
            filter: "blur(30px)",
            top: "-40px",
            right: "-30px",
            pointerEvents: "none",
          }}
        />

        {/* ---------------------------------------------
            TOP ROW
        --------------------------------------------- */}

        <div
          style={{
            position: "relative",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "12px",
          }}
        >

          <div>

            <div
              style={{
                fontSize: "12px",
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color:
                  "rgba(255,255,255,0.50)",
                marginBottom: "7px",
              }}
            >
              Budget Category
            </div>

            <h3
              style={{
                margin: 0,
                fontSize: "18px",
                fontWeight: 700,
                color: "#ffffff",
              }}
            >
              {getCategoryName(
                budget.category_id
              )}
            </h3>

          </div>

          <div
            style={{
              padding: "6px 10px",
              borderRadius: "999px",
              background:
                "rgba(112,72,255,0.18)",
              border:
                "1px solid rgba(150,120,255,0.20)",
              fontSize: "11px",
              fontWeight: 700,
              color: "#cfc4ff",
              whiteSpace: "nowrap",
            }}
          >
            ACTIVE
          </div>

        </div>


        {/* ---------------------------------------------
            MONTH
        --------------------------------------------- */}

        <div
          style={{
            position: "relative",
            marginTop: "18px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            color:
              "rgba(255,255,255,0.58)",
            fontSize: "13px",
          }}
        >

          <span>📅</span>

          <span>
            {budget.month}
          </span>

        </div>


        {/* ---------------------------------------------
            BUDGET AMOUNT
        --------------------------------------------- */}

        <div
          style={{
            position: "relative",
            marginTop: "20px",
            paddingTop: "16px",
            borderTop:
              "1px solid rgba(255,255,255,0.08)",
          }}
        >

          <div
            style={{
              fontSize: "12px",
              color:
                "rgba(255,255,255,0.50)",
              marginBottom: "5px",
            }}
          >
            Monthly Budget
          </div>

          <div
            style={{
              fontSize: "28px",
              lineHeight: 1.2,
              fontWeight: 800,
              color: "#ffffff",
              letterSpacing: "-0.02em",
            }}
          >
            {formatCurrency(
              budget.amount
            )}
          </div>

        </div>


        {/* ---------------------------------------------
            PROGRESS PLACEHOLDER
            Actual spending will be connected next.
        --------------------------------------------- */}

        <div
          style={{
            position: "relative",
            marginTop: "18px",
          }}
        >

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "11px",
              color:
                "rgba(255,255,255,0.45)",
              marginBottom: "7px",
            }}
          >

            <span>
  {Math.min(
    100,
    Math.round(
      (
        getActualSpending(
          budget.category_id,
          budget.month
        ) / Number(budget.amount || 0)
      ) * 100
    )
  )}%
</span>

          </div>

          <div
            style={{
              height: "7px",
              borderRadius: "999px",
              background:
                "rgba(255,255,255,0.08)",
              overflow: "hidden",
            }}
          >

            <div
              style={{
                width: `${Math.min(
  100,
  Math.round(
    (
      getActualSpending(
        budget.category_id,
        budget.month
      ) / Number(budget.amount || 0)
    ) * 100
  )
)}%`,
                height: "100%",
                borderRadius: "999px",
                background:
                  "linear-gradient(90deg, #7048ff, #f45b69)",
              }}
            />

          </div>

        </div>

  
{/* ---------------------------------------------
    CARD ACTIONS
--------------------------------------------- */}

<div
  style={{
    position: "relative",
    display: "flex",
    justifyContent: "flex-end",
    gap: "8px",
    marginTop: "16px",
  }}
>
  <button
    type="button"
    className="secondary-button"
    onClick={() => openEditBudgetForm(budget)}
    style={{
      padding: "7px 12px",
      fontSize: "11px",
    }}
  >
    Edit
  </button>
  <button
  type="button"
  className="secondary-button"
  onClick={() => setBudgetToDelete(budget)}
  disabled={budgetDeleting}
  style={{
    padding: "7px 12px",
    fontSize: "11px",
    marginLeft: "6px",
    color: "#fb7185",
    borderColor: "rgba(251,113,133,0.25)",
  }}
>
  Delete
</button>
</div>

        {/* ---------------------------------------------
            FOOTER
        --------------------------------------------- */}

        <div
          style={{
            position: "relative",
            marginTop: "18px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "11px",
            color:
              "rgba(255,255,255,0.42)",
          }}
        >

          <span>
            Budget #{budget.id}
          </span>

          <span>
            Monthly plan
          </span>

        </div>

      </div>

    ))}

  </div>

)}

  </section>    
      
      {/* ====================================================
          ADD BUDGET FORM
      ==================================================== */}

      {showForm && (

        <div className="glass-card">

          <div className="card-header">

            <div>

              <p className="card-label">
                NEW BUDGET
              </p>

              <h3>
                Create Budget
              </h3>

            </div>

          </div>


          <form onSubmit={saveBudget}>

            {/* MONTH */}

            <div style={{ marginBottom: "16px" }}>

              <label>
                Month
              </label>

              <input
                type="month"
                value={formData.month}
                onChange={(event) =>
                  updateForm(
                    "month",
                    event.target.value
                  )
                }
                style={{
                  width: "100%",
                  marginTop: "8px",
                  padding: "12px",
                  borderRadius: "12px",
                }}
              />

            </div>


            {/* CATEGORY */}

            <div style={{ marginBottom: "16px" }}>

              <label>
                Category
              </label>

              <select
                value={formData.category_id}
                onChange={(event) =>
                  updateForm(
                    "category_id",
                    event.target.value
                  )
                }
                style={{
                  width: "100%",
                  marginTop: "8px",
                  padding: "12px",
                  borderRadius: "12px",
                }}
              >

                <option value="">
                  Select category
                </option>

                {categories.map((category) => (

                  <option
                    key={category.id}
                    value={category.id}
                  >
                    {category.name}
                  </option>

                ))}

              </select>

            </div>


            {/* AMOUNT */}

            <div style={{ marginBottom: "16px" }}>

              <label>
                Monthly Budget Amount
              </label>

              <input
                type="number"
                min="0"
                step="0.01"
                placeholder="Enter amount"
                value={formData.amount}
                onChange={(event) =>
                  updateForm(
                    "amount",
                    event.target.value
                  )
                }
                style={{
                  width: "100%",
                  marginTop: "8px",
                  padding: "12px",
                  borderRadius: "12px",
                }}
              />

            </div>


            {/* ACTIONS */}

            <div
              style={{
                display: "flex",
                gap: "12px",
              }}
            >

              <button
                type="submit"
                className="primary-button"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : "Save Budget"}
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setShowForm(false)
                }
              >
                Cancel
              </button>

            </div>

          </form>

        </div>

            )}

      {/* ====================================================
          DELETE BUDGET CONFIRMATION
      ==================================================== */}

      {budgetToDelete && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 10000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            background: "rgba(0,0,0,0.65)",
            backdropFilter: "blur(10px)",
          }}
        >
          <div
            className="glass-card"
            style={{
              width: "100%",
              maxWidth: "420px",
              padding: "24px",
            }}
          >
            <p className="card-label">
              DELETE BUDGET
            </p>

            <h3>
              Delete this budget?
            </h3>

            <p
              style={{
                color: "rgba(255,255,255,0.60)",
                fontSize: "13px",
                lineHeight: 1.6,
                marginTop: "10px",
              }}
            >
              This budget will be permanently removed.
            </p>

            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "10px",
                marginTop: "22px",
              }}
            >
              <button
                type="button"
                className="secondary-button"
                onClick={() => setBudgetToDelete(null)}
                disabled={budgetDeleting}
              >
                Cancel
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={deleteBudget}
                disabled={budgetDeleting}
                style={{
                  color: "#fb7185",
                  borderColor:
                    "rgba(251,113,133,0.30)",
                }}
              >
                {budgetDeleting
                  ? "Deleting..."
                  : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>

  );

}



// ============================================================
// TRANSACTIONS
// ============================================================

function Transactions() {

  // ----------------------------------------------------------
  // STATE
  // ----------------------------------------------------------

  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

   
  // ----------------------------------------------------------
  // ACCOUNT & CATEGORY OPTIONS
  // ----------------------------------------------------------

  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);

  // ----------------------------------------------------------
  // ADD TRANSACTION FORM STATE
  // ----------------------------------------------------------

  const [showForm, setShowForm] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [deletingTransaction, setDeletingTransaction] = useState(null);
  const [formData, setFormData] = useState({
    account_id: "",
    category_id: "",
    transaction_type: "expense",
    amount: "",
    transaction_date: new Date().toISOString().split("T")[0],
    description: "",
    reference: "",
    loan_name: "",
    lender_name: "",
    loan_type: "Personal Loan",
    principal_amount: "",
    interest_rate: "",
    interest_type: "reducing_balance",
    tenure_months: "",
    emi_amount: "",
    first_payment_date: "",
    processing_fee: "0",
    loan_notes: "",
  });

// ----------------------------------------------------------
// TRANSACTION FORM OPTIONS & SAVE STATE
// ----------------------------------------------------------

const [savingTransaction, setSavingTransaction] = useState(false);
const [formMessage, setFormMessage] = useState("");

// Loan Disbursement is a special category within the existing Income flow.
const isLoanDisbursement = categories.some((category) =>
  String(category.id) === String(formData.category_id) &&
  String(category.name || "").trim().toLowerCase() === "loan disbursement"
) || formData.category_id === "__loan_disbursement__";
  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";

  const USER_ID = 1;

  const loanInputStyle = { width: "100%", boxSizing: "border-box", display: "block", marginTop: "6px", padding: "10px 11px", borderRadius: "9px", border: "1px solid rgba(255,255,255,0.14)", background: "#151525", color: "#fff", outline: "none" };

  // ----------------------------------------------------------
  // LOAD TRANSACTIONS
  // ----------------------------------------------------------

  useEffect(() => {

    const loadTransactions = async () => {

      try {

        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_BASE_URL}/api/transactions/?user_id=${USER_ID}`
        );

        if (!response.ok) {
          throw new Error(
            `Transactions API error: ${response.status}`
          );
        }

        const data = await response.json();

        setTransactions(data);

      } catch (err) {

        console.error(
          "Transactions API error:",
          err
        );

        setError(
          "Unable to load transactions."
        );

      } finally {

        setLoading(false);

      }

    };

    loadTransactions();

  }, []);

  // ----------------------------------------------------------
  // FORMAT CURRENCY
  // ----------------------------------------------------------

  const formatCurrency = (value) => {

    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(value || 0);

  };

  // ----------------------------------------------------------
  // TRANSACTION TYPE
  // ----------------------------------------------------------

  const isIncome = (transaction) => {

    return (
      transaction.transaction_type === "income"
    );

  };

  // ----------------------------------------------------------
  // FORM HANDLERS
  // ----------------------------------------------------------

  const handleFormChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // ----------------------------------------------------------
  // LOAD ACCOUNT & CATEGORY OPTIONS
  // ----------------------------------------------------------

  const loadFormOptions = async () => {
    try {
      const [accountsResponse, categoriesResponse] =
        await Promise.all([
          fetch(
            `${API_BASE_URL}/api/accounts/?user_id=${USER_ID}`
          ),
          fetch(
            `${API_BASE_URL}/api/categories/?user_id=${USER_ID}`
          ),
        ]);

      if (!accountsResponse.ok) {
        throw new Error(
          `Accounts API error: ${accountsResponse.status}`
        );
      }

      if (!categoriesResponse.ok) {
        throw new Error(
          `Categories API error: ${categoriesResponse.status}`
        );
      }

      const accountsData =
        await accountsResponse.json();

      const categoriesData =
        await categoriesResponse.json();

      setAccounts(
        Array.isArray(accountsData)
          ? accountsData
          : []
      );

      setCategories(
        Array.isArray(categoriesData)
          ? categoriesData
          : []
      );

    } catch (err) {
      console.error(
        "Transaction form options error:",
        err
      );

      setError(
        err?.message ||
        "Unable to load accounts and categories."
      );
    }
  };

  const openTransactionForm = async () => {
  setFormData({
    account_id: "",
    category_id: "",
    transaction_type: "expense",
    amount: "",
    transaction_date:
      new Date().toISOString().split("T")[0],
    description: "",
    reference: "",
    loan_name: "",
    lender_name: "",
    loan_type: "Personal Loan",
    principal_amount: "",
    interest_rate: "",
    interest_type: "reducing_balance",
    tenure_months: "",
    emi_amount: "",
    first_payment_date: "",
    processing_fee: "0",
    loan_notes: "",
  });

  setShowForm(true);
  setError("");

  await loadFormOptions();
};
  
  // ----------------------------------------------------------
  // OPEN EDIT TRANSACTION FORM
  // ----------------------------------------------------------

  const openEditTransactionForm = async (transaction) => {
    setEditingTransaction(transaction);

    setFormData({
      account_id: String(transaction.account_id || ""),
      category_id: String(transaction.category_id || ""),
      transaction_type: transaction.transaction_type || "expense",
      amount: transaction.amount ?? "",
      transaction_date:
        transaction.transaction_date ||
        new Date().toISOString().split("T")[0],
      description: transaction.description || "",
      reference: transaction.reference || "",
    });

    setError("");
    setFormMessage("");

    await loadFormOptions();

    setShowForm(true);
  };
  
  const closeTransactionForm = () => {
    setShowForm(false);
    setError("");
  };

// ----------------------------------------------------------
// SAVE TRANSACTION
// ----------------------------------------------------------

const handleTransactionSubmit = async () => {
  try {
    setError("");
    setFormMessage("");

    // Validate required fields
    if (!formData.account_id) {
      setFormMessage("Please select an account.");
      return;
    }

    if (!formData.category_id) {
      setFormMessage("Please select a category.");
      return;
    }

    const selectedCategory = categories.find((category) => String(category.id) === String(formData.category_id));
    const loanDisbursement = formData.transaction_type === "income" && (
      formData.category_id === "__loan_disbursement__" ||
      String(selectedCategory?.name || "").trim().toLowerCase() === "loan disbursement"
    );
    if (loanDisbursement) {
      if (!formData.loan_name.trim() || !formData.lender_name.trim() || !formData.principal_amount || Number(formData.principal_amount) <= 0) {
        setFormMessage("Enter the loan name, lender, and a valid gross principal amount.");
        return;
      }
      if (Number(formData.principal_amount) < Number(formData.amount)) {
        setFormMessage("Gross principal cannot be less than the amount received.");
        return;
      }
    }

    if (!formData.amount || Number(formData.amount) <= 0) {
      setFormMessage("Please enter a valid amount.");
      return;
    }

    if (!formData.transaction_date) {
      setFormMessage("Please select a transaction date.");
      return;
    }

    setSavingTransaction(true);

    const payload = {
      user_id: USER_ID,
      account_id: Number(formData.account_id),
      category_id: formData.category_id === "__loan_disbursement__" ? null : Number(formData.category_id),
      transaction_type: formData.transaction_type,
      amount: Number(formData.amount),
      description: formData.description.trim(),
      transaction_date: formData.transaction_date,
      reference: formData.reference.trim(),
      ...(loanDisbursement ? {
        loan_details: {
          name: formData.loan_name.trim(),
          lender_name: formData.lender_name.trim(),
          loan_type: formData.loan_type,
          principal_amount: Number(formData.principal_amount),
          interest_rate: formData.interest_rate === "" ? null : Number(formData.interest_rate),
          interest_type: formData.interest_type || "reducing_balance",
          tenure_months: formData.tenure_months === "" ? null : Number(formData.tenure_months),
          emi_amount: formData.emi_amount === "" ? null : Number(formData.emi_amount),
          first_payment_date: formData.first_payment_date || null,
          repayment_frequency: "monthly",
          processing_fee: Number(formData.processing_fee || 0),
          notes: formData.loan_notes.trim() || null,
        }
      } : {})
    };

  const isEditing = Boolean(editingTransaction);

const response = await fetch(
  isEditing
    ? `${API_BASE_URL}/api/transactions/${editingTransaction.id}`
    : `${API_BASE_URL}/api/transactions/`,
  {
    method: isEditing ? "PUT" : "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  }
);

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          "Unable to create transaction."
      );
    }

    // Refresh transaction list
    const refreshResponse = await fetch(
      `${API_BASE_URL}/api/transactions/?user_id=${USER_ID}`
    );

    if (!refreshResponse.ok) {
      throw new Error(
        "Transaction was saved, but the list could not be refreshed."
      );
    }

    const refreshedTransactions =
      await refreshResponse.json();

    setTransactions(refreshedTransactions);
    // Notify dashboard and other transaction-derived views to refresh from the API.
    window.dispatchEvent(new Event("financial-os:transactions-changed"));

    // Close and reset form
    setShowForm(false);

    setFormData({
      account_id: "",
      category_id: "",
      transaction_type: "expense",
      amount: "",
      transaction_date:
        new Date().toISOString().split("T")[0],
      description: "",
      reference: "",
    });

  } catch (err) {
    console.error(
      "Create transaction error:",
      err
    );

    setFormMessage(
      err.message ||
        "Unable to save transaction."
    );
  } finally {
    setSavingTransaction(false);
  }
};

  // ----------------------------------------------------------
  // DELETE TRANSACTION
  // ----------------------------------------------------------

  const handleDeleteTransaction = async (transactionId) => {
    if (!transactionId) {
      return;
    }

    setDeletingTransaction(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/transactions/${transactionId}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
          data?.message ||
          "Unable to delete transaction."
        );
      }

      setDeletingTransaction(null);


      const transactionsResponse = await fetch(
        `${API_BASE_URL}/api/transactions/?user_id=${USER_ID}`
      );

      if (transactionsResponse.ok) {
        const transactionsData =
          await transactionsResponse.json();

        setTransactions(
          Array.isArray(transactionsData)
            ? transactionsData
            : []
        );
        // Notify dashboard and other transaction-derived views after deletion.
        window.dispatchEvent(new Event("financial-os:transactions-changed"));
      }

    } catch (err) {
      console.error(
        "Delete transaction error:",
        err
      );

      setError(
        err?.message ||
        "Unable to delete transaction."
      );
    } finally {
      setDeletingTransaction(false);
    }
  };

// ----------------------------------------------------------
// TRANSACTION FORM MODAL
// ----------------------------------------------------------

const transactionFormModal = showForm && (
  <div
    style={{
      position: "fixed",
      inset: 0,
      zIndex: 9999,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "20px",
      background: "rgba(0,0,0,0.65)",
      backdropFilter: "blur(10px)",
    }}
    onClick={closeTransactionForm}
  >
    <div
      className="glass-card"
      style={{
        width: "100%",
        maxWidth: "620px",
        maxHeight: "90vh",
        overflowY: "auto",
        padding: "28px",
      }}
      onClick={(event) => event.stopPropagation()}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
        }}
      >
        <div>
          <p className="card-label">MONEY</p>
          <h3>Add Transaction</h3>
        </div>

        <button
          type="button"
          className="icon-button"
          onClick={closeTransactionForm}
        >
          <X size={20} />
        </button>
      </div>

      {/* TRANSACTION TYPE */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "12px",
          marginBottom: "18px",
        }}
      >
        <button
          type="button"
          onClick={() =>
            setFormData((previous) => ({
              ...previous,
              transaction_type: "expense",
            }))
          }
          style={{
            padding: "14px",
            borderRadius: "14px",
            border:
              formData.transaction_type === "expense"
                ? "1px solid rgba(239,68,68,0.7)"
                : "1px solid rgba(255,255,255,0.10)",
            background:
              formData.transaction_type === "expense"
                ? "rgba(239,68,68,0.16)"
                : "rgba(255,255,255,0.05)",
            color: "#fff",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          Expense
        </button>

        <button
          type="button"
          onClick={() =>
            setFormData((previous) => ({
              ...previous,
              transaction_type: "income",
            }))
          }
          style={{
            padding: "14px",
            borderRadius: "14px",
            border:
              formData.transaction_type === "income"
                ? "1px solid rgba(34,197,94,0.7)"
                : "1px solid rgba(255,255,255,0.10)",
            background:
              formData.transaction_type === "income"
                ? "rgba(34,197,94,0.16)"
                : "rgba(255,255,255,0.05)",
            color: "#fff",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          Income
        </button>
      </div>

      {/* ACCOUNT */}

      <div style={{ marginBottom: "16px" }}>
        <label
          style={{
            display: "block",
            marginBottom: "7px",
            fontSize: "13px",
            color: "rgba(255,255,255,0.70)",
          }}
        >
          Account
        </label>

        <select
          name="account_id"
          value={formData.account_id}
          onChange={handleFormChange}
          style={{
            width: "100%",
            padding: "13px 14px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.12)",
            background: "#151525",
            color: "#fff",
            outline: "none",
            boxSizing: "border-box",
          }}
        >
          <option value="">Select account</option>
{accounts.map((account) => (
  <option
    key={account.id}
    value={account.id}
  >
    {account.name}
  </option>
))}
        </select>
      </div>

      {/* CATEGORY */}

      <div style={{ marginBottom: "16px" }}>
        <label
          style={{
            display: "block",
            marginBottom: "7px",
            fontSize: "13px",
            color: "rgba(255,255,255,0.70)",
          }}
        >
          Category
        </label>

        <select
          name="category_id"
          value={formData.category_id}
          onChange={handleFormChange}
          style={{
            width: "100%",
            padding: "13px 14px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.12)",
            background: "#151525",
            color: "#fff",
            outline: "none",
            boxSizing: "border-box",
          }}
        >
          <option value="">Select category</option>
          {!categories.some((category) => String(category.name || "").trim().toLowerCase() === "loan disbursement") && (
            <option value="__loan_disbursement__">Loan Disbursement</option>
          )}

{categories.map((category) => (
  <option
    key={category.id}
    value={category.id}
  >
    {category.name}
  </option>
))}
        </select>
      </div>

      {/* AMOUNT + DATE */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "14px",
          marginBottom: "16px",
        }}
      >
        <div>
          <label
            style={{
              display: "block",
              marginBottom: "7px",
              fontSize: "13px",
              color: "rgba(255,255,255,0.70)",
            }}
          >
            Amount
          </label>

          <input
            type="number"
            name="amount"
            value={formData.amount}
            onChange={handleFormChange}
            placeholder="0.00"
            min="0"
            step="0.01"
            style={{
              width: "100%",
              padding: "13px 14px",
              borderRadius: "12px",
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.06)",
              color: "#fff",
              outline: "none",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div>
          <label
            style={{
              display: "block",
              marginBottom: "7px",
              fontSize: "13px",
              color: "rgba(255,255,255,0.70)",
            }}
          >
            Date
          </label>

          <input
            type="date"
            name="transaction_date"
            value={formData.transaction_date}
            onChange={handleFormChange}
            style={{
              width: "100%",
              padding: "13px 14px",
              borderRadius: "12px",
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.06)",
              color: "#fff",
              outline: "none",
              boxSizing: "border-box",
            }}
          />
        </div>
      </div>


      {/* LOAN DETAILS: shown only for Income → Loan Disbursement */}
      {formData.transaction_type === "income" && isLoanDisbursement && (
        <div style={{ margin: "8px 0 20px", padding: "18px", borderRadius: "14px", border: "1px solid rgba(168,85,247,0.35)", background: "rgba(168,85,247,0.08)" }}>
          <h4 style={{ margin: "0 0 14px", color: "#e9d5ff" }}>Loan Details</h4>
          <p style={{ margin: "0 0 14px", color: "rgba(255,255,255,0.65)", fontSize: "12px" }}>Amount is the money received into your account. Principal is the total amount you owe the lender.</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>Loan Name *<input required value={formData.loan_name} name="loan_name" onChange={handleFormChange} placeholder="e.g. HDFC Personal Loan" style={loanInputStyle} /></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>Lender Name *<input required value={formData.lender_name} name="lender_name" onChange={handleFormChange} placeholder="e.g. HDFC Bank" style={loanInputStyle} /></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>Loan Type *<select required name="loan_type" value={formData.loan_type} onChange={handleFormChange} style={loanInputStyle}>{["Personal Loan","Home Loan","Car Loan","Education Loan","Business Loan","Gold Loan","Loan Against Property","Other"].map((x) => <option key={x} value={x}>{x}</option>)}</select></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>Gross Principal (₹) *<input required type="number" min="0.01" step="0.01" name="principal_amount" value={formData.principal_amount} onChange={handleFormChange} placeholder="500000" style={loanInputStyle} /></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>Interest Rate (% p.a.)<input type="number" min="0" max="100" step="0.01" name="interest_rate" value={formData.interest_rate} onChange={handleFormChange} placeholder="12" style={loanInputStyle} /></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>Tenure (months)<input type="number" min="1" max="600" name="tenure_months" value={formData.tenure_months} onChange={handleFormChange} placeholder="36" style={loanInputStyle} /></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>EMI Amount (₹)<input type="number" min="0.01" step="0.01" name="emi_amount" value={formData.emi_amount} onChange={handleFormChange} placeholder="Optional" style={loanInputStyle} /></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>First EMI Date<input type="date" name="first_payment_date" value={formData.first_payment_date} onChange={handleFormChange} style={loanInputStyle} /></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>Processing Fee (₹)<input type="number" min="0" step="0.01" name="processing_fee" value={formData.processing_fee} onChange={handleFormChange} style={loanInputStyle} /></label>
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)", gridColumn: "1 / -1" }}>Loan Notes<textarea name="loan_notes" value={formData.loan_notes} onChange={handleFormChange} rows="2" placeholder="Optional loan terms or notes" style={{ ...loanInputStyle, resize: "vertical" }} /></label>
          </div>
        </div>
      )}

      {/* DESCRIPTION */}

      <div style={{ marginBottom: "16px" }}>
        <label
          style={{
            display: "block",
            marginBottom: "7px",
            fontSize: "13px",
            color: "rgba(255,255,255,0.70)",
          }}
        >
          Description
        </label>

        <input
          type="text"
          name="description"
          value={formData.description}
          onChange={handleFormChange}
          placeholder="e.g. Grocery shopping"
          style={{
            width: "100%",
            padding: "13px 14px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(255,255,255,0.06)",
            color: "#fff",
            outline: "none",
            boxSizing: "border-box",
          }}
        />
      </div>

      {/* REFERENCE */}

      <div style={{ marginBottom: "24px" }}>
        <label
          style={{
            display: "block",
            marginBottom: "7px",
            fontSize: "13px",
            color: "rgba(255,255,255,0.70)",
          }}
        >
          Reference
        </label>

        <input
          type="text"
          name="reference"
          value={formData.reference}
          onChange={handleFormChange}
          placeholder="Optional reference"
          style={{
            width: "100%",
            padding: "13px 14px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(255,255,255,0.06)",
            color: "#fff",
            outline: "none",
            boxSizing: "border-box",
          }}
        />
      </div>

      {formMessage && (
  <div
    style={{
      marginBottom: "16px",
      padding: "12px 14px",
      borderRadius: "12px",
      background: "rgba(239,68,68,0.12)",
      border: "1px solid rgba(239,68,68,0.25)",
      color: "#fca5a5",
      fontSize: "13px",
    }}
  >
    {formMessage}
  </div>
)}
      {/* ACTIONS */}

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: "12px",
        }}
      >
        <button
          type="button"
          className="secondary-button"
          onClick={closeTransactionForm}
        >
          Cancel
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={handleTransactionSubmit}
        >
          <Plus size={17} />
          Save Transaction
        </button>
      </div>
    </div>
  </div>
);
  
  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (

    <div className="dashboard">

      {/* ====================================================
          HEADER
      ==================================================== */}

      <section className="welcome-section">

        <div>

          <p className="welcome-label">
            MONEY
          </p>

          <h2>
            Your <span>transactions.</span>
          </h2>

          <p className="welcome-description">
            Track your income, expenses and
            financial activity in one place.
          </p>

        </div>

      <button
  className="primary-button"
  onClick={openTransactionForm}
>
  <Plus size={18} />
  Add Transaction
</button>

      </section>


      {/* ====================================================
          SUMMARY
      ==================================================== */}

      <section className="metrics-grid">

        <MetricCard
          title="Transactions"
          value={
            loading
              ? "Loading..."
              : String(transactions.length)
          }
          change="Total"
          positive
          icon={Receipt}
        />

        <MetricCard
          title="Expenses"
          value={
            loading
              ? "Loading..."
              : formatCurrency(
                  transactions
                    .filter(
                      (transaction) =>
                        !isIncome(transaction)
                    )
                    .reduce(
                      (total, transaction) =>
                        total +
                        Number(
                          transaction.amount || 0
                        ),
                      0
                    )
                )
          }
          change="Recorded"
          positive={false}
          icon={CreditCard}
        />

      </section>


      {/* ====================================================
          ERROR
      ==================================================== */}

      {error && (

        <div className="glass-card">

          <strong>
            {error}
          </strong>

        </div>

      )}


      {/* ====================================================
          TRANSACTION LIST
      ==================================================== */}

      <section className="glass-card">

        <div className="card-header">

          <div>

            <p className="card-label">
              TRANSACTION HISTORY
            </p>

            <h3>
              Recent Transactions
            </h3>

          </div>

          <span className="score">
            {transactions.length}
          </span>

        </div>


        {/* --------------------------------------------------
            LOADING
        -------------------------------------------------- */}

        {loading && (

          <div className="empty-chart">

            <strong>
              Loading transactions...
            </strong>

          </div>

        )}


        {/* --------------------------------------------------
            EMPTY
        -------------------------------------------------- */}

        {!loading &&
          transactions.length === 0 && (

            <div className="empty-chart">

              <div className="chart-icon">
                <Receipt size={28} />
              </div>

              <strong>
                No transactions found
              </strong>

              <span>
                Add your first transaction
                to start tracking your finances.
              </span>

              <button className="secondary-button">
                Add Transaction
              </button>

            </div>

          )}


        {/* --------------------------------------------------
            TRANSACTION CARDS
        -------------------------------------------------- */}

        {!loading &&
          transactions.length > 0 && (

            <div
              style={{
                display: "grid",
                gap: "12px",
                marginTop: "20px",
              }}
            >

              {transactions.map(
                (transaction) => {

                  const income =
                    isIncome(transaction);

                  return (

                    <div
                      key={transaction.id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent:
                          "space-between",
                        gap: "16px",
                        padding: "18px",
                        borderRadius: "18px",
                        background:
                          "linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03))",
                        border:
                          "1px solid rgba(255,255,255,0.08)",
                      }}
                    >

                      {/* LEFT SIDE */}

                      <div
                        style={{
                          display: "flex",
                          alignItems:
                            "center",
                          gap: "14px",
                          minWidth: 0,
                        }}
                      >

                        <div
                          style={{
                            width: "46px",
                            height: "46px",
                            minWidth: "46px",
                            borderRadius: "14px",
                            display: "flex",
                            alignItems:
                              "center",
                            justifyContent:
                              "center",
                            background:
                              income
                                ? "rgba(34,197,94,0.16)"
                                : "rgba(239,68,68,0.16)",
                          }}
                        >

                          <Receipt
                            size={20}
                          />

                        </div>


                        <div
                          style={{
                            minWidth: 0,
                          }}
                        >

                          <div
                            style={{
                              fontSize:
                                "15px",
                              fontWeight:
                                700,
                              color:
                                "#ffffff",
                              marginBottom:
                                "5px",
                              overflow:
                                "hidden",
                              textOverflow:
                                "ellipsis",
                              whiteSpace:
                                "nowrap",
                            }}
                          >
                            {transaction.description ||
                              "Transaction"}
                          </div>


                          <div
                            style={{
                              fontSize:
                                "12px",
                              color:
                                "rgba(255,255,255,0.55)",
                            }}
                          >

                            {transaction.transaction_date ||
                              "No date"}

                            {" • "}

                            {transaction.transaction_type}

                          </div>


                          {transaction.reference && (

                            <div
                              style={{
                                fontSize:
                                  "11px",
                                color:
                                  "rgba(255,255,255,0.35)",
                                marginTop:
                                  "4px",
                              }}
                            >
                              {transaction.reference}
                            </div>

                          )}

                        </div>

                      </div>


                      {/* RIGHT SIDE */}

                      <div
                        style={{
                          textAlign:
                            "right",
                          minWidth:
                            "105px",
                        }}
                      >

                        <div
                          style={{
                            fontSize:
                              "16px",
                            fontWeight:
                              800,
                            color:
                              income
                                ? "#4ade80"
                                : "#fb7185",
                            whiteSpace:
                              "nowrap",
                          }}
                        >

                          {income
                            ? "+"
                            : "-"}
                          {formatCurrency(
                            transaction.amount
                          )}

                        </div>
                        <button
                          type="button"
                          onClick={() =>
                            openEditTransactionForm(transaction)
                          }
                          style={{
                            marginTop: "8px",
                            padding: "7px 12px",
                            borderRadius: "10px",
                            border:
                              "1px solid rgba(255,255,255,0.12)",
                            background:
                              "rgba(255,255,255,0.06)",
                            color: "#ffffff",
                            cursor: "pointer",
                            fontSize: "12px",
                            fontWeight: 700,
                          }}
                        >
                          Edit
                        </button>
                                           <button
                          type="button"
                          onClick={() => {
                            if (
                              window.confirm(
                                "Are you sure you want to delete this transaction?"
                              )
                            ) {
                              handleDeleteTransaction(
                                transaction.id
                              );
                            }
                          }}
                          disabled={Boolean(deletingTransaction)}
                          style={{
                            marginTop: "8px",
                            marginLeft: "6px",
                            padding: "7px 12px",
                            borderRadius: "10px",
                            border:
                              "1px solid rgba(251,113,133,0.25)",
                            background:
                              "rgba(251,113,133,0.08)",
                            color: "#fb7185",
                            cursor: deletingTransaction
                              ? "not-allowed"
                              : "pointer",
                            fontSize: "12px",
                            fontWeight: 700,
                            opacity: deletingTransaction
                              ? 0.6
                              : 1,
                          }}
                        >
                          Delete
                        </button>     
                      </div>

                    </div>

                  );

                }
              )}

            </div>

          )}

            </section>

      {/* ====================================================
          TRANSACTION FORM MODAL
      ==================================================== */}

      {transactionFormModal}

    </div>

  );

}

// ============================================================
// CATEGORIES
// ============================================================

function Category() {

  // ----------------------------------------------------------
  // STATE
  // ----------------------------------------------------------

  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [categoryToDelete, setCategoryToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    category_type: "expense",
    description: "",
  });

  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";

  const USER_ID = 1;

  // ----------------------------------------------------------
  // LOAD CATEGORIES
  // ----------------------------------------------------------

  async function loadCategories() {

    try {

      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/categories/?user_id=${USER_ID}`
      );

      if (!response.ok) {
        throw new Error(
          `Categories API error: ${response.status}`
        );
      }

      const data = await response.json();

      setCategories(
        Array.isArray(data) ? data : []
      );

    } catch (err) {

      console.error(
        "Categories API error:",
        err
      );

      setError(
        err?.message ||
        "Unable to load categories."
      );

    } finally {

      setLoading(false);

    }
  }

  // ----------------------------------------------------------
  // LOAD WHEN PAGE OPENS
  // ----------------------------------------------------------

  useEffect(() => {

    loadCategories();

  }, []);

  // ----------------------------------------------------------
  // OPEN ADD FORM
  // ----------------------------------------------------------

  function openAddCategoryForm() {

    setEditingCategory(null);

    setFormData({
      name: "",
      category_type: "expense",
      description: "",
    });

    setMessage("");
    setError("");
    setShowForm(true);

  }

  // ----------------------------------------------------------
  // OPEN EDIT FORM
  // ----------------------------------------------------------

  function openEditCategoryForm(category) {

    setEditingCategory(category);

    setFormData({
      name: category.name || "",
      category_type:
        category.category_type || "expense",
      description:
        category.description || "",
    });

    setMessage("");
    setError("");
    setShowForm(true);

  }

  // ----------------------------------------------------------
  // FORM CHANGE
  // ----------------------------------------------------------

  function updateForm(field, value) {

    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));

  }

  // ----------------------------------------------------------
  // SAVE CATEGORY
  // CREATE / UPDATE
  // ----------------------------------------------------------

  async function saveCategory(event) {

    event.preventDefault();

    setMessage("");
    setError("");

    const name =
      formData.name.trim();

    if (!name) {

      setError(
        "Category name is required."
      );

      return;
    }

    if (
      !["income", "expense", "other"]
        .includes(formData.category_type)
    ) {

      setError(
        "Please select a valid category type."
      );

      return;
    }

    try {

      setSaving(true);

      const isEditing =
        Boolean(editingCategory);

      const response = await fetch(

        isEditing
          ? `${API_BASE_URL}/api/categories/${editingCategory.id}`
          : `${API_BASE_URL}/api/categories/`,

        {
          method:
            isEditing
              ? "PUT"
              : "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify(

            isEditing

              ? {
                  name: name,
                  category_type:
                    formData.category_type,
                  description:
                    formData.description.trim() ||
                    null,
                }

              : {
                  user_id: USER_ID,
                  name: name,
                  category_type:
                    formData.category_type,
                  description:
                    formData.description.trim() ||
                    null,
                }

          ),
        }

      );

      const data =
        await response
          .json()
          .catch(() => null);

      if (!response.ok) {

        throw new Error(
          data?.detail ||
          data?.message ||
          "Unable to save category."
        );

      }

      setShowForm(false);
      setEditingCategory(null);

      setFormData({
        name: "",
        category_type: "expense",
        description: "",
      });

      setMessage(
        isEditing
          ? "Category updated successfully."
          : "Category created successfully."
      );

      await loadCategories();

    } catch (err) {

      console.error(
        "Save category error:",
        err
      );

      setError(
        err?.message ||
        "Unable to save category."
      );

    } finally {

      setSaving(false);

    }
  }

  // ----------------------------------------------------------
  // DELETE CATEGORY
  // ----------------------------------------------------------

  async function deleteCategory() {

    if (!categoryToDelete) {
      return;
    }

    try {

      setDeleting(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/categories/${categoryToDelete.id}`,
        {
          method: "DELETE",
        }
      );

      const data =
        await response
          .json()
          .catch(() => null);

      if (!response.ok) {

        throw new Error(
          data?.detail ||
          data?.message ||
          "Unable to delete category."
        );

      }

      setCategoryToDelete(null);

      setMessage(
        "Category deleted successfully."
      );

      await loadCategories();

    } catch (err) {

      console.error(
        "Delete category error:",
        err
      );

      setError(
        err?.message ||
        "Unable to delete category."
      );

    } finally {

      setDeleting(false);

    }
  }

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (

    <div className="dashboard">

      {/* ====================================================
          HEADER
      ==================================================== */}

      <section className="welcome-section">

        <div>

          <p className="welcome-label">
            MONEY
          </p>

          <h2>
            Your <span>categories.</span>
          </h2>

          <p className="welcome-description">
            Organize your income and expenses
            for better financial tracking.
          </p>

        </div>

        <button
          className="primary-button"
          onClick={openAddCategoryForm}
        >
          <Plus size={18} />
          Add Category
        </button>

      </section>


      {/* ====================================================
          MESSAGE
      ==================================================== */}

      {message && (

        <div className="glass-card">

          <strong>
            {message}
          </strong>

        </div>

      )}


      {/* ====================================================
          ERROR
      ==================================================== */}

      {error && (

        <div className="glass-card">

          <strong>
            {error}
          </strong>

        </div>

      )}


      {/* ====================================================
          SUMMARY
      ==================================================== */}

      <section className="metrics-grid">

        <MetricCard
          title="Total Categories"
          value={
            loading
              ? "Loading..."
              : String(categories.length)
          }
          change="Categories"
          positive
          icon={PieChart}
        />

        <MetricCard
          title="Income Categories"
          value={
            loading
              ? "Loading..."
              : String(
                  categories.filter(
                    (category) =>
                      category.category_type ===
                      "income"
                  ).length
                )
          }
          change="Income"
          positive
          icon={TrendingUp}
        />

        <MetricCard
          title="Expense Categories"
          value={
            loading
              ? "Loading..."
              : String(
                  categories.filter(
                    (category) =>
                      category.category_type ===
                      "expense"
                  ).length
                )
          }
          change="Expenses"
          positive={false}
          icon={CreditCard}
        />

      </section>


      {/* ====================================================
          CATEGORY LIST
      ==================================================== */}

      <section className="glass-card">

        <div className="card-header">

          <div>

            <p className="card-label">
              CATEGORY MANAGEMENT
            </p>

            <h3>
              Your Categories
            </h3>

          </div>

          <span className="score">
            {categories.length}
          </span>

        </div>


        {loading && (

          <div className="empty-chart">

            <strong>
              Loading categories...
            </strong>

          </div>

        )}


        {!loading &&
          categories.length === 0 && (

          <div className="empty-chart">

            <div className="chart-icon">
              <PieChart size={28} />
            </div>

            <strong>
              No categories found.
            </strong>

            <span>
              Create your first category
              to organize your transactions.
            </span>

          </div>

        )}


        {!loading &&
          categories.length > 0 && (

          <div
            style={{
              display: "grid",
              gap: "14px",
              marginTop: "20px",
            }}
          >

            {categories.map((category) => (

              <div
                key={category.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent:
                    "space-between",
                  gap: "16px",
                  padding: "18px",
                  borderRadius: "18px",
                  background:
                    "linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03))",
                  border:
                    "1px solid rgba(255,255,255,0.08)",
                }}
              >

                <div>

                  <div
                    style={{
                      fontSize: "15px",
                      fontWeight: 700,
                      color: "#ffffff",
                    }}
                  >
                    {category.name}
                  </div>

                  <div
                    style={{
                      marginTop: "5px",
                      fontSize: "12px",
                      color:
                        "rgba(255,255,255,0.55)",
                      textTransform:
                        "capitalize",
                    }}
                  >
                    {category.category_type}

                    {category.description
                      ? ` • ${category.description}`
                      : ""}
                  </div>

                </div>


                <div
                  style={{
                    display: "flex",
                    gap: "8px",
                    flexShrink: 0,
                  }}
                >

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      openEditCategoryForm(
                        category
                      )
                    }
                    style={{
                      padding:
                        "7px 12px",
                      fontSize: "11px",
                    }}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      setCategoryToDelete(
                        category
                      )
                    }
                    style={{
                      padding:
                        "7px 12px",
                      fontSize: "11px",
                      color: "#fb7185",
                      borderColor:
                        "rgba(251,113,133,0.25)",
                    }}
                  >
                    Delete
                  </button>

                </div>

              </div>

            ))}

          </div>

        )}

      </section>


      {/* ====================================================
          CATEGORY FORM
      ==================================================== */}

      {showForm && (

        <div className="glass-card">

          <div className="card-header">

            <div>

              <p className="card-label">
                {editingCategory
                  ? "EDIT CATEGORY"
                  : "NEW CATEGORY"}
              </p>

              <h3>
                {editingCategory
                  ? "Update Category"
                  : "Create Category"}
              </h3>

            </div>

          </div>


          <form onSubmit={saveCategory}>

            {/* NAME */}

            <div
              style={{
                marginBottom: "16px",
              }}
            >

              <label>
                Category Name
              </label>

              <input
                type="text"
                placeholder="e.g. Food & Dining"
                value={formData.name}
                onChange={(event) =>
                  updateForm(
                    "name",
                    event.target.value
                  )
                }
                style={{
                  width: "100%",
                  marginTop: "8px",
                  padding: "12px",
                  borderRadius: "12px",
                }}
              />

            </div>


            {/* TYPE */}

            <div
              style={{
                marginBottom: "16px",
              }}
            >

              <label>
                Category Type
              </label>

              <select
                value={
                  formData.category_type
                }
                onChange={(event) =>
                  updateForm(
                    "category_type",
                    event.target.value
                  )
                }
                style={{
                  width: "100%",
                  marginTop: "8px",
                  padding: "12px",
                  borderRadius: "12px",
                }}
              >

                <option value="expense">
                  Expense
                </option>

                <option value="income">
                  Income
                </option>

                <option value="other">
                  Other
                </option>

              </select>

            </div>


            {/* DESCRIPTION */}

            <div
              style={{
                marginBottom: "16px",
              }}
            >

              <label>
                Description
              </label>

              <textarea
                placeholder="Optional description"
                value={
                  formData.description
                }
                onChange={(event) =>
                  updateForm(
                    "description",
                    event.target.value
                  )
                }
                rows="3"
                style={{
                  width: "100%",
                  marginTop: "8px",
                  padding: "12px",
                  borderRadius: "12px",
                  resize: "vertical",
                  boxSizing: "border-box",
                }}
              />

            </div>


            {/* ACTIONS */}

            <div
              style={{
                display: "flex",
                gap: "12px",
              }}
            >

              <button
                type="submit"
                className="primary-button"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : editingCategory
                  ? "Update Category"
                  : "Save Category"}
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setShowForm(false)
                }
                disabled={saving}
              >
                Cancel
              </button>

            </div>

          </form>

        </div>

      )}


      {/* ====================================================
          DELETE CONFIRMATION
      ==================================================== */}

      {categoryToDelete && (

        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 10000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            background:
              "rgba(0,0,0,0.65)",
            backdropFilter:
              "blur(10px)",
          }}
        >

          <div
            className="glass-card"
            style={{
              width: "100%",
              maxWidth: "420px",
              padding: "24px",
            }}
          >

            <p className="card-label">
              DELETE CATEGORY
            </p>

            <h3>
              Delete this category?
            </h3>

            <p
              style={{
                color:
                  "rgba(255,255,255,0.60)",
                fontSize: "13px",
                lineHeight: 1.6,
                marginTop: "10px",
              }}
            >
              This will permanently remove{" "}
              <strong>
                {categoryToDelete.name}
              </strong>
              .
            </p>

            <div
              style={{
                display: "flex",
                justifyContent:
                  "flex-end",
                gap: "10px",
                marginTop: "22px",
              }}
            >

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setCategoryToDelete(null)
                }
                disabled={deleting}
              >
                Cancel
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={deleteCategory}
                disabled={deleting}
                style={{
                  color: "#fb7185",
                  borderColor:
                    "rgba(251,113,133,0.30)",
                }}
              >
                {deleting
                  ? "Deleting..."
                  : "Delete"}
              </button>

            </div>

          </div>

        </div>

      )}

    </div>

  );

}


// ============================================================
// BILLS & SUBSCRIPTIONS
// ============================================================

function Bills() {

  // ----------------------------------------------------------
  // API
  // ----------------------------------------------------------

  const BILLS_API =
    "https://ai-finance-trading-os-api.onrender.com/api/bills";

  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";


  // ----------------------------------------------------------
  // STATE
  // ----------------------------------------------------------

  const [bills, setBills] = useState([]);
  const [categories, setCategories] = useState([]);
  const [accounts, setAccounts] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingBill, setEditingBill] = useState(null);
  const [billToDelete, setBillToDelete] = useState(null);


  // ----------------------------------------------------------
  // FORM
  // ----------------------------------------------------------

  const [formData, setFormData] = useState({
    name: "",
    category_id: "",
    account_id: "",
    amount: "",
    frequency: "monthly",
    next_due_date: new Date()
      .toISOString()
      .slice(0, 10),
    status: "active",
    notes: "",
  });


  // ----------------------------------------------------------
  // FORMAT CURRENCY
  // ----------------------------------------------------------

  const formatBillCurrency = (value) => {

    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value || 0));

  };


  // ----------------------------------------------------------
  // LOAD BILLS
  // ----------------------------------------------------------

  const loadBills = async () => {

    try {

      setLoading(true);
      setError("");

      const response = await fetch(
        `${BILLS_API}/`
      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(
          data?.detail ||
          "Unable to load bills."
        );

      }

      setBills(
        Array.isArray(data)
          ? data
          : []
      );

    } catch (err) {

      console.error(
        "Load bills error:",
        err
      );

      setError(
        err?.message ||
        "Unable to load bills."
      );

    } finally {

      setLoading(false);

    }

  };


  // ----------------------------------------------------------
  // LOAD CATEGORIES
  // ----------------------------------------------------------

  const loadCategories = async () => {

    try {

      const response = await fetch(
        `${API_BASE_URL}/api/categories/?user_id=1`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
          "Unable to load categories."
        );
      }

      setCategories(
        Array.isArray(data)
          ? data
          : []
      );

    } catch (err) {

      console.error(
        "Load bill categories error:",
        err
      );

    }

  };


  // ----------------------------------------------------------
  // LOAD ACCOUNTS
  // ----------------------------------------------------------

  const loadAccounts = async () => {

    try {

      const response = await fetch(
        `${API_BASE_URL}/api/accounts/?user_id=1`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
          "Unable to load accounts."
        );
      }

      setAccounts(
        Array.isArray(data)
          ? data
          : []
      );

    } catch (err) {

      console.error(
        "Load bill accounts error:",
        err
      );

    }

  };


  // ----------------------------------------------------------
  // INITIAL LOAD
  // ----------------------------------------------------------

  useEffect(() => {

    loadBills();
    loadCategories();
    loadAccounts();

  }, []);


  // ----------------------------------------------------------
  // RESET FORM
  // ----------------------------------------------------------

  const resetForm = () => {

    setFormData({
      name: "",
      category_id: "",
      account_id: "",
      amount: "",
      frequency: "monthly",
      next_due_date: new Date()
        .toISOString()
        .slice(0, 10),
      status: "active",
      notes: "",
    });

    setEditingBill(null);

  };


  // ----------------------------------------------------------
  // OPEN ADD FORM
  // ----------------------------------------------------------

  const handleAddBill = () => {

    resetForm();

    setError("");
    setMessage("");

    setShowForm(true);

  };


  // ----------------------------------------------------------
  // OPEN EDIT FORM
  // ----------------------------------------------------------

  const handleEditBill = (bill) => {

    setEditingBill(bill);

    setFormData({
      name: bill.name || "",

      category_id:
        bill.category_id !== null &&
        bill.category_id !== undefined
          ? String(bill.category_id)
          : "",

      account_id:
        bill.account_id !== null &&
        bill.account_id !== undefined
          ? String(bill.account_id)
          : "",

      amount:
        bill.amount !== null &&
        bill.amount !== undefined
          ? String(bill.amount)
          : "",

      frequency:
        bill.frequency || "monthly",

      next_due_date:
        bill.next_due_date ||
        new Date()
          .toISOString()
          .slice(0, 10),

      status:
        bill.status || "active",

      notes:
        bill.notes || "",
    });

    setError("");
    setMessage("");

    setShowForm(true);

  };


  // ----------------------------------------------------------
  // FORM CHANGE
  // ----------------------------------------------------------

  const handleChange = (field, value) => {

    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));

  };


  // ----------------------------------------------------------
  // SAVE BILL
  // CREATE / UPDATE
  // ----------------------------------------------------------

  const handleSaveBill = async () => {

    try {

      setError("");
      setMessage("");

      if (!formData.name.trim()) {

        setError(
          "Bill name is required."
        );

        return;

      }

      if (
        formData.amount === "" ||
        Number(formData.amount) <= 0
      ) {

        setError(
          "Bill amount must be greater than 0."
        );

        return;

      }

      if (!formData.next_due_date) {

        setError(
          "Next due date is required."
        );

        return;

      }

      setSaving(true);

      const isEditing =
        Boolean(editingBill);

      const payload = {

        name:
          formData.name.trim(),

        category_id:
          formData.category_id === ""
            ? null
            : Number(formData.category_id),

        account_id:
          formData.account_id === ""
            ? null
            : Number(formData.account_id),

        amount:
          Number(formData.amount),

        frequency:
          formData.frequency,

        next_due_date:
          formData.next_due_date,

        status:
          formData.status,

        notes:
          formData.notes.trim() || null,

      };


      const response = await fetch(

        isEditing
          ? `${BILLS_API}/${editingBill.id}`
          : `${BILLS_API}/`,

        {
          method:
            isEditing
              ? "PUT"
              : "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify(payload),

        }

      );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data?.detail ||
          "Unable to save bill."
        );

      }


      resetForm();

      setShowForm(false);

      setMessage(
        isEditing
          ? "Bill updated successfully."
          : "Bill created successfully."
      );


      await loadBills();

    } catch (err) {

      console.error(
        "Save bill error:",
        err
      );

      setError(
        err?.message ||
        "Unable to save bill."
      );

    } finally {

      setSaving(false);

    }

  };


  // ----------------------------------------------------------
  // DELETE BILL
  // ----------------------------------------------------------

  const handleDeleteBill = async () => {

    if (!billToDelete) {
      return;
    }

    try {

      setDeleting(true);
      setError("");
      setMessage("");

      const response = await fetch(
        `${BILLS_API}/${billToDelete.id}`,
        {
          method: "DELETE",
        }
      );


      const data =
        await response.json()
          .catch(() => null);


      if (!response.ok) {

        throw new Error(
          data?.detail ||
          "Unable to delete bill."
        );

      }


      setBillToDelete(null);

      setMessage(
        "Bill deleted successfully."
      );

      await loadBills();

    } catch (err) {

      console.error(
        "Delete bill error:",
        err
      );

      setError(
        err?.message ||
        "Unable to delete bill."
      );

    } finally {

      setDeleting(false);

    }

  };


  // ----------------------------------------------------------
  // SUMMARY VALUES
  // ----------------------------------------------------------

  const activeBills =
    bills.filter(
      (bill) =>
        bill.status === "active"
    );

  const pausedBills =
    bills.filter(
      (bill) =>
        bill.status === "paused"
    );

  const totalMonthlyAmount =
    activeBills.reduce(
      (total, bill) => {

        const amount =
          Number(
            bill.amount || 0
          );

        if (
          bill.frequency ===
          "monthly"
        ) {

          return total + amount;

        }

        if (
          bill.frequency ===
          "weekly"
        ) {

          return total +
            amount * 4.33;

        }

        if (
          bill.frequency ===
          "daily"
        ) {

          return total +
            amount * 30;

        }

        if (
          bill.frequency ===
          "quarterly"
        ) {

          return total +
            amount / 3;

        }

        if (
          bill.frequency ===
          "half_yearly"
        ) {

          return total +
            amount / 6;

        }

        if (
          bill.frequency ===
          "yearly"
        ) {

          return total +
            amount / 12;

        }

        return total;

      },
      0
    );


  // ----------------------------------------------------------
  // CATEGORY NAME
  // ----------------------------------------------------------

  const getCategoryName =
    (categoryId) => {

      const category =
        categories.find(
          (item) =>
            Number(item.id) ===
            Number(categoryId)
        );

      return (
        category?.name ||
        "Uncategorized"
      );

    };


  // ----------------------------------------------------------
  // ACCOUNT NAME
  // ----------------------------------------------------------

  const getAccountName =
    (accountId) => {

      const account =
        accounts.find(
          (item) =>
            Number(item.id) ===
            Number(accountId)
        );

      return (
        account?.name ||
        "No account"
      );

    };


  // ----------------------------------------------------------
  // STATUS DISPLAY
  // ----------------------------------------------------------

  const getStatusStyle =
    (status) => {

      if (status === "active") {

        return {
          color: "#4ade80",
          background:
            "rgba(74,222,128,0.10)",
          borderColor:
            "rgba(74,222,128,0.25)",
        };

      }

      if (status === "paused") {

        return {
          color: "#fbbf24",
          background:
            "rgba(251,191,36,0.10)",
          borderColor:
            "rgba(251,191,36,0.25)",
        };

      }

      return {
        color: "#fb7185",
        background:
          "rgba(251,113,133,0.10)",
        borderColor:
          "rgba(251,113,133,0.25)",
      };

    };


  // ----------------------------------------------------------
  // FREQUENCY DISPLAY
  // ----------------------------------------------------------

  const getFrequencyLabel =
    (frequency) => {

      const labels = {

        daily: "Daily",

        weekly: "Weekly",

        monthly: "Monthly",

        quarterly: "Quarterly",

        half_yearly:
          "Half-Yearly",

        yearly: "Yearly",

        custom: "Custom",

      };

      return (
        labels[frequency] ||
        frequency
      );

    };


  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (

    <div>

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <div
        style={{
          display: "flex",
          justifyContent:
            "space-between",
          alignItems: "center",
          gap: "20px",
          flexWrap: "wrap",
        }}
      >

        <div>

          <div
            className="eyebrow"
          >
            MONEY
          </div>

          <h1
            style={{
              margin: "6px 0 8px",
            }}
          >
            Your bills.
          </h1>

          <p
            style={{
              color:
                "rgba(255,255,255,0.55)",
              margin: 0,
            }}
          >
            Manage recurring bills,
            subscriptions and upcoming
            payments.
          </p>

        </div>


        <button
          type="button"
          className="primary-button"
          onClick={handleAddBill}
        >
          + Add Bill
        </button>

      </div>


      {/* ================================================== */}
      {/* SUMMARY */}
      {/* ================================================== */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(3, minmax(0, 1fr))",
          gap: "14px",
          marginTop: "28px",
        }}
      >

        <div
          className="glass-card"
          style={{
            padding: "20px",
          }}
        >

          <div
            className="card-label"
          >
            TOTAL BILLS
          </div>

          <div
            style={{
              fontSize: "24px",
              fontWeight: 800,
              marginTop: "8px",
            }}
          >
            {bills.length}
          </div>

        </div>


        <div
          className="glass-card"
          style={{
            padding: "20px",
          }}
        >

          <div
            className="card-label"
          >
            ACTIVE BILLS
          </div>

          <div
            style={{
              fontSize: "24px",
              fontWeight: 800,
              marginTop: "8px",
              color: "#4ade80",
            }}
          >
            {activeBills.length}
          </div>

        </div>


        <div
          className="glass-card"
          style={{
            padding: "20px",
          }}
        >

          <div
            className="card-label"
          >
            MONTHLY COMMITMENT
          </div>

          <div
            style={{
              fontSize: "24px",
              fontWeight: 800,
              marginTop: "8px",
            }}
          >
            {formatBillCurrency(
              totalMonthlyAmount
            )}
          </div>

        </div>

      </div>


      {/* ================================================== */}
      {/* MESSAGES */}
      {/* ================================================== */}

      {error && (

        <div
          className="glass-card"
          style={{
            marginTop: "18px",
            padding: "14px 16px",
            color: "#fb7185",
            border:
              "1px solid rgba(251,113,133,0.25)",
          }}
        >
          {error}
        </div>

      )}


      {message && (

        <div
          className="glass-card"
          style={{
            marginTop: "18px",
            padding: "14px 16px",
            color: "#4ade80",
            border:
              "1px solid rgba(74,222,128,0.25)",
          }}
        >
          {message}
        </div>

      )}


      {/* ================================================== */}
      {/* BILL LIST */}
      {/* ================================================== */}

      <div
        style={{
          marginTop: "22px",
        }}
      >

        <div
          className="card-label"
          style={{
            marginBottom: "10px",
          }}
        >
          YOUR BILLS
        </div>


        {loading ? (

          <div
            className="glass-card"
            style={{
              padding: "30px",
              textAlign: "center",
              color:
                "rgba(255,255,255,0.55)",
            }}
          >
            Loading bills...
          </div>

        ) : bills.length === 0 ? (

          <div
            className="glass-card"
            style={{
              padding: "35px",
              textAlign: "center",
            }}
          >

            <div
              style={{
                fontSize: "18px",
                fontWeight: 700,
              }}
            >
              No bills yet
            </div>

            <p
              style={{
                color:
                  "rgba(255,255,255,0.50)",
                margin:
                  "8px 0 20px",
              }}
            >
              Add your first recurring
              bill or subscription.
            </p>

            <button
              type="button"
              className="primary-button"
              onClick={handleAddBill}
            >
              + Add Bill
            </button>

          </div>

        ) : (

          <div
            style={{
              display: "grid",
              gap: "12px",
            }}
          >

            {bills.map((bill) => (

             <div
  key={bill.id}
  className="glass-card"
  style={{
    display: "grid",
    gridTemplateColumns:
      "minmax(0, 1fr) minmax(120px, 1fr) 90px",
    alignItems: "center",
    columnGap: "20px",
    padding: "20px",
    borderRadius: "18px",
    background:
      "linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03))",
    border:
      "1px solid rgba(255,255,255,0.08)",
    boxShadow:
      "0 12px 30px rgba(0,0,0,0.18)",
    minHeight: "90px",
  }}
> 

                {/* BILL INFORMATION */}

                <div
                  style={{
                    minWidth: 0,
                  }}
                >

                  <div
                    style={{
                      fontSize: "15px",
                      fontWeight: 800,
                    }}
                  >
                    {bill.name}
                  </div>

                  <div
                    style={{
                      color:
                        "rgba(255,255,255,0.50)",
                      fontSize: "12px",
                      marginTop: "5px",
                    }}
                  >
                    {getCategoryName(
                      bill.category_id
                    )}
                    {" • "}
                    {getAccountName(
                      bill.account_id
                    )}
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      marginTop: "8px",
                      flexWrap: "wrap",
                    }}
                  >

                    <span
                      style={{
                        fontSize: "11px",
                        padding:
                          "4px 8px",
                        borderRadius:
                          "999px",
                        border:
                          "1px solid rgba(255,255,255,0.10)",
                        color:
                          "rgba(255,255,255,0.65)",
                      }}
                    >
                      {getFrequencyLabel(
                        bill.frequency
                      )}
                    </span>

                    <span
                      style={{
                        fontSize: "11px",
                        padding:
                          "4px 8px",
                        borderRadius:
                          "999px",
                        border:
                          "1px solid",
                        ...getStatusStyle(
                          bill.status
                        ),
                      }}
                    >
                      {bill.status
                        ? bill.status
                            .charAt(0)
                            .toUpperCase() +
                          bill.status.slice(1)
                        : "Active"}
                    </span>

                  </div>

                </div>


                {/* AMOUNT / DUE */}

                <div
                  style={{
                    textAlign:
                      "center",
                  }}
                >

                  <div
                    style={{
                      fontSize: "10px",
                      color:
                        "rgba(255,255,255,0.40)",
                      textTransform:
                        "uppercase",
                      letterSpacing:
                        "0.08em",
                    }}
                  >
                    Amount
                  </div>

                  <div
                    style={{
                      fontSize: "17px",
                      fontWeight: 800,
                      marginTop: "4px",
                    }}
                  >
                    {formatBillCurrency(
                      bill.amount
                    )}
                  </div>

                  <div
                    style={{
                      fontSize: "11px",
                      color:
                        "rgba(255,255,255,0.45)",
                      marginTop: "4px",
                    }}
                  >
                    Due{" "}
                    {bill.next_due_date}
                  </div>

                </div>


                {/* ACTIONS */}

                <div
                  style={{
                    display: "flex",
                    flexDirection:
                      "column",
                    gap: "7px",
                    alignItems:
                      "stretch",
                  }}
                >

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      handleEditBill(
                        bill
                      )
                    }
                    style={{
                      width: "100%",
                      padding:
                        "7px 12px",
                      fontSize: "11px",
                    }}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      setBillToDelete(
                        bill
                      )
                    }
                    style={{
                      width: "100%",
                      padding:
                        "7px 12px",
                      fontSize: "11px",
                      color: "#fb7185",
                      borderColor:
                        "rgba(251,113,133,0.25)",
                    }}
                  >
                    Delete
                  </button>

                </div>

              </div>

            ))}

          </div>

        )}

      </div>


      {/* ================================================== */}
      {/* ADD / EDIT BILL FORM */}
      {/* ================================================== */}

      {showForm && (

        <div
          className="glass-card"
          style={{
            marginTop: "22px",
            padding: "22px",
          }}
        >

          <div
            style={{
              display: "flex",
              justifyContent:
                "space-between",
              alignItems: "center",
              gap: "12px",
              marginBottom:
                "18px",
            }}
          >

            <div>

              <div
                className="card-label"
              >
                {editingBill
                  ? "EDIT BILL"
                  : "ADD BILL"}
              </div>

              <h3
                style={{
                  margin:
                    "5px 0 0",
                }}
              >
                {editingBill
                  ? "Update bill"
                  : "Create a new bill"}
              </h3>

            </div>

            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                resetForm();
                setShowForm(false);
              }}
            >
              Cancel
            </button>

          </div>


          <div
  style={{
    display: "grid",
    gridTemplateColumns:
      "repeat(2, minmax(0, 1fr))",
    gap: "16px",
  }}
>
  {/* BILL NAME */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "7px",
    }}
  >
    <label
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: "rgba(255,255,255,0.60)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      Bill Name
    </label>

    <input
      value={formData.name}
      onChange={(event) =>
        handleChange(
          "name",
          event.target.value
        )
      }
      placeholder="Electricity"
      style={{
        width: "100%",
        minHeight: "42px",
        padding: "10px 12px",
        border:
          "1px solid rgba(255,255,255,0.12)",
        borderRadius: "12px",
        background: "rgba(255,255,255,0.05)",
        color: "#ffffff",
        outline: "none",
        fontSize: "13px",
        boxSizing: "border-box",
      }}
    />
  </div>

  {/* AMOUNT */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "7px",
    }}
  >
    <label
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: "rgba(255,255,255,0.60)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      Amount
    </label>

    <input
      type="number"
      min="0"
      step="0.01"
      value={formData.amount}
      onChange={(event) =>
        handleChange(
          "amount",
          event.target.value
        )
      }
      placeholder="1000"
      style={{
        width: "100%",
        minHeight: "42px",
        padding: "10px 12px",
        border:
          "1px solid rgba(255,255,255,0.12)",
        borderRadius: "12px",
        background: "rgba(255,255,255,0.05)",
        color: "#ffffff",
        outline: "none",
        fontSize: "13px",
        boxSizing: "border-box",
      }}
    />
  </div>

  {/* CATEGORY */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "7px",
    }}
  >
    <label
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: "rgba(255,255,255,0.60)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      Category
    </label>

    <select
      value={formData.category_id}
      onChange={(event) =>
        handleChange(
          "category_id",
          event.target.value
        )
      }
      style={{
        width: "100%",
        minHeight: "42px",
        padding: "10px 12px",
        border:
          "1px solid rgba(255,255,255,0.12)",
        borderRadius: "12px",
        background: "#151525",
        color: "#ffffff",
        outline: "none",
        fontSize: "13px",
        boxSizing: "border-box",
      }}
    >
      <option value="">
        Select category
      </option>

      {categories
        .filter(
          (category) =>
            category.category_type ===
              "expense" ||
            category.category_type ===
              "Expense"
        )
        .map((category) => (
          <option
            key={category.id}
            value={category.id}
          >
            {category.name}
          </option>
        ))}
    </select>
  </div>

  {/* PAYMENT ACCOUNT */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "7px",
    }}
  >
    <label
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: "rgba(255,255,255,0.60)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      Payment Account
    </label>

    <select
      value={formData.account_id}
      onChange={(event) =>
        handleChange(
          "account_id",
          event.target.value
        )
      }
      style={{
        width: "100%",
        minHeight: "42px",
        padding: "10px 12px",
        border:
          "1px solid rgba(255,255,255,0.12)",
        borderRadius: "12px",
        background: "#151525",
        color: "#ffffff",
        outline: "none",
        fontSize: "13px",
        boxSizing: "border-box",
      }}
    >
      <option value="">
        Select account
      </option>

      {accounts
        .filter(
          (account) =>
            account.is_active
        )
        .map((account) => (
          <option
            key={account.id}
            value={account.id}
          >
            {account.name}
          </option>
        ))}
    </select>
  </div>

  {/* FREQUENCY */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "7px",
    }}
  >
    <label
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: "rgba(255,255,255,0.60)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      Frequency
    </label>

    <select
      value={formData.frequency}
      onChange={(event) =>
        handleChange(
          "frequency",
          event.target.value
        )
      }
      style={{
        width: "100%",
        minHeight: "42px",
        padding: "10px 12px",
        border:
          "1px solid rgba(255,255,255,0.12)",
        borderRadius: "12px",
        background: "#151525",
        color: "#ffffff",
        outline: "none",
        fontSize: "13px",
        boxSizing: "border-box",
      }}
    >
      <option value="daily">Daily</option>
      <option value="weekly">Weekly</option>
      <option value="monthly">Monthly</option>
      <option value="quarterly">Quarterly</option>
      <option value="half_yearly">
        Half-Yearly
      </option>
      <option value="yearly">Yearly</option>
      <option value="custom">Custom</option>
    </select>
  </div>

  {/* NEXT DUE DATE */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "7px",
    }}
  >
    <label
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: "rgba(255,255,255,0.60)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      Next Due Date
    </label>

    <input
      type="date"
      value={formData.next_due_date}
      onChange={(event) =>
        handleChange(
          "next_due_date",
          event.target.value
        )
      }
      style={{
        width: "100%",
        minHeight: "42px",
        padding: "10px 12px",
        border:
          "1px solid rgba(255,255,255,0.12)",
        borderRadius: "12px",
        background: "#151525",
        color: "#ffffff",
        outline: "none",
        fontSize: "13px",
        boxSizing: "border-box",
      }}
    />
  </div>

  {/* STATUS */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "7px",
    }}
  >
    <label
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: "rgba(255,255,255,0.60)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      Status
    </label>

    <select
      value={formData.status}
      onChange={(event) =>
        handleChange(
          "status",
          event.target.value
        )
      }
      style={{
        width: "100%",
        minHeight: "42px",
        padding: "10px 12px",
        border:
          "1px solid rgba(255,255,255,0.12)",
        borderRadius: "12px",
        background: "#151525",
        color: "#ffffff",
        outline: "none",
        fontSize: "13px",
        boxSizing: "border-box",
      }}
    >
      <option value="active">Active</option>
      <option value="paused">Paused</option>
      <option value="cancelled">
        Cancelled
      </option>
    </select>
  </div>

  {/* NOTES */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "7px",
    }}
  >
    <label
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: "rgba(255,255,255,0.60)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      Notes
    </label>

    <input
      value={formData.notes}
      onChange={(event) =>
        handleChange(
          "notes",
          event.target.value
        )
      }
      placeholder="Optional notes"
      style={{
        width: "100%",
        minHeight: "42px",
        padding: "10px 12px",
        border:
          "1px solid rgba(255,255,255,0.12)",
        borderRadius: "12px",
        background: "rgba(255,255,255,0.05)",
        color: "#ffffff",
        outline: "none",
        fontSize: "13px",
        boxSizing: "border-box",
      }}
    />
  </div>
</div>

          <div
            style={{
              display: "flex",
              justifyContent:
                "flex-end",
              gap: "10px",
              marginTop: "20px",
            }}
          >

            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                resetForm();
                setShowForm(false);
              }}
              disabled={saving}
            >
              Cancel
            </button>

            <button
              type="button"
              className="primary-button"
              onClick={
                handleSaveBill
              }
              disabled={saving}
            >
              {saving
                ? "Saving..."
                : editingBill
                ? "Update Bill"
                : "Save Bill"}
            </button>

          </div>

        </div>

      )}


      {/* ================================================== */}
      {/* DELETE CONFIRMATION */}
      {/* ================================================== */}

      {billToDelete && (

        <div
          style={{
            position: "fixed",
            inset: 0,
            background:
              "rgba(0,0,0,0.65)",
            display: "flex",
            alignItems: "center",
            justifyContent:
              "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >

          <div
            className="glass-card"
            style={{
              width: "100%",
              maxWidth: "420px",
              padding: "24px",
            }}
          >

            <div
              className="card-label"
            >
              DELETE BILL
            </div>

            <h3
              style={{
                margin:
                  "6px 0 10px",
              }}
            >
              Delete this bill?
            </h3>

            <p
              style={{
                color:
                  "rgba(255,255,255,0.60)",
                fontSize: "13px",
                lineHeight: 1.6,
              }}
            >
              This will permanently
              remove{" "}
              <strong>
                {billToDelete.name}
              </strong>
              .
            </p>

            <div
              style={{
                display: "flex",
                justifyContent:
                  "flex-end",
                gap: "10px",
                marginTop: "20px",
              }}
            >

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setBillToDelete(
                    null
                  )
                }
                disabled={deleting}
              >
                Cancel
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={
                  handleDeleteBill
                }
                disabled={deleting}
                style={{
                  color: "#fb7185",
                  borderColor:
                    "rgba(251,113,133,0.30)",
                }}
              >
                {deleting
                  ? "Deleting..."
                  : "Delete"}
              </button>

            </div>

          </div>

        </div>

      )}

    </div>

  );

}










