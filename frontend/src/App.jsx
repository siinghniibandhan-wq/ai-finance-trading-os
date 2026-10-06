// ============================================================
// FINANCIAL OS
// MAIN APPLICATION
// ============================================================

import React, { useState } from "react";

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
          METRICS
      ==================================================== */}

      <section className="metrics-grid">

        <MetricCard
          title="Net Worth"
          value="₹0"
          change="+0.00%"
          positive
          icon={Wallet}
        />

        <MetricCard
          title="Cash Balance"
          value="₹0"
          change="+0.00%"
          positive
          icon={Landmark}
        />

        <MetricCard
          title="Investments"
          value="₹0"
          change="+0.00%"
          positive
          icon={TrendingUp}
        />

        <MetricCard
          title="Credit / Debt"
          value="₹0"
          change="0.00%"
          positive={false}
          icon={CreditCard}
        />

      </section>

      {/* ====================================================
          MAIN GRID
      ==================================================== */}

      <section className="dashboard-grid">

        {/* CASH FLOW */}

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
              This Month
            </button>

          </div>

          <div className="empty-chart">

            <div className="chart-icon">
              <BarChart3 size={28} />
            </div>

            <strong>
              No financial data yet
            </strong>

            <span>
              Add your first transaction to
              start seeing your cash flow.
            </span>

            <button className="secondary-button">
              Add Transaction
            </button>

          </div>

        </div>

        {/* AI INSIGHT */}

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
          FINANCIAL HEALTH
      ==================================================== */}

      <section className="glass-card health-card">

        <div className="card-header">

          <div>
            <p className="card-label">
              FINANCIAL HEALTH
            </p>

            <h3>
              Financial Health Score
            </h3>
          </div>

          <span className="score">
            0 / 100
          </span>

        </div>

        <div className="health-progress">

          <div className="health-progress-fill" />

        </div>

        <div className="health-footer">

          <span>
            Add your financial information
            to calculate your score.
          </span>

          <button className="secondary-button">
            Complete Profile
          </button>

        </div>

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
