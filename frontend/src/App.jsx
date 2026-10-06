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

        <button className="primary-button">
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
              : String(accounts.length)
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
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "20px",
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

          </div>

        </div>


        {/* BALANCE */}

        <div
          style={{
            textAlign: "right",
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

      </div>

    ))}

  </div>

)}

      </section>

    </div>
    
    );
}














