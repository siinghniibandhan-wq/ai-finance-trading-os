// ============================================================
// FINANCIAL OS
// MAIN APPLICATION
// ============================================================

import React, { useEffect, useState } from "react";

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
  CircleDollarSign
} from "lucide-react";

// ============================================================
// NAVIGATION
// ============================================================

const navigation = [
  {
    section: "Overview",
    items: [
      {
        name: "Dashboard",
        icon: LayoutDashboard
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
      }
    ]
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

  {
    section: "AI",
    items: [
      {
        name: "AI Assistant",
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

  const [activePage, setActivePage] = useState("Dashboard");

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
  // ----------------------------------------------------------
  // DASHBOARD STATE
  // ----------------------------------------------------------

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";

  const USER_ID = 1;

  // ----------------------------------------------------------
  // LOAD DASHBOARD DATA
  // ----------------------------------------------------------

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_BASE_URL}/api/dashboard/summary?user_id=${USER_ID}`
        );

        if (!response.ok) {
          throw new Error(
            `Dashboard API error: ${response.status}`
          );
        }

        const data = await response.json();

        setDashboardData(data);
      } catch (err) {
        console.error("Dashboard API error:", err);

        setError(
          "Unable to load financial data."
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
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
  // DATA
  // ----------------------------------------------------------

  const summary = dashboardData?.summary || {};

  const totalBalance = summary.total_balance || 0;
  const totalIncome = summary.total_income || 0;
  const totalExpense = summary.total_expense || 0;
  const netCashFlow = summary.net_cash_flow || 0;

  const recentTransactions =
    dashboardData?.recent_transactions || [];

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (
    <div className="dashboard">

      {/* ====================================================
          WELCOME
      ==================================================== */}

      <section className="welcome-section">

        <div>

          <p className="welcome-label">
            PERSONAL FINANCE
          </p>

          <h2>
            Your money,
            <br />
            <span>under control.</span>
          </h2>

          <p className="welcome-description">
            Track your wealth, spending, investments
            and financial goals from one place.
          </p>

        </div>

        <button className="primary-button">
          <Plus size={18} />
          Add Transaction
        </button>

      </section>


      {/* ====================================================
          ERROR
      ==================================================== */}

      {error && (
        <div className="glass-card">
          <strong>{error}</strong>
        </div>
      )}


      {/* ====================================================
          METRICS
      ==================================================== */}

      <section className="metrics-grid">

        <MetricCard
          title="Cash Balance"
          value={
            loading
              ? "Loading..."
              : formatCurrency(totalBalance)
          }
          change="Current"
          positive
          icon={Wallet}
        />

        <MetricCard
          title="Total Income"
          value={
            loading
              ? "Loading..."
              : formatCurrency(totalIncome)
          }
          change="Income"
          positive
          icon={TrendingUp}
        />

        <MetricCard
          title="Total Expenses"
          value={
            loading
              ? "Loading..."
              : formatCurrency(totalExpense)
          }
          change="Expenses"
          positive={false}
          icon={CreditCard}
        />

        <MetricCard
          title="Net Cash Flow"
          value={
            loading
              ? "Loading..."
              : formatCurrency(netCashFlow)
          }
          change={
            netCashFlow >= 0
              ? "Positive"
              : "Negative"
          }
          positive={netCashFlow >= 0}
          icon={CircleDollarSign}
        />

      </section>


      {/* ====================================================
          MAIN GRID
      ==================================================== */}

      <section className="dashboard-grid">

        {/* ==================================================
            CASH FLOW
        ================================================== */}

        <div className="glass-card large-card">

          <div className="card-header">

            <div>

              <p className="card-label">
                CASH FLOW
              </p>

              <h3>
                Income & Expenses
              </h3>

            </div>

            <button className="small-button">
              Current
            </button>

          </div>


          {loading ? (

            <div className="empty-chart">

              <strong>
                Loading financial data...
              </strong>

            </div>

          ) : (

            <div className="empty-chart">

              <div className="chart-icon">
                <BarChart3 size={28} />
              </div>

              <strong>
                {formatCurrency(totalIncome)}
                {" income / "}
                {formatCurrency(totalExpense)}
                {" expenses"}
              </strong>

              <span>
                Net cash flow:{" "}
                {formatCurrency(netCashFlow)}
              </span>

            </div>

          )}

        </div>


        {/* ==================================================
            AI INSIGHT
        ================================================== */}

        <div className="glass-card ai-card">

          <div className="ai-glow" />

          <div className="card-header">

            <div className="ai-title">

              <div className="ai-icon">
                <Sparkles size={19} />
              </div>

              <div>

                <p className="card-label">
                  AI INSIGHT
                </p>

                <h3>
                  Financial Assistant
                </h3>

              </div>

            </div>

          </div>

          <div className="ai-empty">

            <p>
              Your AI financial assistant
              will analyze your finances here.
            </p>

            <button className="primary-button">
              <Sparkles size={17} />
              Ask AI
            </button>

          </div>

        </div>

      </section>


      {/* ====================================================
          RECENT TRANSACTIONS
      ==================================================== */}

      <section className="glass-card health-card">

        <div className="card-header">

          <div>

            <p className="card-label">
              RECENT ACTIVITY
            </p>

            <h3>
              Recent Transactions
            </h3>

          </div>

          <span className="score">
            {summary.transaction_count || 0}
          </span>

        </div>


        {recentTransactions.length === 0 ? (

          <div className="health-footer">

            <span>
              No transactions available.
            </span>

          </div>

        ) : (

          <div>

            {recentTransactions.map((transaction) => (

              <div
                key={transaction.id}
                className="health-footer"
              >

                <span>
                  {transaction.description ||
                    "Transaction"}
                  {" • "}
                  {transaction.transaction_date}
                </span>

                <strong>
                  {transaction.transaction_type ===
                  "expense"
                    ? "-"
                    : "+"}
                  {formatCurrency(transaction.amount)}
                </strong>

              </div>

            ))}

          </div>

        )}

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
// PORTFOLIO
// ============================================================

function Portfolio() {
  
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

  // ----------------------------------------------------------
  // SAVE INVESTMENT
  // ----------------------------------------------------------

  const handleInvestmentSubmit = async () => {
    try {
      // Validate required fields
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

      const payload = {
        user_id: 1,
        name: investmentForm.name.trim(),
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

      // Reset form
      setInvestmentForm({
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

 // Close form
const wasEditing = Boolean(editingInvestmentId);

setShowInvestmentForm(false);
setEditingInvestmentId(null);

await loadInvestments();

alert(
  wasEditing
    ? "Investment updated successfully."
    : "Investment saved successfully."
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
    onClick={() =>
      setShowInvestmentForm(true)
    }
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

            {/* INVESTMENT NAME */}

            <input
              type="text"
              placeholder="Investment name"
              value={investmentForm.name}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  name: event.target.value,
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


            {/* INVESTMENT TYPE */}

            <select
              value={investmentForm.investment_type}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  investment_type:
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


            {/* SYMBOL / ISIN */}

            <input
              type="text"
              placeholder="Symbol / ISIN"
              value={investmentForm.symbol}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  symbol: event.target.value,
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


            {/* BROKER */}

            <input
              type="text"
              placeholder="Broker / Platform"
              value={investmentForm.broker}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  broker: event.target.value,
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
              onClick={() =>
                setShowInvestmentForm(false)
              }
            >
              Cancel
            </button>

          </div>

        </div>
      )}     
              
            

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

  {/* EDIT BUTTON */}
  <button
    type="button"
    className="small-button"
    style={{
      marginTop: "8px",
      cursor: "pointer",
    }}
    onClick={() =>
      handleEditInvestment(investment)
    }
  >
    Edit
  </button>
</div>  

        </div>
      );
    })

  )}

</div>
         </div>

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
  });

// ----------------------------------------------------------
// TRANSACTION FORM OPTIONS & SAVE STATE
// ----------------------------------------------------------

const [savingTransaction, setSavingTransaction] = useState(false);
const [formMessage, setFormMessage] = useState("");
  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://ai-finance-trading-os-api.onrender.com";

  const USER_ID = 1;

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
      category_id: Number(formData.category_id),
      transaction_type: formData.transaction_type,
      amount: Number(formData.amount),
      description: formData.description.trim(),
      transaction_date: formData.transaction_date,
      reference: formData.reference.trim(),
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










