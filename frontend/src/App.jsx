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
) : activePage === "Transactions" ? (
  <Transactions />
) : activePage === "Budget" ? (
  <Budget />
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
        `${API_BASE_URL}/api/budgets/`,
        {
          method: "POST",
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
              Spending progress
            </span>

            <span>
              0%
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
                width: "0%",
                height: "100%",
                borderRadius: "999px",
                background:
                  "linear-gradient(90deg, #7048ff, #f45b69)",
              }}
            />

          </div>

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










