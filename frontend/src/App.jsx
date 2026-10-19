// ============================================================
// FINANCIAL OS
// MAIN APPLICATION
// ============================================================

import React, { useEffect, useRef, useState } from "react";
import "./account-layout.css";
import AdminPanel from "./AdminPanel";
import AccountContactSettings from "./AccountContactSettings";
import WealthManager from "./WealthManager";
import LoanManagement from "./LoanManagement";
import { API_BASE_URL, apiFetch, getCurrentUserId, getCurrentUser, clearSession } from "./api";

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
  Trash2,
  ShieldCheck
} from "lucide-react";


// ============================================================
// CUSTOM FINANCIAL OS SELECT — branded dropdown instead of the
// browser/Android native selection sheet. Keeps select-like props.
// ============================================================
function StyledSelect({ children, value, onChange, className = "", style = {}, disabled = false, name, id, "aria-label": ariaLabel }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const options = React.Children.toArray(children).filter((child) => React.isValidElement(child) && child.type === "option");
  const selected = options.find((option) => String(option.props.value ?? option.props.children) === String(value));
  const selectedLabel = selected ? selected.props.children : (options[0]?.props.children ?? "Select an option");
  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutside = (event) => { if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false); };
    const closeOnEscape = (event) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("pointerdown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => { document.removeEventListener("pointerdown", closeOnOutside); document.removeEventListener("keydown", closeOnEscape); };
  }, [open]);
  return <div ref={rootRef} className={`finos-select-wrap ${className}`} style={{ position: "relative", minWidth: 0, ...style }}>
    <button type="button" id={id} aria-label={ariaLabel} aria-haspopup="listbox" aria-expanded={open} disabled={disabled} onClick={() => setOpen((previous) => !previous)} className="finos-select-trigger">
      <span>{selectedLabel}</span><span className={`finos-select-chevron ${open ? "is-open" : ""}`}>⌄</span>
    </button>
    {open && <div className="finos-select-menu" role="listbox" aria-label={ariaLabel || name || "Options"}>
      {options.map((option, index) => {
        const optionValue = String(option.props.value ?? option.props.children);
        const active = optionValue === String(value);
        return <button type="button" role="option" aria-selected={active} key={`${optionValue}-${index}`} disabled={option.props.disabled} className={`finos-select-option ${active ? "is-selected" : ""}`} onClick={() => { onChange?.({ target: { name, value: optionValue } }); setOpen(false); }}>
          <span>{option.props.children}</span><span className="finos-select-check">{active ? "✓" : ""}</span>
        </button>;
      })}
    </div>}
  </div>;
}

// ============================================================
// API REQUESTS — centralized authenticated API wrapper
// ============================================================

// ============================================================
// NAVIGATION
// ============================================================

const navigation = [
  {
    section: "Home",
    items: [
      {
        name: "Dashboard",
        icon: LayoutDashboard
      },
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
        name: "Ledger",
        icon: Receipt
      },
      {
        name: "Chart of Accounts",
        icon: CircleDollarSign
      },
      {
        name: "Loans & Liabilities",
        icon: Landmark
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
        name: "Budget",
        icon: PieChart
      },
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


// Appearance themes are local preferences; they do not change financial data or calculations.
const FINOS_THEMES = ["Default","Light","Dark","Aurora","Emerald","Ocean","Sunset","Minimal","Retro Terminal","Glass","Skeuomorphism","Neumorphism","Glassmorphism","Claymorphism","Brutalism","Maximalism","Liquid Glass","Bento Grid","Elegant Plain"];
const FINOS_THEME_DESCRIPTIONS = {
  "Default": "The original Financial OS dark-purple workspace.",
  "Light": "Bright, clean surfaces with dark readable text.",
  "Dark": "A low-glare dark workspace.",
  "Aurora": "Purple and pink gradient accents.",
  "Emerald": "Nature-inspired green accents.",
  "Ocean": "Calm professional blue accents.",
  "Sunset": "Warm amber and coral accents.",
  "Minimal": "Quiet, reduced visual decoration.",
  "Retro Terminal": "Terminal-inspired green and monospace details.",
  "Glass": "Translucent panels and soft depth.",
  "Skeuomorphism": "Tactile surfaces with subtle inset and raised depth.",
  "Neumorphism": "Soft, low-contrast raised and inset surfaces.",
  "Glassmorphism": "Frosted translucent cards and blur.",
  "Claymorphism": "Rounded, soft, pillowy card surfaces.",
  "Brutalism": "Bold borders, hard contrast, and square edges.",
  "Maximalism": "Expressive gradients and vivid accent colors.",
  "Liquid Glass": "Glossy translucent surfaces with fluid highlights.",
  "Bento Grid": "Clean modular panels with clear visual grouping.",
  "Elegant Plain": "Plain white, thin borders, restrained spacing, and elegant typography."
};
const readFinosTheme = () => {
  try {
    const saved = window.localStorage.getItem("financial-os-theme");
    return FINOS_THEMES.includes(saved) ? saved : "Default";
  } catch { return "Default"; }
};
const applyFinosTheme = (theme) => {
  const nextTheme = FINOS_THEMES.includes(theme) ? theme : "Default";
  document.documentElement.dataset.finosTheme = nextTheme.toLowerCase().replaceAll(" ", "-");
  document.documentElement.style.colorScheme = ["Light", "Elegant Plain", "Minimal", "Skeuomorphism", "Neumorphism", "Claymorphism", "Bento Grid"].includes(nextTheme) ? "light" : "dark";
  try { window.localStorage.setItem("financial-os-theme", nextTheme); } catch { /* Theme still applies for this session. */ }
};

// ============================================================
// MAIN APP
// ============================================================

// Asset-class-specific product types prevent unrelated investment choices.
const PRODUCT_TYPES_BY_ASSET_CLASS = {
  Equity: ["Stocks", "Mutual Funds", "ETFs", "Index Funds"],
  "Fixed Income": ["Fixed Deposits", "Recurring Deposits", "Bonds", "Government Securities", "Debt Mutual Funds", "NPS"],
  Commodities: ["Gold", "Silver", "Other Commodities"],
  "Real Estate": ["Residential Property", "Commercial Property", "REITs"],
  "Digital Assets": ["Cryptocurrencies", "Other Digital Assets"],
  Alternatives: ["Private Equity", "Venture Capital", "Hedge Funds", "Other Alternatives"],
  Other: ["Other"],
};

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminAccessChecked, setAdminAccessChecked] = useState(false);
  const [headerPanel, setHeaderPanel] = useState("");
  const [headerSearch, setHeaderSearch] = useState("");
  const headerActionsRef = useRef(null);

  useEffect(() => {
    if (!headerPanel) return undefined;
    const closeOutside = (event) => {
      if (headerActionsRef.current && !headerActionsRef.current.contains(event.target)) setHeaderPanel("");
    };
    const closeEscape = (event) => { if (event.key === "Escape") setHeaderPanel(""); };
    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeEscape);
    };
  }, [headerPanel]);

  // Keep navigation in the URL so the current section survives refreshes,
  // direct links, and browser Back/Forward throughout the application.
  const validPages = new Set([
    "Dashboard", "Wealth Manager", "Accounts", "Account Profile", "Transactions", "Ledger", "Chart of Accounts",
    "Loans & Liabilities", "Budget", "Categories", "Bills", "Portfolio",
    "Holdings", "Investment Transactions", "Markets", "Goals",
    "AI Assistant", "Tax", "Playground", "Settings", "Finance Diary", "Admin Panel"
  ]);
  const getPageFromLocation = () => {
    const params = new URLSearchParams(window.location.search);
    const page = params.get("page");
    return page && validPages.has(page) ? page : "Wealth Manager";
  };
  const [activePage, setActivePage] = useState(getPageFromLocation);
  const [selectedTheme, setSelectedTheme] = useState(readFinosTheme);

  useEffect(() => {
    let cancelled = false;
    const checkAdminAccess = async () => {
      try {
        const response = await apiFetch(`${API_BASE_URL}/api/auth/admin/users?limit=1&offset=0`);
        if (!cancelled) setIsAdmin(response.ok);
      } catch {
        if (!cancelled) setIsAdmin(false);
      } finally {
        if (!cancelled) setAdminAccessChecked(true);
      }
    };
    if (getCurrentUserId()) {
      checkAdminAccess();
    } else {
      setIsAdmin(false);
      setAdminAccessChecked(true);
    }
    return () => { cancelled = true; };
  }, []);

  // Show the Admin Panel navigation only when the backend confirms administrator access.
  // The backend remains the security boundary for every administrative API request.
  const visibleNavigation = isAdmin
    ? [...navigation, { section: "Administration", items: [{ name: "Admin Panel", icon: ShieldCheck }] }]
    : navigation;

  useEffect(() => { applyFinosTheme(selectedTheme); }, [selectedTheme]);
  const changeTheme = (theme) => { setSelectedTheme(theme); applyFinosTheme(theme); };

  useEffect(() => {
    const restoreLocation = () => setActivePage(getPageFromLocation());
    window.addEventListener("popstate", restoreLocation);
    return () => window.removeEventListener("popstate", restoreLocation);
  }, []);

  // ----------------------------------------------------------
  // NAVIGATION HANDLER
  // ----------------------------------------------------------

  const handleNavigation = (page) => {
    const nextPage = validPages.has(page) ? page : "Wealth Manager";
    const url = new URL(window.location.href);
    url.searchParams.set("page", nextPage);
    window.history.pushState({ page: nextPage }, "", `${url.pathname}${url.search}${url.hash}`);
    setActivePage(nextPage);
    setSidebarOpen(false);
  };

  // Direct links must not expose the Admin Panel to unauthorised sessions.
  // Wait for backend authorization before redirecting the configured admin.
  useEffect(() => {
    if (activePage === "Admin Panel" && adminAccessChecked && !isAdmin) {
      const url = new URL(window.location.href);
      url.searchParams.set("page", "Wealth Manager");
      window.history.replaceState({ page: "Wealth Manager" }, "", `${url.pathname}${url.search}${url.hash}`);
      setActivePage("Wealth Manager");
    }
  }, [activePage, adminAccessChecked, isAdmin]);

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
        id="financial-os-sidebar"
        aria-label="Main navigation"
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

          {visibleNavigation.map((group) => (

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
              type="button"
              aria-label={sidebarOpen ? "Close navigation menu" : "Open navigation menu"}
              aria-expanded={sidebarOpen}
              aria-controls="financial-os-sidebar"
              onClick={() => setSidebarOpen((open) => !open)}
            >
              {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
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

          <div className="topbar-actions" ref={headerActionsRef}>
            <div className="header-action-wrap">
              <button className="icon-button" type="button" aria-label="Search pages" title="Search" aria-expanded={headerPanel === "search"} onClick={() => setHeaderPanel((panel) => panel === "search" ? "" : "search")}>
                <Search size={19} />
              </button>
              {headerPanel === "search" && (
                <div className="header-popover header-search-popover" role="dialog" aria-label="Search Financial OS">
                  <label htmlFor="global-page-search">Search Financial OS</label>
                  <input id="global-page-search" autoFocus value={headerSearch} onChange={(event) => setHeaderSearch(event.target.value)} placeholder="Search pages…" />
                  <div className="header-search-results">
                    {["Dashboard", "Wealth Manager", "Accounts", "Transactions", "Ledger", "Chart of Accounts", "Loans & Liabilities", "Budget", "Categories", "Bills", "Portfolio", "Holdings", "Investment Transactions", "Markets", "Goals", "AI Assistant", "Tax", "Playground", "Settings", "Finance Diary", "Account Profile"]
                      .filter((page) => page.toLowerCase().includes(headerSearch.trim().toLowerCase()))
                      .slice(0, 8)
                      .map((page) => <button type="button" key={page} onClick={() => { setHeaderPanel(""); setHeaderSearch(""); handleNavigation(page); }}>{page}</button>)}
                    {headerSearch.trim() && !["Dashboard", "Wealth Manager", "Accounts", "Transactions", "Ledger", "Chart of Accounts", "Loans & Liabilities", "Budget", "Categories", "Bills", "Portfolio", "Holdings", "Investment Transactions", "Markets", "Goals", "AI Assistant", "Tax", "Playground", "Settings", "Finance Diary", "Account Profile"].some((page) => page.toLowerCase().includes(headerSearch.trim().toLowerCase())) && <p className="header-popover-empty">No matching pages found.</p>}
                  </div>
                </div>
              )}
            </div>

            <div className="header-action-wrap">
              <button className="icon-button" type="button" aria-label="Notifications" title="Notifications" aria-expanded={headerPanel === "notifications"} onClick={() => setHeaderPanel((panel) => panel === "notifications" ? "" : "notifications")}>
                <Bell size={19} />
              </button>
              {headerPanel === "notifications" && (
                <div className="header-popover header-notifications-popover" role="dialog" aria-label="Notifications">
                  <div className="header-popover-heading"><strong>Notifications</strong><span>Financial OS</span></div>
                  <p className="header-popover-empty">Your financial reminders and budget alerts are available on the Dashboard.</p>
                  <button type="button" className="header-popover-primary" onClick={() => { setHeaderPanel(""); handleNavigation("Dashboard"); }}>View alerts &amp; notifications <span>→</span></button>
                </div>
              )}
            </div>

            <div className="header-action-wrap">
              <button className="profile" type="button" onClick={() => setHeaderPanel((panel) => panel === "profile" ? "" : "profile")} aria-label="Open user menu" title="User menu" aria-expanded={headerPanel === "profile"} style={{ cursor: "pointer", color: "inherit", font: "inherit", textAlign: "left", border: 0, background: "transparent", padding: 0 }}>
                <div className="profile-avatar">{(getCurrentUser()?.name || "U").trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()}</div>
                <div className="profile-info"><strong>{getCurrentUser()?.name || "User"}</strong><span>{getCurrentUser()?.email || "Personal workspace"}</span></div>
              </button>
              {headerPanel === "profile" && (
                <div className="header-popover header-profile-popover" role="menu" aria-label="User menu" style={{ width: "min(280px, calc(100vw - 24px))", maxWidth: "280px", boxSizing: "border-box" }}>
                  <div className="header-profile-summary"><div className="profile-avatar">{(getCurrentUser()?.name || "U").trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()}</div><div><strong>{getCurrentUser()?.name || "User"}</strong><span>{getCurrentUser()?.email || "Personal workspace"}</span></div></div>
                  <button type="button" role="menuitem" onClick={() => { setHeaderPanel(""); handleNavigation("Account Profile"); }}>Account profile</button>
                  <div role="none"><TradingControlSettings compact /></div>
                  <button type="button" role="menuitem" onClick={() => { setHeaderPanel(""); handleNavigation("Settings"); }}><Settings size={16}/> Settings &amp; preferences <span>›</span></button>
                  <button type="button" role="menuitem" onClick={() => { setHeaderPanel(""); handleNavigation("Settings"); }}>Theme &amp; appearance <span>›</span></button>
                  <div className="header-profile-divider"/>
                  <button type="button" role="menuitem" className="header-signout" onClick={() => {
                    const token = sessionStorage.getItem("financial_os_access_token") || "";
                    try {
                      if (token) fetch(`${API_BASE_URL}/api/auth/logout`, { method: "POST", keepalive: true, headers: { Accept: "application/json", Authorization: `Bearer ${token}` } }).catch((error) => console.warn("Server-side logout could not be confirmed.", error));
                    } finally {
                      clearSession();
                      window.location.replace("/login");
                    }
                  }}>Sign out</button>
                </div>
              )}
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
) : activePage === "Account Profile" ? (
  <AccountCompletionPage />
) : activePage === "Transactions" ? (
  <Transactions />
) : activePage === "Ledger" ? (
  <LedgerPage />
) : activePage === "Chart of Accounts" ? (
  <ChartOfAccountsPage />
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
) : activePage === "Playground" ? (
   <PlaygroundPage />
) : activePage === "Tax" ? (
   <TaxPage />
) : activePage === "Goals" ? (
   <PlanPage />
) : activePage === "AI Assistant" ? (
   <AIAssistantPage />
) : activePage === "Finance Diary" ? (
   <FinanceDiaryPage />
) : activePage === "Admin Panel" ? (
   isAdmin ? <AdminPanel /> : <div className="admin-access-denied" role="alert">Administrator access is required. Your backend admin configuration must be set before this panel is available.</div>
) : activePage === "Settings" ? (
   <SettingsPage onNavigate={handleNavigation} selectedTheme={selectedTheme} onThemeChange={changeTheme} />
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
  const [receivablePayable, setReceivablePayable] = useState({ total_receivable: 0, total_payable: 0, items: [] });
  const [settlementAccounts, setSettlementAccounts] = useState([]);
  const [settlementDraft, setSettlementDraft] = useState(null);
  const [settlementError, setSettlementError] = useState("");
  const [settlementSaving, setSettlementSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const API_BASE_URL = "https://wealthmanager.duckdns.org";
  const USER_ID = getCurrentUserId();


  const loadDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const [dashboardResponse, goalsResponse, receivablePayableResponse, accountsResponse] = await Promise.all([
        apiFetch(`${API_BASE_URL}/api/dashboard/summary?user_id=${USER_ID}`, { cache: "no-store" }),
        apiFetch(`${API_BASE_URL}/api/goals/?user_id=${USER_ID}`, { cache: "no-store" }).catch(() => null),
        apiFetch(`${API_BASE_URL}/api/transactions/receivables-payables`, { cache: "no-store" }).catch(() => null),
        apiFetch(`${API_BASE_URL}/api/accounts/?user_id=${USER_ID}`, { cache: "no-store" }).catch(() => null),
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
      if (receivablePayableResponse?.ok) {
        const rpPayload = await receivablePayableResponse.json();
        setReceivablePayable({
          total_receivable: Number(rpPayload.total_receivable || 0),
          total_payable: Number(rpPayload.total_payable || 0),
          items: Array.isArray(rpPayload.items) ? rpPayload.items : [],
        });
      } else {
        setReceivablePayable({ total_receivable: 0, total_payable: 0, items: [] });
      }
      if (accountsResponse?.ok) {
        const accountPayload = await accountsResponse.json();
        setSettlementAccounts(Array.isArray(accountPayload) ? accountPayload.filter((account) => {
          const type = String(account.account_type || "").toLowerCase();
          return account.is_active !== false && !/(receivable|payable|loan|investment|broker|credit.?card|credit.?line)/.test(type);
        }) : []);
      } else {
        setSettlementAccounts([]);
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
  const dashboardInputStyle = { width: "100%", boxSizing: "border-box", display: "block", marginTop: "6px", padding: "10px 11px", borderRadius: "9px", border: "1px solid rgba(255,255,255,0.14)", background: "#151525", color: "#fff", outline: "none" };

  const submitOutstandingSettlement = async (event) => {
    event.preventDefault();
    if (!settlementDraft?.transaction_id || !settlementDraft.account_id || Number(settlementDraft.amount) <= 0) {
      setSettlementError("Choose a bank/cash account and enter a valid settlement amount.");
      return;
    }
    setSettlementSaving(true);
    setSettlementError("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/transactions/${settlementDraft.transaction_id}/settle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          account_id: Number(settlementDraft.account_id),
          amount: Number(settlementDraft.amount),
          transaction_date: settlementDraft.transaction_date,
          description: settlementDraft.description || null,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Unable to settle this outstanding amount.");
      setSettlementDraft(null);
      await loadDashboard();
      window.dispatchEvent(new Event("financial-os:transactions-changed"));
    } catch (err) {
      setSettlementError(err?.message || "Unable to settle this outstanding amount.");
    } finally {
      setSettlementSaving(false);
    }
  };

  const summary = dashboardData?.summary || {};
  const trend = (dashboardData?.monthly_trend || []).slice(-6);
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

  return (
    <div className="dashboard dashboard-overview">
      <section className="welcome-section">
        <div>
          <p className="welcome-label">FINANCIAL COMMAND CENTRE</p>
          <h2>Your financial <br /><span>overview.</span></h2>
          <p className="welcome-description">
            Your at-a-glance financial status. Open Money for detailed cash-flow analysis, Portfolio for investments, and Wealth Manager for your complete balance sheet.
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
        <div role="button" tabIndex={0} onClick={() => goTo("Accounts")} onKeyDown={(event) => event.key === "Enter" && goTo("Accounts")} className="dashboard-clickable-card" aria-label="Open accounts"><MetricCard title="Cash Balance" value={loading ? "Loading…" : formatCurrency(totalBalance)} change={`${summary.account_count || 0} active accounts · Open accounts`} positive icon={Wallet} /></div>
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} className="dashboard-clickable-card" aria-label="Open income transactions"><MetricCard title="Total Income" value={loading ? "Loading…" : formatCurrency(totalIncome)} change="All recorded income · View details" positive icon={TrendingUp} /></div>
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} className="dashboard-clickable-card" aria-label="Open expense transactions"><MetricCard title="Total Expenses" value={loading ? "Loading…" : formatCurrency(totalExpense)} change="All recorded expenses · View details" positive={false} icon={CreditCard} /></div>
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} className="dashboard-clickable-card" aria-label="Open cash flow details"><MetricCard title="Net Cash Flow" value={loading ? "Loading…" : formatCurrency(netCashFlow)} change={`${netCashFlow >= 0 ? "Positive" : "Negative"} · View details`} positive={netCashFlow >= 0} icon={CircleDollarSign} /></div>
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} className="dashboard-clickable-card" aria-label="Open income analysis"><MetricCard title="Avg. Monthly Income" value={loading ? "Loading…" : formatCurrency(avgIncome)} change="Last 90 days ÷ 3 · View details" positive icon={ArrowUpRight} /></div>
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} className="dashboard-clickable-card" aria-label="Open expense analysis"><MetricCard title="Avg. Monthly Expenses" value={loading ? "Loading…" : formatCurrency(avgExpense)} change="Last 90 days ÷ 3 · View details" positive={false} icon={ArrowDownRight} /></div>
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} className="dashboard-clickable-card" aria-label="Open savings and cash flow details"><MetricCard title="Estimated Monthly Savings" value={loading ? "Loading…" : formatCurrency(monthlySavings)} change="Income minus expenses · View details" positive={monthlySavings >= 0} icon={WalletCards} /></div>
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} className="dashboard-clickable-card" aria-label="Open savings rate details"><MetricCard title="Savings Rate" value={loading ? "Loading…" : `${savingsRate.toFixed(1)}%`} change={`${avgIncome > 0 ? "90-day average" : "Add income records"} · View details`} positive={savingsRate >= 0} icon={PieChart} /></div>
      </section>

      <section className="metrics-grid" aria-label="Outstanding balances">
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} style={{cursor:"pointer"}}>
          <MetricCard title="Receivable" value={loading ? "Loading…" : formatCurrency(receivablePayable.total_receivable)} change="Money owed to you" positive icon={ArrowDownRight} />
        </div>
        <div role="button" tabIndex={0} onClick={() => goTo("Transactions")} onKeyDown={(event) => event.key === "Enter" && goTo("Transactions")} style={{cursor:"pointer"}}>
          <MetricCard title="Payable" value={loading ? "Loading…" : formatCurrency(receivablePayable.total_payable)} change="Money you owe" positive={false} icon={ArrowUpRight} />
        </div>
      </section>

      <section className="glass-card" style={{ marginBottom: "24px" }}>
        <div className="card-header">
          <div><p className="card-label">MONEY • OUTSTANDING</p><h3>Receivables & Payables</h3></div>
          <span className="small-button">{receivablePayable.items.length} open items</span>
        </div>
        {settlementError && <p role="alert" style={{ color: "#fca5a5" }}>{settlementError}</p>}
        {receivablePayable.items.length === 0 ? (
          <p className="chart-footnote">No outstanding receivables or payables. Add one from Money → Transactions → Add Transaction.</p>
        ) : (
          <div style={{ display: "grid", gap: "10px" }}>
            {receivablePayable.items.map((item) => (
              <div key={item.id} style={{ border: "1px solid rgba(255,255,255,0.10)", borderRadius: "12px", padding: "12px 14px" }}>
                <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "10px" }}>
                  <div>
                    <strong>{item.type === "receivable" ? "To receive" : "To pay"} · {item.party_name || item.description || `Transaction #${item.id}`}</strong>
                    <div className="chart-footnote">Due: {item.due_date || "Not specified"} · Outstanding: {formatCurrency(item.outstanding_amount)}</div>
                  </div>
                  <button className="small-button" type="button" onClick={() => { setSettlementError(""); setSettlementDraft({ transaction_id: item.id, amount: String(item.outstanding_amount), account_id: "", transaction_date: new Date().toISOString().slice(0, 10), description: "" }); }}>
                    {item.type === "receivable" ? "Receive payment" : "Make payment"}
                  </button>
                </div>
                {settlementDraft?.transaction_id === item.id && (
                  <form onSubmit={submitOutstandingSettlement} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "10px", marginTop: "12px" }}>
                    <label style={{ fontSize: "12px" }}>Bank / Cash account
                      <select required value={settlementDraft.account_id} onChange={(e) => setSettlementDraft((draft) => ({ ...draft, account_id: e.target.value }))} style={{ ...dashboardInputStyle, colorScheme: "dark" }}>
                        <option value="">Select account</option>
                        {settlementAccounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
                      </select>
                    </label>
                    <label style={{ fontSize: "12px" }}>Amount
                      <input required type="number" min="0.01" max={Number(item.outstanding_amount)} step="0.01" value={settlementDraft.amount} onChange={(e) => setSettlementDraft((draft) => ({ ...draft, amount: e.target.value }))} style={dashboardInputStyle} />
                    </label>
                    <label style={{ fontSize: "12px" }}>Settlement date
                      <input required type="date" value={settlementDraft.transaction_date} onChange={(e) => setSettlementDraft((draft) => ({ ...draft, transaction_date: e.target.value }))} style={dashboardInputStyle} />
                    </label>
                    <label style={{ fontSize: "12px" }}>Note (optional)
                      <input value={settlementDraft.description} onChange={(e) => setSettlementDraft((draft) => ({ ...draft, description: e.target.value }))} style={dashboardInputStyle} />
                    </label>
                    <div style={{ display: "flex", alignItems: "end", gap: "8px" }}>
                      <button className="primary-button" type="submit" disabled={settlementSaving}>{settlementSaving ? "Saving…" : "Confirm settlement"}</button>
                      <button className="small-button" type="button" onClick={() => setSettlementDraft(null)}>Cancel</button>
                    </div>
                  </form>
                )}
              </div>
            ))}
          </div>
        )}
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

        <div className="glass-card dashboard-money-drilldown">
          <div className="card-header">
            <div><p className="card-label">MONEY / FULL ANALYSIS</p><h3>Explore your cash flow</h3></div>
            <ArrowUpRight size={18} />
          </div>
          <p className="chart-footnote">Detailed spending categories, budgets and transaction analysis belong in the Money workspace. This dashboard keeps the trend summary concise.</p>
          <button className="primary-button" type="button" onClick={() => goTo("Transactions")}>Open Money analysis</button>
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
// Tax Centre sections use existing tax APIs; HRA calculator is estimate-only.
// ============================================================

function TaxPage() {
  const API_BASE_URL =
    "https://wealthmanager.duckdns.org";
  const USER_ID = getCurrentUserId();

  const [section, setSection] = useState("Overview");
  const [financialYear, setFinancialYear] = useState("2026-27");
  const [taxRegime, setTaxRegime] = useState(""); // Require regime selection before showing tax calculations.
  const [sttConfirmed, setSttConfirmed] = useState(false);
  const [taxData, setTaxData] = useState(null);
  const [incomeData, setIncomeData] = useState(null);
  const [businessIncomeData, setBusinessIncomeData] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [comparisonReportData, setComparisonReportData] = useState(null);
  const [finalLiabilityData, setFinalLiabilityData] = useState(null);
  const [residentialStatus, setResidentialStatus] = useState("resident");
  const [ageCategory, setAgeCategory] = useState("under_60");
  const [deductionData, setDeductionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [salaryProfile, setSalaryProfile] = useState({
    employer_name: "",
    gross_salary: "",
    basic_salary: "",
    hra: "",
    da: "0",
    other_allowances: "",
    employee_pf: "0",
    professional_tax: "0",
    tds: "0",
  });
  const [salaryComponentsTouched, setSalaryComponentsTouched] = useState(false);

  const [hraInputs, setHraInputs] = useState({
    gross_salary: "",
    annual_basic_salary: "",
    annual_da_forming_retirement_benefits: "0",
    annual_commission_on_turnover_at_fixed_percentage: "0",
    annual_hra_received: "",
    annual_rent_paid: "",
    accommodation_owned_by_taxpayer: false,
    rent_actually_paid: false,
    city: "",
    city_classification: "non_metro",
  });
  const [hraCityCatalog, setHraCityCatalog] = useState({ metro: [], non_metro: [] });
  const [hraCityCatalogError, setHraCityCatalogError] = useState("");
  const [hraResult, setHraResult] = useState(null);
  const [hraLoading, setHraLoading] = useState(false);
  const [hraError, setHraError] = useState("");
  const [hraSalaryEvidence, setHraSalaryEvidence] = useState("");
  const [hraRentEvidence, setHraRentEvidence] = useState("");
  const [hraSalarySaving, setHraSalarySaving] = useState(false);
  const [hraSalaryMessage, setHraSalaryMessage] = useState("");
  const [hraSalaryError, setHraSalaryError] = useState("");
  const [taxCredits, setTaxCredits] = useState([]);
  const [creditForm, setCreditForm] = useState({ credit_type: "tds", amount: "", source_reference: "" });
  const [creditBusy, setCreditBusy] = useState(false);
  const [creditMessage, setCreditMessage] = useState("");
  const [creditError, setCreditError] = useState("");
  const [taxReviewState, setTaxReviewState] = useState({});
  const [taxReviewBusy, setTaxReviewBusy] = useState(false);
  const [taxReviewError, setTaxReviewError] = useState("");
  const [taxReviewMessage, setTaxReviewMessage] = useState("");
  const [form26asTotal, setForm26asTotal] = useState("");
  const [dedClaims, setDedClaims] = useState([]);
  const [dedForm, setDedForm] = useState({ deduction_key: "", claimed_amount: "", evidence_reference: "" });
  const [dedBusy, setDedBusy] = useState(false);
  const [dedError, setDedError] = useState("");
  const [dedMessage, setDedMessage] = useState("");
  const [hpRecords, setHpRecords] = useState([]);
  const [hpForm, setHpForm] = useState({ property_type: "let_out", property_label: "", annual_rent_received: "", municipal_taxes_paid: "", interest_on_housing_loan: "" });
  const [hpBusy, setHpBusy] = useState(false);
  const [hpMessage, setHpMessage] = useState("");
  const [hpError, setHpError] = useState("");

  const sections = [
    "Overview",
    "Income",
    "Capital Gains",
    "Deductions",
    "HRA Calculator",
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
    const response = await apiFetch(`${API_BASE_URL}${path}`);
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
      const [capitalTax, taxableIncome, deductionCatalog] = await Promise.all([
        readApi(
          `/api/tax-calculation/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&stt_confirmed=${sttConfirmed}`
        ),
        readApi(
          `/api/final-taxable-income/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&tax_regime=${encodeURIComponent(taxRegime)}`
        ),
        readApi(
          `/api/deductions-exempt-income/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&tax_regime=${encodeURIComponent(taxRegime)}`
        ),
      ]);
      setTaxData(capitalTax);
      setIncomeData(taxableIncome);
      setDeductionData(deductionCatalog);
      // Business-income endpoint is a read-only review queue: candidates are
      // never auto-created or counted as taxable until explicitly recorded and verified.
      try {
        const businessIncome = await readApi(
          `/api/tax-business-income/?financial_year=${encodeURIComponent(financialYear)}`
        );
        setBusinessIncomeData(businessIncome);
      } catch (businessIncomeError) {
        setBusinessIncomeData({ status: "unavailable", unlinked_money_transactions: [], message: businessIncomeError.message });
        console.info("Business-income review candidates are unavailable:", businessIncomeError);
      }
      setNotice("Tax data refreshed. Business-income candidates are review-only and are not included in taxable income until verified.");

      // The final liability engine currently has a verified rule set for 2026-27 only.
      // Keep older years provisional rather than applying the wrong year's rules.
      if (financialYear === "2026-27") {
        try {
          const liability = await readApi(
            `/api/final-tax-liability/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&tax_regime=${encodeURIComponent(taxRegime)}&residential_status=${encodeURIComponent(residentialStatus)}&age_category=${encodeURIComponent(ageCategory)}&stt_confirmed=${sttConfirmed}`
          );
          setFinalLiabilityData(liability);
        } catch (liabilityError) {
          setFinalLiabilityData({ status: "unavailable", message: liabilityError.message });
          console.info("Final tax liability is not available:", liabilityError);
        }
      } else {
        setFinalLiabilityData({
          status: "rules_not_configured",
          message: "The final liability engine does not yet have a verified rule set for this financial year."
        });
      }

      // This report endpoint is optional: show report content only if deployed.
      try {
        const report = await readApi(
          // This endpoint expects the query parameter `regime`, not `tax_regime`.
          `/api/itr-ready-tax-report/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&regime=${encodeURIComponent(taxRegime)}&stt_confirmed=${sttConfirmed}`
        );
        setReportData(report);
        // Always compare the alternative regime using the same financial-year data.
        try {
          const comparisonRegime = taxRegime === "new" ? "old" : "new";
          const comparison = await readApi(
            `/api/itr-ready-tax-report/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&regime=${comparisonRegime}&stt_confirmed=${sttConfirmed}`
          );
          setComparisonReportData(comparison);
        } catch (comparisonError) {
          setComparisonReportData(null);
          console.info("Tax-regime comparison is not available yet:", comparisonError);
        }
      } catch (reportError) {
        setReportData(null);
        setComparisonReportData(null);
        console.info("ITR report endpoint is not available yet:", reportError);
      }
    } catch (err) {
      console.error("Tax Centre load error:", err);
      setError(err?.message || "Unable to load tax data.");
    } finally {
      setLoading(false);
    }
  };

  // HRA calculator is estimate-only: it calls the existing backend endpoint and does not save a claim.
  const calculateHra = async (event) => {
    event.preventDefault();
    setHraLoading(true);
    setHraError("");
    setHraResult(null);
    try {
      if (!taxRegime) throw new Error("Choose a tax regime before calculating HRA.");
      if (taxRegime !== "old") throw new Error("HRA exemption is not available under the selected New Regime.");
      const payload = {
        financial_year: financialYear,
        tax_regime: taxRegime,
        annual_basic_salary: Number(hraInputs.annual_basic_salary),
        annual_da_forming_retirement_benefits: Number(hraInputs.annual_da_forming_retirement_benefits || 0),
        annual_commission_on_turnover_at_fixed_percentage: Number(hraInputs.annual_commission_on_turnover_at_fixed_percentage || 0),
        annual_hra_received: Number(hraInputs.annual_hra_received),
        annual_rent_paid: Number(hraInputs.annual_rent_paid),
        accommodation_owned_by_taxpayer: hraInputs.accommodation_owned_by_taxpayer,
        rent_actually_paid: hraInputs.rent_actually_paid,
        city: hraInputs.city.trim(),
      };
      const response = await apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/hra-calculator`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result?.detail || `HRA calculator returned ${response.status}`);
      setHraResult(result);
    } catch (err) {
      setHraError(err?.message || "Unable to calculate HRA exemption.");
    } finally {
      setHraLoading(false);
    }
  };

  const saveAndVerifyHraSalary = async () => {
    setHraSalarySaving(true);
    setHraSalaryError("");
    setHraSalaryMessage("");
    try {
      if (taxRegime !== "old") throw new Error("Select Old Regime to save an HRA salary source.");
      if (!hraResult) throw new Error("Calculate HRA first so the salary and rent inputs are complete.");
      if (!String(hraInputs.gross_salary || "").trim() || Number(hraInputs.gross_salary) <= 0) throw new Error("Enter annual gross salary from your salary statement/Form 16.");
      if (!hraSalaryEvidence.trim()) throw new Error("Enter a reference for your salary statement/Form 16 before verification.");
      if (!hraRentEvidence.trim()) throw new Error("Enter a separate reference for rent receipts, rental agreement, or other HRA evidence.");
      // Pre-flight, before anything is saved: the backend refuses to replace a
      // verified HRA claim, which used to leave the salary half-saved. Check
      // first, ask the person, and only then continue.
      const claimsResponse = await apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/claims?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}`);
      const claimsResult = await claimsResponse.json().catch(() => ({}));
      if (!claimsResponse.ok) throw new Error(claimsResult?.detail || `Could not check existing HRA claims (${claimsResponse.status}). Nothing was saved.`);
      const existingVerifiedHra = (Array.isArray(claimsResult?.claims) ? claimsResult.claims : []).find((c) => c.deduction_key === "hra_exemption" && c.status === "verified");
      if (existingVerifiedHra) {
        const proceed = window.confirm(`A verified HRA claim of ${formatCurrency(existingVerifiedHra.claimed_amount)} already exists for ${financialYear}. Continue? It will be set back to pending and replaced by this new claim.`);
        if (!proceed) throw new Error("Cancelled. Nothing was saved and your existing verified HRA claim is unchanged.");
        const unverifyResponse = await apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/claims/${existingVerifiedHra.id}/unverify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: USER_ID, evidence_reference: hraRentEvidence.trim() }),
        });
        const unverifyResult = await unverifyResponse.json().catch(() => ({}));
        if (!unverifyResponse.ok) throw new Error(unverifyResult?.detail || `Could not set the old HRA claim back to pending (${unverifyResponse.status}). Nothing else was saved.`);
      }
      const payload = {
        financial_year: financialYear,
        gross_salary: Number(hraInputs.gross_salary),
        annual_basic_salary: Number(hraInputs.annual_basic_salary),
        annual_da_forming_retirement_benefits: Number(hraInputs.annual_da_forming_retirement_benefits || 0),
        annual_commission_on_turnover_at_fixed_percentage: Number(hraInputs.annual_commission_on_turnover_at_fixed_percentage || 0),
        annual_hra_received: Number(hraInputs.annual_hra_received),
        annual_rent_paid: Number(hraInputs.annual_rent_paid),
        accommodation_owned_by_taxpayer: hraInputs.accommodation_owned_by_taxpayer,
        rent_actually_paid: hraInputs.rent_actually_paid,
        city: hraInputs.city.trim(),
        evidence_reference: hraSalaryEvidence.trim(),
      };
      let response = await apiFetch(`${API_BASE_URL}/api/final-taxable-income/salary-income`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      });
      let result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result?.detail || `Salary source save returned ${response.status}`);
      response = await apiFetch(`${API_BASE_URL}/api/final-taxable-income/salary-income/verify?financial_year=${encodeURIComponent(financialYear)}&evidence_reference=${encodeURIComponent(hraSalaryEvidence.trim())}`, { method: "POST" });
      result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result?.detail || `Salary source verification returned ${response.status}`);

      // Save/update the HRA claim from the same calculator inputs, then mark
      // it verified only after the user provides a separate HRA/rent evidence reference.
      response = await apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/claims`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          financial_year: financialYear,
          tax_regime: "old",
          deduction_key: "hra_exemption",
          evidence_reference: hraRentEvidence.trim(),
          hra_inputs: {
            annual_basic_salary: Number(hraInputs.annual_basic_salary),
            annual_da_forming_retirement_benefits: Number(hraInputs.annual_da_forming_retirement_benefits || 0),
            annual_commission_on_turnover_at_fixed_percentage: Number(hraInputs.annual_commission_on_turnover_at_fixed_percentage || 0),
            annual_hra_received: Number(hraInputs.annual_hra_received),
            annual_rent_paid: Number(hraInputs.annual_rent_paid),
            accommodation_owned_by_taxpayer: hraInputs.accommodation_owned_by_taxpayer,
            rent_actually_paid: hraInputs.rent_actually_paid,
            city: hraInputs.city.trim(),
          },
        }),
      });
      result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result?.detail || `HRA claim save returned ${response.status}`);
      const hraClaimId = result.id;
      response = await apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/claims/${hraClaimId}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, evidence_reference: hraRentEvidence.trim() }),
      });
      result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result?.detail || `HRA claim verification returned ${response.status}`);
      setHraSalaryMessage("Salary source and HRA claim saved. Both are marked verified based on your confirmation; the app does not inspect documents. Refreshing tax calculations.");
      await loadTaxData();
    } catch (err) {
      setHraSalaryError(err?.message || "Unable to save the salary source.");
    } finally {
      setHraSalarySaving(false);
    }
  };

  // Undo: puts the salary record and any verified HRA claim back to "pending
  // review" so they stop affecting taxable income. Saved figures are kept.
  const undoHraSalaryVerification = async () => {
    if (!window.confirm(`This sets your verified salary record and verified HRA claim for ${financialYear} back to pending review. They will stop counting in your taxable income until you verify them again. Your saved figures are kept. Continue?`)) return;
    setHraSalarySaving(true);
    setHraSalaryError("");
    setHraSalaryMessage("");
    try {
      const claimsResponse = await apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/claims?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}`);
      const claimsResult = await claimsResponse.json().catch(() => ({}));
      if (!claimsResponse.ok) throw new Error(claimsResult?.detail || `Could not read HRA claims (${claimsResponse.status}). Nothing was changed.`);
      const verifiedHra = (Array.isArray(claimsResult?.claims) ? claimsResult.claims : []).filter((c) => c.deduction_key === "hra_exemption" && c.status === "verified");
      for (const claim of verifiedHra) {
        const r = await apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/claims/${claim.id}/unverify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: USER_ID }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d?.detail || `Could not set the HRA claim back to pending (${r.status}).`);
      }
      const salaryResponse = await apiFetch(`${API_BASE_URL}/api/final-taxable-income/salary-income/unverify?financial_year=${encodeURIComponent(financialYear)}`, { method: "POST" });
      const salaryResult = await salaryResponse.json().catch(() => ({}));
      if (salaryResponse.status === 404) {
        // No salary record exists: nothing to undo for salary.
      } else if (!salaryResponse.ok) {
        throw new Error(salaryResult?.detail || `Could not set the salary record back to pending (${salaryResponse.status}).`);
      }
      setHraSalaryMessage("Salary record and HRA claim are back to pending review and no longer affect taxable income. Refreshing tax calculations.");
      await loadTaxData();
    } catch (err) {
      setHraSalaryError(err?.message || "Unable to undo verification.");
    } finally {
      setHraSalarySaving(false);
    }
  };

  // House property income (let-out, self-occupied, or "none"). Entries are saved
  // as pending and count in taxable income only after the person verifies them.
  const loadHouseProperty = async () => {
    try {
      const r = await apiFetch(`${API_BASE_URL}/api/tax-house-property/?financial_year=${encodeURIComponent(financialYear)}`);
      const d = await r.json().catch(() => ({}));
      if (r.ok) setHpRecords(Array.isArray(d?.entries) ? d.entries : []);
    } catch (err) { /* list stays as it was */ }
  };
  useEffect(() => { loadHouseProperty(); }, [financialYear]);

  const hpCall = async (url, options, doneMessage) => {
    setHpBusy(true); setHpError(""); setHpMessage("");
    try {
      const r = await apiFetch(url, options);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof d?.detail === "string" ? d.detail : `Request failed (${r.status}).`);
      setHpMessage(doneMessage);
      await loadHouseProperty();
      await loadTaxData();
      return true;
    } catch (err) {
      setHpError(err?.message || "Unable to update the house property record.");
      return false;
    } finally { setHpBusy(false); }
  };
  const hpPost = (body) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const addHouseProperty = async () => {
    const isNone = hpForm.property_type === "none";
    const isLetOut = hpForm.property_type === "let_out";
    if (isLetOut && !(Number(hpForm.annual_rent_received) > 0)) { setHpError("Enter the yearly rent received for a let-out property."); return; }
    const ok = await hpCall(`${API_BASE_URL}/api/tax-house-property/`, hpPost({
      financial_year: financialYear,
      property_type: hpForm.property_type,
      property_label: hpForm.property_label.trim() || null,
      annual_rent_received: isLetOut ? Number(hpForm.annual_rent_received) || 0 : 0,
      municipal_taxes_paid: isLetOut ? Number(hpForm.municipal_taxes_paid) || 0 : 0,
      interest_on_housing_loan: isNone ? 0 : Number(hpForm.interest_on_housing_loan) || 0,
    }), "Saved as pending. It does not affect your taxable income until you verify it.");
    if (ok) setHpForm((f) => ({ ...f, property_label: "", annual_rent_received: "", municipal_taxes_paid: "", interest_on_housing_loan: "" }));
  };
  const verifyHouseProperty = (id) => {
    const reference = window.prompt("Enter an evidence reference you can find later (for example: rent agreement, loan interest certificate). The app does not check documents.");
    if (!reference || reference.trim().length < 3) return;
    hpCall(`${API_BASE_URL}/api/tax-house-property/${id}/verify`, hpPost({ evidence_reference: reference.trim() }), "Marked verified on your confirmation. Keep the supporting documents.");
  };
  const unverifyHouseProperty = (id) => hpCall(`${API_BASE_URL}/api/tax-house-property/${id}/unverify`, hpPost({}), "Returned to pending review. It no longer affects taxable income.");
  const deleteHouseProperty = (id) => { if (window.confirm("Delete this house property record?")) hpCall(`${API_BASE_URL}/api/tax-house-property/${id}`, { method: "DELETE" }, "Record deleted."); };

  const renderHouseProperty = () => {
    const box = { width: "100%", boxSizing: "border-box", padding: "10px 11px", borderRadius: "9px", border: "1px solid rgba(255,255,255,0.14)", background: "rgba(12,16,30,0.72)", color: "inherit" };
    const head = incomeData?.income_heads?.house_property || {};
    const typeNames = { let_out: "Let-out property", self_occupied: "Self-occupied property", none: "No house property income" };
    const isNone = hpForm.property_type === "none";
    const isLetOut = hpForm.property_type === "let_out";
    return (
      <section className="tax-house-property-panel" style={{ ...panelStyle, marginTop: 0 }}>
        <h3 style={{ marginTop: 0 }}>House property income</h3>
        <p style={{ color: "rgba(255,255,255,0.58)", fontSize: 12, lineHeight: 1.6 }}>Add each property for {financialYear}, or confirm that you have none. A record counts in your taxable income only after you verify it. Rent receipts in Money are never counted automatically. The app does not inspect documents.</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "10px", marginBottom: "12px" }}>
          <div style={cardStyle}><div style={labelStyle}>House property income counted</div><div style={valueStyle}>{head.available ? formatCurrency(head.amount) : "Not available"}</div>{!head.available && <div style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px", marginTop: 4 }}>{safeText(head.reason, "No verified record yet.")}</div>}</div>
          {head.available && Number(head.loss_not_set_off) > 0 && <div style={cardStyle}><div style={labelStyle}>Loss not set off</div><div style={valueStyle}>{formatCurrency(head.loss_not_set_off)}</div><div style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px", marginTop: 4 }}>Above the allowed limit, or not allowed in this regime. Carry-forward is not calculated here.</div></div>}
        </div>
        {Number(head.money_rent_transactions_detected) > 0 && <div style={{ color: "#fbbf24", fontSize: 12, marginBottom: 12 }}>{head.money_rent_transactions_detected} rent receipt(s) totalling {formatCurrency(head.money_rent_total_detected)} are recorded in Money under House Property. They are not counted until you add and verify a house property record.</div>}
        <div style={{ display: "grid", gap: "8px" }}>
          <select aria-label="Property type" style={box} value={hpForm.property_type} onChange={(e) => setHpForm((f) => ({ ...f, property_type: e.target.value }))}>
            <option value="let_out">Let-out property (rented to someone)</option>
            <option value="self_occupied">Self-occupied property</option>
            <option value="none">I have no house property income</option>
          </select>
          {!isNone && <input aria-label="Property name" style={box} type="text" maxLength={120} placeholder="Property name (optional)" value={hpForm.property_label} onChange={(e) => setHpForm((f) => ({ ...f, property_label: e.target.value }))} />}
          {isLetOut && <input aria-label="Yearly rent received" style={box} type="number" min="0" step="0.01" placeholder="Rent received in the year (₹)" value={hpForm.annual_rent_received} onChange={(e) => setHpForm((f) => ({ ...f, annual_rent_received: e.target.value }))} />}
          {isLetOut && <input aria-label="Municipal taxes paid" style={box} type="number" min="0" step="0.01" placeholder="Municipal taxes paid by you (₹, optional)" value={hpForm.municipal_taxes_paid} onChange={(e) => setHpForm((f) => ({ ...f, municipal_taxes_paid: e.target.value }))} />}
          {!isNone && <input aria-label="Home loan interest" style={box} type="number" min="0" step="0.01" placeholder="Home loan interest paid in the year (₹, optional)" value={hpForm.interest_on_housing_loan} onChange={(e) => setHpForm((f) => ({ ...f, interest_on_housing_loan: e.target.value }))} />}
          <button type="button" className="primary-button" disabled={hpBusy} onClick={addHouseProperty}>Add house property record</button>
          {hpError && <div role="alert" style={{ color: "#fca5a5", fontSize: "12px" }}>{hpError}</div>}
          {hpMessage && <div role="status" style={{ color: "#86efac", fontSize: "12px" }}>{hpMessage}</div>}
        </div>
        <div style={{ display: "grid", gap: "10px", marginTop: "14px" }}>
          {hpRecords.length === 0 && <div style={{ color: "rgba(255,255,255,0.5)", fontSize: "12px" }}>No house property records for this year.</div>}
          {hpRecords.map((r) => (
            <div key={r.id} style={{ ...cardStyle, padding: "13px" }}>
              <div style={labelStyle}>{typeNames[r.property_type] || r.property_type}{r.property_label ? ` · ${r.property_label}` : ""} · {r.status === "verified" ? "Verified" : "Pending review"}</div>
              {r.property_type !== "none" && <div style={{ color: "rgba(255,255,255,0.62)", fontSize: "12px", margin: "6px 0" }}>
                {r.property_type === "let_out" && <>Rent {formatCurrency(r.annual_rent_received)} · Municipal taxes {formatCurrency(r.municipal_taxes_paid)} · </>}Loan interest {formatCurrency(r.interest_on_housing_loan)}
              </div>}
              {r.property_type !== "none" && <div style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px", marginBottom: "8px" }}>Estimated income from this property (old regime): {formatCurrency(r.estimated_income_old_regime)}</div>}
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {r.status === "verified"
                  ? <button type="button" className="secondary-button" disabled={hpBusy} onClick={() => unverifyHouseProperty(r.id)}>Set back to pending</button>
                  : <button type="button" className="secondary-button" disabled={hpBusy} onClick={() => verifyHouseProperty(r.id)}>Verify</button>}
                <button type="button" className="secondary-button" disabled={hpBusy} onClick={() => deleteHouseProperty(r.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      </section>
    );
  };

  const loadTaxReview = async () => {
    try {
      const r = await apiFetch(`${API_BASE_URL}/api/tax-review/?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}`);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d?.detail || `Tax review returned ${r.status}`);
      setTaxReviewState(d?.sections || {});
      setTaxReviewError("");
    } catch (err) {
      setTaxReviewError(err?.message || "Unable to load tax review confirmations.");
    }
  };
  useEffect(() => { loadTaxReview(); }, [financialYear]);

  const changeTaxReview = async (sectionKey, confirm) => {
    setTaxReviewBusy(true);
    setTaxReviewError("");
    setTaxReviewMessage("");
    try {
      const url = confirm
        ? `${API_BASE_URL}/api/tax-review/confirm`
        : `${API_BASE_URL}/api/tax-review/confirm?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}&section=${encodeURIComponent(sectionKey)}`;
      const options = confirm
        ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: USER_ID, financial_year: financialYear, section: sectionKey }) }
        : { method: "DELETE" };
      const r = await apiFetch(url, options);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof d?.detail === "string" ? d.detail : `Request failed (${r.status}).`);
      if (d?.sections) setTaxReviewState(d.sections);
      else await loadTaxReview();
      setTaxReviewMessage(confirm ? "Your confirmation was saved. Pending entries still block completion." : "Your confirmation was removed.");
      await loadTaxData();
    } catch (err) {
      setTaxReviewError(err?.message || "Unable to save your confirmation.");
    } finally {
      setTaxReviewBusy(false);
    }
  };

  const renderTaxReviewConfirm = (sectionKey, description, buttonLabel) => {
    const info = taxReviewState?.[sectionKey] || {};
    return (
      <div style={{ ...cardStyle, padding: "13px", marginTop: "14px", borderColor: info.complete ? "rgba(34,197,94,0.35)" : "rgba(255,255,255,0.12)" }}>
        <div style={{ fontWeight: 750, fontSize: "12px" }}>{info.complete ? "Section complete" : info.confirmed_by_user ? "Confirmation saved · review still pending" : "Your confirmation is required"}</div>
        <p style={{ color: "rgba(255,255,255,0.58)", fontSize: "11px", lineHeight: 1.6, margin: "7px 0" }}>{description}</p>
        <p style={{ color: info.complete ? "#86efac" : "#fbbf24", fontSize: "11px", margin: "6px 0" }}>{info.reason || "Review status is not available yet."}</p>
        <button type="button" className="secondary-button" disabled={taxReviewBusy} onClick={() => changeTaxReview(sectionKey, !info.confirmed_by_user)}>
          {info.confirmed_by_user ? "Undo my confirmation" : buttonLabel}
        </button>
      </div>
    );
  };

  // Tax credits (TDS, advance tax, self-assessment tax). Entries are saved as
  // pending and only count once verified on the person's own confirmation.
  const loadTaxCredits = async () => {
    try {
      const r = await apiFetch(`${API_BASE_URL}/api/final-tax-liability/credits?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}`);
      const d = await r.json().catch(() => ({}));
      if (r.ok) setTaxCredits(Array.isArray(d?.entries) ? d.entries : []);
    } catch (err) { /* list stays as it was */ }
  };
  useEffect(() => { loadTaxCredits(); }, [financialYear]);

  const creditCall = async (url, options, doneMessage) => {
    setCreditBusy(true); setCreditError(""); setCreditMessage("");
    try {
      const r = await apiFetch(url, options);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof d?.detail === "string" ? d.detail : `Request failed (${r.status}).`);
      setCreditMessage(doneMessage);
      await loadTaxCredits();
      await loadTaxData();
    } catch (err) {
      setCreditError(err?.message || "Unable to update the tax credit.");
    } finally { setCreditBusy(false); }
  };
  const jsonPost = (body) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const addTaxCredit = () => {
    if (!(Number(creditForm.amount) > 0)) { setCreditError("Enter an amount greater than zero."); return; }
    creditCall(`${API_BASE_URL}/api/final-tax-liability/credits`, jsonPost({ user_id: USER_ID, financial_year: financialYear, credit_type: creditForm.credit_type, amount: Number(creditForm.amount), source_reference: creditForm.source_reference.trim() || null }), "Saved as pending. It does not reduce your tax until you verify it.")
      .then(() => setCreditForm((f) => ({ ...f, amount: "", source_reference: "" })));
  };
  const verifyTaxCredit = (id) => creditCall(`${API_BASE_URL}/api/final-tax-liability/credits/${id}/verify`, jsonPost({ user_id: USER_ID }), "Marked verified on your confirmation. Keep the challan or statement; the app does not check it.");
  const unverifyTaxCredit = (id) => creditCall(`${API_BASE_URL}/api/final-tax-liability/credits/${id}/unverify`, jsonPost({ user_id: USER_ID }), "Returned to pending review.");
  const deleteTaxCredit = (id) => { if (window.confirm("Delete this tax credit entry?")) creditCall(`${API_BASE_URL}/api/final-tax-liability/credits/${id}?user_id=${USER_ID}`, { method: "DELETE" }, "Entry deleted."); };

  const renderTaxCredits = () => {
    const box = { width: "100%", boxSizing: "border-box", padding: "10px 11px", borderRadius: "9px", border: "1px solid rgba(255,255,255,0.14)", background: "rgba(12,16,30,0.72)", color: "inherit" };
    const names = { tds: "TDS", advance_tax: "Advance tax", self_assessment_tax: "Self-assessment tax" };
    return (
      <div style={panelStyle}>
        <h3 style={{ marginTop: 0 }}>Tax already paid (TDS and advance tax)</h3>
        <p style={{ color: "rgba(255,255,255,0.58)", fontSize: "12px", lineHeight: 1.6 }}>Add tax already paid for {financialYear}. An entry reduces your tax only after you verify it with a challan or Form 26AS / AIS reference. The app does not inspect documents.</p>
        <div style={{ ...cardStyle, padding: "13px", marginBottom: "12px" }}>
          <div style={labelStyle}>Check against Form 26AS / AIS · comparison only</div>
          <p style={{ color: "rgba(255,255,255,0.58)", fontSize: "11px", lineHeight: 1.6, marginTop: 0 }}>Compare the total shown in Form 26AS / AIS with the verified tax-credit entries below. This does not import data or change tax calculations.</p>
          <label style={{ display: "grid", gap: "6px", fontSize: "11px", color: "rgba(255,255,255,0.7)" }}>Total tax credits shown in Form 26AS / AIS (₹)
            <input aria-label="Form 26AS AIS tax credit total" style={box} type="number" min="0" step="0.01" value={form26asTotal} onChange={(event) => setForm26asTotal(event.target.value)} placeholder="Enter the total to compare" />
          </label>
          <div style={{ marginTop: "9px", fontSize: "12px" }}>Verified entries in Financial OS: <strong>{formatCurrency(taxCredits.filter((c) => c?.status === "verified").reduce((sum, c) => sum + (Number(c.amount) || 0), 0))}</strong></div>
          {form26asTotal !== "" && Number.isFinite(Number(form26asTotal)) && Number(form26asTotal) >= 0 && <div style={{ marginTop: "6px", fontSize: "12px" }}>AIS / 26AS less verified entries: <strong>{formatCurrency(Number(form26asTotal) - taxCredits.filter((c) => c?.status === "verified").reduce((sum, c) => sum + (Number(c.amount) || 0), 0))}</strong></div>}
        </div>
        <div style={{ display: "grid", gap: "8px" }}>
          <select aria-label="Credit type" style={box} value={creditForm.credit_type} onChange={(e) => setCreditForm((f) => ({ ...f, credit_type: e.target.value }))}>
            <option value="tds">TDS (tax deducted at source)</option>
            <option value="advance_tax">Advance tax</option>
            <option value="self_assessment_tax">Self-assessment tax</option>
          </select>
          <input aria-label="Credit amount" style={box} type="number" min="0" step="0.01" placeholder="Amount (₹)" value={creditForm.amount} onChange={(e) => setCreditForm((f) => ({ ...f, amount: e.target.value }))} />
          <input aria-label="Credit reference" style={box} type="text" maxLength={200} placeholder="Challan / certificate reference (needed to verify)" value={creditForm.source_reference} onChange={(e) => setCreditForm((f) => ({ ...f, source_reference: e.target.value }))} />
          <button type="button" className="primary-button" disabled={creditBusy} onClick={addTaxCredit}>Add tax credit</button>
          {creditError && <div role="alert" style={{ color: "#fca5a5", fontSize: "12px" }}>{creditError}</div>}
          {creditMessage && <div role="status" style={{ color: "#86efac", fontSize: "12px" }}>{creditMessage}</div>}
        </div>
        <div style={{ display: "grid", gap: "10px", marginTop: "14px" }}>
          {taxCredits.length === 0 && <div style={{ color: "rgba(255,255,255,0.5)", fontSize: "12px" }}>No tax credits added for this year.</div>}
          {taxCredits.map((c) => (
            <div key={c.id} style={{ ...cardStyle, padding: "13px" }}>
              <div style={labelStyle}>{names[c.credit_type] || c.credit_type} · {c.status === "verified" ? "Verified" : "Pending review"}</div>
              <div style={valueStyle}>{formatCurrency(c.amount)}</div>
              <div style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px", margin: "4px 0 8px" }}>{c.source_reference || "No reference yet"}</div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {c.status === "verified"
                  ? <button type="button" className="secondary-button" disabled={creditBusy} onClick={() => unverifyTaxCredit(c.id)}>Set back to pending</button>
                  : <button type="button" className="secondary-button" disabled={creditBusy} onClick={() => verifyTaxCredit(c.id)}>Verify</button>}
                <button type="button" className="secondary-button" disabled={creditBusy} onClick={() => deleteTaxCredit(c.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  useEffect(() => {
    let cancelled = false;
    apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/hra-cities?financial_year=${encodeURIComponent(financialYear)}`, { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data?.detail || `City catalogue returned ${response.status}`);
        return data;
      })
      .then((data) => { if (!cancelled) { setHraCityCatalog({ metro: data.metro || [], non_metro: data.non_metro || [] }); setHraCityCatalogError(""); } })
      .catch((error) => { if (!cancelled) setHraCityCatalogError(error?.message || "City suggestions are unavailable; you can still enter a city."); });
    return () => { cancelled = true; };
  }, [financialYear]);

  useEffect(() => {
    // Do not request tax calculations until the user chooses a regime.
    if (taxRegime) loadTaxData();
    // Regime changes reload the existing read-only tax engines.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taxRegime, financialYear, residentialStatus, ageCategory, sttConfirmed]);

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
  const otherSources = incomeData?.income_heads?.other_sources || {};
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
    <div className="tax-income-layout" style={{ display: "grid", gap: "18px" }}>
    <section className="tax-income-aggregation" style={panelStyle}>
      <h3 style={{ marginTop: 0 }}>Income aggregation</h3>
      <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "12px", lineHeight: 1.6 }}>Amounts are taken from the existing final taxable-income engine. Missing income heads are shown as unavailable rather than assumed to be zero.</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "12px" }}>
        {[
          ["Other-source income", otherSources.income],
          ["Interest", otherSources.interest],
          ["Dividend", otherSources.dividend],
          ["Other-source total", otherSources.total],
          ["Capital gains after set-off", incomeData?.income_heads?.capital_gains?.total_after_setoff],
          ["Available gross income", taxable.available_gross_income],
        ].map(([label, value]) => <div key={label} style={cardStyle}><div style={labelStyle}>{label}</div><div style={{ fontSize: "18px", fontWeight: 750 }}>{value == null ? "Unavailable" : formatCurrency(value)}</div></div>)}
      </div>
      <div style={{ marginTop: "16px", color: "rgba(255,255,255,0.55)", fontSize: "12px" }}>Salary, house-property and business/profession income must not be treated as zero if the engine marks those heads unavailable.</div>
    </section>
    <section className="tax-business-income-review" style={{ ...panelStyle, marginTop: 0 }}>
        <h3 style={{ marginTop: 0 }}>Money transactions awaiting business-income review</h3>
        <p style={{ color: "rgba(255,255,255,0.58)", fontSize: 12, lineHeight: 1.6 }}>
          These are unlinked Money transactions that may be business or professional income. Being listed here does not make them business income, and nothing is saved or verified automatically. Only verified records count as business income. An entry filed under an Other Sources category may already be counted above as other-source income.
        </p>
        {businessIncomeData?.status === "unavailable" ? (
          <p role="status" style={{ color: "#fbbf24", fontSize: 12 }}>Review candidates could not be loaded: {safeText(businessIncomeData.message, "endpoint unavailable")}</p>
        ) : !Array.isArray(businessIncomeData?.unlinked_money_transactions) || businessIncomeData.unlinked_money_transactions.length === 0 ? (
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>No unlinked Money transactions were returned for this financial year.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr>{["Date", "Type", "Category", "Description", "Amount", "Status"].map((label) => <th key={label} style={{ ...tableCellStyle, color: "rgba(255,255,255,0.55)" }}>{label}</th>)}</tr></thead>
              <tbody>{businessIncomeData.unlinked_money_transactions.map((row) => (
                <tr key={row.source_transaction_id}>
                  <td style={tableCellStyle}>{safeText(row.transaction_date)}</td>
                  <td style={tableCellStyle}>{safeText(row.record_type)}</td>
                  <td style={tableCellStyle}>{safeText(row.category)}</td>
                  <td style={tableCellStyle}>{safeText(row.description)}</td>
                  <td style={tableCellStyle}>{formatCurrency(row.amount)}</td>
                  <td style={tableCellStyle}><span style={{ color: "#fbbf24" }}>Review required</span></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
    </section>
    {renderHouseProperty()}
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


  // User-managed deduction claims. Claims remain pending until the user explicitly verifies evidence.
  const loadDedClaims = async () => {
    try {
      const r = await apiFetch(`${API_BASE_URL}/api/deductions-exempt-income/claims?user_id=${USER_ID}&financial_year=${encodeURIComponent(financialYear)}`);
      const d = await r.json().catch(() => ({}));
      if (r.ok) setDedClaims((Array.isArray(d?.claims) ? d.claims : []).filter((c) => c.claim_type === "deduction" && c.deduction_key !== "hra_exemption"));
    } catch (err) {
      setDedError(err?.message || "Could not load deduction claims.");
    }
  };

  const dedPost = (body) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

  const dedCall = async (url, options, doneMessage) => {
    setDedBusy(true);
    setDedError("");
    setDedMessage("");
    try {
      const r = await apiFetch(url, options);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof d?.detail === "string" ? d.detail : `Request failed (${r.status}).`);
      setDedMessage(doneMessage);
      await loadDedClaims();
      await loadTaxData();
      return true;
    } catch (err) {
      setDedError(err?.message || "Unable to update the deduction claim.");
      return false;
    } finally {
      setDedBusy(false);
    }
  };

  const addDedClaim = async () => {
    if (!taxRegime) { setDedError("Choose a tax regime first."); return; }
    if (!dedForm.deduction_key) { setDedError("Choose a deduction."); return; }
    if (!(Number(dedForm.claimed_amount) > 0)) { setDedError("Enter an amount greater than zero."); return; }
    const saved = await dedCall(
      `${API_BASE_URL}/api/deductions-exempt-income/claims`,
      dedPost({
        user_id: USER_ID,
        financial_year: financialYear,
        tax_regime: taxRegime,
        deduction_key: dedForm.deduction_key,
        claimed_amount: Number(dedForm.claimed_amount),
        evidence_reference: dedForm.evidence_reference.trim() || null
      }),
      "Saved as pending. It does not reduce taxable income until you verify it."
    );
    if (saved) setDedForm((f) => ({ ...f, claimed_amount: "", evidence_reference: "" }));
  };

  const verifyDedClaim = (claim) => {
    if (!(claim.evidence_reference || "").trim()) {
      setDedError("Add a receipt, policy or certificate reference before verifying this claim.");
      return;
    }
    dedCall(`${API_BASE_URL}/api/deductions-exempt-income/claims/${claim.id}/verify`,
      dedPost({ user_id: USER_ID, evidence_reference: claim.evidence_reference.trim() }),
      "Claim marked verified. Keep the supporting document; the app does not check it.");
  };

  const unverifyDedClaim = (claimId) => dedCall(
    `${API_BASE_URL}/api/deductions-exempt-income/claims/${claimId}/unverify`,
    dedPost({ user_id: USER_ID }),
    "Claim returned to pending review."
  );

  const deleteDedClaim = (claimId) => {
    if (window.confirm("Delete this deduction claim?")) {
      dedCall(`${API_BASE_URL}/api/deductions-exempt-income/claims/${claimId}?user_id=${USER_ID}`,
        { method: "DELETE" }, "Deduction claim deleted.");
    }
  };

  const renderDeductionClaims = () => {
    const box = { width: "100%", boxSizing: "border-box", padding: "10px 11px", borderRadius: "9px", border: "1px solid rgba(255,255,255,0.14)", background: "rgba(12,16,30,0.72)", color: "inherit" };
    const options = (Array.isArray(deductionData?.applicable_deductions) ? deductionData.applicable_deductions : [])
      .filter((item) => item.deduction_key && item.deduction_key !== "hra_exemption");
    return (
      <div style={{ marginTop: "18px" }}>
        <h4 style={{ margin: "0 0 8px" }}>Your deduction claims · {financialYear}</h4>
        <p style={{ color: "rgba(255,255,255,0.58)", fontSize: "12px", lineHeight: 1.6, marginTop: 0 }}>
          Add a receipt, policy or certificate reference. Claims affect taxable income only when verified and eligible under the selected regime. The app does not independently verify documents. HRA is handled in the HRA Calculator.
        </p>
        <div style={{ display: "grid", gap: "8px" }}>
          <select aria-label="Deduction" style={box} value={dedForm.deduction_key} onChange={(e) => setDedForm((f) => ({ ...f, deduction_key: e.target.value }))}>
            <option value="">Choose a deduction</option>
            {options.map((item) => <option key={item.deduction_key} value={item.deduction_key}>{item.section} · {item.name}</option>)}
          </select>
          <input aria-label="Claim amount" style={box} type="number" min="0.01" step="0.01" placeholder="Amount (₹)" value={dedForm.claimed_amount} onChange={(e) => setDedForm((f) => ({ ...f, claimed_amount: e.target.value }))} />
          <input aria-label="Evidence reference" style={box} type="text" maxLength={2000} placeholder="Receipt / policy / certificate reference" value={dedForm.evidence_reference} onChange={(e) => setDedForm((f) => ({ ...f, evidence_reference: e.target.value }))} />
          <button type="button" className="primary-button" disabled={dedBusy} onClick={addDedClaim}>{dedBusy ? "Saving..." : "Add deduction claim"}</button>
          {dedError && <div role="alert" style={{ color: "#fca5a5", fontSize: "12px" }}>{dedError}</div>}
          {dedMessage && <div role="status" style={{ color: "#86efac", fontSize: "12px" }}>{dedMessage}</div>}
        </div>
        <div style={{ overflowX: "auto", marginTop: "14px" }}>
          {dedClaims.length === 0 ? <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "12px" }}>No deduction claims recorded for this financial year.</p> : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr>{["Deduction", "Claimed", "Evidence reference", "Status", "Actions"].map((label) => <th key={label} style={{ ...tableCellStyle, color: "rgba(255,255,255,0.55)", textAlign: "left" }}>{label}</th>)}</tr></thead>
              <tbody>{dedClaims.map((claim) => (
                <tr key={claim.id}>
                  <td style={tableCellStyle}>{safeText(claim.section || claim.deduction_key)}<div style={{ fontSize: "10px", color: "rgba(255,255,255,0.45)" }}>{claim.tax_regime === "old" ? "Old regime" : "New regime"}</div></td>
                  <td style={tableCellStyle}>{formatCurrency(claim.claimed_amount)}</td>
                  <td style={tableCellStyle}><input aria-label={`Evidence reference for claim ${claim.id}`} style={{ ...box, minWidth: "160px" }} maxLength={2000} value={claim.evidence_reference || ""} onChange={(e) => setDedClaims((items) => items.map((item) => item.id === claim.id ? { ...item, evidence_reference: e.target.value } : item))} /></td>
                  <td style={tableCellStyle}><span style={{ color: claim.status === "verified" ? "#86efac" : "#fbbf24" }}>{claim.status === "verified" ? "Verified" : "Pending review"}</span></td>
                  <td style={tableCellStyle}><div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    {claim.status === "verified"
                      ? <button type="button" className="secondary-button" disabled={dedBusy} onClick={() => unverifyDedClaim(claim.id)}>Set pending</button>
                      : <button type="button" className="secondary-button" disabled={dedBusy} onClick={() => verifyDedClaim(claim)}>Verify</button>}
                    <button type="button" className="secondary-button" disabled={dedBusy} onClick={() => deleteDedClaim(claim.id)}>Delete</button>
                  </div></td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </div>
        {renderTaxReviewConfirm("tds_advance_tax", "Confirm only after every TDS, advance-tax and self-assessment payment for this financial year is entered and verified. Any pending entry blocks completion.", "I have entered all tax already paid")}
        {taxReviewError && <div role="alert" style={{ color: "#fca5a5", fontSize: "11px", marginTop: "8px" }}>{taxReviewError}</div>}
        {taxReviewMessage && <div role="status" style={{ color: "#86efac", fontSize: "11px", marginTop: "8px" }}>{taxReviewMessage}</div>}
      </div>
    );
  };

  useEffect(() => { loadDedClaims(); }, [financialYear]);

  const renderDeductions = () => (
    <div style={panelStyle}>
      <h3 style={{ marginTop: 0 }}>Deductions and exempt income</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "12px" }}>
        <div style={cardStyle}><div style={labelStyle}>Verified deductions</div><div style={valueStyle}>{formatCurrency(deductions.verified_amount)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>{deductions.status || "Status unavailable"}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Verified exempt income</div><div style={valueStyle}>{formatCurrency(exemptIncome.verified_amount)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>{exemptIncome.status || "Status unavailable"}</div></div>
      </div>
      <p style={{ color: "rgba(255,255,255,0.62)", fontSize: "13px", lineHeight: 1.7 }}>
        The list below is filtered for the selected regime. “Potentially available” does not mean the deduction is claimed or approved. The current repository does not yet store verified claim amounts and evidence, so unverified deductions are not silently subtracted from taxable income.
      </p>
      <h4 style={{ margin: "18px 0 10px" }}>Applicable deduction catalogue · {taxRegime === "new" ? "New" : "Old"} regime</h4>
      {Array.isArray(deductionData?.applicable_deductions) && deductionData.applicable_deductions.length > 0 ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "10px" }}>
          {deductionData.applicable_deductions.map((item) => (
            <div key={item.section} style={{ ...cardStyle, padding: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "start" }}>
                <strong style={{ fontSize: "13px" }}>{safeText(item.section)} · {safeText(item.name)}</strong>
                <span style={{ fontSize: "10px", color: "#fbbf24", whiteSpace: "nowrap" }}>Needs verification</span>
              </div>
              <div style={{ color: "rgba(255,255,255,0.58)", fontSize: "11px", lineHeight: 1.5, marginTop: "8px" }}>Limit: {item.maximum_amount == null ? "Subject to rules" : formatCurrency(item.maximum_amount)}</div>
              <div style={{ color: "rgba(255,255,255,0.48)", fontSize: "10px", marginTop: "5px" }}>Basis: {safeText(item.basis, "Eligibility conditions apply")}</div>
              <div style={{ color: "rgba(255,255,255,0.58)", fontSize: "11px", marginTop: "8px" }}>Verified claim: {formatCurrency(item.verified_claimed_amount ?? 0)}</div>
            </div>
          ))}
        </div>
      ) : <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "12px" }}>Deduction catalogue is unavailable from the backend. Refresh the tax data or check that the deductions endpoint is deployed.</p>}
      {renderDeductionClaims()}
      {renderTaxReviewConfirm("deductions_exemptions", "Confirm only after all deductions and exempt-income claims you want to make are saved and verified. Any pending claim blocks completion.", "I have added all my deductions")}
      <h4 style={{ margin: "20px 0 10px" }}>Exempt-income / allowance checks</h4>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
        {(Array.isArray(deductionData?.exempt_income) ? deductionData.exempt_income : []).map((item) => (
          <div key={`${item.section}-${item.category}`} style={{ ...cardStyle, padding: "13px" }}>
            <strong style={{ fontSize: "12px" }}>{safeText(item.section)} · {safeText(item.category)}</strong>
            <div style={{ color: "rgba(255,255,255,0.52)", fontSize: "11px", marginTop: "7px" }}>No verified amount connected</div>
          </div>
        ))}
      </div>
      {deductionData?.rule_year_status && <p style={{ color: "rgba(255,255,255,0.42)", fontSize: "10px", lineHeight: 1.5, marginTop: "12px" }}>Rules status: {safeText(deductionData.rule_year_status)}</p>}
      {Array.isArray(deductionData?.regime_restricted_deductions) && deductionData.regime_restricted_deductions.length > 0 && (
        <details style={{ marginTop: "14px" }}>
          <summary style={{ cursor: "pointer", color: "rgba(255,255,255,0.65)", fontSize: "12px" }}>Show deductions restricted under this regime ({deductionData.regime_restricted_deductions.length})</summary>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "8px", marginTop: "10px" }}>
            {deductionData.regime_restricted_deductions.map((item) => <div key={item.section} style={{ ...cardStyle, padding: "12px", opacity: 0.7 }}><strong style={{ fontSize: "12px" }}>{safeText(item.section)} · {safeText(item.name)}</strong><div style={{ fontSize: "10px", marginTop: "5px" }}>Not available under the selected regime framework</div></div>)}
          </div>
        </details>
      )}
    </div>
  );

  const updateSalaryProfile = (key, value) => {
    setSalaryProfile((current) => {
      const next = { ...current, [key]: value };
      if (key === "gross_salary") {
        const gross = Math.max(0, Number(value) || 0);
        const basic = Math.round(gross * 0.40 * 100) / 100;
        const hra = Math.round(basic * 0.40 * 100) / 100;
        next.basic_salary = String(basic);
        next.hra = String(hra);
        next.other_allowances = String(Math.round((gross - basic - hra - (Number(next.da) || 0)) * 100) / 100);
        setHraInputs((hraCurrent) => ({ ...hraCurrent, gross_salary: String(gross), annual_basic_salary: String(basic), annual_hra_received: String(hra), annual_da_forming_retirement_benefits: String(Number(next.da) || 0) }));
      } else if (["basic_salary", "hra", "da", "other_allowances"].includes(key)) {
        const gross = Math.max(0, Number(next.gross_salary) || 0);
        const basic = Math.max(0, Number(next.basic_salary) || 0);
        const hra = Math.max(0, Number(next.hra) || 0);
        const da = Math.max(0, Number(next.da) || 0);
        if (key !== "other_allowances") next.other_allowances = String(Math.round((gross - basic - hra - da) * 100) / 100);
        setHraInputs((hraCurrent) => ({ ...hraCurrent, gross_salary: String(gross), annual_basic_salary: String(basic), annual_hra_received: String(hra), annual_da_forming_retirement_benefits: String(da) }));
      }
      return next;
    });
    setSalaryComponentsTouched(true);
  };

  const renderHraCalculator = () => {
    const inputStyle = { width: "100%", boxSizing: "border-box", padding: "10px 11px", borderRadius: "9px", border: "1px solid rgba(255,255,255,0.14)", background: "rgba(12,16,30,0.72)", color: "inherit" };
    const fieldStyle = { display: "grid", gap: "7px", color: "rgba(255,255,255,0.72)", fontSize: "12px" };
    const fields = [
      ["gross_salary", "Annual gross salary (₹) — before deductions", "number", true],
      ["annual_basic_salary", "Annual basic salary (₹)", "number", true],
      ["annual_da_forming_retirement_benefits", "Eligible DA (₹)", "number", false],
      ["annual_commission_on_turnover_at_fixed_percentage", "Eligible fixed-percentage commission (₹)", "number", false],
      ["annual_hra_received", "Annual HRA received (₹)", "number", true],
      ["annual_rent_paid", "Annual rent paid (₹)", "number", true],
    ];
    return <section className="tax-hra-panel" style={panelStyle}>
      <header className="tax-hra-heading">
      <h3 style={{ marginTop: 0 }}>HRA exemption calculator</h3>
      <p style={{ color: "rgba(255,255,255,0.62)", fontSize: "13px", lineHeight: 1.7 }}>Calculate the potential exemption under section 10(13A). To connect salary to the taxable-income engine, enter gross salary from your salary statement/Form 16 and save a salary-source evidence reference below. Bank deposits are not treated as gross salary.</p>
      </header>
      {taxRegime !== "old" && <div role="status" style={{ padding: "12px 14px", borderRadius: "10px", marginBottom: "14px", background: "rgba(245,158,11,0.10)", border: "1px solid rgba(245,158,11,0.28)", color: "#fcd34d", fontSize: "12px" }}>Select Old Regime above to calculate HRA exemption. HRA exemption is not available under the New Regime.</div>}
      <section className="tax-hra-salary-section" style={{ ...panelStyle, marginBottom: "16px", border: "1px solid rgba(168,85,247,0.24)" }}>
        <h3 style={{ marginTop: 0 }}>Salary components</h3>
        <p style={{ color: "rgba(255,255,255,0.58)", fontSize: "12px", lineHeight: 1.6 }}>Enter employer and gross salary. A suggested breakdown is generated using editable defaults (Basic 40% of gross; HRA 40% of Basic; DA 0%; other allowances balance). These percentages are not statutory Indian salary limits. Adjust figures to match actual payroll/Form 16. The actual net salary remains the existing Money income transaction; this form does not create or change a transaction.</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "12px" }}>
          {[["employer_name", "Company / employer name", "text"], ["gross_salary", "Gross salary (₹)", "number"], ["basic_salary", "Basic salary (₹)", "number"], ["hra", "HRA received (₹)", "number"], ["da", "DA (₹)", "number"], ["other_allowances", "Other allowances (₹)", "number"], ["employee_pf", "Employee PF (₹)", "number"], ["professional_tax", "Professional tax (₹)", "number"], ["tds", "TDS (₹)", "number"]].map(([key, label, type]) => <label key={key} style={fieldStyle}>{label}<input type={type} min={type === "number" ? "0" : undefined} step={type === "number" ? "0.01" : undefined} value={salaryProfile[key]} onChange={(event) => updateSalaryProfile(key, event.target.value)} placeholder={key === "employer_name" ? "Employer name" : "0.00"} style={inputStyle} /></label>)}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "10px", marginTop: "14px" }}>
          <div style={cardStyle}><div style={labelStyle}>Component total</div><div style={valueStyle}>{formatCurrency(["basic_salary", "hra", "da", "other_allowances"].reduce((sum, key) => sum + (Number(salaryProfile[key]) || 0), 0))}</div></div>
          <div style={cardStyle}><div style={labelStyle}>Gross less components</div><div style={valueStyle}>{formatCurrency((Number(salaryProfile.gross_salary) || 0) - ["basic_salary", "hra", "da", "other_allowances"].reduce((sum, key) => sum + (Number(salaryProfile[key]) || 0), 0))}</div></div>
          <div style={cardStyle}><div style={labelStyle}>Gross less entered deductions</div><div style={valueStyle}>{formatCurrency((Number(salaryProfile.gross_salary) || 0) - ["employee_pf", "professional_tax", "tds"].reduce((sum, key) => sum + (Number(salaryProfile[key]) || 0), 0))}</div></div>
        </div>
        <p style={{ color: "rgba(255,255,255,0.48)", fontSize: "10px", lineHeight: 1.5, marginBottom: 0 }}>PF, professional tax and TDS are not automatically assumed from gross salary because eligibility and rates depend on applicable rules and payroll facts. Enter verified amounts. Unreconciled differences are shown, not silently classified as deductions. Actual salary received must remain the amount of the existing Money income transaction; this tax panel does not create or change that transaction.</p>
      </section>
      <form className="tax-hra-form" onSubmit={calculateHra} style={{ display: "grid", gap: "14px" }}>
        <section className="tax-hra-rent-section">
          <h4>Rent and salary details</h4>
          <p>Enter annual figures from your salary and rent records. Required fields are marked by the browser.</p>
        <div className="tax-hra-fields" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "12px" }}>
          {fields.map(([key, label, type, required]) => <label key={key} style={fieldStyle}>{label}<input aria-label={label} type={type} min={type === "number" ? "0" : undefined} step={type === "number" ? "0.01" : undefined} required={required} value={hraInputs[key]} onChange={(event) => { const value = event.target.value; setHraInputs((current) => ({ ...current, [key]: value })); const profileKey = ({ gross_salary: "gross_salary", annual_basic_salary: "basic_salary", annual_da_forming_retirement_benefits: "da", annual_hra_received: "hra" })[key]; if (profileKey) setSalaryProfile((current) => ({ ...current, [profileKey]: value })); }} style={inputStyle} /></label>)}
          <label style={{ ...fieldStyle, display: "flex", alignItems: "center", flexDirection: "row", gap: "9px" }}><input type="checkbox" checked={hraInputs.accommodation_owned_by_taxpayer} onChange={(event) => { setHraInputs((current) => ({ ...current, accommodation_owned_by_taxpayer: event.target.checked })); setHraResult(null); }} /> I own the accommodation for which I am entering rent</label>
          <label style={{ ...fieldStyle, display: "flex", alignItems: "center", flexDirection: "row", gap: "9px" }}><input type="checkbox" checked={hraInputs.rent_actually_paid} onChange={(event) => { setHraInputs((current) => ({ ...current, rent_actually_paid: event.target.checked })); setHraResult(null); }} /> I confirm that rent was actually paid for this period</label>
          <label style={fieldStyle}>City of residence (search or type)
            <input aria-label="City of residence" list="hra-city-suggestions" type="text" minLength={2} maxLength={100} required value={hraInputs.city} placeholder="Search city or choose Other City" onChange={(event) => { const city = event.target.value; const normalized = city.trim().toLocaleLowerCase(); const known = [...hraCityCatalog.metro, ...hraCityCatalog.non_metro].find((item) => item.name.toLocaleLowerCase() === normalized); setHraInputs((current) => ({ ...current, city, city_classification: known?.classification || "non_metro" })); setHraResult(null); }} style={inputStyle} />
            <datalist id="hra-city-suggestions">
              {hraCityCatalog.metro.map((item) => <option key={item.name} value={item.name} label="Metro" />)}
              {hraCityCatalog.non_metro.map((item) => <option key={item.name} value={item.name} label="Non-metro" />)}
            </datalist>
            <span style={{ color: "rgba(255,255,255,0.48)", fontSize: "10px" }}>Choose a suggestion or type an unlisted city. Unlisted cities default to Non-metro.</span>
            {hraCityCatalogError && <span role="status" style={{ color: "#fbbf24", fontSize: "10px" }}>{hraCityCatalogError}</span>}
          </label>
          <div className="tax-hra-classification" style={fieldStyle}>Tax-rule classification
            <div aria-live="polite" style={{ ...inputStyle, minHeight: "40px", display: "flex", alignItems: "center", borderColor: hraInputs.city.trim() ? "rgba(34,197,94,0.28)" : "rgba(255,255,255,0.14)" }}>
              {hraInputs.city.trim() ? (hraInputs.city_classification === "metro" ? "Metro · 50% salary limit" : "Non-metro · 40% salary limit") : "Select or enter a city"}
            </div>
            <span style={{ color: "rgba(255,255,255,0.48)", fontSize: "10px" }}>Classification is determined by the backend tax-rules mapping; it cannot be selected manually.</span>
          </div>
        </div>
        </section>
        <div className="tax-hra-actions" style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
          <button type="submit" className="primary-button" disabled={hraLoading || taxRegime !== "old"}>{hraLoading ? "Calculating…" : "Calculate HRA exemption"}</button>
          <button type="button" className="secondary-button" onClick={() => { setHraInputs({ gross_salary: "", annual_basic_salary: "", annual_da_forming_retirement_benefits: "0", annual_commission_on_turnover_at_fixed_percentage: "0", annual_hra_received: "", annual_rent_paid: "", city: "", city_classification: "non_metro" }); setHraResult(null); setHraError(""); setHraSalaryMessage(""); setHraSalaryError(""); }}>Clear inputs</button>
        </div>
      </form>
      {hraError && <div role="alert" style={{ marginTop: "14px", padding: "12px", borderRadius: "10px", color: "#fca5a5", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)", fontSize: "12px" }}>{hraError}</div>}
      {hraResult && <div aria-live="polite" style={{ marginTop: "18px", display: "grid", gap: "12px" }}>
        <div style={{ ...cardStyle, borderColor: "rgba(34,197,94,0.25)" }}><div style={labelStyle}>Indicative HRA exemption</div><div style={valueStyle}>{formatCurrency(hraResult.calculated_exemption)}</div><div style={{ color: "rgba(255,255,255,0.52)", fontSize: "11px", marginTop: "8px" }}>FY {safeText(hraResult.financial_year)} · Old Regime · Estimate only</div></div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "10px" }}>
          {Object.entries(hraResult.limits || {}).map(([key, value]) => <div key={key} style={{ ...cardStyle, padding: "13px" }}><div style={labelStyle}>{key.replaceAll("_", " ")}</div><div style={{ fontWeight: 750, marginTop: "7px" }}>{formatCurrency(value)}</div></div>)}
        </div>
        <p style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", lineHeight: 1.6, marginBottom: 0 }}>{safeText(hraResult.verification_notice, "Verify salary components, residence and rent evidence before filing.")} The calculator result alone does not change taxable income.</p>
        <label style={fieldStyle}>Salary statement / Form 16 evidence reference
          <input aria-label="Salary statement or Form 16 evidence reference" type="text" maxLength={2000} value={hraSalaryEvidence} onChange={(event) => setHraSalaryEvidence(event.target.value)} placeholder="e.g. Form 16 FY 2026-27, employer statement reference" style={inputStyle} />
          <span style={{ color: "rgba(255,255,255,0.48)", fontSize: "10px" }}>Your confirmation marks this salary record verified; the app does not inspect the document.</span>
        </label>
        <label style={fieldStyle}>Separate HRA / rent evidence reference
          <input aria-label="HRA rent evidence reference" type="text" maxLength={2000} value={hraRentEvidence} onChange={(event) => setHraRentEvidence(event.target.value)} placeholder="e.g. rent receipts and rental agreement reference" style={inputStyle} />
          <span style={{ color: "rgba(255,255,255,0.48)", fontSize: "10px" }}>Keep this separate from the salary statement reference. Verification records your confirmation; the app does not inspect documents.</span>
        </label>
        <button type="button" className="primary-button" disabled={hraSalarySaving || taxRegime !== "old"} onClick={saveAndVerifyHraSalary}>{hraSalarySaving ? "Saving salary and HRA claim…" : "Save salary & verify HRA claim"}</button>
        {hraSalaryError && <div role="alert" style={{ color: "#fca5a5", fontSize: "12px" }}>{hraSalaryError}</div>}
        {hraSalaryMessage && <div role="status" style={{ color: "#86efac", fontSize: "12px" }}>{hraSalaryMessage}</div>}
      </div>}
      <div style={{ marginTop: "18px", display: "grid", gap: "8px" }}>
        <button type="button" className="secondary-button" disabled={hraSalarySaving} onClick={undoHraSalaryVerification}>Undo verification (salary &amp; HRA)</button>
        {!hraResult && hraSalaryError && <div role="alert" style={{ color: "#fca5a5", fontSize: "12px" }}>{hraSalaryError}</div>}
        {!hraResult && hraSalaryMessage && <div role="status" style={{ color: "#86efac", fontSize: "12px" }}>{hraSalaryMessage}</div>}
      </div>
    </section>;
  };

  const renderTaxCalculation = () => (
    <>
      <div className="tax-calculation-liability" style={panelStyle}>
        <h3 style={{ marginTop: 0 }}>Final tax liability estimate</h3>
        <p style={{ color: "rgba(255,255,255,0.58)", fontSize: "12px", lineHeight: 1.6 }}>
          This uses the existing liability engine for the selected tax year and taxpayer inputs. Missing income heads, unverified claims, capital-gains eligibility or tax credits can keep the result provisional.
        </p>
        {finalLiabilityData?.status === "rules_not_configured" || finalLiabilityData?.status === "unavailable" ? (
          <div style={{ color: "#fbbf24", fontSize: "12px" }}>{safeText(finalLiabilityData?.message, "Final liability is not available for these settings.")}</div>
        ) : finalLiabilityData ? (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "12px" }}>
              <div style={cardStyle}><div style={labelStyle}>Tax + cess</div><div style={valueStyle}>{formatCurrency(finalLiabilityData?.final_tax?.total_tax_payable)}</div></div>
              <div style={cardStyle}><div style={labelStyle}>Tax credits</div><div style={valueStyle}>{formatCurrency(finalLiabilityData?.tax_credits?.total)}</div></div>
              <div style={cardStyle}><div style={labelStyle}>Balance payable / refund</div><div style={valueStyle}>{formatCurrency(finalLiabilityData?.balance_after_credits?.amount)}</div></div>
            </div>
            <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px", marginBottom: 0 }}>Engine status: {safeText(finalLiabilityData?.liability_status ?? finalLiabilityData?.engine_status, "Review required")}. Verify all warnings and source data before relying on the estimate.</p>
            {Array.isArray(finalLiabilityData?.missing_data?.income_heads) && finalLiabilityData.missing_data.income_heads.length > 0 && (
              <div style={{ marginTop: "12px", padding: "12px", borderRadius: "10px", background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.25)", color: "#fcd34d", fontSize: "12px", lineHeight: 1.6 }}>
                <strong>Incomplete income data:</strong> {finalLiabilityData.missing_data.income_heads.map(safeText).join(", ")}. These heads are unavailable, so this is not a final filing amount.
              </div>
            )}
            {Array.isArray(finalLiabilityData?.capital_gains_review?.reasons) && finalLiabilityData.capital_gains_review.reasons.length > 0 && (
              <div style={{ marginTop: "10px", color: "#fcd34d", fontSize: "12px", lineHeight: 1.6 }}>
                <strong>Capital-gains review required:</strong> {finalLiabilityData.capital_gains_review.reasons.map(safeText).join("; ")}
              </div>
            )}
            {finalLiabilityData?.scope?.final_liability_complete === false && (
              <div style={{ marginTop: "10px", color: "#fca5a5", fontSize: "12px" }}>The engine explicitly marks this result incomplete. Do not use it as a final ITR liability without resolving the missing data and review flags.</div>
            )}
          </>
        ) : <div style={{ color: "rgba(255,255,255,0.5)", fontSize: "12px" }}>Choose a regime to load the estimate.</div>}
      </div>
      <div className="tax-calculation-settings" style={panelStyle}>
        <h3 style={{ marginTop: 0 }}>Calculation settings</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", alignItems: "end" }}>
          <label style={{ display: "grid", gap: "7px", fontSize: "12px", color: "rgba(255,255,255,0.65)" }}>Financial year<StyledSelect value={financialYear} onChange={e => setFinancialYear(e.target.value)}><option value="2026-27">2026-27</option></StyledSelect></label>
          <label style={{ display: "grid", gap: "7px", fontSize: "12px", color: "rgba(255,255,255,0.65)" }}>Tax regime framework<StyledSelect value={taxRegime} onChange={e => setTaxRegime(e.target.value)}><option value="new">New regime</option><option value="old">Old regime</option></StyledSelect></label>
          <label style={{ display: "grid", gap: "7px", fontSize: "12px", color: "rgba(255,255,255,0.65)" }}>Residential status<StyledSelect value={residentialStatus} onChange={e => setResidentialStatus(e.target.value)}><option value="resident">Resident</option><option value="non_resident">Non-resident</option></StyledSelect></label>
          <label style={{ display: "grid", gap: "7px", fontSize: "12px", color: "rgba(255,255,255,0.65)" }}>Age group<StyledSelect value={ageCategory} onChange={e => setAgeCategory(e.target.value)}><option value="under_60">Under 60</option><option value="60_to_79">60–79</option><option value="80_plus">80+</option></StyledSelect></label>
          <label style={{ display: "flex", alignItems: "center", gap: "9px", fontSize: "12px", color: "rgba(255,255,255,0.65)", minHeight: "42px" }}><input type="checkbox" checked={sttConfirmed} onChange={e => setSttConfirmed(e.target.checked)} /> Confirm applicable STT condition for STCG</label>
          <button type="button" className="primary-button" onClick={loadTaxData} disabled={loading}>{loading ? "Calculating..." : "Refresh / Calculate"}</button>
        </div>
      </div>
      <div className="tax-calculation-breakdown" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
        <div style={cardStyle}><div style={labelStyle}>STCG tax</div><div style={valueStyle}>{formatCurrency(tax?.stcg?.tax)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>{tax?.stcg?.status || "Awaiting calculation"}</div></div>
        <div style={cardStyle}><div style={labelStyle}>LTCG tax</div><div style={valueStyle}>{formatCurrency(tax?.ltcg?.tax)}</div><div style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px", marginTop: "8px" }}>Taxable gain: {formatCurrency(tax?.ltcg?.taxable_gain)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Base tax</div><div style={valueStyle}>{formatCurrency(taxSummary.base_tax)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Health & education cess</div><div style={valueStyle}>{formatCurrency(taxSummary.health_education_cess)}</div></div>
        <div style={cardStyle}><div style={labelStyle}>Total calculated tax + cess</div><div style={valueStyle}>{formatCurrency(taxSummary.tax_plus_cess)}</div></div>
      </div>
      <div className="tax-calculation-scope" style={{ ...panelStyle, color: "rgba(255,255,255,0.6)", fontSize: "12px", lineHeight: 1.7 }}>This tax-calculation endpoint estimates tax on qualifying realised capital gains only. It does not calculate complete ITR liability, slab-rate tax, surcharge, rebate or all deductions. The selected tax regime is used by the provisional taxable-income endpoint and does not convert this special-rate calculation into a complete tax assessment.</div>
      {renderTaxCredits()}
    </>
  );


  const printTaxSummary = () => {
    const esc = (value) => String(value == null || value === "" ? "Unavailable" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    const money = (value) => value == null || value === "" ? "Unavailable" : esc(formatCurrency(value));
    const income = reportData?.income || {};
    const liability = reportData?.tax_liability || {};
    const taxpayer = reportData?.taxpayer || {};
    const rows = [
      ["Salary", income.salary?.taxable_amount ?? income.salary?.amount],
      ["House property", income.house_property?.taxable_amount ?? income.house_property?.amount],
      ["Business / profession", income.business_or_profession?.taxable_amount ?? income.business_or_profession?.amount],
      ["Other sources", income.other_sources?.taxable_amount ?? income.other_sources?.amount],
      ["Capital gains", reportData?.capital_gains?.total_taxable_gain],
      ["Verified deductions", deductions?.verified_amount],
      ["Tax payable (reported)", liability.total_tax_payable],
    ];
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>Financial OS — Tax Summary</title>
      <style>
        @page { size: A4; margin: 14mm; }
        body { font: 12px Arial, sans-serif; color: #172033; margin: 0; }
        h1 { font-size: 20px; margin: 0 0 5px; } .muted { color: #5b6475; }
        .meta { margin: 0 0 18px; line-height: 1.6; }
        table { border-collapse: collapse; width: 100%; margin: 14px 0; }
        th, td { padding: 9px; border-bottom: 1px solid #dce1e8; text-align: left; }
        th { background: #f2f4f8; } td:last-child { text-align: right; }
        .note { font-size: 10px; line-height: 1.6; color: #596273; margin-top: 20px; }
      </style></head><body>
      <h1>Financial OS — Tax Summary</h1>
      <p class="meta muted">Financial year: ${esc(financialYear)}<br>Regime: ${esc((taxpayer.regime || taxRegime) === "old" ? "Old regime" : "New regime")}<br>Assessment year: ${esc(reportData?.assessment_year || "Unavailable")}</p>
      <table><thead><tr><th>Summary item</th><th>Amount</th></tr></thead><tbody>
      ${rows.map(([label, value]) => `<tr><td>${esc(label)}</td><td>${money(value)}</td></tr>`).join("")}
      </tbody></table>
      <p class="note">Preliminary summary from information currently available in Financial OS. This is not a filed return or tax advice. Missing or unavailable amounts must be checked against source documents before filing. Verified deduction claims remain subject to eligibility and applicable tax rules.</p>
      </body></html>`;
    const w = window.open("", "_blank");
    if (!w) { window.alert("Please allow pop-ups for this site, then tap Print / save as PDF again."); return; }
    w.document.open();
    w.document.write(html);
    w.document.close();
    w.focus();
    setTimeout(() => { try { w.print(); } catch (err) { /* user can print from the browser menu */ } }, 350);
  };

  const renderReport = () => (
    <div style={panelStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
        <div><h3 style={{ margin: "0 0 6px" }}>ITR readiness report</h3><p style={{ color: "rgba(255,255,255,0.5)", fontSize: "12px", margin: 0 }}>Financial year {financialYear} · {taxRegime === "new" ? "New" : "Old"} regime framework</p></div>
        <button className="secondary-button" type="button" onClick={loadTaxData} disabled={loading}>{loading ? "Refreshing..." : "Refresh report"}</button><button className="secondary-button" type="button" onClick={printTaxSummary}>Print / save as PDF</button>
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
            <h4 style={{ margin: "0 0 12px" }}>Old vs New regime comparison</h4>
            <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "12px", lineHeight: 1.6, marginTop: 0 }}>Both estimates use the current report engine and the same source data. Because some income heads, verified deductions and tax credits are not connected, this is an indicative comparison—not a final regime recommendation.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
              <div style={cardStyle}><div style={smallLabel}>Old regime · calculated tax</div><div style={reportValue}>{safeAmount((taxpayer.regime === "old" ? reportData : comparisonReportData)?.tax_liability?.total_tax_payable)}</div><div style={{ color: "rgba(255,255,255,0.5)", fontSize: "10px", marginTop: "5px" }}>{taxpayer.regime === "old" ? "Selected regime" : "Alternative estimate"}</div></div>
              <div style={cardStyle}><div style={smallLabel}>New regime · calculated tax</div><div style={reportValue}>{safeAmount((taxpayer.regime === "new" ? reportData : comparisonReportData)?.tax_liability?.total_tax_payable)}</div><div style={{ color: "rgba(255,255,255,0.5)", fontSize: "10px", marginTop: "5px" }}>{taxpayer.regime === "new" ? "Selected regime" : "Alternative estimate"}</div></div>
              <div style={cardStyle}><div style={smallLabel}>Difference</div><div style={reportValue}>{(() => { const oldTax = Number((taxpayer.regime === "old" ? reportData : comparisonReportData)?.tax_liability?.total_tax_payable); const newTax = Number((taxpayer.regime === "new" ? reportData : comparisonReportData)?.tax_liability?.total_tax_payable); return Number.isFinite(oldTax) && Number.isFinite(newTax) ? formatCurrency(Math.abs(oldTax - newTax)) : "Unavailable"; })()}</div><div style={{ color: "rgba(255,255,255,0.5)", fontSize: "10px", marginTop: "5px" }}>Before missing data and credits are resolved</div></div>
            </div>
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
            <h4 style={{ margin: "0 0 12px" }}>ITR form preparation</h4>
            <p style={{ color: "rgba(255,255,255,0.58)", fontSize: "12px", lineHeight: 1.6, marginTop: 0 }}>These are preliminary form guides, not a final eligibility decision or electronic filing. Eligibility requires complete income, residency, asset and business details.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "10px" }}>
              {Object.entries(reportData.itr_forms || {}).filter(([key]) => ["ITR-1", "ITR-2", "ITR-3"].includes(key)).map(([formName, info]) => <div key={formName} style={cardStyle}><div style={smallLabel}>{formName}</div><div style={{ ...reportValue, fontSize: "13px" }}>{safeText(info.status)}</div><div style={{ color: "rgba(255,255,255,0.58)", fontSize: "11px", lineHeight: 1.55, marginTop: "7px" }}>{safeText(info.note)}</div></div>)}
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
            <h4 style={{ margin: "0 0 12px" }}>Money transaction classification checks</h4>
            <p style={{ color: "rgba(255,255,255,0.56)", fontSize: "12px", lineHeight: 1.6, marginTop: 0 }}>Loan proceeds identified from transaction category or description are excluded from taxable income. Keyword matches and conflicts are review aids; check them before relying on the report.</p>
            {(() => {
              const excludedLoans = Array.isArray(reportIncome.excluded_loan_proceeds) ? reportIncome.excluded_loan_proceeds : [];
              const conflicts = Array.isArray(reportIncome.classification_review) ? reportIncome.classification_review : [];
              return <>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "10px" }}>
                  <div style={cardStyle}><div style={smallLabel}>Loan proceeds excluded</div><div style={reportValue}>{excludedLoans.length}</div></div>
                  <div style={cardStyle}><div style={smallLabel}>Classification conflicts</div><div style={reportValue}>{conflicts.length}</div></div>
                </div>
                {excludedLoans.length > 0 && <div style={{ overflowX: "auto", marginTop: "12px" }}><table style={{ width: "100%", borderCollapse: "collapse", minWidth: "420px" }}><thead><tr>{["Date", "Category", "Description", "Excluded amount"].map(label => <th key={label} style={{ ...tableCellStyle, color: "rgba(255,255,255,0.55)" }}>{label}</th>)}</tr></thead><tbody>{excludedLoans.map((row) => <tr key={row.transaction_id}><td style={tableCellStyle}>{safeText(row.date)}</td><td style={tableCellStyle}>{safeText(row.category)}</td><td style={tableCellStyle}>{safeText(row.description)}</td><td style={tableCellStyle}>{safeAmount(row.amount)}</td></tr>)}</tbody></table></div>}
                {conflicts.length > 0 && <div style={{ overflowX: "auto", marginTop: "12px" }}><table style={{ width: "100%", borderCollapse: "collapse", minWidth: "420px" }}><thead><tr>{["Date", "Current type", "Description", "Suggested head"].map(label => <th key={label} style={{ ...tableCellStyle, color: "rgba(255,255,255,0.55)" }}>{label}</th>)}</tr></thead><tbody>{conflicts.map((row) => <tr key={row.transaction_id}><td style={tableCellStyle}>{safeText(row.date)}</td><td style={tableCellStyle}>{safeText(row.type)}</td><td style={tableCellStyle}>{safeText(row.description)}</td><td style={tableCellStyle}>{safeText(row.suggested_head)}</td></tr>)}</tbody></table></div>}
                {excludedLoans.length === 0 && conflicts.length === 0 && <p style={{ color: "rgba(255,255,255,0.48)", fontSize: "12px", marginBottom: 0 }}>No loan-proceeds exclusions or classification conflicts were detected by the current keyword checks.</p>}
              </>;
            })()}
          </div>
          <div style={panelStyle}>
            <h4 style={{ margin: "0 0 12px" }}>Capital gains summary</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))", gap: "10px" }}>
              {[["STCG before set-off", reportGains.stcg_before_setoff], ["LTCG before set-off", reportGains.ltcg_before_setoff], ["STCG after set-off", reportGains.stcg_after_setoff], ["LTCG after set-off", reportGains.ltcg_after_setoff], ["Unclassified gain", reportGains.unclassified_gain]].map(([label, value]) => <div key={label} style={cardStyle}><div style={smallLabel}>{label}</div><div style={reportValue}>{safeAmount(value)}</div></div>)}
            </div>
            <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "12px", marginBottom: 0 }}>Sales reported: {Number(reportGains.sales_count ?? reportSales.length)}</p>
            {reportSales.length > 0 && <div style={{ overflowX: "auto", marginTop: "12px" }}><table style={{ width: "100%", borderCollapse: "collapse", minWidth: "460px" }}><thead><tr>{["Investment", "Sale date", "Quantity", "Gain", "Class"].map(label => <th key={label} style={{ ...tableCellStyle, color: "rgba(255,255,255,0.55)" }}>{label}</th>)}</tr></thead><tbody>{reportSales.map((sale, index) => <tr key={sale.sale_transaction_id || `${sale.investment_id || "sale"}-${index}`}><td style={tableCellStyle}>{sale.name || sale.symbol || `Investment ${sale.investment_id ?? ""}`}</td><td style={tableCellStyle}>{sale.sale_date || "—"}</td><td style={tableCellStyle}>{sale.quantity ?? "—"}</td><td style={tableCellStyle}>{safeAmount(sale.gain)}</td><td style={tableCellStyle}>{sale.classification || "—"}</td></tr>)}</tbody></table></div>}
          </div>
          <div style={panelStyle}>
            <h4 style={{ margin: "0 0 12px" }}>Tax liability and credits</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "10px" }}>
              {[["Normal slab tax", reportData.tax_liability?.normal_slab_tax], ["Special-rate tax", reportData.tax_liability?.special_rate_tax], ["Rebate", reportData.tax_liability?.rebate_87a], ["Surcharge", reportData.tax_liability?.surcharge], ["Cess", reportData.tax_liability?.cess], ["Calculated tax", reportData.tax_liability?.total_tax_payable], ["TDS credit", reportData.tax_credits?.tds], ["Advance tax", reportData.tax_credits?.advance_tax], ["Self-assessment tax", reportData.tax_credits?.self_assessment_tax], ["Balance payable / refund", reportData.tax_credits?.balance_payable_or_refund]].map(([label, value]) => <div key={label} style={cardStyle}><div style={smallLabel}>{label}</div><div style={reportValue}>{safeAmount(value)}</div></div>)}
            </div>
            <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "11px", lineHeight: 1.6, marginBottom: 0, marginTop: "12px" }}>Tax credits are shown as unavailable until TDS certificates, advance-tax and self-assessment payment records are connected. “Calculated tax” is provisional while income heads and deductions are incomplete.</p>
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

  // First-entry gate: select the tax regime before loading or displaying tax results.
  if (!taxRegime) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "18px", maxWidth: "900px", margin: "0 auto", padding: "24px 0" }}>
        <section className="glass-card" style={{ padding: "24px", borderRadius: "18px" }}>
          <p className="card-label">FINANCIAL OS / TAX SETUP</p>
          <h2 style={{ margin: "6px 0 8px", fontSize: "28px", fontWeight: 800 }}>Choose your tax regime</h2>
          <p style={{ color: "rgba(255,255,255,0.65)", fontSize: "14px", lineHeight: 1.7, marginTop: 0 }}>
            Choose a regime to begin. The Tax Centre will use this selection for its current calculations. You can change it later and refresh the report.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px", marginTop: "18px" }}>
            <button type="button" onClick={() => setTaxRegime("new")} className="secondary-button" style={{ padding: "18px", textAlign: "left", whiteSpace: "normal" }}>
              <strong style={{ display: "block", fontSize: "16px", marginBottom: "8px" }}>New Tax Regime</strong>
              <span style={{ display: "block", fontSize: "12px", lineHeight: 1.6, opacity: 0.8 }}>Lower slab rates with fewer deductions and exemptions.</span>
            </button>
            <button type="button" onClick={() => setTaxRegime("old")} className="secondary-button" style={{ padding: "18px", textAlign: "left", whiteSpace: "normal" }}>
              <strong style={{ display: "block", fontSize: "16px", marginBottom: "8px" }}>Old Tax Regime</strong>
              <span style={{ display: "block", fontSize: "12px", lineHeight: 1.6, opacity: 0.8 }}>Higher slab rates with eligible deductions and exemptions.</span>
            </button>
          </div>
          <p style={{ color: "rgba(255,255,255,0.45)", fontSize: "11px", lineHeight: 1.6, marginBottom: 0, marginTop: "16px" }}>
            This selection starts the review only; it does not elect a regime with the Income Tax Department or file a return.
          </p>
        </section>
      </div>
    );
  }

  return (
    <div className="tax-centre" style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
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
        {section === "HRA Calculator" && renderHraCalculator()}
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
// Pure, deterministic technical-indicator calculations over historical OHLCV candles.
function calculateTechnicalIndicators(rows) {
  const numeric = (row, key) => {
    const raw = row?.[key];
    if (raw === null || raw === undefined || raw === "") return null;
    const value = Number(raw);
    return Number.isFinite(value) ? value : null;
  };
  const closes = rows.map((row) => numeric(row, "close")).filter((value) => value !== null && value > 0);
  const validRows = rows.filter((row) => numeric(row, "close") > 0);
  const last = (values) => values.length ? values[values.length - 1] : null;
  const sma = (values, period) => values.length >= period ? values.slice(-period).reduce((sum, value) => sum + value, 0) / period : null;
  const emaSeries = (values, period) => {
    if (values.length < period) return [];
    const multiplier = 2 / (period + 1);
    const series = [values.slice(0, period).reduce((sum, value) => sum + value, 0) / period];
    for (let i = period; i < values.length; i++) series.push(values[i] * multiplier + series[series.length - 1] * (1 - multiplier));
    return series;
  };
  const rsiWilder = (values, period = 14) => {
    if (values.length <= period) return null;
    let gain = 0, loss = 0;
    for (let i = 1; i <= period; i++) {
      const delta = values[i] - values[i - 1];
      gain += Math.max(delta, 0); loss += Math.max(-delta, 0);
    }
    let avgGain = gain / period, avgLoss = loss / period;
    for (let i = period + 1; i < values.length; i++) {
      const delta = values[i] - values[i - 1];
      avgGain = (avgGain * (period - 1) + Math.max(delta, 0)) / period;
      avgLoss = (avgLoss * (period - 1) + Math.max(-delta, 0)) / period;
    }
    if (avgGain === 0 && avgLoss === 0) return 50;
    if (avgLoss === 0) return 100;
    return 100 - 100 / (1 + avgGain / avgLoss);
  };
  const sma20 = sma(closes, 20);
  const sma50 = sma(closes, 50);
  const ema12Series = emaSeries(closes, 12);
  const ema26Series = emaSeries(closes, 26);
  const ema12 = last(ema12Series), ema26 = last(ema26Series);
  const macdSeries = [];
  if (ema12Series.length && ema26Series.length) {
    const offset = 26 - 12;
    for (let i = 0; i < ema26Series.length; i++) macdSeries.push(ema12Series[i + offset] - ema26Series[i]);
  }
  const macdSignalSeries = emaSeries(macdSeries, 9);
  const macd = last(macdSeries), macdSignal = last(macdSignalSeries);
  const macdHistogram = macd != null && macdSignal != null ? macd - macdSignal : null;
  const last20 = closes.slice(-20);
  const bollingerMiddle = sma20;
  const bollingerStd = last20.length === 20 && sma20 != null
    ? Math.sqrt(last20.reduce((sum, value) => sum + (value - sma20) ** 2, 0) / 20) : null;
  const bollingerUpper = bollingerMiddle != null && bollingerStd != null ? bollingerMiddle + 2 * bollingerStd : null;
  const bollingerLower = bollingerMiddle != null && bollingerStd != null ? bollingerMiddle - 2 * bollingerStd : null;
  const typicals = validRows.map((row) => {
    const high = numeric(row, "high"), low = numeric(row, "low"), close = numeric(row, "close");
    return high != null && low != null && close != null ? (high + low + close) / 3 : null;
  });
  let volumeSum = 0, typicalVolumeSum = 0;
  validRows.forEach((row, index) => {
    const volume = numeric(row, "volume");
    if (volume != null && volume >= 0 && typicals[index] != null) {
      volumeSum += volume; typicalVolumeSum += typicals[index] * volume;
    }
  });
  const vwap = volumeSum > 0 ? typicalVolumeSum / volumeSum : null;
  const trueRanges = [];
  validRows.forEach((row, index) => {
    const high = numeric(row, "high"), low = numeric(row, "low"), close = numeric(row, "close");
    if (high == null || low == null) return;
    const previousClose = index > 0 ? numeric(validRows[index - 1], "close") : null;
    trueRanges.push(previousClose == null ? high - low : Math.max(high - low, Math.abs(high - previousClose), Math.abs(low - previousClose)));
  });
  const atr14 = trueRanges.length >= 14 ? trueRanges.slice(-14).reduce((sum, value) => sum + value, 0) / 14 : null;
  const stochasticWindow = validRows.slice(-14);
  const stochasticHighs = stochasticWindow.map((row) => numeric(row, "high")).filter((value) => value != null);
  const stochasticLows = stochasticWindow.map((row) => numeric(row, "low")).filter((value) => value != null);
  const currentClose = last(closes);
  const highest14 = stochasticHighs.length === 14 ? Math.max(...stochasticHighs) : null;
  const lowest14 = stochasticLows.length === 14 ? Math.min(...stochasticLows) : null;
  const stochasticK = highest14 != null && lowest14 != null && highest14 !== lowest14 && currentClose != null
    ? (currentClose - lowest14) / (highest14 - lowest14) * 100 : null;
  let obv = 0;
  for (let i = 1; i < validRows.length; i++) {
    const currentClose = numeric(validRows[i], "close"), previousClose = numeric(validRows[i - 1], "close");
    const volume = numeric(validRows[i], "volume");
    if (volume == null || currentClose == null || previousClose == null) continue;
    if (currentClose > previousClose) obv += volume;
    else if (currentClose < previousClose) obv -= volume;
  }
  return { closes, latestClose: last(closes), previousClose: closes.length > 1 ? closes[closes.length - 2] : null,
    sma20, sma50, ema12, ema26, rsi14: rsiWilder(closes), macd, macdSignal, macdHistogram,
    bollingerUpper, bollingerMiddle, bollingerLower, vwap, atr14, stochasticK, obv };
}

// MARKETS WORKSPACE — existing read-only m.Stock/AWS APIs
// ============================================================
function MarketsPage() {
  const API = "https://wealthmanager.duckdns.org";
  const [overview, setOverview] = useState(null);
  const [busy, setBusy] = useState(true);
  const [overviewError, setOverviewError] = useState("");
  const [query, setQuery] = useState("RELIANCE");
  const [results, setResults] = useState([]);
  // Selected instrument controls a focused, single-stock view.
  const [selectedInstrument, setSelectedInstrument] = useState(null);
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [searchWarning, setSearchWarning] = useState("");
  const [quote, setQuote] = useState(null);
  const [quoteBusy, setQuoteBusy] = useState(false);
  const [quoteError, setQuoteError] = useState("");
  const [orderModalSide, setOrderModalSide] = useState("");
  const [orderDraft, setOrderDraft] = useState({ product_type: "DELIVERY", order_type: "MARKET", validity: "DAY", quantity: "1", limit_price: "" });
  const [orderSubmitting, setOrderSubmitting] = useState(false);
  const [orderError, setOrderError] = useState("");
  const [orderSuccess, setOrderSuccess] = useState(null);
  const [orderClientId, setOrderClientId] = useState("");
  // Prevent overlapping refreshes for the same symbol and ignore stale responses
  // when the user switches instruments before a previous request completes.
  const quoteRequestRef = useRef({ activeSymbol: null, inFlightSymbols: new Set() });
  const [updated, setUpdated] = useState("");
  // Historical chart state — uses the existing read-only backend route.
  const [chartSymbol, setChartSymbol] = useState("RELIANCE");
  const [chartExchange, setChartExchange] = useState("NSE");
  const [chartRange, setChartRange] = useState("1M");
  const [chartData, setChartData] = useState([]);
  // Keep a full-year daily dataset for 52-week range metrics even when the visible chart is set to 1M/3M.
  const [yearRangeData, setYearRangeData] = useState([]);
  const yearRangeRequestRef = useRef(0);
  const [chartInfo, setChartInfo] = useState(null);
  const [chartBusy, setChartBusy] = useState(false);
  const [chartError, setChartError] = useState("");
  // Selected-stock research tabs; data is derived from available instrument and chart responses only.
  const [researchTab, setResearchTab] = useState("overview");
  const [expandedMetric, setExpandedMetric] = useState("");
  // Personal watchlist persists in this browser; no backend writes are made.
  const [watchlist, setWatchlist] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("financial-os-market-watchlist") || "[]");
      return Array.isArray(saved) ? saved.filter((item) => item && item.symbol) : [];
    } catch { return []; }
  });
  const [watchlistQuotes, setWatchlistQuotes] = useState({});

  const card = { padding: "16px", borderRadius: "var(--t-radius, 15px)", border: "1px solid var(--finos-border)", background: "var(--t-card-bg, var(--finos-surface))", color: "var(--finos-text)", minWidth: 0, boxSizing: "border-box" };
  const muted = { color: "var(--finos-muted)", fontSize: "12px", lineHeight: 1.6 };
  const input = { width: "100%", boxSizing: "border-box", padding: "11px 12px", borderRadius: "var(--t-radius-sm, 10px)", border: "1px solid var(--finos-border)", background: "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))", color: "var(--finos-text)", fontSize: "13px" };
  const money = (value) => {
    if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return "—";
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(Number(value));
  };
  const createOrderClientId = () => {
    if (globalThis.crypto?.randomUUID) return `finos-${globalThis.crypto.randomUUID()}`;
    return `finos-${Date.now()}-${Math.random().toString(36).slice(2, 14)}`;
  };

  const refresh = async () => {
    setBusy(true); setOverviewError("");
    try {
      const response = await apiFetch(`${API}/api/market-overview/`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Market overview returned ${response.status}`);
      setOverview(data); setUpdated(new Date().toLocaleString("en-IN"));
      if (data?.status === "error") setOverviewError("Market provider returned no usable data. Check the gateway.");
      else if (Array.isArray(data?.errors) && data.errors.length) setOverviewError("Some market sources are unavailable; available results are shown.");
    } catch (e) { setOverviewError(e?.message || "Unable to load market overview."); }
    finally { setBusy(false); }
  };
  // Initial market load. Manual refresh remains available as a fallback.
  useEffect(() => { refresh(); }, []);

  // Auto-refresh the market overview every 30 seconds while this page is visible.
  // This is intentionally slower than quote refresh to reduce provider/API load.
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") refresh();
    }, 30000);
    return () => window.clearInterval(timer);
  }, []);

  const search = async (event) => {
    event.preventDefault();
    if (!query.trim()) { setSearchError("Enter a company name or symbol."); return; }
    setSearchBusy(true); setSearchError(""); setSearchWarning(""); setResults([]); setQuote(null); setQuoteError(""); setSelectedInstrument(null);
    try {
      const response = await apiFetch(`${API}/api/market-search/?query=${encodeURIComponent(query.trim())}&exchange=ALL&limit=20`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Search returned ${response.status}`);
      const rows = Array.isArray(data?.results) ? data.results : [];
      setResults(rows);
      setSearchWarning(typeof data?.warning === "string" ? data.warning : (typeof data?.source?.warning === "string" ? data.source.warning : ""));
      if (!rows.length) setSearchError("No matching instruments returned.");
    } catch (e) { setSearchError(e?.message || "Market search failed."); }
    finally { setSearchBusy(false); }
  };
  // Fetch the selected instrument quote. Keep the previous valid quote visible
  // during background refreshes to avoid flicker on the price card.
  const getQuote = async (symbol, options = {}) => {
    if (!symbol) return;
    const cleanedSymbol = String(symbol).trim().toUpperCase();
    const cleanedExchange = String(options.exchange || "NSE").trim().toUpperCase();
    const qualifiedSymbol = cleanedSymbol.includes(":")
      ? cleanedSymbol
      : `${cleanedExchange}:${cleanedSymbol}`;
    const requestKey = qualifiedSymbol;
    const requestState = quoteRequestRef.current;
    // The 10-second timer must not start another request if the same symbol's
    // previous request is still waiting on the gateway.
    if (requestState.inFlightSymbols.has(requestKey)) return;
    requestState.activeSymbol = requestKey;
    requestState.inFlightSymbols.add(requestKey);
    const initialLoad = options.initial === true;
    if (initialLoad) setQuoteBusy(true);
    setQuoteError("");
    try {
      const response = await apiFetch(`${API}/api/market-quote/?symbol=${encodeURIComponent(cleanedSymbol)}&exchange=${encodeURIComponent(cleanedExchange)}`, { cache: "no-store" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Quote returned ${response.status}`);
      // Only the most recently requested instrument may update the visible card.
      if (quoteRequestRef.current.activeSymbol === requestKey) {
        setQuote(data);
      }
    } catch (e) {
      // A stale request must not overwrite the selected instrument's error state.
      if (quoteRequestRef.current.activeSymbol === requestKey) {
        setQuoteError(e?.message || "Quote refresh failed; showing the last available price if present.");
      }
    } finally {
      requestState.inFlightSymbols.delete(requestKey);
      if (quoteRequestRef.current.activeSymbol === requestKey && initialLoad) setQuoteBusy(false);
    }
  };

  // Automatically refresh selected stock LTP every 10 seconds while visible.
  // Ten seconds is a safer default than 5 seconds for provider rate limits.
  useEffect(() => {
    if (!selectedInstrument?.symbol) return undefined;
    const symbol = selectedInstrument.symbol;
    const marketExchange = selectedInstrument.exchange || "NSE";
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") getQuote(symbol, { exchange: marketExchange });
    }, 10000);
    return () => window.clearInterval(timer);
  }, [selectedInstrument?.symbol, selectedInstrument?.exchange]);

  // Watchlist quote refresh: use the existing quote API, preserve the last
  // successful value during refresh, and limit concurrency to three requests.
  // The quote route supports NSE and BSE, so pass each instrument's real exchange.
  useEffect(() => {
    let cancelled = false;
    let refreshing = false;

    const loadWatchlistQuotes = async () => {
      if (cancelled || refreshing || document.visibilityState !== "visible") return;
      refreshing = true;
      try {
        const eligible = watchlist.filter((item) => ["NSE", "BSE"].includes(String(item.exchange || "NSE").toUpperCase()));
        const unsupported = watchlist.filter((item) => !["NSE", "BSE"].includes(String(item.exchange || "NSE").toUpperCase()));
        if (unsupported.length) {
          setWatchlistQuotes((previous) => {
            const next = { ...previous };
            unsupported.forEach((item) => {
              const key = `${String(item.exchange || "NSE").toUpperCase()}:${String(item.symbol).toUpperCase()}`;
              next[key] = { ...(next[key] || {}), error: "Live quotes are supported only for NSE and BSE instruments." };
            });
            return next;
          });
        }

        let cursor = 0;
        const workers = Array.from({ length: Math.min(3, eligible.length) }, async () => {
          while (!cancelled) {
            const index = cursor++;
            if (index >= eligible.length) return;
            const item = eligible[index];
            const symbol = String(item.symbol).trim().toUpperCase();
            const itemExchange = String(item.exchange || "NSE").toUpperCase();
            const key = `${itemExchange}:${symbol}`;
            try {
              const response = await apiFetch(`${API}/api/market-quote/?symbol=${encodeURIComponent(symbol)}&exchange=${encodeURIComponent(itemExchange)}`, { cache: "no-store" });
              const data = await response.json().catch(() => ({}));
              if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Quote returned ${response.status}`);
              const price = Number(data?.quote?.last_price);
              if (!Number.isFinite(price) || price <= 0) throw new Error("The quote API returned no valid price.");
              if (!cancelled) setWatchlistQuotes((previous) => ({
                ...previous,
                [key]: {
                  price,
                  retrievedAt: data.retrieved_at || data.last_updated || null,
                  cacheHit: data.cache_hit === true,
                  error: "",
                },
              }));
            } catch (error) {
              if (!cancelled) setWatchlistQuotes((previous) => ({
                ...previous,
                [key]: {
                  ...(previous[key] || {}),
                  error: error?.message || "Unable to load quote.",
                },
              }));
            }
          }
        });
        await Promise.all(workers);
      } finally {
        refreshing = false;
      }
    };

    loadWatchlistQuotes();
    const timer = window.setInterval(loadWatchlistQuotes, 30000);
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") loadWatchlistQuotes();
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [watchlist]);

  // Fetch historical daily candles from the existing Market Charts API.
  const loadChart = async (symbol = chartSymbol, marketExchange = chartExchange, range = chartRange) => {
    if (!symbol) { setChartError("Choose a stock before loading its chart."); return; }
    const daysByRange = { "1D": 1, "1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365, "5Y": 1825 };
    const intervalByRange = { "1D": "minute", "1W": "day", "1M": "day", "3M": "day", "6M": "day", "1Y": "day", "5Y": "day" };
    const toDate = new Date();
    const fromDate = new Date(toDate);
    fromDate.setDate(fromDate.getDate() - (daysByRange[range] || 30));
    const isoDate = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    setChartBusy(true); setChartError(""); setChartData([]); setChartInfo(null);
    try {
      const url = `${API}/api/market-charts/?symbol=${encodeURIComponent(symbol)}&exchange=${encodeURIComponent(marketExchange)}&interval=${encodeURIComponent(intervalByRange[range] || "day")}&from=${isoDate(fromDate)}&to=${isoDate(toDate)}`;
      const response = await apiFetch(url);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Historical data returned ${response.status}`);
      const rows = Array.isArray(data?.data) ? data.data : [];
      const validRows = rows.map((row) => ({ ...row, open: Number(row.open), high: Number(row.high), low: Number(row.low), close: Number(row.close), volume: Number(row.volume) })).filter((row) => Number.isFinite(row.close) && row.close > 0);
      setChartData(validRows); setChartInfo(data?.chart || null);
      if (!validRows.length) setChartError("The historical-data API responded, but no usable daily prices were returned for this period.");
    } catch (e) {
      setChartError(e?.message || "Unable to load historical prices. Check the market gateway and symbol.");
    } finally { setChartBusy(false); }
  };

  const loadYearRange = async (symbol, marketExchange) => {
    if (!symbol) return;
    const requestId = ++yearRangeRequestRef.current;
    const toDate = new Date();
    const fromDate = new Date(toDate);
    fromDate.setDate(fromDate.getDate() - 365);
    const isoDate = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    try {
      const url = `${API}/api/market-charts/?symbol=${encodeURIComponent(symbol)}&exchange=${encodeURIComponent(marketExchange || "NSE")}&interval=day&from=${isoDate(fromDate)}&to=${isoDate(toDate)}`;
      const response = await apiFetch(url, { cache: "no-store" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Year history returned ${response.status}`);
      const rows = Array.isArray(data?.data) ? data.data : [];
      if (requestId === yearRangeRequestRef.current) {
        setYearRangeData(rows.map((row) => ({
          ...row,
          high: Number(row.high),
          low: Number(row.low),
          close: Number(row.close),
        })).filter((row) => [row.high, row.low, row.close].some((value) => Number.isFinite(value) && value > 0)));
      }
    } catch (error) {
      // Keep the page usable when the history endpoint is unavailable; quote-provided 52-week fields still display.
      if (requestId === yearRangeRequestRef.current) setYearRangeData([]);
      console.warn("One-year price history unavailable for 52-week range metrics.", error);
    }
  };

  const chooseChart = (symbol, marketExchange) => {
    setChartSymbol(symbol || "RELIANCE"); setChartExchange(marketExchange || "NSE");
    loadChart(symbol || "RELIANCE", marketExchange || "NSE", chartRange);
  };

  // Selecting a search result closes the match list and focuses the page
  // on that instrument's quote and historical prices.
  const selectInstrument = (row) => {
    if (!row?.symbol) return;
    const instrument = {
      ...row,
      symbol: String(row.symbol).toUpperCase(),
      exchange: row.exchange || "NSE",
    };
    setSelectedInstrument(instrument);
    setResearchTab("overview");
    setQuery(instrument.symbol);
    setResults([]);
    setSearchError("");
    setYearRangeData([]);
    getQuote(instrument.symbol, { initial: true, exchange: instrument.exchange });
    chooseChart(instrument.symbol, instrument.exchange);
    loadYearRange(instrument.symbol, instrument.exchange);
  };

  const indices = Array.isArray(overview?.indices) ? overview.indices : [];
  // Show only the four requested benchmarks. Values are mapped from the API;
  // unavailable instruments are explicitly labelled instead of being fabricated.
  const requestedIndices = [
    { label: "NIFTY 50", aliases: ["NIFTY 50", "NIFTY50", "NIFTY"] },
    { label: "SENSEX", aliases: ["SENSEX", "BSE SENSEX"] },
    { label: "NIFTY BANK", aliases: ["NIFTY BANK", "BANK NIFTY", "BANKNIFTY", "NIFTYBANK"] },
    { label: "INDIA VIX", aliases: ["INDIA VIX", "INDIAVIX", "VIX"] },
  ].map((target) => ({
    ...target,
    data: indices.find((row) => {
      const candidates = [row.name, row.symbol, row.index, row.trading_symbol].filter(Boolean).map((v) => String(v).toUpperCase().replace(/[^A-Z0-9]/g, ""));
      return target.aliases.some((alias) => candidates.includes(alias.toUpperCase().replace(/[^A-Z0-9]/g, "")));
    }) || null,
  }));
  const saveWatchlist = (next) => {
    setWatchlist(next);
    try { localStorage.setItem("financial-os-market-watchlist", JSON.stringify(next)); } catch { /* storage may be unavailable */ }
  };
  const addToWatchlist = (instrument) => {
    if (!instrument?.symbol) return;
    const key = `${String(instrument.exchange || "NSE").toUpperCase()}:${String(instrument.symbol).toUpperCase()}`;
    if (watchlist.some((item) => `${String(item.exchange || "NSE").toUpperCase()}:${String(item.symbol).toUpperCase()}` === key)) return;
    saveWatchlist([...watchlist, { symbol: String(instrument.symbol).toUpperCase(), name: instrument.name || instrument.symbol, exchange: instrument.exchange || "NSE" }]);
  };
  const removeFromWatchlist = (instrument) => saveWatchlist(watchlist.filter((item) => !(String(item.symbol).toUpperCase() === String(instrument.symbol).toUpperCase() && String(item.exchange || "NSE").toUpperCase() === String(instrument.exchange || "NSE").toUpperCase())));
  const movers = overview?.market_movers || {};
  const gainers = Array.isArray(movers.gainers) ? movers.gainers : [];
  const losers = Array.isArray(movers.losers) ? movers.losers : [];
  return <div className="markets-workspace" style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
    <section aria-label="Market overview" style={{ padding: "4px 0 2px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", flexWrap: "wrap", marginBottom: "14px" }}>
        <div><p className="card-label" style={{ margin: "0 0 4px" }}>INDIA MARKETS</p><h2 style={{ margin: 0, fontSize: "25px", fontWeight: 850, letterSpacing: "-.035em" }}>Market Pulse</h2></div>
        <button className="secondary-button" type="button" onClick={refresh} disabled={busy}>{busy ? "Refreshing…" : "↻ Refresh"}</button>
      </div>
    </section>
      <section aria-label="Major Indian market indices" style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "10px" }}>
        {requestedIndices.map((item, i) => <div key={item.label} style={{ ...card, position: "relative", overflow: "hidden", padding: "15px", borderRadius: "18px", border: "1px solid rgba(167,139,250,.18)", background: i % 2 === 0 ? "linear-gradient(145deg, rgba(124,58,237,0.24), rgba(13,18,38,.78))" : "linear-gradient(145deg, rgba(14,165,233,0.18), rgba(13,18,38,.78))", boxShadow: "0 12px 28px rgba(0,0,0,.12)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "center" }}><strong style={{ fontSize: "11px", letterSpacing: ".07em" }}>{item.label}</strong><span style={{ ...muted, fontSize: "10px" }}>{item.data?.status || (busy ? "Loading" : "Market index")}</span></div>
          <div style={{ fontSize: "clamp(20px, 4vw, 27px)", fontWeight: 850, marginTop: "12px", letterSpacing: "-.04em", overflowWrap: "anywhere" }}>{item.data?.last_price != null && Number.isFinite(Number(item.data.last_price)) ? Number(item.data.last_price).toLocaleString("en-IN", { maximumFractionDigits: 2 }) : busy ? "Loading…" : "Unavailable"}</div>
          <div style={{ ...muted, marginTop: "5px", fontSize: "11px" }}>{item.data ? `${item.data.exchange || "Indian market"} · Latest available` : "Not currently returned by market API"}</div>
          <div aria-hidden="true" style={{ height: "3px", borderRadius: "9px", marginTop: "14px", background: "linear-gradient(90deg, rgba(167,139,250,.95), rgba(56,189,248,.35), transparent)" }} />
        </div>)}
      </section>
    <section className="instrument-search-panel" aria-label="Market instrument search" style={{ padding: "4px 0 18px", borderBottom: "1px solid rgba(255,255,255,.07)" }}>
      <div style={{ marginBottom: "12px" }}>
        <h3 style={{ margin: "0 0 8px", fontSize: "19px", fontWeight: 800, letterSpacing: "-.02em" }}>Find an instrument</h3>
      </div>
      <form onSubmit={search} style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) auto", gap: "10px", alignItems: "stretch" }}>
        <div style={{ position: "relative", minWidth: 0 }}>
          <Search aria-hidden="true" size={22} style={{ position: "absolute", left: "17px", top: "50%", transform: "translateY(-50%)", color: "var(--finos-accent)", pointerEvents: "none" }} />
          <input aria-label="Search company, stock or instrument" autoComplete="off" style={{ ...input, width: "100%", minHeight: "60px", padding: "15px 18px 15px 50px", borderRadius: "18px", border: "1px solid rgba(167,139,250,.62)", background: "linear-gradient(115deg, rgba(124,58,237,.22), rgba(15,23,42,.94) 72%)", boxShadow: "0 0 0 4px rgba(124,58,237,.07), 0 14px 32px rgba(0,0,0,.16)", fontSize: "16px" }} value={query} onChange={e => setQuery(e.target.value)} placeholder="Try Reliance, HDFC Bank, TCS…" />
        </div>
        <button className="primary-button" type="submit" disabled={searchBusy} style={{ minWidth: "118px", minHeight: "60px", padding: "0 18px", borderRadius: "16px", fontSize: "14px", fontWeight: 750, whiteSpace: "nowrap" }}>
          {searchBusy ? "Searching…" : <><Search size={17} style={{ marginRight: "7px", verticalAlign: "middle" }} />Search</>}
        </button>
      </form>
      
      {searchBusy && <p role="status" style={{ ...muted, marginTop: "12px" }}>Searching the instrument master…</p>}
      {searchError && <p role="status" style={{ color: "var(--finos-negative)", fontSize: "12px", marginTop: "12px" }}>{searchError}</p>}
      {searchWarning && <p role="status" style={{ color: "var(--finos-warning)", fontSize: "12px", marginTop: "8px" }}>Data freshness warning: {searchWarning}</p>}
      {results.length > 0 && <p style={{ ...muted, margin: "12px 0 4px" }}>{results.length} matching instruments · Select a result to open its quote and chart.</p>}
      {selectedInstrument && <div style={{ ...card, marginTop: "12px", padding: "12px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", flexWrap: "wrap" }}><div><div style={muted}>Selected instrument</div><strong>{selectedInstrument.symbol}</strong><div style={muted}>{selectedInstrument.name || "Company name unavailable"} · {selectedInstrument.exchange || "NSE"}</div></div><div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}><button type="button" className="primary-button" style={{ minWidth: "88px", padding: "10px 20px", fontWeight: 800, letterSpacing: "0.04em", background: "linear-gradient(135deg, #059669, #10b981)", border: "1px solid rgba(52,211,153,0.4)", boxShadow: "0 6px 18px rgba(16,185,129,0.18)" }} onClick={() => { setOrderError(""); setOrderSuccess(null); setOrderClientId(createOrderClientId()); setOrderDraft((previous) => ({ ...previous, quantity: previous.quantity || "1", limit_price: "" })); setOrderModalSide("BUY"); }}>BUY</button><button type="button" className="primary-button" style={{ minWidth: "88px", padding: "10px 20px", fontWeight: 800, letterSpacing: "0.04em", background: "linear-gradient(135deg, #b91c1c, #ef4444)", border: "1px solid rgba(248,113,113,0.4)", boxShadow: "0 6px 18px rgba(239,68,68,0.18)" }} onClick={() => { setOrderError(""); setOrderSuccess(null); setOrderClientId(createOrderClientId()); setOrderDraft((previous) => ({ ...previous, quantity: previous.quantity || "1", limit_price: "" })); setOrderModalSide("SELL"); }}>SELL</button><button type="button" className="secondary-button" onClick={() => addToWatchlist(selectedInstrument)} disabled={watchlist.some((item) => String(item.symbol).toUpperCase() === String(selectedInstrument.symbol).toUpperCase() && String(item.exchange || "NSE").toUpperCase() === String(selectedInstrument.exchange || "NSE").toUpperCase())}>{watchlist.some((item) => String(item.symbol).toUpperCase() === String(selectedInstrument.symbol).toUpperCase() && String(item.exchange || "NSE").toUpperCase() === String(selectedInstrument.exchange || "NSE").toUpperCase()) ? "In watchlist" : "Add to watchlist"}</button><button type="button" className="secondary-button" onClick={() => { setSelectedInstrument(null); setQuote(null); setQuoteError(""); setChartData([]); setChartInfo(null); setChartError(""); }}>Back to Markets</button></div></div>}
      {orderModalSide && selectedInstrument && <div className="broker-order-overlay" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !orderSubmitting) setOrderModalSide(""); }}>
        <form onSubmit={async (event) => {
          event.preventDefault();
          setOrderError(""); setOrderSuccess(null);
          const quantity = Number(orderDraft.quantity);
          const livePrice = Number(quote?.quote?.last_price);
          const orderPrice = orderDraft.order_type === "LIMIT" ? Number(orderDraft.limit_price) : livePrice;
          if (!Number.isInteger(quantity) || quantity < 1) { setOrderError("Enter a whole-number quantity greater than zero."); return; }
          if (!Number.isFinite(livePrice) || livePrice <= 0) { setOrderError("A valid live quote is required before placing an order."); return; }
          if (orderDraft.order_type === "LIMIT" && (!Number.isFinite(Number(orderDraft.limit_price)) || Number(orderDraft.limit_price) <= 0)) { setOrderError("Enter a valid limit price."); return; }
          setOrderSubmitting(true);
          try {
            const response = await apiFetch(`${API}/api/broker-orders/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
              side: orderModalSide, symbol: selectedInstrument.symbol, exchange: selectedInstrument.exchange || "NSE",
              product_type: orderDraft.product_type, order_type: orderDraft.order_type, validity: orderDraft.validity,
              quantity, price: orderDraft.order_type === "LIMIT" ? Number(orderDraft.limit_price) : 0,
              quote_price: livePrice,
              client_id: orderClientId || createOrderClientId()
            }) });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || `Order request failed (${response.status}).`);
            setOrderSuccess(data);
          } catch (error) { setOrderError(error?.message || "Unable to place order."); }
          finally { setOrderSubmitting(false); }
        }} className="broker-order-modal" style={{ width: "min(100%, 460px)", maxHeight: "90vh", overflowY: "auto", padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", marginBottom: "14px" }}>
            <div><div style={{ ...muted, textTransform: "uppercase", letterSpacing: ".08em" }}>Broker order · m.Stock</div><h2 style={{ margin: "4px 0", fontSize: "22px" }}>{orderModalSide} {selectedInstrument.symbol}</h2><div style={muted}>{selectedInstrument.name || selectedInstrument.symbol} · {selectedInstrument.exchange || "NSE"}</div><div style={{ ...muted, marginTop: "6px" }}>Broker account: m.Stock · routed through the configured AWS gateway</div></div>
            <button type="button" className="secondary-button" onClick={() => setOrderModalSide("")} disabled={orderSubmitting} aria-label="Close order form">✕</button>
          </div>
          <div className="broker-order-quote" style={{ ...card, padding: "12px", marginBottom: "14px" }}><div style={muted}>Latest available quote</div><strong style={{ fontSize: "22px" }}>{money(quote?.quote?.last_price)}</strong><div style={muted}>{quote?.retrieved_at ? `Retrieved ${new Date(quote.retrieved_at).toLocaleTimeString("en-IN")}` : "Quote retrieval time unavailable"} · indicative, not a guaranteed execution price</div></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <label style={{ ...muted, display: "block" }}>Product Type *<select required value={orderDraft.product_type} onChange={(e) => setOrderDraft((p) => ({ ...p, product_type: e.target.value }))} style={{ ...input, marginTop: "5px" }}><option value="DELIVERY">Delivery (CNC)</option><option value="INTRADAY">Intraday (MIS)</option></select></label>
            <label style={{ ...muted, display: "block" }}>Order Validity *<select required value={orderDraft.validity} onChange={(e) => setOrderDraft((p) => ({ ...p, validity: e.target.value }))} style={{ ...input, marginTop: "5px" }}><option value="DAY">Day</option><option value="IOC">IOC</option></select></label>
            <label style={{ ...muted, display: "block" }}>Order Type *<select required value={orderDraft.order_type} onChange={(e) => setOrderDraft((p) => ({ ...p, order_type: e.target.value, limit_price: "" }))} style={{ ...input, marginTop: "5px" }}><option value="MARKET">Market</option><option value="LIMIT">Limit</option></select></label>
            <label style={{ ...muted, display: "block" }}>Quantity *<input required type="number" min="1" step="1" value={orderDraft.quantity} onChange={(e) => setOrderDraft((p) => ({ ...p, quantity: e.target.value }))} style={{ ...input, marginTop: "5px" }} /></label>
            {orderDraft.order_type === "LIMIT" && <label style={{ ...muted, display: "block", gridColumn: "1 / -1" }}>Limit Price *<input required type="number" min="0.01" step="0.01" value={orderDraft.limit_price} onChange={(e) => setOrderDraft((p) => ({ ...p, limit_price: e.target.value }))} style={{ ...input, marginTop: "5px" }} /></label>}
          </div>
          <div style={{ borderTop: "1px solid var(--finos-border)", marginTop: "16px", paddingTop: "12px", display: "grid", gap: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}><span style={muted}>Estimated order value</span><strong>{money((Number(orderDraft.quantity) > 0 ? Number(orderDraft.quantity) : 0) * (orderDraft.order_type === "LIMIT" && Number(orderDraft.limit_price) > 0 ? Number(orderDraft.limit_price) : Number(quote?.quote?.last_price)))}</strong></div>
            <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}><span style={muted}>Brokerage & charges</span><span style={{ fontSize: "13px" }}>Calculated by broker</span></div>
            <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}><span style={muted}>Estimated total</span><strong>{money((Number(orderDraft.quantity) > 0 ? Number(orderDraft.quantity) : 0) * (orderDraft.order_type === "LIMIT" && Number(orderDraft.limit_price) > 0 ? Number(orderDraft.limit_price) : Number(quote?.quote?.last_price))) + " + broker charges"}</strong></div>
          </div>
          {orderError && <div role="alert" style={{ marginTop: "12px", padding: "10px", borderRadius: "9px", background: "color-mix(in srgb, var(--finos-negative) 10%, var(--t-card-bg, var(--finos-surface)))", color: "var(--finos-negative)", fontSize: "13px" }}>{orderError}</div>}
          {orderSuccess && <div role="status" style={{ marginTop: "12px", padding: "10px", borderRadius: "9px", background: "color-mix(in srgb, var(--finos-positive) 10%, var(--t-card-bg, var(--finos-surface)))", color: "var(--finos-positive)", fontSize: "13px" }}><strong>Order accepted by gateway.</strong><div>{orderSuccess.order_id ? `Order ID: ${orderSuccess.order_id}` : JSON.stringify(orderSuccess)}</div><div style={{ marginTop: "4px" }}>Holdings update only after confirmed fills are reconciled.</div></div>}
          <div style={{ ...muted, marginTop: "12px" }}>Review all fields carefully. Market orders may execute at a different price. No portfolio holding is changed by this form alone.</div>
          <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}><button type="submit" className="primary-button" disabled={orderSubmitting || Boolean(orderSuccess)} style={{ flex: 1 }}>{orderSubmitting ? "Submitting…" : orderSuccess ? "Order submitted" : `Confirm ${orderModalSide}`}</button><button type="button" className="secondary-button" disabled={orderSubmitting} onClick={() => setOrderModalSide("")}>Cancel</button></div>
        </form>
      </div>}
      {results.map((row, i) => <div key={`${row.exchange || "NSE"}-${row.symbol || row.instrument_token || i}`} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", padding: "13px 12px", marginTop: "8px", borderRadius: "12px", border: "1px solid rgba(255,255,255,.08)", background: "rgba(255,255,255,.025)", flexWrap: "wrap" }}><button type="button" onClick={() => selectInstrument(row)} aria-label={`Select ${row.name || row.symbol}`} style={{ flex: "1 1 180px", textAlign: "left", padding: "4px 0", border: 0, background: "transparent", color: "inherit", cursor: "pointer" }}><strong>{row.symbol || "Unknown symbol"}</strong><div style={muted}>{row.name || "Company name unavailable"} · {row.exchange || "Exchange unavailable"}{(row.series || row.instrument_type) ? ` · ${row.series || row.instrument_type}` : ""}</div><div style={{ ...muted, marginTop: "3px" }}>Tap to open this instrument</div></button><div style={{ display: "flex", gap: "10px", alignItems: "center" }}><strong style={{ fontSize: "12px" }}>{money(row.last_price)}</strong><button type="button" className="secondary-button" onClick={() => selectInstrument(row)}>Select</button></div></div>)}
    </section>
    {overviewError && <div role="status" className="instrument-provider-error">{overviewError}</div>}
    {!selectedInstrument && <>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px" }}>
        <div style={{ ...card, display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px" }}><div><div style={muted}>Market breadth · returned by provider</div><strong style={{ fontSize: "18px" }}>Top gainers</strong><div style={muted}>Stocks moving higher</div></div><div style={{ fontSize: "28px", fontWeight: 850, color: "var(--finos-positive)" }}>{gainers.length}</div></div>
        <div style={{ ...card, display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px" }}><div><div style={muted}>Market breadth · returned by provider</div><strong style={{ fontSize: "18px" }}>Top losers</strong><div style={muted}>Stocks moving lower</div></div><div style={{ fontSize: "28px", fontWeight: 850, color: "var(--finos-negative)" }}>{losers.length}</div></div>
      </section>
      <section style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", flexWrap: "wrap" }}><div><h3 style={{ margin: "0 0 4px" }}>My Watchlist</h3><p style={{ ...muted, margin: 0 }}>Your saved instruments on this device.</p></div><span style={muted}>{watchlist.length} saved</span></div>
        {!watchlist.length ? <p style={{ ...muted, marginBottom: 0 }}>Your watchlist is empty. Search for a stock, select it, then choose “Add to watchlist”.</p> : <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "10px", marginTop: "12px" }}>{watchlist.map((item) => { const key = `${String(item.exchange || "NSE").toUpperCase()}:${String(item.symbol).toUpperCase()}`; const liveQuote = watchlistQuotes[key]; return <div key={key} className="instrument-watchlist-card"><button type="button" onClick={() => selectInstrument(item)} style={{ display: "block", width: "100%", textAlign: "left", border: 0, padding: 0, background: "transparent", color: "inherit", cursor: "pointer" }}><strong>{item.symbol}</strong><div style={muted}>{item.name} · {item.exchange || "NSE"}</div><div style={{ fontSize: "20px", fontWeight: 800, marginTop: "8px" }}>{liveQuote?.price != null ? money(liveQuote.price) : "—"}</div><div style={{ ...muted, marginTop: "3px" }}>{liveQuote?.retrievedAt ? `Gateway retrieved ${new Date(liveQuote.retrievedAt).toLocaleTimeString("en-IN")}${liveQuote.cacheHit ? " · cached" : ""}` : liveQuote?.error || "Loading latest available quote…"}</div><div style={{ ...muted, marginTop: "5px" }}>Tap to open instrument</div></button>{liveQuote?.error && liveQuote?.price != null && <div style={{ ...muted, color: "var(--finos-warning)", marginTop: "4px" }}>Refresh issue: {liveQuote.error}</div>}<button type="button" className="secondary-button" style={{ marginTop: "10px", padding: "6px 9px", fontSize: "11px" }} onClick={() => removeFromWatchlist(item)}>Remove</button></div>; })}</div>}
      </section>
      <section className="instrument-market-news-panel" style={card}><div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}><div><h3 style={{ margin: "0 0 5px" }}>Market News</h3><p style={{ ...muted, margin: 0 }}>A news feed has not been connected to the current market API yet.</p></div><span className="instrument-market-news-badge" style={muted}>Source required</span></div><p style={{ ...muted, marginBottom: 0, marginTop: "10px" }}>We’ll show sourced headlines here once a reliable news provider is configured; no sample or fabricated headlines are displayed.</p></section>
    </>}
    {selectedInstrument && <section className="instrument-ltp-panel" style={card}><h3 style={{ margin: "0 0 10px", fontSize: "13px", color: "var(--finos-muted)", fontWeight: 650 }}>Latest Traded Price (LTP)</h3>{quoteBusy && <p style={muted}>Loading price…</p>}{quoteError && <p role="status" style={{ color: "var(--finos-negative)", fontSize: "12px" }}>{quoteError}</p>}{quote && <><div style={{ fontSize: "34px", fontWeight: 900, letterSpacing: "-.035em" }}>{money(quote.quote?.last_price)}</div><p style={{ ...muted, marginTop: "6px", marginBottom: 0 }}>Backend retrieved {quote.last_updated ? new Date(quote.last_updated).toLocaleTimeString("en-IN") : "time unavailable"}{quote.cache_hit ? ` · cached (${quote.cache_age_seconds ?? 0}s old)` : " · fetched from gateway"}{quote.provider_latency_ms != null ? ` · ${quote.cache_hit ? "last provider fetch" : "provider"} ${quote.provider_latency_ms}ms` : ""}. Provider market timestamp is not supplied.</p></>}{!quoteBusy && !quoteError && !quote && <p style={muted}>Price unavailable.</p>}</section>}
    {/* Historical chart belongs only to the selected instrument workspace, never the market landing page. */}
    {selectedInstrument && <section className="instrument-chart-panel" style={card}>
      <div className="instrument-chart-header">
        <div className="instrument-chart-heading"><h3>Historical price chart</h3><p>{chartInfo ? `${chartInfo.symbol || chartSymbol} · ${chartInfo.exchange || chartExchange} · Daily close` : "Choose a stock and period to load daily closing prices."}</p></div>
        <div className="instrument-chart-ranges" aria-label="Historical chart period">{["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"].map((range) => <button key={range} type="button" className={`instrument-chart-range-button${chartRange === range ? " is-active" : ""}`} aria-pressed={chartRange === range} onClick={() => { setChartRange(range); loadChart(chartSymbol, chartExchange, range); }}>{range}</button>)}</div>
      </div>
      <div className="instrument-chart-controls"><input className="instrument-chart-symbol-input" aria-label="Chart stock symbol" value={chartSymbol} onChange={(e) => setChartSymbol(e.target.value.toUpperCase())} placeholder="e.g. RELIANCE"/><StyledSelect aria-label="Chart exchange" className="instrument-chart-exchange-select" value={chartExchange} onChange={(e) => setChartExchange(e.target.value)}><option value="NSE">NSE</option><option value="BSE">BSE</option></StyledSelect><button type="button" className="secondary-button" disabled={chartBusy} onClick={() => loadChart()}>{chartBusy ? "Loading chart..." : "Load chart"}</button></div>
      {chartError && <p role="status" className="instrument-chart-message instrument-chart-warning">{chartError}</p>}
      {chartBusy && <p style={muted}>Requesting historical prices from the existing market API...</p>}
      {!chartBusy && chartData.length > 1 && (() => {
        const values = chartData.map((row) => row.close);
        const min = Math.min(...values); const max = Math.max(...values); const span = max - min || 1;
        const width = 720; const height = 240; const pad = 18;
        const points = values.map((value, i) => `${pad + i * (width - pad * 2) / Math.max(values.length - 1, 1)},${height - pad - ((value - min) / span) * (height - pad * 2)}`).join(" ");
        const first = values[0]; const last = values[values.length - 1]; const change = last - first; const percent = first ? (change / first) * 100 : 0;
        return <div style={{ marginTop: "14px" }}><div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap", marginBottom: "8px" }}><div><div style={muted}>Last price in selected chart</div><strong style={{ fontSize: "22px" }}>{money(last)}</strong></div><div style={{ textAlign: "right" }}><div style={muted}>Period return</div><strong className={`instrument-chart-period-return${change >= 0 ? " is-positive" : " is-negative"}`}>{change >= 0 ? "+" : ""}{money(change)} ({percent >= 0 ? "+" : ""}{percent.toFixed(2)}%)</strong></div></div><div style={{ width: "100%", overflow: "hidden" }}><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${chartSymbol} historical daily closing-price chart`} style={{ display: "block", width: "100%", minHeight: "150px" }}><line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="var(--finos-border)" strokeWidth="1"/><line x1={pad} y1={height/2} x2={width-pad} y2={height/2} stroke="var(--finos-border)" strokeWidth="1"/><polyline points={points} fill="none" stroke="var(--finos-chart-series-1, var(--finos-accent))" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round"/></svg></div><div style={{ display: "flex", justifyContent: "space-between", ...muted }}><span>{String(chartData[0].timestamp || "").slice(0, 10)}</span><span>{chartData.length} prices</span><span>{String(chartData[chartData.length - 1].timestamp || "").slice(0, 10)}</span></div></div>;
      })()}
      {!chartBusy && !chartError && chartData.length === 1 && <p style={muted}>Only one historical price was returned; at least two points are needed to draw a chart.</p>}
      {!chartBusy && !chartData.length && !chartError && <p style={muted}>No chart loaded yet. Select a period and tap Load chart.</p>}
      <p style={{ ...muted, marginBottom: 0, marginTop: "12px" }}>Historical prices may be delayed or unavailable. This chart uses daily closing prices and is for research only; it does not place trades.</p>
    </section>}

    {/* Stock research tabs appear only after an instrument is selected. */}
    {selectedInstrument && (() => {
      const indicators = calculateTechnicalIndicators(chartData);
      const { closes, latestClose, previousClose, sma20, sma50, ema12, ema26, rsi14, macd, macdSignal, macdHistogram, bollingerUpper, bollingerMiddle, bollingerLower, vwap, atr14, stochasticK, obv } = indicators;
      const periodChange = closes.length > 1 ? closes[closes.length - 1] - closes[0] : null;
      const periodChangePct = closes.length > 1 && closes[0] ? (periodChange / closes[0]) * 100 : null;
      const technicalSignal = latestClose == null || sma20 == null || rsi14 == null
        ? "Insufficient historical data"
        : latestClose > sma20 && rsi14 >= 50 && (macdHistogram == null || macdHistogram >= 0) ? "Positive momentum"
        : latestClose < sma20 && rsi14 < 50 && (macdHistogram == null || macdHistogram <= 0) ? "Negative momentum" : "Mixed / neutral";
      const tabButton = (id, label) => <button key={id} type="button" role="tab" onClick={() => setResearchTab(id)} aria-selected={researchTab === id} aria-controls="instrument-research-tabpanel" className={`instrument-research-tab${researchTab === id ? " is-active" : ""}`}>{label}</button>;
      const metricExplanations = {
        "Latest Traded Price (LTP)": "The most recent traded price reported by the quote provider. It may be delayed depending on the data subscription.",
        "Previous Closing Price": "The official closing price from the previous trading session. It is the reference used to calculate today's change.",
        "Today's Change": "The latest traded price minus the previous closing price. The percentage shows that difference relative to the previous close.",
        "Today's High": "The highest traded price reported for the current trading session.",
        "Today's Low": "The lowest traded price reported for the current trading session.",
        "52-Week High": "The highest price found in the available 52-week historical dataset. This is shown only when a full-year history is loaded.",
        "52-Week Low": "The lowest price found in the available 52-week historical dataset. This is shown only when a full-year history is loaded.",
        "Period Return": "The percentage difference between the first and last prices in the selected chart period. It is not necessarily today's change.",
        "20-day Average Price": "The average of the last 20 available daily closing prices. Traders often compare the current price with this average to assess trend direction.",
        "RSI (14)": "The Relative Strength Index ranges from 0 to 100 and measures recent price momentum. Around 70 is commonly considered overbought and around 30 oversold; neither is a guaranteed signal.",
        "Market Capitalization": "The market value of a company's outstanding shares. It is generally calculated as share price multiplied by shares outstanding.",
        "P/E Ratio": "Share price divided by earnings per share. It is one way investors compare a company's price with its earnings.",
        "EPS": "Earnings per share: the company's profit allocated to each ordinary share over the stated reporting period.",
        "Dividend Yield": "Annual dividend per share divided by the share price, expressed as a percentage. It can change as price or dividends change.",
      };
      const metric = (label, value, hint = "") => <button key={label} type="button" className="instrument-metric-card" onClick={() => setExpandedMetric((current) => current === label ? "" : label)} aria-expanded={expandedMetric === label}><span className="instrument-metric-label">{label}</span><strong className="instrument-metric-value">{value}</strong>{hint ? <span className="instrument-metric-hint">{hint}</span> : null}<span className="instrument-metric-help">{expandedMetric === label ? "Tap to hide explanation" : "Tap to understand this metric"}</span>{expandedMetric === label && <span className="instrument-metric-explanation">{metricExplanations[label] || hint || "This value is provided by the connected data source when available. Check the reporting period and source before making a decision."}</span>}</button>;
      return <section className="instrument-research-panel" style={card}>
        <div className="instrument-research-heading">
          <p className="card-label">INSTRUMENT RESEARCH</p>
          <h3>{selectedInstrument.name || selectedInstrument.symbol}</h3>
          <p>{selectedInstrument.symbol} · {selectedInstrument.exchange || exchange} · Research workspace</p>
        </div>
        <div className="instrument-research-tabs" role="tablist" aria-label="Stock research sections">
          {tabButton("overview", "Overview")}
          {tabButton("fundamental", "Fundamental Analysis")}
          {tabButton("technical", "Technical Analysis")}
          {tabButton("company", "Company Details")}
          {tabButton("dividends", "Dividends & Actions")}
          {tabButton("news", "News")}
        </div>
        <div id="instrument-research-tabpanel" role="tabpanel" className="instrument-research-tabpanel" tabIndex={0}>
          {researchTab === "overview" && <>
            <h4 style={{ margin: "0 0 10px" }}>Price overview</h4>
            {(() => {
              const q = quote?.quote || quote || {};
              const quoteValue = (...keys) => { for (const key of keys) { const n = Number(q?.[key]); if (q?.[key] !== undefined && q?.[key] !== null && q?.[key] !== "" && Number.isFinite(n)) return n; } return null; };
              const ltp = quoteValue("last_price", "ltp", "lastPrice");
              const prev = quoteValue("previous_close", "prev_close", "close", "previousClose");
              const dayHigh = quoteValue("high", "day_high", "high_price");
              const dayLow = quoteValue("low", "day_low", "low_price");
              const dayChange = ltp != null && prev != null ? ltp - prev : null;
              const dayPct = dayChange != null && prev ? dayChange / prev * 100 : null;
              const providerYearHigh = quoteValue("year_high", "yearHigh", "52_week_high", "52WeekHigh", "high_52_week", "fifty_two_week_high", "week_52_high");
              const providerYearLow = quoteValue("year_low", "yearLow", "52_week_low", "52WeekLow", "low_52_week", "fifty_two_week_low", "week_52_low");
              const historyHighs = yearRangeData.map((row) => Number(row.high)).filter((value) => Number.isFinite(value) && value > 0);
              const historyLows = yearRangeData.map((row) => Number(row.low)).filter((value) => Number.isFinite(value) && value > 0);
              const historyCloses = yearRangeData.map((row) => Number(row.close)).filter((value) => Number.isFinite(value) && value > 0);
              const hasYearHistory = yearRangeData.length > 1 || (["1Y", "5Y"].includes(chartRange) && chartData.length > 1);
              const yearHigh = providerYearHigh ?? (historyHighs.length ? Math.max(...historyHighs) : (historyCloses.length ? Math.max(...historyCloses) : (hasYearHistory ? Math.max(...closes) : null)));
              const yearLow = providerYearLow ?? (historyLows.length ? Math.min(...historyLows) : (historyCloses.length ? Math.min(...historyCloses) : (hasYearHistory ? Math.min(...closes) : null)));
              const averagePrice = quoteValue("average_price", "avg_price", "average_traded_price", "averageTradedPrice", "avgPrice");
              const volume = quoteValue("volume", "volume_traded_today", "volumeTradedToday", "total_traded_volume");
              const lastTradedQuantity = quoteValue("last_traded_quantity", "last_traded_qty", "lastTradedQty");
              const buyQuantity = quoteValue("total_buy_quantity", "total_buy_qty", "totalBuyQty", "buy_quantity");
              const sellQuantity = quoteValue("total_sell_quantity", "total_sell_qty", "totalSellQty", "sell_quantity");
              const upperCircuit = quoteValue("upper_circuit_limit", "upper_circuit", "upperCircuit", "upperCircuitLimit");
              const lowerCircuit = quoteValue("lower_circuit_limit", "lower_circuit", "lowerCircuit", "lowerCircuitLimit");
              return <div className="instrument-price-metrics" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "10px" }}>
                {metric("Latest Traded Price (LTP)", ltp != null ? money(ltp) : "Unavailable", "Most recent price returned by the quote provider")}
                {metric("Previous Closing Price", prev != null ? money(prev) : "Unavailable", "Previous trading session's close")}
                {metric("Today's Change", dayChange != null ? `${dayChange >= 0 ? "+" : "−"}${money(Math.abs(dayChange))}` : "Unavailable", dayPct != null ? `${dayPct >= 0 ? "+" : ""}${dayPct.toFixed(2)}% vs previous close` : "Provider must return LTP and previous close")}
                {metric("Today's High", dayHigh != null ? money(dayHigh) : "Unavailable", "Highest price in today's session, if returned")}
                {metric("Today's Low", dayLow != null ? money(dayLow) : "Unavailable", "Lowest price in today's session, if returned")}
                {metric("52-Week High", yearHigh != null ? money(yearHigh) : "Unavailable", providerYearHigh != null ? "From m.Stock quote data" : hasYearHistory ? "Highest daily high in the automatically loaded one-year history" : "Requires a successful one-year history response")}
                {metric("52-Week Low", yearLow != null ? money(yearLow) : "Unavailable", providerYearLow != null ? "From m.Stock quote data" : hasYearHistory ? "Lowest daily low in the automatically loaded one-year history" : "Requires a successful one-year history response")}
                {metric("Average Traded Price", averagePrice != null ? money(averagePrice) : "Unavailable", "Provider quote field when supplied")}
                {metric("Volume Traded Today", volume != null ? new Intl.NumberFormat("en-IN").format(volume) : "Unavailable", "Shares/units traded during the current session")}
                {metric("Last Traded Quantity", lastTradedQuantity != null ? new Intl.NumberFormat("en-IN").format(lastTradedQuantity) : "Unavailable", "Quantity in the latest reported trade")}
                {metric("Total Buy Quantity", buyQuantity != null ? new Intl.NumberFormat("en-IN").format(buyQuantity) : "Unavailable", "Aggregate bid quantity when supplied")}
                {metric("Total Sell Quantity", sellQuantity != null ? new Intl.NumberFormat("en-IN").format(sellQuantity) : "Unavailable", "Aggregate ask quantity when supplied")}
                {metric("Upper Circuit Limit", upperCircuit != null ? money(upperCircuit) : "Unavailable", "Exchange-provided upper price band")}
                {metric("Lower Circuit Limit", lowerCircuit != null ? money(lowerCircuit) : "Unavailable", "Exchange-provided lower price band")}
                {metric("Period Return", periodChangePct != null ? `${periodChangePct >= 0 ? "+" : ""}${periodChangePct.toFixed(2)}%` : "Unavailable", `Change across the selected ${chartRange} chart period`)}
              </div>;
            })()}
            <p style={{ ...muted, marginBottom: 0, marginTop: "12px" }}>Tap any metric card to learn what it means. 52-week values use m.Stock quote fields when available, otherwise the automatically fetched one-year daily history. Other values appear only when supplied by the connected gateway.</p>
            <p style={{ ...muted, marginBottom: 0, marginTop: "6px" }}>Quote source: m.Stock via Financial OS gateway · Retrieved: {quote?.retrieved_at || quote?.last_updated || "Not available"}{quote?.cache_hit ? " · Cached response" : ""}</p>
          </>}
          {researchTab === "fundamental" && <>
            <h4 style={{ margin: "0 0 6px" }}>Fundamental Analysis</h4>
            <p style={muted}>Company financial statements and valuation data are not yet connected to the current market API.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "10px" }}>
              {["Revenue", "Net profit", "Earnings per share (EPS)", "Price-to-earnings (P/E)", "Return on equity (ROE)", "Debt-to-equity", "Market capitalization", "Dividend yield"].map((name) => metric(name, "Not available", "Requires a verified fundamentals data source"))}
            </div>
            <p style={{ ...muted, marginBottom: 0, marginTop: "12px" }}>These metrics will populate after a fundamentals provider is integrated. No sample financial figures are shown.</p>
          </>}
          {researchTab === "technical" && <>
            <h4 style={{ margin: "0 0 6px" }}>Technical Analysis</h4>
            <p style={muted}>Indicators are calculated from the loaded historical OHLCV candles. A metric shows “Insufficient data” when its required lookback or source fields are missing; VWAP uses the loaded period's volume-weighted typical price.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "10px" }}>
              {metric("SMA (20)", sma20 != null ? money(sma20) : "Insufficient data", "20-candle simple moving average")}
              {metric("SMA (50)", sma50 != null ? money(sma50) : "Insufficient data", "50-candle simple moving average")}
              {metric("EMA (12)", ema12 != null ? money(ema12) : "Insufficient data", "12-candle exponential moving average")}
              {metric("EMA (26)", ema26 != null ? money(ema26) : "Insufficient data", "26-candle exponential moving average")}
              {metric("RSI (14)", rsi14 != null ? rsi14.toFixed(2) : "Insufficient data", "Wilder's smoothed Relative Strength Index (0–100)")}
              {metric("MACD (12,26)", macd != null ? macd.toFixed(4) : "Insufficient data", "EMA 12 minus EMA 26")}
              {metric("MACD Signal (9)", macdSignal != null ? macdSignal.toFixed(4) : "Insufficient data", "9-period EMA of MACD")}
              {metric("MACD Histogram", macdHistogram != null ? macdHistogram.toFixed(4) : "Insufficient data", "MACD minus signal line")}
              {metric("VWAP", vwap != null ? money(vwap) : "Volume data unavailable", "Volume-weighted average typical price for loaded candles")}
              {metric("Bollinger Upper (20,2)", bollingerUpper != null ? money(bollingerUpper) : "Insufficient data", "20-period mean plus 2 population standard deviations")}
              {metric("Bollinger Middle (20)", bollingerMiddle != null ? money(bollingerMiddle) : "Insufficient data", "20-period simple moving average")}
              {metric("Bollinger Lower (20,2)", bollingerLower != null ? money(bollingerLower) : "Insufficient data", "20-period mean minus 2 population standard deviations")}
              {metric("ATR (14)", atr14 != null ? money(atr14) : "Insufficient OHLC data", "Average of the latest 14 true ranges")}
              {metric("Stochastic %K (14)", stochasticK != null ? stochasticK.toFixed(2) : "Insufficient OHLC data", "Close position within the latest 14-candle range")}
              {metric("On-Balance Volume", closes.length > 1 && chartData.some((row) => Number.isFinite(Number(row.volume))) ? new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(obv) : "Volume data unavailable", "Cumulative volume signed by candle-to-candle close direction")}
              {metric("Last Price in Chart", latestClose != null ? money(latestClose) : "Unavailable", "Last close in the selected chart period")}
              {metric("Period Return", periodChangePct != null ? `${periodChangePct >= 0 ? "+" : ""}${periodChangePct.toFixed(2)}%` : "Unavailable", `Price change across selected ${chartRange} period`)}
            </div>
            <div style={{ ...card, marginTop: "12px" }}>
              <h4 style={{ margin: "0 0 6px" }}>Technical / Buy-Sell Summary</h4>
              <strong className={`instrument-technical-signal ${technicalSignal === "Positive momentum" ? "is-positive" : technicalSignal === "Negative momentum" ? "is-negative" : "is-neutral"}`}>{technicalSignal}</strong>
              <p style={{ ...muted, margin: "6px 0 0" }}>{technicalSignal === "Positive momentum" ? "The latest loaded close is above its 20-period SMA and RSI is at least 50." : technicalSignal === "Negative momentum" ? "The latest loaded close is below its 20-period SMA and RSI is below 50." : "More historical data may be needed, or the available indicators do not agree. This is a basic technical rule, not a personalized investment recommendation."}</p>
            </div>
            <p style={{ ...muted, marginBottom: 0, marginTop: "10px" }}>This rule-based indicator is educational and does not account for fundamentals, risk tolerance, costs or investment objectives. It is not a guaranteed Buy/Sell recommendation.</p>
          </>}
          {researchTab === "company" && <>
            <h4 style={{ margin: "0 0 10px" }}>Company / Instrument Details</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "10px" }}>
              {metric("Instrument name", selectedInstrument.name || "Not provided")}
              {metric("Trading symbol", selectedInstrument.symbol || "Not provided")}
              {metric("Exchange", selectedInstrument.exchange || exchange)}
              {metric("Instrument type", selectedInstrument.instrument_type || selectedInstrument.type || "Not provided")}
              {metric("Instrument token", selectedInstrument.instrument_token || selectedInstrument.token || "Not provided")}
              {metric("Exchange token", selectedInstrument.exchange_token || "Not provided")}
              {metric("Segment", selectedInstrument.segment || "Not provided")}
              {metric("Series", selectedInstrument.series || selectedInstrument.instrument_type || "Not provided")}
              {metric("Lot size", selectedInstrument.lot_size || "Not applicable")}
              {metric("ISIN", selectedInstrument.isin || "Not provided")}
            </div>
            <p style={{ ...muted, marginBottom: 0, marginTop: "10px" }}>Only fields supplied by the instrument search response are shown. Additional company profile details require a verified company-data source.</p>
          </>}
          {researchTab === "dividends" && <>
            <h4 style={{ margin: "0 0 6px" }}>Dividends & Corporate Actions</h4>
            <p style={muted}>Dividend history, splits, bonuses and ex-dates are not provided by the currently connected market endpoints.</p>
            <div style={{ ...card }}><strong>Corporate actions data source required</strong><p style={{ ...muted, marginBottom: 0, marginTop: "6px" }}>This section is ready for verified dividend and corporate-action records once a suitable provider is connected.</p></div>
          </>}
          {researchTab === "news" && <>
            <h4 style={{ margin: "0 0 6px" }}>{selectedInstrument.symbol} News</h4>
            <p style={muted}>Company-specific news has not been connected to the current market API.</p>
            <div style={{ ...card }}><strong>News source required</strong><p style={{ ...muted, marginBottom: 0, marginTop: "6px" }}>Verified headlines, publisher, publication time and original article links will appear here after a news provider is integrated. No fabricated headlines are displayed.</p></div>
          </>}
        </div>
      </section>;
    })()}

    {!selectedInstrument && <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "14px" }}>{[{ title: "Top gainers", rows: gainers }, { title: "Top losers", rows: losers }].map(group => <div key={group.title} style={card}><h3 style={{ margin: "0 0 12px" }}>{group.title}</h3>{!group.rows.length ? <p style={muted}>No rows returned by the provider.</p> : group.rows.slice(0, 8).map((row, i) => <div key={`${row.symbol || "item"}-${i}`} className="instrument-market-mover-row"><div><strong style={{ fontSize: "12px" }}>{row.symbol || row.name || "Instrument"}</strong><div style={muted}>{row.name || row.exchange || ""}</div></div><div style={{ textAlign: "right", whiteSpace: "nowrap" }}><div style={{ fontSize: "12px", fontWeight: 700 }}>{money(row.ltp)}</div><div className={`instrument-action-change ${Number(row.percent_change) < 0 ? "is-negative" : "is-positive"}`}>{row.percent_change == null ? "Change unavailable" : `${row.percent_change}%`}</div></div></div>)}</div>)}</section>}
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
  const API_BASE_URL = "https://wealthmanager.duckdns.org";
  const USER_ID = getCurrentUserId();
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
    const response = await apiFetch(`${API_BASE_URL}/api/goals/?user_id=${USER_ID}`);
    if (!response.ok) throw new Error(`Goals API returned ${response.status}`);
    const data = await response.json();
    if (data.status !== "success") throw new Error("Could not load saved goals.");
    setGoals(data.goals || []);
  };
  const loadPlan = async () => {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/financial-plan/?user_id=${USER_ID}`);
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
      const response = await apiFetch(`${API_BASE_URL}/api/goals/${editingId ? `${editingId}` : ""}`, { method: editingId ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
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
    try { const response = await apiFetch(`${API_BASE_URL}/api/goals/${goal.id}?user_id=${USER_ID}`, { method: "DELETE" }); const data = await response.json().catch(() => ({})); if (!response.ok) throw new Error(data.detail || `Delete failed (${response.status})`); setGoals(prev => prev.filter(g => g.id !== goal.id)); if (editingId === goal.id) resetForm(); setSuccess("Goal deleted."); }
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

  return <div className="plan-workspace" style={{ display: "grid", gap: "18px" }}>
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
        <label style={muted}>Category<StyledSelect value={form.category} onChange={e => updateForm("category", e.target.value)} style={field}>{categories.map(c => <option key={c}>{c}</option>)}</StyledSelect></label>
        <label style={muted}>Target amount (₹) *<input required type="number" min="1" step="0.01" value={form.target_amount} onChange={e => updateForm("target_amount", e.target.value)} style={field} /></label>
        <label style={muted}>Already saved / allocated (₹)<input type="number" min="0" step="0.01" value={form.current_amount} onChange={e => updateForm("current_amount", e.target.value)} style={field} /></label>
        <label style={muted}>Target date<input type="date" min={new Date().toISOString().slice(0,10)} value={form.target_date} onChange={e => updateForm("target_date", e.target.value)} style={field} /></label>
        <label style={muted}>Monthly contribution (₹)<input type="number" min="0" step="0.01" value={form.monthly_contribution} onChange={e => updateForm("monthly_contribution", e.target.value)} style={field} /></label>
        <label style={muted}>Status<StyledSelect value={form.status} onChange={e => updateForm("status", e.target.value)} style={field}><option value="active">Active</option><option value="paused">Paused</option><option value="completed">Completed</option></StyledSelect></label>
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
// GEMINI AI ASSISTANT
// ============================================================
function AIAssistantPage() {
  const API_BASE_URL = "https://wealthmanager.duckdns.org";
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function sendMessage(event) {
    event.preventDefault(); const text = message.trim(); if (!text || busy) return;
    setMessages(old => [...old, { role: "you", text }]); setMessage(""); setError(""); setBusy(true);
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/ai/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
      setMessages(old => [...old, { role: "gemini", text: data.answer || "Gemini returned an empty response." }]);
    } catch (err) { setError(err.message || "Unable to reach Gemini."); } finally { setBusy(false); }
  }
  return <div style={{ maxWidth: 980, margin: "0 auto", padding: "8px 0 24px" }}>
    <div className="glass-card" style={{ padding: 22, marginBottom: 16 }}><p className="card-label">GOOGLE GEMINI</p><h2 style={{ margin: "6px 0" }}>AI Financial Assistant</h2><p style={{ color: "rgba(255,255,255,.65)", lineHeight: 1.6, marginBottom: 0 }}>Ask about budgeting, investing concepts, financial goals, or planning. This initial connection does not automatically access your private Financial OS records or live market data.</p></div>
    <div className="glass-card" style={{ padding: 18 }}><div style={{ minHeight: 180, maxHeight: 430, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12, marginBottom: 16 }}>
      {messages.length === 0 && <p style={{ color: "rgba(255,255,255,.55)" }}>Example: “Help me create a monthly budget”</p>}
      {messages.map((item, index) => <div key={index} style={{ alignSelf: item.role === "you" ? "flex-end" : "stretch", maxWidth: "95%", padding: 12, borderRadius: 12, background: item.role === "you" ? "rgba(168,85,247,.20)" : "rgba(255,255,255,.06)", whiteSpace: "pre-wrap", lineHeight: 1.6 }}><strong style={{ display: "block", fontSize: 12, opacity: .7, marginBottom: 5 }}>{item.role === "you" ? "YOU" : "GEMINI"}</strong>{item.text}</div>)}
      {busy && <p style={{ color: "rgba(255,255,255,.65)" }}>Gemini is thinking…</p>}</div>
      {error && <p role="alert" style={{ color: "#fb7185" }}>{error}</p>}
      <form onSubmit={sendMessage} style={{ display: "flex", gap: 10, flexWrap: "wrap" }}><input aria-label="Message Gemini" value={message} onChange={e => setMessage(e.target.value)} placeholder="Ask your financial assistant…" maxLength={8000} style={{ flex: "1 1 260px", minWidth: 0, padding: "13px 14px", borderRadius: 10, color: "inherit", background: "rgba(255,255,255,.06)", border: "1px solid rgba(255,255,255,.14)" }} /><button type="submit" className="primary-button" disabled={busy || !message.trim()}>{busy ? "Sending…" : "Ask Gemini"}</button></form>
    </div></div>;
}

// ============================================================
// PLAYGROUND — LIVE DATA WORKSPACE (READ-ONLY)
// Uses existing Financial OS Vibe Trading endpoints. No orders.
// ============================================================
function PlaygroundPage() {
  const API = "https://wealthmanager.duckdns.org";
  const [status, setStatus] = useState(null);
  const [tab, setTab] = useState("Market Data");
  const [symbolsText, setSymbolsText] = useState("RELIANCE, TCS, INFY, HDFCBANK");
  const [quotes, setQuotes] = useState([]);
  const [question, setQuestion] = useState("Review these symbols using only the retrieved market evidence. State uncertainties and do not give a guaranteed prediction.");
  const [research, setResearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState("");
  const [strategyName, setStrategyName] = useState("Moving average crossover");
  const [fastPeriod, setFastPeriod] = useState(10);
  const [slowPeriod, setSlowPeriod] = useState(30);
  const [riskPercent, setRiskPercent] = useState(1);
  const [notice, setNotice] = useState("");
  const symbols = () => [...new Set(symbolsText.split(/[\s,;]+/).map(s => s.trim().toUpperCase()).filter(Boolean))].slice(0, 20);
  useEffect(() => { let cancelled=false; apiFetch(`${API}/api/vibe-trading/status`).then(async r=>{const d=await r.json(); if(!r.ok) throw new Error(d.detail||`Status ${r.status}`); return d;}).then(d=>{if(!cancelled)setStatus(d);}).catch(e=>{if(!cancelled)setError(`API status unavailable: ${e.message}`);}); return ()=>{cancelled=true;}; }, []);
  const loadQuotes = async (e) => { if(e)e.preventDefault(); const list=symbols(); if(!list.length){setError("Enter at least one symbol.");return;} setBusy(true);setError("");setNotice("");try{const r=await apiFetch(`${API}/api/vibe-trading/quotes`,{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify({symbols:list})});const d=await r.json();if(!r.ok)throw new Error(typeof d.detail==="string"?d.detail:JSON.stringify(d.detail||`Request failed (${r.status})`));setQuotes(Array.isArray(d.quotes)?d.quotes:[]);setUpdatedAt(new Date().toLocaleString());if(!d.quotes?.length)setError("No quote rows were returned.");}catch(e){setError(e.message||"Unable to load quotes.");}finally{setBusy(false);} };
  const runResearch = async (e) => { if(e)e.preventDefault();setBusy(true);setError("");setResearch("");try{const r=await apiFetch(`${API}/api/vibe-trading/research`,{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify({question,symbols:symbols()})});const d=await r.json();if(!r.ok)throw new Error(typeof d.detail==="string"?d.detail:JSON.stringify(d.detail||`Research failed (${r.status})`));setResearch(d.answer||"The research service returned no answer.");}catch(e){setError(e.message||"Research request failed.");}finally{setBusy(false);} };
  const panel={background:"rgba(255,255,255,.035)",border:"1px solid rgba(255,255,255,.10)",borderRadius:14,padding:16,minWidth:0};
  const muted={color:"rgba(255,255,255,.65)",fontSize:13,lineHeight:1.65};
  const input={width:"100%",minWidth:0,padding:"12px 13px",borderRadius:10,color:"inherit",background:"rgba(255,255,255,.06)",border:"1px solid rgba(255,255,255,.16)",marginTop:6};
  const tabs=["Market Data","AI Research","Strategy Builder","Backtesting","Paper Trading","Risk Controls","Agent Lab","Execution"];
  const btn={padding:"10px 12px",borderRadius:9,border:"1px solid rgba(255,255,255,.15)",background:"rgba(255,255,255,.05)",color:"inherit",cursor:"pointer"};
  const coming=(name,desc)=> <section style={panel}><p className="card-label">PLAYGROUND WORKSPACE</p><h3 style={{marginTop:4}}>{name}</h3><p style={muted}>{desc}</p><div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",gap:10,marginTop:14}}>{["Inputs & configuration","Results & diagnostics","Saved workspace"].map(x=><div key={x} style={{padding:12,borderRadius:10,border:"1px solid rgba(255,255,255,.10)"}}><strong>{x}</strong><p style={muted}>Workspace section reserved and visible. This feature is not connected to a calculation or storage engine yet.</p></div>)}</div><p style={muted}>Availability: interface scaffold only. No fabricated backtest, paper order, strategy signal, or broker action is produced.</p><button type="button" style={btn} onClick={()=>setNotice(`${name}: workspace selected. Backend implementation is the next development step.`)}>Check workspace status</button>{notice&&<p role="status" style={muted}>{notice}</p>}</section>;
  return <div style={{display:"grid",gap:14,minWidth:0}}>
    <section style={panel}><p className="card-label">FINANCIAL OS / PLAYGROUND</p><h2 style={{margin:"5px 0"}}>Trading & Research Playground</h2><p style={muted}>One workspace for market data, AI research, strategy design, backtesting, paper trading, risk controls, agent research, and execution readiness. Each section is selectable; unfinished engines are labelled rather than pretending to work.</p><div style={{display:"flex",gap:8,flexWrap:"wrap",marginTop:12}}><span style={muted}>API: {status?.status||"Checking…"}</span><span style={muted}>Provider: {status?.market_provider||"m.Stock gateway"}</span><span style={muted}>Real orders: disabled</span></div></section>
    <nav aria-label="Playground tools" style={{display:"flex",gap:8,flexWrap:"wrap"}}>{tabs.map(t=><button key={t} type="button" onClick={()=>{setTab(t);setError("");setNotice("");}} aria-pressed={tab===t} style={{...btn,background:tab===t?"rgba(168,85,247,.24)":"rgba(255,255,255,.05)",borderColor:tab===t?"rgba(168,85,247,.7)":"rgba(255,255,255,.15)"}}>{t}{["Strategy Builder","Backtesting","Paper Trading","Risk Controls","Agent Lab","Execution"].includes(t)?" ·":""}</button>)}</nav>
    {error&&<div role="alert" style={{...panel,color:"#fca5a5"}}>{error}</div>}
    {tab==="Market Data"&&<><section style={panel}><h3 style={{marginTop:0}}>Market quotes</h3><p style={muted}>Enter up to 20 NSE symbols. Requests use the existing Vibe Trading batch endpoint.</p><form onSubmit={loadQuotes} style={{display:"grid",gap:10}}><label style={muted}>Symbols<input aria-label="Market symbols" value={symbolsText} onChange={e=>setSymbolsText(e.target.value)} style={input} placeholder="RELIANCE, TCS, INFY"/></label><button className="primary-button" type="submit" disabled={busy}>{busy?"Loading…":"Load market data"}</button></form>{updatedAt&&<p style={muted}>Retrieved by this page: {updatedAt}. Retrieval time is not a verified exchange timestamp.</p>}</section>{quotes.length>0&&<section style={{...panel,overflowX:"auto"}}><h3>Quote results ({quotes.length})</h3><table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}><thead><tr>{["Symbol","Status","Price","Provider timestamp","Details"].map(h=><th key={h} style={{textAlign:"left",padding:8,borderBottom:"1px solid rgba(255,255,255,.14)"}}>{h}</th>)}</tr></thead><tbody>{quotes.map((q,i)=><tr key={`${q.symbol}-${i}`}>{[q.symbol||"—",q.status||"unknown",q.quote?.last_price??q.price??q.last_price??"—",q.provider_market_timestamp||"Not supplied",q.error||(q.cache_hit?"Cached":"API response")].map((v,j)=><td key={j} style={{padding:8,borderBottom:"1px solid rgba(255,255,255,.07)"}}>{String(v)}</td>)}</tr>)}</tbody></table><p style={muted}>No provider timestamp means live-price freshness is unverified.</p></section>}</>}
    {tab==="AI Research"&&<section style={panel}><h3 style={{marginTop:0}}>Evidence-grounded AI research</h3><p style={muted}>Gemini analyses your question using successfully retrieved quotes where available. It does not place orders.</p><form onSubmit={runResearch} style={{display:"grid",gap:10}}><label style={muted}>Symbols<input value={symbolsText} onChange={e=>setSymbolsText(e.target.value)} style={input}/></label><label style={muted}>Research question<textarea value={question} onChange={e=>setQuestion(e.target.value)} rows={4} style={{...input,resize:"vertical"}}/></label><button className="primary-button" disabled={busy||question.trim().length<3}>{busy?"Researching…":"Run AI research"}</button></form>{research&&<div style={{marginTop:14,padding:14,borderRadius:10,background:"rgba(255,255,255,.04)",whiteSpace:"pre-wrap",lineHeight:1.7}}><strong>Research result</strong><p>{research}</p></div>}</section>}
    {tab==="Strategy Builder"&&<section style={panel}><h3 style={{marginTop:0}}>Strategy builder</h3><p style={muted}>Configure a draft strategy. This currently saves only in this page's state; it does not create signals or submit orders.</p><label style={muted}>Strategy template<select value={strategyName} onChange={e=>setStrategyName(e.target.value)} style={input}><option>Moving average crossover</option><option>Momentum watchlist</option><option>Mean reversion</option><option>Breakout watchlist</option></select></label><div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(140px,1fr))",gap:10}}><label style={muted}>Fast period<input type="number" min="1" max="200" value={fastPeriod} onChange={e=>setFastPeriod(Number(e.target.value))} style={input}/></label><label style={muted}>Slow period<input type="number" min="2" max="500" value={slowPeriod} onChange={e=>setSlowPeriod(Number(e.target.value))} style={input}/></label></div><button style={btn} type="button" onClick={()=>setNotice(fastPeriod>0&&slowPeriod>fastPeriod?`Draft configured: ${strategyName}, fast ${fastPeriod}, slow ${slowPeriod}. No signal has been generated.`:"Set valid periods: fast must be positive and slow must be greater than fast.")}>Validate draft</button>{notice&&<p role="status" style={muted}>{notice}</p>}</section>}
    {tab==="Backtesting"&&coming("Backtesting","Choose a strategy, instrument universe, date range, benchmark, fees, and slippage. Historical data and a tested simulation engine must be connected before performance metrics can be trusted.")}
    {tab==="Paper Trading"&&coming("Paper trading","Simulated orders, positions, fills, and P&L will be isolated from real holdings. No simulation is presented as active until its engine and persistence are implemented.")}
    {tab==="Risk Controls"&&<section style={panel}><h3 style={{marginTop:0}}>Risk controls draft</h3><p style={muted}>Set a draft risk budget. These values are not yet enforced by an execution engine.</p><label style={muted}>Risk per trade (%)<input type="number" min="0.1" max="5" step="0.1" value={riskPercent} onChange={e=>setRiskPercent(Number(e.target.value))} style={input}/></label><button type="button" style={btn} onClick={()=>setNotice(riskPercent>=0.1&&riskPercent<=5?`Draft risk budget: ${riskPercent}% per trade. Not enforced against orders.`:"Choose a risk budget from 0.1% to 5%.")}>Validate risk setting</button>{notice&&<p role="status" style={muted}>{notice}</p>}<ul style={muted}><li>Position-size limits — planned</li><li>Daily loss and drawdown limits — planned</li><li>Order validation and kill switch — required before live execution</li></ul></section>}
    {tab==="Agent Lab"&&coming("Multi-agent research lab","The planned roles are market researcher, news/fundamental analyst, strategy reviewer, and risk critic. Agent orchestration and source citations must be implemented before this panel runs agents.")}
    {tab==="Execution"&&<section style={panel}><h3 style={{marginTop:0}}>Broker execution</h3><p style={muted}>Real-order execution is intentionally disabled. It will require explicit approval, authenticated broker session checks, order previews, risk validation, audit logs, and a kill switch.</p><button type="button" disabled style={{...btn,opacity:.55,cursor:"not-allowed"}}>Live execution unavailable — safety gate</button></section>}
    <section style={panel}><h3 style={{marginTop:0}}>Capability map</h3><div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(170px,1fr))",gap:8}}>{tabs.map(t=><button type="button" key={t} onClick={()=>{setTab(t);setError("");setNotice("");}} style={{...btn,textAlign:"left"}}><strong>{t}</strong><div style={muted}>{t==="Market Data"||t==="AI Research"?"Connected API workflow":t==="Strategy Builder"||t==="Risk Controls"?"Interactive draft workspace":t==="Execution"?"Disabled for safety":"Visible workspace; engine pending"}</div></button>)}</div></section>
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

  const USER_ID = getCurrentUserId();

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

  // EDIT FORM: keep the selected transaction separate from the list.
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [editForm, setEditForm] = useState({
    quantity: "", price: "", fees: "0", transaction_date: "", notes: "",
  });
  const [savingEdit, setSavingEdit] = useState(false);
  const [editError, setEditError] = useState("");

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
        apiFetch(
          `${API_BASE_URL}/api/investment-transactions/?user_id=${USER_ID}`
        ),
        apiFetch(
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

  // Open an in-page edit form instead of a sequence of browser prompts.
  const editInvestmentTransaction = (transaction) => {
    if ((transaction.status || "ACTIVE") !== "ACTIVE") {
      alert("Only active transactions can be edited.");
      return;
    }
    setEditError("");
    setEditingTransaction(transaction);
    setEditForm({
      quantity: String(transaction.quantity ?? ""),
      price: String(transaction.price ?? ""),
      fees: String(transaction.fees ?? 0),
      transaction_date: String(transaction.transaction_date ?? "").slice(0, 10),
      notes: transaction.notes ?? "",
    });
  };

  // Submit once, updating the existing transaction ID (never creating a new row).
  const saveInvestmentTransactionEdit = async (event) => {
    event.preventDefault();
    if (!editingTransaction || savingEdit) return;

    const quantity = Number(editForm.quantity);
    const price = Number(editForm.price);
    const fees = Number(editForm.fees);
    if (!Number.isFinite(quantity) || quantity <= 0 ||
        !Number.isFinite(price) || price <= 0 ||
        !Number.isFinite(fees) || fees < 0 ||
        !/^\d{4}-\d{2}-\d{2}$/.test(editForm.transaction_date)) {
      setEditError("Enter a valid quantity, price, non-negative fees and transaction date.");
      return;
    }

    setSavingEdit(true);
    setEditError("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/investment-transactions/${editingTransaction.id}?user_id=${USER_ID}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_type: editingTransaction.transaction_type,
          quantity, price, fees,
          transaction_date: editForm.transaction_date,
          notes: editForm.notes.trim() || null,
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result?.detail || `Unable to update transaction (${response.status}).`);
      setEditingTransaction(null);
      await loadInvestmentTransactions();
      window.dispatchEvent(new Event("financial-os:transactions-changed"));
      alert("Investment transaction updated successfully.");
    } catch (err) {
      setEditError(err?.message || "Unable to update transaction.");
    } finally {
      setSavingEdit(false);
    }
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
    const response = await apiFetch(`${API_BASE_URL}/api/investment-transactions/${transaction.id}/void?user_id=${USER_ID}`, {
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

      <section className="glass-card investment-activity-filter-panel">

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

          <StyledSelect className="finos-select"
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
          </StyledSelect>


          <StyledSelect className="finos-select"
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
          </StyledSelect>


          <StyledSelect className="finos-select"
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
          </StyledSelect>


          <StyledSelect className="finos-select"
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
          </StyledSelect>

        </div>

      </section>


      {/* TRANSACTION HISTORY */}

      <section className="glass-card investment-history-panel">

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
                          "var(--t-card-bg, var(--finos-surface, #ffffff))",
                        border:
                          "1px solid var(--finos-border, #e1e6ef)",
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
                              "var(--finos-muted, #64748b)",
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
                              "var(--finos-muted, #64748b)",
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
                              "var(--finos-muted, #64748b)",
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
                              "var(--finos-muted, #64748b)",
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
                              "var(--finos-muted, #64748b)",
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
                        {transaction.status === "VOIDED" && transaction.void_reason && <small style={{ color: "var(--finos-muted, #64748b)" }}>Reason: {transaction.void_reason}</small>}
                      </div>

                    </div>

                  );

                }
              )}

            </div>

          )}

      </section>


      {/* EDIT TRANSACTION MODAL: mobile-friendly and avoids browser prompt chains. */}
      {editingTransaction && (
        <div role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget && !savingEdit) setEditingTransaction(null);
        }} style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,0,0,.72)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
          <form role="dialog" aria-modal="true" aria-labelledby="edit-investment-transaction-title" onSubmit={saveInvestmentTransactionEdit} className="glass-card" style={{ width: "100%", maxWidth: 520, maxHeight: "90vh", overflowY: "auto", padding: 22, background: "#111322", boxSizing: "border-box" }}>
            <p className="card-label">INVESTMENT TRANSACTIONS</p>
            <h2 id="edit-investment-transaction-title" style={{ margin: "6px 0 4px" }}>Edit {editingTransaction.transaction_type} transaction</h2>
            <p style={{ marginTop: 0, color: "rgba(255,255,255,.6)", fontSize: 13 }}>{editingTransaction.instrument_name} · Transaction #{editingTransaction.id}</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
              {[{key:"quantity",label:"Quantity",type:"number",step:"any",min:"0.000001"},{key:"price",label:"Price per unit (₹)",type:"number",step:"any",min:"0.0001"},{key:"fees",label:"Fees (₹)",type:"number",step:"any",min:"0"},{key:"transaction_date",label:"Transaction date",type:"date"}].map(field => (
                <label key={field.key} style={{ display: "grid", gap: 6, fontSize: 12, color: "rgba(255,255,255,.75)" }}>
                  {field.label}
                  <input required type={field.type} step={field.step} min={field.min} value={editForm[field.key]} onChange={event => setEditForm(current => ({ ...current, [field.key]: event.target.value }))} style={{ width: "100%", boxSizing: "border-box", padding: 12, borderRadius: 9, border: "1px solid rgba(255,255,255,.16)", background: "#191b2b", color: "white" }} />
                </label>
              ))}
              <label style={{ display: "grid", gap: 6, gridColumn: "1 / -1", fontSize: 12, color: "rgba(255,255,255,.75)" }}>Notes (optional)
                <textarea rows={3} value={editForm.notes} onChange={event => setEditForm(current => ({ ...current, notes: event.target.value }))} maxLength={2000} style={{ width: "100%", boxSizing: "border-box", padding: 12, borderRadius: 9, border: "1px solid rgba(255,255,255,.16)", background: "#191b2b", color: "white", resize: "vertical" }} />
              </label>
            </div>
            {editError && <p role="alert" style={{ color: "#fca5a5", fontSize: 13 }}>{editError}</p>}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, flexWrap: "wrap", marginTop: 18 }}>
              <button type="button" className="secondary-button" disabled={savingEdit} onClick={() => setEditingTransaction(null)}>Cancel</button>
              <button type="submit" className="primary-button" disabled={savingEdit}>{savingEdit ? "Saving…" : "Save changes"}</button>
            </div>
          </form>
        </div>
      )}

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
  const USER_ID = getCurrentUserId();

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
          apiFetch(
            `${API_BASE_URL}/api/holdings/?user_id=${USER_ID}`
          ),
          apiFetch(
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

      const response = await apiFetch(
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

  // Allocation is derived only from the current holdings API response.
  // It is a concentration view, not a recommendation or a second portfolio ledger.
  const allocationRows = holdings
    .map((holding, index) => ({
      key: holding.symbol || holding.instrument_name || `holding-${index}`,
      name: holding.name || holding.instrument_name || holding.symbol || "Instrument",
      symbol: holding.symbol || "",
      value: Number(holding.current_value || 0),
    }))
    .filter((holding) => Number.isFinite(holding.value) && holding.value > 0)
    .sort((a, b) => b.value - a.value);
  const allocationTotal = allocationRows.reduce((sum, holding) => sum + holding.value, 0);

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (
    <div
      className="holdings-workspace"
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
          gridTemplateColumns: "repeat(6, minmax(0, 1fr))",
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

      {/* Portfolio concentration: calculated from current API-backed holdings. */}
      <section className="glass-card holdings-allocation-panel">
        <div className="card-header">
          <div>
            <p className="card-label">PORTFOLIO ANALYTICS</p>
            <h3>Holdings allocation</h3>
            <p className="chart-footnote">Share of recorded current market value by holding.</p>
          </div>
          <span className="small-button">{allocationRows.length} positions with value</span>
        </div>
        {loading ? (
          <div className="empty-chart">Loading allocation from current holdings…</div>
        ) : allocationRows.length === 0 || allocationTotal <= 0 ? (
          <div className="empty-chart">Allocation will appear when holdings have a valid current market value.</div>
        ) : (
          <div className="holdings-allocation-list">
            {allocationRows.slice(0, 8).map((holding) => {
              const share = (holding.value / allocationTotal) * 100;
              return (
                <div className="holdings-allocation-row" key={holding.key}>
                  <div className="holdings-allocation-label">
                    <span><strong>{holding.name}</strong>{holding.symbol && holding.symbol !== holding.name ? <small>{holding.symbol}</small> : null}</span>
                    <strong>{share.toFixed(1)}%</strong>
                  </div>
                  <div className="holdings-allocation-track" aria-label={`${holding.name}: ${share.toFixed(1)} percent of portfolio value`}>
                    <span style={{ width: `${share}%` }} />
                  </div>
                  <div className="holdings-allocation-value">{formatCurrency(holding.value)}</div>
                </div>
              );
            })}
            {allocationRows.length > 8 ? <p className="chart-footnote">Showing the 8 largest positions by current value. Total allocation uses all {allocationRows.length} valued holdings.</p> : null}
          </div>
        )}
      </section>

      {/* HOLDINGS LIST */}

      <section className="glass-card holdings-list-panel">
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
          <div className="holdings-list">
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
                    className="portfolio-holding-card"
                    style={{
                      border: "1px solid var(--finos-border, rgba(255,255,255,0.08))",
                      borderRadius: "16px",
                      padding: "16px",
                      background: "var(--t-card-bg, rgba(255,255,255,0.03))",
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

                      <div
                        style={{
                          padding: "10px 12px",
                          borderRadius: "12px",
                          border: "1px solid rgba(52, 211, 153, 0.24)",
                          background: "linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(16, 185, 129, 0.035))",
                          minWidth: 0,
                        }}
                      >
                        <div
                          className="card-label"
                          style={{ display: "flex", alignItems: "center", gap: "6px", color: "rgba(110, 231, 183, 0.9)" }}
                        >
                          <span aria-hidden="true" style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#34d399", boxShadow: "0 0 8px rgba(52, 211, 153, 0.65)", flexShrink: 0 }} />
                          CURRENT PRICE
                        </div>
                        <strong style={{ display: "block", marginTop: "5px", fontSize: "14px", fontVariantNumeric: "tabular-nums", color: "#a7f3d0", overflowWrap: "anywhere" }}>
                          {formatCurrency(holding.current_price)}
                        </strong>
                        <div style={{ marginTop: "3px", fontSize: "10px", color: "rgba(255,255,255,0.45)" }}>
                          Per unit
                        </div>
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

                      <div style={{ display: "flex", flexDirection: "column", gap: "6px", alignItems: "stretch", minWidth: "84px" }}>
                        <button type="button" className="primary-button holding-action-buy" onClick={() => { try { sessionStorage.setItem("financialOS.portfolioAction", JSON.stringify({ type: "BUY", symbol: holding.symbol || "", name: holding.name || "", exchange: holding.exchange || "NSE" })); } catch {} const url = new URL(window.location.href); url.searchParams.set("page", "Portfolio"); window.history.pushState({ page: "Portfolio" }, "", `${url.pathname}${url.search}${url.hash}`); window.dispatchEvent(new PopStateEvent("popstate")); }}>BUY</button>
                        <button type="button" className="secondary-button holding-action-sell" onClick={() => { try { sessionStorage.setItem("financialOS.portfolioAction", JSON.stringify({ type: "SELL", symbol: holding.symbol || "", name: holding.name || "", exchange: holding.exchange || "NSE" })); } catch {} const url = new URL(window.location.href); url.searchParams.set("page", "Portfolio"); window.history.pushState({ page: "Portfolio" }, "", `${url.pathname}${url.search}${url.hash}`); window.dispatchEvent(new PopStateEvent("popstate")); }}>SELL</button>
                        <button type="button" className="secondary-button holding-action-neutral" onClick={() => { try { sessionStorage.setItem("financialOS.portfolioAction", JSON.stringify({ type: "EDIT", symbol: holding.symbol || "", name: holding.name || "", exchange: holding.exchange || "NSE" })); } catch {} const url = new URL(window.location.href); url.searchParams.set("page", "Portfolio"); window.history.pushState({ page: "Portfolio" }, "", `${url.pathname}${url.search}${url.hash}`); window.dispatchEvent(new PopStateEvent("popstate")); }}>EDIT</button>
                        <button type="button" className="secondary-button" style={{ padding: "7px 12px", minWidth: "78px", fontSize: "11px" }} onClick={() => setExpandedSymbol(expanded ? null : holdingKey)}>{expanded ? "Hide details" : "History / View"}</button>
                      </div>
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

  const USER_ID = getCurrentUserId();
  const getLocalDateString = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 10);
  };
  const isListedProductType = (productType) => ["Stocks", "Stock", "ETFs", "ETF", "REITs", "REIT"].includes(productType);

  // Shared muted text style used by Portfolio and the investment form.
  // Keep this local to Portfolio so it does not depend on MarketsPage state.
  const muted = { color: "var(--finos-muted)", fontSize: "12px", lineHeight: 1.6 };
  
  // ----------------------------------------------------------
  // ADD INVESTMENT FORM STATE
  // ----------------------------------------------------------

  const [showInvestmentForm, setShowInvestmentForm] =
    useState(false);
  const [editingInvestmentId, setEditingInvestmentId] =
  useState(null);

  const [investmentForm, setInvestmentForm] = useState({
    name: "",
    exchange: "",
    asset_class: "Equity",
    investment_type: "Stocks",
    symbol: "",
    quantity: "",
    buy_price: "",
    current_price: "",
    buy_date: getLocalDateString(),
    broker: "",
    investment_account_id: "",
    fees: "",
    notes: "",
  });
  // Searchable instrument picker state. Uses the existing read-only market-search API.
  const [instrumentQuery, setInstrumentQuery] = useState("");
  const [instrumentResults, setInstrumentResults] = useState([]);
  const [instrumentSearchBusy, setInstrumentSearchBusy] = useState(false);
  const [instrumentSearchError, setInstrumentSearchError] = useState("");
  const [liveInstrumentQuoteLoading, setLiveInstrumentQuoteLoading] = useState(false);
  const instrumentSearchRequestRef = useRef(0);
  const selectedInstrumentQuoteRef = useRef("");
  const transactionQuoteRequestRef = useRef(0);
  const activeTransactionInstrumentRef = useRef("");
  const [brokerAccounts, setBrokerAccounts] = useState([]);
  const [brokerAccountsLoading, setBrokerAccountsLoading] = useState(false);
  const [brokerAccountsError, setBrokerAccountsError] = useState("");
  const investmentSubmitInFlightRef = useRef(false);

  // Reset every add/edit field so the two form modes never leak into each other.
  const resetInvestmentForm = () => {
    instrumentSearchRequestRef.current += 1;
    selectedInstrumentQuoteRef.current = "";
    setLiveInstrumentQuoteLoading(false);
    setInvestmentForm({ name: "", exchange: "", asset_class: "Equity", investment_type: "Stocks", symbol: "", quantity: "", buy_price: "", current_price: "", buy_date: getLocalDateString(), broker: "", investment_account_id: "", fees: "", notes: "" });
    setInstrumentQuery("");
    setInstrumentResults([]);
    setInstrumentSearchError("");
    setInstrumentSearchBusy(false);
    setEditingInvestmentId(null);
  };

  // Search the correct instrument catalogue for the selected asset category.
  // Stocks/ETFs keep using the existing market-search API; Mutual Funds use AMFI.
  const searchInvestmentInstruments = async (value) => {
    const requestId = ++instrumentSearchRequestRef.current;
    setInstrumentQuery(value);
    setInstrumentSearchError("");
    const productType = investmentForm.investment_type;
    const isMutualFund = ["Mutual Funds", "Index Funds", "Debt Mutual Funds"].includes(productType);
    const usesListedCatalogue = ["Stocks", "ETFs", "REITs"].includes(productType);
    if (!value.trim()) { setInstrumentResults([]); setInstrumentSearchBusy(false); return; }
    if (!isMutualFund && !usesListedCatalogue) {
      setInstrumentResults([]);
      setInstrumentSearchBusy(false);
      setInstrumentSearchError("This product type uses manual entry; no dedicated instrument catalogue is connected.");
      setInvestmentForm((previous) => ({ ...previous, name: value, symbol: "" }));
      return;
    }
    setInstrumentSearchBusy(true);
    try {
      const endpoint = isMutualFund
        ? `${API_BASE_URL}/api/mutual-funds/search/?query=${encodeURIComponent(value.trim())}&limit=12`
        : `${API_BASE_URL}/api/market-search/?query=${encodeURIComponent(value.trim())}&exchange=ALL&product_type=${encodeURIComponent(productType)}&limit=12`;
      const response = await apiFetch(endpoint);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : `Instrument search failed (${response.status})`;
        throw new Error(detail);
      }
      if (requestId !== instrumentSearchRequestRef.current) return;
      const safeResults = Array.isArray(data?.results)
        ? data.results.filter((item) => item && typeof item === "object").map((item) => {
            const symbol = typeof item.symbol === "string" ? item.symbol
              : (typeof item.scheme_code === "string" ? item.scheme_code
              : (typeof item.tradingsymbol === "string" ? item.tradingsymbol : ""));
            const name = isMutualFund
              ? (typeof item.scheme_name === "string" && item.scheme_name.trim() ? item.scheme_name.trim()
              : (typeof item.name === "string" && item.name.trim() ? item.name.trim() : String(symbol || "Mutual Fund Scheme")))
              : (typeof item.name === "string" ? item.name
              : (typeof item.scheme_name === "string" ? item.scheme_name
              : (typeof item.company_name === "string" ? item.company_name : String(symbol || "Instrument"))));
            return { ...item, name, symbol, exchange: typeof item.exchange === "string" ? item.exchange : (isMutualFund ? "AMFI" : "") };
          })
        : [];
      setInstrumentResults(safeResults);
      setInstrumentSearchError(safeResults.length ? "" : (isMutualFund ? "No matching mutual fund schemes found." : "No matching listed instruments found."));
    } catch (error) {
      if (requestId === instrumentSearchRequestRef.current) {
        setInstrumentResults([]);
        setInstrumentSearchError(error?.message || "Instrument search is unavailable.");
      }
    } finally {
      if (requestId === instrumentSearchRequestRef.current) setInstrumentSearchBusy(false);
    }
  };

  const selectInvestmentInstrument = (instrument) => {
    const symbol = instrument?.tradingsymbol || instrument?.symbol || "";
    const name = instrument?.name || instrument?.company_name || symbol;
    const exchange = instrument?.exchange || "";
    const quotedPrice = instrument?.last_price != null && Number(instrument.last_price) > 0
      ? String(instrument.last_price)
      : "";
    const quoteKey = isListedProductType(investmentForm.investment_type) && symbol && ["NSE", "BSE"].includes(exchange.toUpperCase())
      ? exchange.toUpperCase() + ":" + symbol
      : "";
    selectedInstrumentQuoteRef.current = quoteKey;
    setLiveInstrumentQuoteLoading(Boolean(quoteKey));
    setInvestmentForm((previous) => ({
      ...previous,
      name,
      symbol,
      exchange: exchange || (["Mutual Funds", "Index Funds", "Debt Mutual Funds"].includes(previous.investment_type) ? "AMFI" : ""),
      current_price: quotedPrice || previous.current_price,
      buy_price: previous.buy_date === getLocalDateString() && quotedPrice
        ? quotedPrice
        : previous.buy_price,
    }));
    setInstrumentQuery(name + (symbol ? " (" + symbol + ")" : ""));
    setInstrumentResults([]);

    // Close the picker immediately, then refresh the displayed quote in the background.
    if (quoteKey) {
      apiFetch(API_BASE_URL + "/api/market/quote?symbol=" + encodeURIComponent(quoteKey))
        .then(async (response) => {
          const quoteData = await response.json().catch(() => ({}));
          if (!response.ok || selectedInstrumentQuoteRef.current !== quoteKey || !(Number(quoteData?.price) > 0)) return;
          const livePrice = String(quoteData.price);
          setInvestmentForm((previous) => ({
            ...previous,
            current_price: livePrice,
            ...(previous.buy_date === getLocalDateString() ? { buy_price: livePrice } : {}),
          }));
        })
        .catch((error) => console.warn("Live investment quote unavailable; keeping the latest search quote.", error))
        .finally(() => {
          if (selectedInstrumentQuoteRef.current === quoteKey) setLiveInstrumentQuoteLoading(false);
        });
    }
  };

  // ----------------------------------------------------------
  // INVESTMENT DATA
  // ----------------------------------------------------------

  const [investments, setInvestments] = useState([]);
  const [loadingInvestments, setLoadingInvestments] = useState(true);
  const [investmentsLoadError, setInvestmentsLoadError] = useState("");
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

const [editingTransactionId, setEditingTransactionId] = useState(null);

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
    setLoadingInvestments(true);
    setInvestmentsLoadError("");
    try {
      const response = await apiFetch(
        `${API_BASE_URL}/api/investments/?user_id=${USER_ID}`
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
      setInvestmentsLoadError(error?.message || "Unable to load portfolio investments.");
    } finally {
      setLoadingInvestments(false);
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
      const response = await apiFetch(
        `${API_BASE_URL}/api/investments/${encodeURIComponent(investment.id)}?user_id=${USER_ID}`,
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

    const response = await apiFetch(
      `${API_BASE_URL}/api/investments/refresh?user_id=${USER_ID}`,
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
  setInvestmentForm({
    name: investment.name || "",
    exchange: investment.exchange || investment.instrument_exchange || "",
    asset_class: investment.asset_class || (["Stocks", "ETFs", "Mutual Funds"].includes(investment.investment_type) ? "Equity" : (["Bonds", "Fixed Deposits"].includes(investment.investment_type) ? "Fixed Income" : (["Gold", "Silver"].includes(investment.investment_type) ? "Commodities" : "Other"))),
    investment_type:
      investment.investment_type || "Stocks",
    symbol: investment.symbol || "",
    quantity: investment.quantity || "",
    buy_price: investment.buy_price || "",
    current_price: investment.current_price || "",
    buy_date: investment.buy_date || "",
    broker: investment.broker || "",
    investment_account_id: investment.investment_account_id ? String(investment.investment_account_id) : "",
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

    const response = await apiFetch(
      `${API_BASE_URL}/api/investment-transactions/?user_id=${USER_ID}&investment_id=${investmentId}`
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

  const quoteRequestId = ++transactionQuoteRequestRef.current;
  activeTransactionInstrumentRef.current = String(investment?.id) + ":" + type;
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
    transaction_date: getLocalDateString(),
    notes: "",
  });

  setInvestmentTransactions([]);
  setTransactionMessage("");

  const exchange = String(investment?.exchange || investment?.instrument_exchange || "").toUpperCase();
  const symbol = String(investment?.symbol || investment?.tradingsymbol || "").trim();
  const quoteKey = type === "BUY" && isListedProductType(investment?.investment_type) && symbol && ["NSE", "BSE"].includes(exchange)
    ? exchange + ":" + symbol
    : "";
  if (quoteKey) {
    apiFetch(API_BASE_URL + "/api/market/quote?symbol=" + encodeURIComponent(quoteKey))
      .then(async (response) => {
        const quoteData = await response.json().catch(() => ({}));
        if (!response.ok || quoteRequestId !== transactionQuoteRequestRef.current || activeTransactionInstrumentRef.current !== String(investment?.id) + ":" + type || !(Number(quoteData?.price) > 0)) return;
        const livePrice = String(quoteData.price);
        setTransactionForm((previous) => ({
          ...previous,
          ...(previous.transaction_date === getLocalDateString() ? { price: livePrice } : {}),
        }));
        setInvestments((previous) => previous.map((item) => item.id === investment.id ? { ...item, current_price: livePrice } : item));
        setTransactionModal((previous) => previous?.investment?.id === investment.id
          ? { ...previous, investment: { ...previous.investment, current_price: livePrice } }
          : previous);
      })
      .catch((error) => console.warn("Live BUY quote unavailable; keeping the latest stored price.", error));
  }

};


// ============================================================
// Consume actions initiated from Holdings or the Market instrument page.
// Match the existing investment record first so BUY/SELL never creates a duplicate holding.
useEffect(() => {
  let raw = null;
  try { raw = sessionStorage.getItem("financialOS.portfolioAction"); } catch {}
  if (!raw || !Array.isArray(investments) || loadingInvestments) return;
  if (investmentsLoadError) {
    setTransactionMessage("Portfolio could not be loaded. Your Buy/Sell action has been kept pending; refresh the portfolio and try again.");
    return;
  }
  let intent;
  try { intent = JSON.parse(raw); } catch { try { sessionStorage.removeItem("financialOS.portfolioAction"); } catch {} return; }
  const symbol = String(intent?.symbol || "").trim().toUpperCase();
  const name = String(intent?.name || "").trim().toUpperCase();
  if (!symbol && !name) return;
  const normalizeInstrument = (value) => String(value || "").trim().toUpperCase().replace(/\s+/g, " ");
  const requestedExchange = normalizeInstrument(intent?.exchange);
  const requestedInstrumentId = normalizeInstrument(intent?.instrument_id || intent?.instrumentId);
  const sameSecurity = (item) => {
    const itemSymbols = [
      item?.symbol, item?.tradingsymbol, item?.instrument_id, item?.instrumentId,
      item?.instrument_master_id, item?.instrumentMasterId,
    ].map(normalizeInstrument).filter(Boolean);
    const itemNames = [item?.name, item?.instrument_name, item?.instrumentName]
      .map(normalizeInstrument).filter(Boolean);
    return (symbol && itemSymbols.includes(symbol))
      || (requestedInstrumentId && itemSymbols.includes(requestedInstrumentId))
      || (!symbol && name && itemNames.includes(name));
  };
  const matched = investments.find((item) => {
    if (!sameSecurity(item)) return false;
    const itemExchange = normalizeInstrument(item?.exchange || item?.instrument_exchange);
    return !requestedExchange || !itemExchange || requestedExchange === itemExchange;
  }) || investments.find(sameSecurity);
  if (!matched) {
    // Keep the pending action until investments have finished loading.
    // If the instrument is not held yet, BUY starts the existing investment-entry
    // form (which creates the investment and its initial BUY ledger row exactly once).
    if (intent.type === "BUY" && !loadingInvestments) {
      try { sessionStorage.removeItem("financialOS.portfolioAction"); } catch {}
      resetInvestmentForm();
      setInvestmentForm((previous) => ({
        ...previous,
        name: intent?.name || "",
        symbol: intent?.symbol || "",
        exchange: intent?.exchange || "",
        investment_type: intent?.product_type || intent?.investment_type || "Stocks",
        product_type: intent?.product_type || intent?.investment_type || "Stocks",
        buy_date: getLocalDateString(),
      }));
      setEditingInvestmentId(null);
      setShowInvestmentForm(true);
    } else if (intent.type === "SELL" || intent.type === "EDIT") {
      try { sessionStorage.removeItem("financialOS.portfolioAction"); } catch {}
      setTransactionMessage(intent.type === "SELL"
        ? "This instrument is not in your portfolio, so there is no holding to sell."
        : "This instrument is not in your portfolio, so there is nothing to edit.");
    }
    return;
  }
  try { sessionStorage.removeItem("financialOS.portfolioAction"); } catch {}
  if (intent.type === "EDIT") {
    handleEditInvestment(matched);
  } else {
    openInvestmentTransaction(matched, intent.type === "SELL" ? "SELL" : "BUY");
  }
}, [investments, loadingInvestments, investmentsLoadError]);

// OPEN TRANSACTION HISTORY
// ============================================================

const openInvestmentTransactions = async (
  investment
) => {

  transactionQuoteRequestRef.current += 1;
  activeTransactionInstrumentRef.current = "";
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

  setEditingTransactionId(null);
  transactionQuoteRequestRef.current += 1;
  activeTransactionInstrumentRef.current = "";
  setTransactionModal(null);

  setInvestmentTransactions([]);

  setTransactionMessage("");

};


// ============================================================
// SUBMIT BUY / SELL TRANSACTION
// ============================================================

const handleInvestmentTransactionSubmit =
  async () => {

    if (transactionLoading || !transactionModal?.investment) {
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

      const fees = Number(transactionForm.fees || 0);
      if (!Number.isFinite(fees) || fees < 0) {
        setTransactionMessage("Fees must be a valid amount greater than or equal to zero.");
        return;
      }

      if (!Number.isFinite(Number(transactionForm.quantity)) || !Number.isFinite(Number(transactionForm.price))) {
        setTransactionMessage("Quantity and price must be valid numbers.");
        return;
      }

      // ------------------------------------------------------
      // TRANSACTION PAYLOAD
      // ------------------------------------------------------

      const payload = {

        user_id: USER_ID,

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

      const response = await apiFetch(
        editingTransactionId
          ? `${API_BASE_URL}/api/investment-transactions/${editingTransactionId}`
          : `${API_BASE_URL}/api/investment-transactions/`,
        {
          method: editingTransactionId ? "PUT" : "POST",

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
            `Unable to ${editingTransactionId ? "update" : "create"} ${transactionType} transaction.`
        );

      }

      // ------------------------------------------------------
      // SUCCESS
      // ------------------------------------------------------

      setTransactionMessage(
        `${transactionType} transaction ${editingTransactionId ? "updated" : "created"} successfully.`
      );

      // Refresh transaction history
      setEditingTransactionId(null);
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
        transaction_date: getLocalDateString(),
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
          `Unable to ${editingTransactionId ? "update" : "create"} ${transactionType} transaction.`
      );

    } finally {

      setTransactionLoading(false);

    }

  };
  
  const loadBrokerAccounts = async () => {
    setBrokerAccountsLoading(true);
    setBrokerAccountsError("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/accounts/`);
      const data = await response.json().catch(() => []);
      if (!response.ok) throw new Error(data?.detail || "Unable to load broker cash accounts.");
      setBrokerAccounts((Array.isArray(data) ? data : []).filter(
        (account) => String(account.account_type || "").trim().toLowerCase() === "investment" && account.is_active !== false
      ));
    } catch (error) {
      setBrokerAccountsError(error?.message || "Unable to load broker cash accounts.");
      setBrokerAccounts([]);
    } finally {
      setBrokerAccountsLoading(false);
    }
  };

  useEffect(() => {
    loadInvestments();
    loadBrokerAccounts();
  }, []);
  
  // ----------------------------------------------------------
  // INVESTMENT FORM FIELD STYLE
  // ----------------------------------------------------------

  const investmentFieldStyle = {
    width: "100%",
    boxSizing: "border-box",
    padding: "11px 12px",
    borderRadius: "10px",
    border: "1px solid var(--finos-border)",
    background: "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
    color: "var(--finos-text)",
    fontSize: "12px",
    outline: "none",
  };


  // ==========================================================
  // SAVE INVESTMENT + CREATE INITIAL BUY TRANSACTION
  // ==========================================================

  const handleInvestmentSubmit = async () => {
    if (investmentSubmitInFlightRef.current) return;
    investmentSubmitInFlightRef.current = true;
    try {
      // --------------------------------------------------------
      // VALIDATION
      // --------------------------------------------------------

      if (liveInstrumentQuoteLoading) {
        alert("Please wait while the latest market price is being refreshed.");
        return;
      }
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
      if (
        !editingInvestmentId &&
        isListedProductType(investmentForm.investment_type) &&
        investmentForm.buy_date === getLocalDateString() &&
        Number(investmentForm.current_price) > 0 &&
        Number(investmentForm.buy_price) !== Number(investmentForm.current_price)
      ) {
        alert("For a purchase dated today, the buy price must match the latest available market price.");
        return;
      }

      if (!investmentForm.investment_account_id) {
        alert("Please select an active Investment / Broker Cash account. Fund it through Money → Transfers before buying.");
        return;
      }
      if (!editingInvestmentId && (!investmentForm.name.trim() || !investmentForm.symbol.trim())) {
        alert("Please search for and select an instrument from the results before adding an investment.");
        return;
      }

      // --------------------------------------------------------
      // INVESTMENT PAYLOAD
      // --------------------------------------------------------

      const selectedBrokerAccount = brokerAccounts.find(
        (account) => Number(account.id) === Number(investmentForm.investment_account_id)
      );
      if (!selectedBrokerAccount) {
        alert("The selected broker cash account is unavailable. Refresh the account list and select an active Investment account.");
        return;
      }
      const existingInvestment = editingInvestmentId
        ? investments.find((item) => Number(item.id) === Number(editingInvestmentId))
        : null;
      const selectedBrokerLabel = selectedBrokerAccount.institution || selectedBrokerAccount.name;

      const payload = {
        user_id: USER_ID,
        investment_account_id: Number(selectedBrokerAccount.id),

        name:
          investmentForm.name.trim(),

        investment_type:
          investmentForm.investment_type,

        asset_class: investmentForm.asset_class || "Other",
        product_type: investmentForm.investment_type,
        instrument_id: investmentForm.symbol.trim() || investmentForm.name.trim().toUpperCase(),
        exchange: investmentForm.exchange || null,

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
          (editingInvestmentId ? existingInvestment?.broker : selectedBrokerLabel) || selectedBrokerLabel,

        fees:
          Number(investmentForm.fees || 0),

        notes:
          investmentForm.notes.trim() || null,
      };

      // --------------------------------------------------------
      // CREATE / UPDATE INVESTMENT
      // --------------------------------------------------------

      const url = editingInvestmentId
        ? `${API_BASE_URL}/api/investments/${editingInvestmentId}`
        : `${API_BASE_URL}/api/investments/`;

      const response = await apiFetch(
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
          user_id: USER_ID,

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
          await apiFetch(
            `${API_BASE_URL}/api/investment-transactions/`,
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
            await apiFetch(
              `${API_BASE_URL}/api/investments/${data.id}`,
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
    } finally {
      investmentSubmitInFlightRef.current = false;
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
      className="investment-workspace"
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
        className="portfolio-header"
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
              color: "var(--finos-muted)",
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
                <label style={{ display: "block", marginBottom: "6px", color: "var(--finos-muted)", fontSize: "12px" }}>Investment Instrument</label>
                <input type="text" value={investmentForm.name} onChange={(event) => setInvestmentForm((previous) => ({ ...previous, name: event.target.value }))} required style={investmentFieldStyle} />
                <div style={{ ...muted, marginTop: "5px" }}>Editing the existing investment. Instrument search is only required when adding a new investment.</div>
              </div>
            ) : (
              <div style={{ gridColumn: "1 / -1", position: "relative" }}>
                {["Stocks", "ETFs", "REITs", "Mutual Funds", "Index Funds", "Debt Mutual Funds"].includes(investmentForm.investment_type) ? (
                  <>
                    <label style={{ display: "block", marginBottom: "6px", color: "var(--finos-muted)", fontSize: "12px" }}>Investment Instrument (required)</label>
                    <input type="text" autoComplete="off" placeholder={["Mutual Funds", "Index Funds", "Debt Mutual Funds"].includes(investmentForm.investment_type) ? "Search mutual fund scheme" : "Search listed instrument, e.g. HDFC Bank"} value={instrumentQuery || investmentForm.name} onChange={(event) => searchInvestmentInstruments(event.target.value)} style={investmentFieldStyle} />
                    {instrumentSearchBusy && <div style={{ ...muted, marginTop: "5px" }}>Searching {["Mutual Funds", "Index Funds", "Debt Mutual Funds"].includes(investmentForm.investment_type) ? "fund schemes" : "listed instruments"}…</div>}
                    {instrumentSearchError && <div role="status" style={{ color: "var(--finos-muted)", fontSize: "12px", marginTop: "5px" }}>{instrumentSearchError}</div>}
                    {instrumentResults.length > 0 && <div className="instrument-search-results" role="listbox" aria-label="Instrument search results" style={{ position: "absolute", zIndex: 20, top: "100%", left: 0, right: 0, maxHeight: "240px", overflowY: "auto" }}>
                      {instrumentResults.map((instrument, index) => {
                        const displayName = instrument.scheme_name || instrument.name || instrument.company_name || instrument.tradingsymbol || instrument.symbol;
                        const isMutualFund = ["Mutual Funds", "Index Funds", "Debt Mutual Funds"].includes(investmentForm.investment_type);
                        const planSource = `${instrument.plan_type || ""} ${instrument.plan || ""} ${displayName}`;
                        const planMatch = isMutualFund && /\bdirect(?:\s+plan)?\b/i.test(planSource) ? "Direct Plan" : (isMutualFund && /\bregular(?:\s+plan)?\b/i.test(planSource) ? "Regular Plan" : "");
                        const optionSource = `${instrument.option_type || ""} ${instrument.option || ""} ${instrument.scheme_option || ""}`;
                        const optionMatch = isMutualFund && /\bidcw\b/i.test(optionSource) ? "IDCW" : (isMutualFund && /\bgrowth\b/i.test(optionSource) ? "Growth" : (isMutualFund && /\bbonus\b/i.test(optionSource) ? "Bonus" : ""));
                        return <button key={`${instrument.scheme_code || instrument.instrument_token || instrument.tradingsymbol || instrument.symbol}-${index}`} type="button" onClick={() => selectInvestmentInstrument({ ...instrument, name: isMutualFund ? `${displayName}${planMatch ? ` - ${planMatch}` : ""}${optionMatch ? ` - ${optionMatch}` : ""}` : displayName })} className="instrument-search-result" role="option" style={{ display: "block", width: "100%", padding: "10px 12px", textAlign: "left", cursor: "pointer" }}>
                          <strong>{displayName}</strong>{!isMutualFund && instrument.exchange && <span style={{ marginLeft: "8px", fontSize: "10px", fontWeight: 700 }}>{instrument.exchange}{instrument.series ? ` ${instrument.series}` : ""}</span>}
                          {planMatch && <span style={{ marginLeft: "8px", fontSize: "10px" }}>{planMatch}</span>}{optionMatch && <span style={{ marginLeft: "6px", fontSize: "10px" }}>{optionMatch}</span>}
                          <div className="instrument-search-result-meta" style={{ marginTop: "4px", fontSize: "11px" }}>{instrument.scheme_code ? `Scheme Code: ${instrument.scheme_code}` : (instrument.tradingsymbol || instrument.symbol)}{isMutualFund ? " · AMFI" : ""}</div>
                        </button>;
                      })}
                    </div>}
                  </>
                ) : (
                  <>
                    <label style={{ display: "block", marginBottom: "6px", color: "var(--finos-muted)", fontSize: "12px" }}>Investment Name (manual entry)</label>
                    <input type="text" value={investmentForm.name} onChange={(event) => setInvestmentForm((previous) => ({ ...previous, name: event.target.value, symbol: "" }))} placeholder={investmentForm.investment_type === "Fixed Deposits" ? "Bank / issuer name" : investmentForm.investment_type === "Recurring Deposits" ? "Bank / RD name" : `Enter ${investmentForm.investment_type} name`} required style={investmentFieldStyle} />
                    <div style={{ ...muted, marginTop: "5px" }}>No dedicated catalogue is connected for this product type. Enter its details manually.</div>
                  </>
                )}
                {investmentForm.name && <div style={{ ...muted, marginTop: "5px" }}>Selected/entered: {investmentForm.name}{investmentForm.symbol ? ` · ${investmentForm.symbol}` : ""}{investmentForm.exchange ? ` · ${investmentForm.exchange}` : ""}</div>}
              </div>
            )}

            {/* ASSET CLASS — high-level investment classification */}
            <div>
              <label style={{ display: "block", marginBottom: "6px", color: "var(--finos-muted)", fontSize: "12px" }}>Asset Class</label>
              <StyledSelect className="finos-select"
                value={investmentForm.asset_class || "Equity"}
                onChange={(event) => {
                  const nextAssetClass = event.target.value;
                  const nextTypes = PRODUCT_TYPES_BY_ASSET_CLASS[nextAssetClass] || ["Other"];
                  instrumentSearchRequestRef.current += 1;
                  selectedInstrumentQuoteRef.current = "";
                  setLiveInstrumentQuoteLoading(false);
                  setInstrumentSearchBusy(false);
                  setInvestmentForm((previous) => ({ ...previous, asset_class: nextAssetClass, investment_type: nextTypes[0], name: "", symbol: "", buy_price: "", current_price: "" }));
                  setInstrumentQuery("");
                  setInstrumentResults([]);
                  setInstrumentSearchError("");
                }}
                style={{ width: "100%", boxSizing: "border-box", padding: "11px 12px", borderRadius: "10px", border: "1px solid var(--finos-border)", background: "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))", color: "var(--finos-text)", fontSize: "12px", outline: "none" }}
              >
                <option value="Equity">Equity</option>
                <option value="Fixed Income">Fixed Income</option>
                <option value="Commodities">Commodities</option>
                <option value="Real Estate">Real Estate</option>
                <option value="Digital Assets">Digital Assets</option>
                <option value="Alternatives">Alternatives</option>
                <option value="Other">Other</option>
              </StyledSelect>
            </div>

            {/* PRODUCT TYPE — existing investment-type catalogue */}
            <div>
            <label style={{ display: "block", marginBottom: "6px", color: "var(--finos-muted)", fontSize: "12px" }}>Product Type</label>
            <StyledSelect className="finos-select"
              value={investmentForm.investment_type}
              onChange={(event) => {
                const nextType = event.target.value;
                instrumentSearchRequestRef.current += 1;
                selectedInstrumentQuoteRef.current = "";
                setLiveInstrumentQuoteLoading(false);
                setInstrumentSearchBusy(false);
                setInvestmentForm((previous) => ({
                  ...previous,
                  investment_type: nextType,
                  name: "",
                  symbol: "",
                  buy_price: "",
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
                  "1px solid var(--finos-border)",
                background:
                  "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
                color: "var(--finos-text)",
                fontSize: "12px",
                outline: "none",
              }}
            >
              {(PRODUCT_TYPES_BY_ASSET_CLASS[investmentForm.asset_class || "Equity"] || ["Other"]).map((productType) => (
                <option key={productType} value={productType}>{productType}</option>
              ))}
            </StyledSelect>
            </div>

            {/* Symbol is selected in Add mode and editable in Edit mode. */}
            <input
              type="text"
              placeholder={editingInvestmentId ? "Symbol" : "Select an instrument above to populate symbol"}
              value={investmentForm.symbol}
              readOnly={!editingInvestmentId}
              required={!editingInvestmentId}
              onChange={(event) => setInvestmentForm((previous) => ({ ...previous, symbol: event.target.value }))}
              style={{ width: "100%", boxSizing: "border-box", padding: "11px 12px", borderRadius: "10px", border: "1px solid var(--finos-border)", background: "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))", color: "var(--finos-text)", fontSize: "12px", outline: "none" }}
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
                  "1px solid var(--finos-border)",
                background:
                  "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
                color: "var(--finos-text)",
                fontSize: "12px",
                outline: "none",
              }}
            />


            {/* BUY PRICE */}

            <input
              type="number"
              placeholder="Buy price"
              value={investmentForm.buy_price}
              readOnly={!editingInvestmentId && isListedProductType(investmentForm.investment_type) && investmentForm.buy_date === getLocalDateString() && Number(investmentForm.current_price) > 0}
              onChange={(event) =>
                setInvestmentForm({
                  ...investmentForm,
                  buy_price: event.target.value,
                })
              }
              title={!editingInvestmentId && isListedProductType(investmentForm.investment_type) && investmentForm.buy_date === getLocalDateString() ? "Today's purchase uses the latest available market price. Select a past date to enter a historical price." : "Enter the actual purchase price."}
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "10px",
                border:
                  "1px solid var(--finos-border)",
                background:
                  "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
                color: "var(--finos-text)",
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
        color: "var(--finos-muted)",
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
              onChange={(event) => {
                const nextDate = event.target.value;
                setInvestmentForm((previous) => ({
                  ...previous,
                  buy_date: nextDate,
                  ...(nextDate === getLocalDateString() && isListedProductType(previous.investment_type) && Number(previous.current_price) > 0
                    ? { buy_price: String(previous.current_price) }
                    : {}),
                }));
              }}
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "11px 12px",
                borderRadius: "10px",
                border:
                  "1px solid var(--finos-border)",
                background:
                  "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
                color: "var(--finos-text)",
                fontSize: "12px",
                outline: "none",
                colorScheme: "dark",
              }}
            />


            {/* BROKER CASH ACCOUNT — sourced from Money → Accounts; no provider names hardcoded */}
            <div>
              <label style={{ display: "block", marginBottom: "6px", color: "var(--finos-muted)", fontSize: "12px" }}>Broker cash account (required)</label>
              <StyledSelect className="finos-select"
                value={String(investmentForm.investment_account_id || "")}
                onChange={(event) => {
                  const accountId = event.target.value;
                  const account = brokerAccounts.find((item) => String(item.id) === String(accountId));
                  setInvestmentForm((previous) => ({
                    ...previous,
                    investment_account_id: accountId,
                    broker: account ? (account.institution || account.name) : "",
                  }));
                }}
                disabled={brokerAccountsLoading || brokerAccounts.length === 0}
                required
                aria-label="Broker cash account"
                style={{ width: "100%", boxSizing: "border-box", padding: "11px 12px", borderRadius: "10px", border: "1px solid var(--finos-border)", background: "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))", color: "var(--finos-text)", fontSize: "12px", outline: "none" }}
              >
                <option value="">{brokerAccountsLoading ? "Loading Investment accounts…" : "Select broker cash account…"}</option>
                {brokerAccounts.map((account) => (
                  <option key={account.id} value={String(account.id)}>
                    {account.name}{account.institution ? ` — ${account.institution}` : ""} · Available ₹{Number(account.balance || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                  </option>
                ))}
              </StyledSelect>
              {brokerAccountsError && <p role="alert" style={{ margin: "6px 0 0", color: "var(--finos-danger, #dc2626)", fontSize: "12px" }}>{brokerAccountsError}</p>}
              {!brokerAccountsLoading && brokerAccounts.length === 0 && <p style={{ margin: "6px 0 0", color: "var(--finos-muted)", fontSize: "12px" }}>Create an account with type “Investment” in Money → Accounts, then transfer funds into it.</p>}
              <p style={{ margin: "6px 0 0", color: "var(--finos-muted)", fontSize: "11px" }}>BUY and SELL cash movements affect only this selected Investment account.</p>
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
                  "1px solid var(--finos-border)",
                background:
                  "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
                color: "var(--finos-text)",
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
                  "1px solid var(--finos-border)",
                background:
                  "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
                color: "var(--finos-text)",
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
    color: var(--finos-text);
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
  className="glass-card portfolio-summary-card"
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
                color: "var(--finos-muted)",
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
                color: "var(--finos-muted)",
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
          className="glass-card portfolio-performance-card"
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
                  color: "var(--finos-muted)",
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
                          : "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
                      border:
                        "1px solid var(--finos-border)",
                      color:
                        index === 3
                          ? "#d8b4fe"
                          : "var(--finos-muted)",
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
                "1px dashed var(--finos-border)",
              background:
                "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
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
      color: "var(--finos-muted)",
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
      color: "var(--finos-muted)",
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
          className="glass-card portfolio-asset-allocation-card"
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
              color: "var(--finos-muted)",
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
                    color: "var(--finos-muted)",
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
              color: "var(--finos-muted)",
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
        className="glass-card portfolio-holdings-preview"
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
                color: "var(--finos-muted)",
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
              color: "var(--finos-muted)",
              background:
                "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
              border:
                "1px solid var(--finos-border)",
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
      "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
    border:
      "1px solid var(--finos-border)",
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
              "var(--finos-muted)",
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
          className="portfolio-holding-preview-item"
          style={{
            display: "grid",
            gridTemplateColumns:
              "minmax(0, 1fr) auto",
            gap: "12px",
            alignItems: "center",
            padding: "14px",
            borderRadius: "12px",
            background:
              "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
            border:
              "1px solid var(--finos-border)",
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
                  "var(--finos-muted)",
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
                  "var(--finos-muted)",
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
      color: "var(--finos-muted)",
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
      color: "var(--finos-muted)",
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
      color: "var(--finos-muted)",
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
      color: "var(--finos-positive)",
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
      color: "var(--finos-negative)",
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
    color: "var(--finos-negative)",
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
        className="glass-card investment-transaction-modal"
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
                color: "var(--finos-muted)",
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
                  ? "var(--finos-positive)"
                  : "var(--finos-muted)",
            }}
            onClick={() => {
              setEditingTransactionId(null);
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
                  ? "var(--finos-negative)"
                  : "var(--finos-muted)",
            }}
            onClick={() => {
              setEditingTransactionId(null);
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

              setEditingTransactionId(null);
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
                    "var(--finos-muted)",
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
                  "var(--finos-muted)",
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
                  "var(--finos-muted)",
              }}
            >
              Price
            </label>

            <input
              type="number"
              min="0"
              step="any"
              value={transactionForm.price}
              readOnly={transactionForm.transaction_date === getLocalDateString() && isListedProductType(investment?.investment_type) && Number(investment?.current_price) > 0}
              onChange={(event) =>
                setTransactionForm((previous) => ({
                  ...previous,
                  price:
                    event.target.value,
                }))
              }
              placeholder="Enter price"
              title={transactionForm.transaction_date === getLocalDateString() && isListedProductType(investment?.investment_type) ? "Today's purchase uses the latest available market price. Select a past date to enter a historical price." : "Enter the actual transaction price."}
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
                  "var(--finos-muted)",
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
                  "var(--finos-muted)",
              }}
            >
              Transaction Date
            </label>

            <input
              type="date"
              value={
                transactionForm.transaction_date
              }
              onChange={(event) => {
                const nextDate = event.target.value;
                setTransactionForm((previous) => ({
                  ...previous,
                  transaction_date: nextDate,
                  ...(nextDate === getLocalDateString() && isListedProductType(investment?.investment_type) && Number(investment?.current_price) > 0
                    ? { price: String(investment.current_price) }
                    : {}),
                }));
              }}
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
                  "var(--finos-muted)",
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
                    "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
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
                : editingTransactionId ? `Save ${transactionType} Changes` : `Confirm ${transactionType}`}
            </button>

          </div>

        )}


        {/* =================================================
            TRANSACTION HISTORY
        ================================================= */}

        {transactionModal.mode === "history" && (

          <div className="portfolio-transaction-history">

            <div
              style={{
                marginBottom: "12px",
                fontSize: "13px",
                fontWeight: 800,
              }}
            >
              Transaction History
            </div>

            {transactionMessage && (
              <div style={{ marginBottom: "12px", padding: "10px", borderRadius: "10px", background: "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))", fontSize: "11px" }}>
                {transactionMessage}
              </div>
            )}

            {transactionHistoryLoading ? (

              <div
                style={{
                  padding: "30px 10px",
                  textAlign: "center",
                  fontSize: "12px",
                  color:
                    "var(--finos-muted)",
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
                    "var(--finos-muted)",
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
                          "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
                        border:
                          "1px solid var(--finos-border)",
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
                                  ? "var(--finos-positive)"
                                  : "var(--finos-negative)",
                            }}
                          >
                            {transaction.transaction_type}
                          </div>

                          <div
                            style={{
                              marginTop: "4px",
                              fontSize: "10px",
                              color:
                                "var(--finos-muted)",
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
                                "var(--finos-muted)",
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
                              "var(--finos-muted)",
                          }}
                        >
                          {transaction.notes}
                        </div>

                      )}

                      <div style={{ display: "flex", gap: "8px", marginTop: "10px", flexWrap: "wrap" }}>
                        {(transaction.status || "ACTIVE") === "ACTIVE" && (
                          <>
                            <button type="button" className="small-button" disabled={transactionLoading} onClick={() => {
                              setEditingTransactionId(transaction.id);
                              setTransactionType(transaction.transaction_type);
                              setTransactionForm({
                                quantity: String(transaction.quantity ?? ""),
                                price: String(transaction.price ?? ""),
                                fees: String(transaction.fees ?? 0),
                                transaction_date: String(transaction.transaction_date || "").slice(0, 10),
                                notes: transaction.notes || "",
                              });
                              setTransactionModal({ ...transactionModal, mode: "form" });
                              setTransactionMessage("Editing this ledger transaction. Save to validate the complete holding timeline.");
                            }}>Edit transaction</button>
                            <button type="button" className="small-button" disabled={transactionLoading} onClick={async () => {
                              const reason = window.prompt("Reason for voiding this transaction (required):");
                              if (reason === null) return;
                              if (reason.trim().length < 3) {
                                setTransactionMessage("Enter a reason of at least 3 characters to void this transaction.");
                                return;
                              }
                              try {
                                setTransactionLoading(true);
                                setTransactionMessage("");
                                const response = await apiFetch(`${API_BASE_URL}/api/investment-transactions/${transaction.id}/void`, {
                                  method: "POST",
                                  headers: { "Content-Type": "application/json" },
                                  body: JSON.stringify({ reason: reason.trim() }),
                                });
                                const data = await response.json().catch(() => ({}));
                                if (!response.ok) throw new Error(data?.detail || "Unable to void transaction.");
                                setTransactionMessage("Transaction voided. Its audit history has been preserved.");
                                await loadInvestmentTransactions(transactionModal.investment.id);
                                await loadInvestments();
                              } catch (error) {
                                setTransactionMessage(error?.message || "Unable to void transaction.");
                              } finally {
                                setTransactionLoading(false);
                              }
                            }}>Void transaction</button>
                          </>
                        )}
                        {(transaction.status || "ACTIVE") !== "ACTIVE" && (
                          <span style={{ fontSize: "11px", color: "var(--finos-muted)" }}>Voided — audit record retained</span>
                        )}
                      </div>

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
// ACCOUNT COMPLETION — personal profile, KYC, employment, tax,
// salary structure, and connection readiness in one guided page.
// Profile data is persisted by the authenticated backend identity.
// ============================================================
function AccountCompletionPage() {
  const emptyProfile = {
    legal_name: "", display_name: "", date_of_birth: "", pan: "", aadhaar_last4: "",
    kyc_method: "manual", kyc_status: "not_verified", tax_residency: "India",
    employment_type: "salaried", employer_name: "", job_title: "", business_name: "",
    business_type: "", gstin: "", financial_year: "2026-27", tax_regime: "undecided",
    salary_source: "manual", salary_frequency: "monthly", gross_salary: "", salary_received: "",
    basic_salary: "", hra: "", da: "0", other_allowances: "", bonus: "", commission: "",
    employee_pf: "0", professional_tax: "0", tds: "0", other_deductions: "",
    broker_connection: "not_connected", bank_connection: "manual_entry"
  };
  const [profile, setProfile] = useState(emptyProfile);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [activeSection, setActiveSection] = useState("Basic Profile");
  const [accountEmail, setAccountEmail] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [emailBusy, setEmailBusy] = useState(false);
  const [emailMsg, setEmailMsg] = useState({ kind: "", text: "" });
  const sections = ["Basic Profile", "KYC", "Employment & Income", "Tax Information", "Salary Setup", "Financial Connections"];
  useEffect(() => {
    let active = true;
    apiFetch(`${API_BASE_URL}/api/profile/me`, { cache: "no-store" })
      .then(async response => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || `Profile load failed (${response.status})`);
        if (active) { setProfile({ ...emptyProfile, ...(data.profile || {}) }); setAccountEmail(data.user?.email || ""); }
      })
      .catch(err => { if (active) setError(err.message || "Unable to load profile."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  const update = (key, value) => setProfile(prev => ({ ...prev, [key]: value }));
  const fieldsBySection = {
    "Basic Profile": [
      ["legal_name", "Full legal name", "text", "Name as shown on PAN"],
      ["display_name", "Display name / nickname", "text", "Optional"],
      ["date_of_birth", "Date of birth", "date", ""],
      ["phone", "Phone number", "tel", "e.g. +919876543210"],
      ["tax_residency", "Tax residency", "select", ["India", "Non-resident / other"]]
    ],
    "KYC": [
      ["pan", "PAN", "text", "ABCDE1234F"],
      ["aadhaar_last4", "Aadhaar last 4 digits (optional)", "text", "Store only last four digits here"],
      ["kyc_method", "Verification method", "select", ["manual", "DigiLocker (planned)"]]
    ],
    "Employment & Income": [
      ["employment_type", "Income profile", "select", ["salaried", "self_employed", "business_owner", "freelancer", "retired", "student", "other"]],
      ["employer_name", "Employer / company name", "text", "For salaried users"],
      ["job_title", "Job title / profession", "text", ""],
      ["business_name", "Business name", "text", "For business / professional users"],
      ["business_type", "Business / professional type", "text", ""],
      ["gstin", "GSTIN (if applicable)", "text", "Optional"]
    ],
    "Tax Information": [
      ["financial_year", "Financial year", "select", ["2025-26", "2026-27", "2027-28"]],
      ["tax_regime", "Preferred tax regime", "select", ["undecided", "new", "old"]]
    ],
    "Salary Setup": [
      ["salary_source", "Salary details source", "select", ["manual", "Form 16 upload (planned)", "salary slip upload (planned)"]],
      ["salary_frequency", "Salary frequency", "select", ["monthly", "annual"]],
      ["gross_salary", "Gross salary (₹)", "number", "Before deductions"],
      ["salary_received", "Salary received / in-hand (₹)", "number", "Actual credited amount"],
      ["basic_salary", "Basic salary (₹)", "number", ""], ["hra", "HRA (₹)", "number", ""],
      ["da", "Dearness allowance (₹)", "number", ""], ["other_allowances", "Other allowances (₹)", "number", ""],
      ["bonus", "Bonus (₹)", "number", ""], ["commission", "Commission (₹)", "number", ""],
      ["employee_pf", "Employee PF (₹)", "number", ""], ["professional_tax", "Professional tax (₹)", "number", ""],
      ["tds", "TDS (₹)", "number", ""], ["other_deductions", "Other deductions (₹)", "number", ""]
    ],
    "Financial Connections": [
      ["bank_connection", "Bank connection", "select", ["manual_entry", "Open banking (planned)"]],
      ["broker_connection", "Broker connection", "select", ["not_connected", "m.Stock", "Other broker (manual for now)"]]
    ]
  };
  const visibleFields = fieldsBySection[activeSection] || [];
  const totalSections = sections.length;
  const sectionComplete = section => {
    const keys = { "Basic Profile": ["legal_name", "date_of_birth"], "KYC": ["pan"], "Employment & Income": ["employment_type"], "Tax Information": ["financial_year", "tax_regime"], "Salary Setup": profile.employment_type === "salaried" ? ["gross_salary", "salary_received"] : [], "Financial Connections": ["bank_connection"] }[section] || [];
    return keys.length === 0 || keys.every(key => String(profile[key] || "").trim());
  };
  const completed = sections.filter(sectionComplete).length;
  const save = async () => {
    setSaving(true); setError(""); setNotice("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/profile/me`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ profile }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Save failed (${response.status})`);
      setNotice("Profile saved. Tax calculations will use these details only where the tax engine supports them.");
    } catch (err) { setError(err.message || "Unable to save profile."); }
    finally { setSaving(false); }
  };
  const changeEmail = async () => {
    setEmailMsg({ kind: "", text: "" });
    if (!newEmail.trim() || !emailPassword) {
      setEmailMsg({ kind: "error", text: "Enter the new email and your current password." });
      return;
    }
    setEmailBusy(true);
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/profile/email`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_email: newEmail.trim(), current_password: emailPassword }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Email change failed (${response.status})`);
      setAccountEmail(data.user?.email || newEmail.trim().toLowerCase());
      setNewEmail("");
      setEmailPassword("");
      setEmailMsg({ kind: "ok", text: `Email updated. Use the new address next time you sign in.${data.admin_notice ? " " + data.admin_notice : ""}` });
    } catch (err) {
      setEmailMsg({ kind: "error", text: err.message || "Unable to change email." });
    } finally {
      setEmailBusy(false);
    }
  };
  const inputStyle = { width: "100%", boxSizing: "border-box", borderRadius: "10px", padding: "11px 12px", color: "var(--finos-text, inherit)", background: "var(--t-inner-bg, var(--t-card-bg, transparent))", border: "1px solid var(--finos-border, currentColor)" };
  return <div className="dashboard">
    <section className="welcome-section"><div><p className="welcome-label">ACCOUNT</p><h2>Account <span>completion.</span></h2><p className="welcome-description">Complete your profile once. These details will support KYC, tax preparation, and future account connections.</p></div></section>
    <AccountContactSettings />
    <section className="metrics-grid"><MetricCard title="Profile progress" value={`${Math.round(completed / totalSections * 100)}%`} change={`${completed} of ${totalSections} sections ready`} positive icon={CircleDollarSign} /><MetricCard title="KYC status" value={profile.kyc_status === "verified" ? "Verified" : "Not verified"} change="Name/PAN entry alone does not verify identity" icon={Receipt} /></section>
    <section className="glass-card" style={{ padding: "18px", marginBottom: "18px" }}><div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>{sections.map(section => <button key={section} type="button" onClick={() => setActiveSection(section)} className={activeSection === section ? "primary-button" : "secondary-button"} style={{ padding: "9px 12px" }}>{section}{sectionComplete(section) ? " ✓" : ""}</button>)}</div></section>
    <section className="glass-card" style={{ padding: "22px" }}><h3 style={{ marginTop: 0 }}>{activeSection}</h3>
      {loading ? <p>Loading your profile…</p> : <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>{visibleFields.map(([key, label, type, hint]) => <label key={key} style={{ display: "grid", gap: "7px", fontSize: "13px", color: "var(--finos-text, inherit)" }}><span>{label}</span>{type === "select" ? <StyledSelect value={profile[key] || ""} onChange={e => update(key, e.target.value)}>{hint.map(option => <option key={option} value={option}>{option === "salaried" ? "Salaried" : option === "self_employed" ? "Self-employed / professional" : option === "business_owner" ? "Business owner" : option === "undecided" ? "Not decided" : option === "new" ? "New regime" : option === "old" ? "Old regime" : option.replaceAll("_", " ")}</option>)}</StyledSelect> : <input style={inputStyle} type={type} value={profile[key] ?? ""} placeholder={hint || "Enter value"} onChange={e => update(key, e.target.value)} min={type === "number" ? "0" : undefined} />}</label>)}</div>}

      {activeSection === "KYC" && <p style={{ color: "var(--finos-muted, inherit)", lineHeight: 1.6, marginTop: "18px" }}>PAN and legal-name similarity can flag a mismatch, but cannot prove identity or PAN ownership. Official PAN verification and DigiLocker consent-based verification are not connected yet. Do not enter your full Aadhaar number here.</p>}
      {activeSection === "Salary Setup" && <p style={{ color: "var(--finos-muted, inherit)", lineHeight: 1.6, marginTop: "18px" }}>Enter the structure manually if you do not have Form 16 or a salary slip. Salary transactions remain separate: recording ₹25,000 received will not create another income record when you save this structure. Upload and reconciliation are planned, not active in this build.</p>}
      {error && <p role="alert" style={{ color: "var(--finos-danger, #b42318)", marginTop: "16px" }}>{error}</p>}{notice && <p role="status" style={{ color: "var(--finos-success, #087443)", marginTop: "16px" }}>{notice}</p>}
      <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", marginTop: "22px", flexWrap: "wrap" }}><button type="button" className="secondary-button" disabled={sections.indexOf(activeSection) === 0} onClick={() => setActiveSection(sections[Math.max(0, sections.indexOf(activeSection) - 1)])}>Previous</button><div style={{ display: "flex", gap: "10px" }}><button type="button" className="primary-button" onClick={save} disabled={saving || loading}>{saving ? "Saving…" : "Save profile"}</button><button type="button" className="secondary-button" disabled={sections.indexOf(activeSection) === totalSections - 1} onClick={() => setActiveSection(sections[Math.min(totalSections - 1, sections.indexOf(activeSection) + 1)])}>Next</button></div></div>
    </section>
  </div>;
}


// ============================================================
// ACCOUNTS
// ============================================================


function TradingControlSettings({ compact = false }) {
  const API = API_BASE_URL;
  const [tradingControl, setTradingControl] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let cancelled = false;
    apiFetch(`${API}/api/broker-orders/trading-control`, { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || `Trading control unavailable (${response.status})`);
        return data;
      })
      .then((data) => { if (!cancelled) setTradingControl(data); })
      .catch((err) => { if (!cancelled) setError(err.message || "Unable to read live-trading status."); });
    return () => { cancelled = true; };
  }, []);

  const toggleTradingControl = async () => {
    if (busy) return;

    // If the initial status request failed (for example, the deployed backend
    // still returns 404), keep this control clickable so an admin can retry.
    // Never send a PUT or infer the current switch state while status is unknown.
    if (!tradingControl) {
      setBusy(true);
      setError("");
      setNotice("");
      try {
        const response = await apiFetch(`${API}/api/broker-orders/trading-control`, { cache: "no-store" });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || `Trading control unavailable (${response.status})`);
        setTradingControl(data);
        setNotice("Trading status refreshed. Review the displayed state before changing it.");
      } catch (err) {
        setError(err.message || "Unable to read live-trading status.");
      } finally {
        setBusy(false);
      }
      return;
    }

    const enabled = !tradingControl.enabled;
    if (enabled && !window.confirm("Enable new real-money orders through Financial OS? Check every order before submitting.")) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const response = await apiFetch(`${API}/api/broker-orders/trading-control`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ enabled }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Unable to update trading switch (${response.status})`);
      setTradingControl(data);
      setNotice(enabled ? "New Financial OS real-money orders are enabled." : "New Financial OS real-money orders are blocked.");
    } catch (err) {
      setError(err.message || "Unable to update live-trading status.");
    } finally {
      setBusy(false);
    }
  };

  const enabled = Boolean(tradingControl?.enabled);
  if (compact) return <div style={{ padding: "10px 12px", borderTop: "1px solid var(--finos-border, rgba(255,255,255,.12))", borderBottom: "1px solid var(--finos-border, rgba(255,255,255,.12))" }} aria-labelledby="live-trading-settings-title">
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
      <strong id="live-trading-settings-title" style={{ fontSize: 13 }}>Live Trading</strong>
      <span role="status" aria-live="polite" style={{ fontSize: 10, fontWeight: 800, color: tradingControl === null ? "var(--finos-muted, #999)" : enabled ? "#22c55e" : "#ef4444" }}>{tradingControl === null ? "UNKNOWN" : enabled ? "ON" : "OFF"}</span>
    </div>
    <button type="button" onClick={toggleTradingControl} disabled={busy} aria-pressed={enabled} style={{ width: "auto", maxWidth: "100%", marginTop: 8, padding: "6px 9px", minHeight: 30, borderRadius: 8, border: "1px solid var(--finos-border, rgba(255,255,255,.18))", background: enabled ? "rgba(239,68,68,.12)" : "rgba(34,197,94,.12)", color: "inherit", cursor: busy ? "not-allowed" : "pointer", opacity: busy ? .6 : 1, font: "inherit", fontSize: 11, lineHeight: 1.2, fontWeight: 700, whiteSpace: "normal" }}>
      {busy ? (tradingControl ? "Saving…" : "Checking…") : tradingControl === null ? "Retry status check" : enabled ? "Turn Trading OFF" : "Turn Trading ON"}
    </button>
    {error && <p role="alert" style={{ color: "var(--finos-negative, #ef4444)", fontSize: 11, lineHeight: 1.4 }}>{error}</p>}
    {notice && <p role="status" style={{ color: "var(--finos-positive, #22c55e)", fontSize: 11, lineHeight: 1.4 }}>{notice}</p>}
    <p style={{ color: "var(--finos-muted, rgba(255,255,255,.62))", fontSize: 10, lineHeight: 1.4, marginBottom: 0 }}>Admin-only. OFF blocks new Financial OS orders.</p>
  </div>;
  return <section className="glass-card" style={{ padding: "22px", marginBottom: "16px" }} aria-labelledby="live-trading-settings-title">
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px", flexWrap: "wrap" }}>
      <div style={{ minWidth: 0, flex: "1 1 280px" }}>
        <p className="finos-theme-eyebrow">ACCOUNT SETTINGS</p>
        <h3 id="live-trading-settings-title" style={{ marginTop: 4 }}>Live Trading</h3>
        <p style={{ color: "var(--finos-muted, rgba(255,255,255,0.68))", lineHeight: 1.6, marginBottom: 0 }}>Control whether new real-money orders can be submitted through Financial OS. Turning this OFF blocks new submissions; it does not cancel orders already accepted by the broker.</p>
      </div>
      <span role="status" aria-live="polite" style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "8px 12px", borderRadius: 999, border: `1px solid ${tradingControl === null ? "var(--finos-border, rgba(255,255,255,0.2))" : enabled ? "rgba(34,197,94,.65)" : "rgba(239,68,68,.65)"}`, background: tradingControl === null ? "var(--finos-surface, rgba(255,255,255,.04))" : enabled ? "rgba(34,197,94,.12)" : "rgba(239,68,68,.10)", fontWeight: 700, fontSize: 12, letterSpacing: ".03em" }}>
        <span aria-hidden="true" style={{ width: 7, height: 7, borderRadius: "50%", background: tradingControl === null ? "var(--finos-muted, #999)" : enabled ? "#22c55e" : "#ef4444" }} />
        {tradingControl === null ? "STATUS UNAVAILABLE" : enabled ? "LIVE TRADING ON" : "LIVE TRADING OFF"}
      </span>
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", marginTop: 18 }}>
      <button type="button" className={enabled ? "secondary-button" : "primary-button"} onClick={toggleTradingControl} disabled={busy} aria-pressed={enabled}>
        {busy ? "Saving…" : enabled ? "Turn LIVE TRADING OFF" : "Turn LIVE TRADING ON"}
      </button>
      <span style={{ color: "var(--finos-muted, rgba(255,255,255,0.62))", fontSize: 12 }}>{busy ? "Saving account setting…" : "Admin-only control · saved on the server"}</span>
    </div>
    {error && <p role="alert" style={{ color: "var(--finos-negative, #ef4444)", marginBottom: 0 }}>{error}</p>}
    {notice && <p role="status" style={{ color: "var(--finos-positive, #22c55e)", marginBottom: 0 }}>{notice}</p>}
    <p style={{ color: "var(--finos-muted, rgba(255,255,255,0.62))", fontSize: 12, lineHeight: 1.6, marginBottom: 0, marginTop: 12 }}>If the API or database migration is unavailable, this control stays unavailable and new orders remain blocked. Enabling this switch permits new Financial OS submissions; review each order carefully.</p>
  </section>;
}

function SettingsPage({ onNavigate, selectedTheme, onThemeChange }) {
  return <div className="dashboard finos-settings-page">
    <section className="welcome-section"><div><p className="welcome-label">PREFERENCES & HISTORY</p><h2>Settings</h2><p className="welcome-description">Personalize your workspace. Your theme is saved on this device and applies throughout Financial OS.</p></div></section>
    <section className="finos-theme-settings glass-card">
      <div className="finos-theme-settings-heading"><div><p className="finos-theme-eyebrow">APPEARANCE</p><h3>Choose your theme</h3><p>19 visual styles. Select a preview to apply it immediately.</p></div><span className="finos-theme-current">Current: {selectedTheme}</span></div>
      <div className="finos-theme-settings-grid">
        {FINOS_THEMES.map((theme) => <button type="button" key={theme} aria-pressed={selectedTheme === theme} onClick={() => onThemeChange(theme)} className={`finos-theme-option finos-theme-option-${theme.toLowerCase().replaceAll(" ", "-")} ${selectedTheme === theme ? "is-active" : ""}`}>
          <span className="finos-theme-sample" aria-hidden="true"><i/><i/><i/><b/></span>
          <span className="finos-theme-option-copy"><strong>{theme}</strong><small>{FINOS_THEME_DESCRIPTIONS[theme]}</small></span>
          <span className="finos-theme-radio" aria-hidden="true">{selectedTheme === theme ? "✓" : ""}</span>
        </button>)}
      </div>
      <p className="finos-theme-footnote">Default remains the standard Financial OS look. Elegant Plain is a clean white theme with thin borders and minimal visual decoration. Theme selection changes appearance only, not your records or calculations.</p>
    </section>
    <TradingControlSettings />
    <AccountContactSettings />
    <section className="glass-card" style={{ padding: "22px", marginBottom: "16px" }}><h3>Account Profile</h3><p style={{ color: "var(--finos-muted, rgba(255,255,255,0.62))", lineHeight: 1.6 }}>Manage your personal details, tax information, and salary setup. This is separate from your bank and investment accounts.</p><button className="primary-button" onClick={() => onNavigate("Account Profile")}>Open Account Profile</button></section>
    <section className="glass-card" style={{ padding: "22px" }}><h3>Finance Diary</h3><p style={{ color: "var(--finos-muted, rgba(255,255,255,0.62))", lineHeight: 1.6 }}>Read-only master history of account and transaction activity. Entries cannot be edited or deleted.</p><button className="primary-button" onClick={() => onNavigate("Finance Diary")}>Open Finance Diary</button></section>
  </div>;
}

function FinanceDiaryPage() {
  const API_BASE_URL = "https://wealthmanager.duckdns.org";
  const USER_ID = getCurrentUserId();
  const [entries, setEntries] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        setLoading(true);
        const response = await apiFetch(`${API_BASE_URL}/api/finance-diary/?user_id=${USER_ID}&limit=500`);
        const data = await response.json().catch(() => []);
        if (!response.ok) throw new Error(data?.detail || "Unable to load Finance Diary.");
        if (active) setEntries(Array.isArray(data) ? data : []);
      } catch (err) { if (active) setError(err.message || "Unable to load Finance Diary."); }
      finally { if (active) setLoading(false); }
    })();
    return () => { active = false; };
  }, []);
  const filtered = entries.filter((entry) => `${entry.event_type} ${entry.entity_type} ${entry.entity_id} ${entry.description} ${entry.snapshot_json || ""}`.toLowerCase().includes(search.toLowerCase()));
  return <div className="dashboard"><section className="welcome-section"><div><p className="welcome-label">PERMANENT HISTORY</p><h2>Finance Diary</h2><p className="welcome-description">Read-only activity history. Existing entries are never edited or deleted through this interface.</p></div></section><section className="glass-card" style={{ padding: "20px" }}><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search history..." style={{ width: "100%", boxSizing: "border-box", padding: "12px", borderRadius: "10px", marginBottom: "16px" }} />{loading ? <p>Loading history…</p> : error ? <p>{error}</p> : filtered.length === 0 ? <p>No diary entries found. New account and transaction activity will appear here when recorded by the backend.</p> : <div style={{ display: "grid", gap: "10px" }}>{filtered.map((entry) => <article key={entry.id} style={{ padding: "14px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.09)", background: "rgba(255,255,255,0.025)" }}><div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}><strong>{entry.event_type} · {entry.entity_type} #{entry.entity_id || "—"}</strong><span style={{ color: "rgba(255,255,255,0.48)", fontSize: "11px" }}>{entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}</span></div><p style={{ margin: "8px 0", color: "rgba(255,255,255,0.72)" }}>{entry.description}</p>{entry.snapshot_json && <details><summary style={{ cursor: "pointer" }}>View event details</summary><pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontSize: "11px" }}>{(() => { try { return JSON.stringify(JSON.parse(entry.snapshot_json), null, 2); } catch { return entry.snapshot_json; } })()}</pre></details>}</article>)}</div>}</section></div>;
}



function ChartOfAccountsPage() {
  const API_BASE_URL = "https://wealthmanager.duckdns.org";
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showDisabled, setShowDisabled] = useState(false);

  const loadAccounts = async () => {
    setLoading(true); setError("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/chart-of-accounts/?include_disabled=${showDisabled}`);
      if (!response.ok) throw new Error(`Chart of Accounts API returned ${response.status}`);
      const data = await response.json();
      // The checkbox is a view filter: unchecked shows enabled accounts only;
      // checked shows disabled accounts only (not both sets).
      const accounts = Array.isArray(data) ? data : [];
      setRows(accounts.filter((account) => showDisabled ? !account.is_enabled : account.is_enabled));
    } catch (e) { setError(e.message || "Unable to load Chart of Accounts."); }
    finally { setLoading(false); }
  };
  useEffect(() => { loadAccounts(); }, [showDisabled]);

  const toggleAccount = async (row) => {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/chart-of-accounts/${row.id}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_enabled: !row.is_enabled }),
      });
      if (!response.ok) throw new Error(`Update failed (${response.status})`);
      await loadAccounts();
    } catch (e) { setError(e.message || "Unable to update account."); }
  };
  const grouped = rows.reduce((acc, row) => { (acc[row.account_type] ||= []).push(row); return acc; }, {});
  // Match the Financial OS dark glass / purple accent theme used throughout the app.
  const card = {
    background: "linear-gradient(145deg, rgba(26, 31, 57, 0.96), rgba(15, 20, 39, 0.96))",
    border: "1px solid rgba(167, 139, 250, 0.16)",
    borderRadius: 16,
    padding: 18,
    marginBottom: 14,
    boxShadow: "0 10px 28px rgba(0, 0, 0, 0.12)",
    color: "rgba(255,255,255,0.88)",
  };
  const cell = {
    textAlign: "left",
    padding: "11px 10px",
    borderBottom: "1px solid rgba(255,255,255,0.075)",
    fontSize: 12,
    color: "rgba(235,238,255,0.82)",
    whiteSpace: "nowrap",
  };
  const headerCell = { ...cell, color: "rgba(255,255,255,0.94)", fontWeight: 650, fontSize: 11, letterSpacing: ".02em" };
  return <section className="dashboard coa-page">
    <div className="coa-page-heading" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap", marginBottom: 18 }}>
      <div><p className="welcome-label" style={{ marginBottom: 6 }}>MONEY · ACCOUNTING</p><h2 style={{ margin: 0 }}>Chart of Accounts</h2><p className="welcome-description" style={{ margin: "6px 0 0" }}>Your accounting account catalogue. Stable account codes support consistent reporting.</p></div>
      <label className="coa-filter" style={{ display: "inline-flex", gap: 9, alignItems: "center", fontSize: 12, color: "rgba(255,255,255,0.78)", padding: "9px 12px", borderRadius: 10, background: "rgba(255,255,255,0.035)", border: "1px solid rgba(255,255,255,0.08)" }}><input type="checkbox" checked={showDisabled} onChange={(e) => setShowDisabled(e.target.checked)} style={{ accentColor: "#a855f7" }} /> Show disabled accounts only</label>
    </div>
    {error && <div role="alert" style={{ ...card, color: "#fecaca", borderColor: "rgba(248,113,113,0.32)", background: "rgba(127,29,29,0.18)" }}>{error}</div>}
    {loading ? <div className="glass-card" style={{ ...card, padding: 20 }}>Loading Chart of Accounts…</div> : Object.entries(grouped).map(([kind, accounts]) => <div key={kind} className="glass-card coa-section-card" style={card}>
      <h3 className="coa-section-title" style={{ margin: "0 0 12px", fontSize: 15, fontWeight: 650, color: "#fff" }}>{kind === "Asset" ? "Assets" : kind === "Liability" ? "Liabilities" : `${kind}s`} <span style={{ fontSize: 12, fontWeight: 400, color: "#b7a4ff" }}>({accounts.length})</span></h3>
      <div className="coa-table-scroll" style={{ overflowX: "auto", borderRadius: 10 }}><table className="coa-table" style={{ width: "100%", borderCollapse: "collapse", minWidth: 620 }}><thead><tr>
        {["Code", "Account", "Parent", "Tax mapping", "Status", ""].map((label) => <th key={label} style={headerCell}>{label}</th>)}
      </tr></thead><tbody>{accounts.map((row) => <tr key={row.id} style={{ background: row.is_enabled ? "transparent" : "rgba(255,255,255,0.018)" }}>
        <td style={{ ...cell, color: "#c4b5fd", fontVariantNumeric: "tabular-nums" }}>{row.code}</td><td style={{ ...cell, color: "rgba(255,255,255,0.94)" }}>{row.name}{row.is_system ? <span style={{ marginLeft: 8, color: "#a99acb", fontSize: 10 }}>Standard</span> : null}</td>
        <td style={cell}>{rows.find((candidate) => candidate.id === row.parent_id)?.name || "—"}</td><td style={cell}>{row.tax_mapping_key || "—"}</td>
        <td style={cell}><span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: row.is_enabled ? "#86efac" : "#fca5a5" }}><span style={{ width: 6, height: 6, borderRadius: "50%", background: row.is_enabled ? "#34d399" : "#f87171" }} />{row.is_enabled ? "Enabled" : "Disabled"}</span></td><td style={cell}><button type="button" className={row.is_enabled ? "secondary-button" : "primary-button"} onClick={() => toggleAccount(row)} style={{ padding: "6px 10px", fontSize: 11, whiteSpace: "nowrap" }}>{row.is_enabled ? "Disable" : "Enable"}</button></td>
      </tr>)}</tbody></table></div>
    </div>)}
    {!loading && !rows.length && <div className="glass-card" style={card}>No accounts found.</div>}
  </section>;
}

function LedgerPage() {
  const API_BASE_URL = "https://wealthmanager.duckdns.org";
  const [entries, setEntries] = useState([]);
  const [totalDebit, setTotalDebit] = useState(0);
  const [totalCredit, setTotalCredit] = useState(0);
  const [loading, setLoading] = useState(true);
  const [backfilling, setBackfilling] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadLedger = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/ledger/`);
      if (!response.ok) throw new Error(`Ledger API returned ${response.status}`);
      const data = await response.json();
      setEntries(Array.isArray(data.entries) ? data.entries : []);
      setTotalDebit(Number(data.total_debit || 0));
      setTotalCredit(Number(data.total_credit || 0));
    } catch (e) {
      setError(e.message || "Unable to load the accounting ledger.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadLedger(); }, []);

  const backfillLedger = async () => {
    setBackfilling(true);
    setMessage("");
    setError("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/ledger/backfill`, { method: "POST" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Ledger backfill returned ${response.status}`);
      setMessage(`${data.posted || 0} historical transactions posted; ${data.skipped_count || 0} skipped for review.`);
      await loadLedger();
    } catch (e) {
      setError(e.message || "Unable to backfill historical ledger entries.");
    } finally {
      setBackfilling(false);
    }
  };

  const money = (value) => new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 2,
  }).format(Number(value || 0));
  const card = { border: "1px solid rgba(255,255,255,.1)", borderRadius: "16px", background: "rgba(255,255,255,.035)", padding: "18px" };
  const muted = { color: "rgba(255,255,255,.62)", fontSize: "12px" };
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.005;

  return <div className="dashboard ledger-page" style={{ display: "grid", gap: "18px" }}>
    <section className="welcome-section">
      <div>
        <p className="welcome-label">MONEY / ACCOUNTING</p>
        <h2>Ledger</h2>
        <p className="welcome-description">Persistent double-entry records generated from Money transactions.</p>
      </div>
      <button className="primary-button" onClick={backfillLedger} disabled={backfilling || loading}>
        {backfilling ? "Posting historical records…" : "Post Historical Transactions"}
      </button>
    </section>
    <section className="metrics-grid">
      <div style={card}><div style={muted}>Ledger lines</div><strong style={{ display: "block", fontSize: "25px", marginTop: "8px" }}>{loading ? "Loading…" : entries.length}</strong></div>
      <div style={card}><div style={muted}>Total debits</div><strong style={{ display: "block", fontSize: "25px", marginTop: "8px" }}>{loading ? "Loading…" : money(totalDebit)}</strong></div>
      <div style={card}><div style={muted}>Total credits</div><strong style={{ display: "block", fontSize: "25px", marginTop: "8px" }}>{loading ? "Loading…" : money(totalCredit)}</strong></div>
      <div style={card}><div style={muted}>Ledger status</div><strong style={{ display: "block", fontSize: "20px", marginTop: "8px", color: isBalanced ? "#86efac" : "#fca5a5" }}>{loading ? "Checking…" : isBalanced ? "Balanced" : "Needs review"}</strong></div>
    </section>
    {message && <div role="status" style={{ ...card, color: "#86efac" }}>{message}</div>}
    {error && <div role="alert" style={{ ...card, color: "#fca5a5" }}>{error}</div>}
    <section className="glass-card" style={{ overflowX: "auto" }}>
      <div className="card-header"><div><p className="card-label">DOUBLE-ENTRY ACCOUNTING</p><h3>Ledger Entries</h3></div><span className="score">{entries.length}</span></div>
      <p style={{ ...muted, margin: "0 0 14px" }}>Each source transaction is represented by balanced debit and credit lines. Historical transactions can be posted once using the button above; unsupported legacy records are reported for review.</p>
      {loading ? <div className="empty-chart">Loading ledger…</div> : entries.length === 0 ? <div className="empty-chart">No posted ledger entries yet. Use “Post Historical Transactions” to create entries for existing transactions.</div> : <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "900px", fontSize: "13px" }}>
        <thead><tr>{["Date", "Account", "Financial Account", "Description", "Transaction", "Debit", "Credit"].map((label) => <th key={label} style={{ textAlign: label === "Debit" || label === "Credit" ? "right" : "left", padding: "12px 10px", borderBottom: "1px solid rgba(255,255,255,.12)", color: "rgba(255,255,255,.65)" }}>{label}</th>)}</tr></thead>
        <tbody>{entries.map((row) => <tr key={row.id}>
          {[row.date, `${row.account_code} · ${row.account_name}`, row.financial_account_name || "—", row.description, `TX-${row.transaction_id}`].map((value, i) => <td key={i} style={{ padding: "12px 10px", borderBottom: "1px solid rgba(255,255,255,.06)" }}>{value || "—"}</td>)}
          <td style={{ textAlign: "right", padding: "12px 10px", borderBottom: "1px solid rgba(255,255,255,.06)" }}>{Number(row.debit) ? money(row.debit) : "—"}</td>
          <td style={{ textAlign: "right", padding: "12px 10px", borderBottom: "1px solid rgba(255,255,255,.06)" }}>{Number(row.credit) ? money(row.credit) : "—"}</td>
        </tr>)}</tbody>
        <tfoot><tr><th colSpan="5" style={{ textAlign: "right", padding: "12px 10px" }}>Totals</th><th style={{ textAlign: "right", padding: "12px 10px" }}>{money(totalDebit)}</th><th style={{ textAlign: "right", padding: "12px 10px" }}>{money(totalCredit)}</th></tr></tfoot>
      </table>}
    </section>
  </div>;
}

function Accounts() {

  // ----------------------------------------------------------
  // STATE
  // ----------------------------------------------------------

  const [accounts, setAccounts] = useState([]);
  const [activeAccountTab, setActiveAccountTab] = useState("bank");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

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
    credit_limit: "",
    loan_principal: "",
    loan_disbursed: "",
    loan_interest_rate: "",
    loan_tenure_months: "",
    loan_emi_amount: "",
    loan_start_date: new Date().toISOString().slice(0, 10),
    loan_first_payment_date: "",
    loan_interest_type: "reducing_balance",
    loan_repayment_frequency: "monthly",
  });

  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://wealthmanager.duckdns.org";

  const USER_ID = getCurrentUserId();

  // ----------------------------------------------------------
  // LOAD ACCOUNTS
  // Keep this function in component scope so deleteAccount can
  // refresh the list after a successful deactivation.
  // ----------------------------------------------------------

  const loadAccounts = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await apiFetch(
        `${API_BASE_URL}/api/accounts/?user_id=${USER_ID}`
      );

      if (!response.ok) {
        throw new Error(`Accounts API error: ${response.status}`);
      }

      const data = await response.json();
      setAccounts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Accounts API error:", err);
      setError("Unable to load accounts.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
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

    if (accountForm.account_type !== "loan" && (accountForm.balance === "" || !Number.isFinite(Number(accountForm.balance)) || Number(accountForm.balance) < 0)) {
      setError("Please enter a valid non-negative opening balance or outstanding amount.");
      return;
    }
    const isCreditAccount = ["credit_card", "credit_line"].includes(accountForm.account_type);
    if (isCreditAccount && (accountForm.credit_limit === "" || Number(accountForm.credit_limit) <= 0 || Number(accountForm.balance) < 0)) {
      setError("Enter a positive credit limit and a non-negative opening outstanding amount.");
      return;
    }
    if (isCreditAccount && Number(accountForm.balance) > Number(accountForm.credit_limit)) {
      setError("Opening outstanding amount cannot exceed the credit limit.");
      return;
    }
    if (accountForm.account_type === "loan" && (!accountForm.loan_principal || Number(accountForm.loan_principal) <= 0 || !accountForm.loan_disbursed || Number(accountForm.loan_disbursed) <= 0 || Number(accountForm.loan_disbursed) > Number(accountForm.loan_principal) || !accountForm.loan_start_date)) {
      setError("Enter a valid loan principal, disbursed amount, and start date. Disbursed amount cannot exceed principal.");
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
          balance: accountForm.account_type === "loan" ? Number(accountForm.loan_principal) : Number(accountForm.balance),
          credit_limit: isCreditAccount ? Number(accountForm.credit_limit) : null,
        }
      : {
          user_id: USER_ID,
          name: accountForm.name.trim(),
          account_type: accountForm.account_type,
          institution: accountForm.institution.trim(),
          account_number: accountForm.account_number.trim(),
          currency: accountForm.currency,
          balance: accountForm.account_type === "loan" ? Number(accountForm.loan_principal) : Number(accountForm.balance),
          credit_limit: isCreditAccount ? Number(accountForm.credit_limit) : null,
        };

    const response = await apiFetch(
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

    if (!isEditing && accountForm.account_type === "loan") {
      const loanPayload = {
        user_id: USER_ID,
        name: accountForm.name.trim(),
        lender_name: accountForm.institution.trim(),
        loan_type: "term_loan",
        principal_amount: Number(accountForm.loan_principal),
        amount_disbursed: Number(accountForm.loan_disbursed),
        linked_account_id: data.id,
        interest_rate: accountForm.loan_interest_rate === "" ? null : Number(accountForm.loan_interest_rate),
        interest_type: accountForm.loan_interest_type,
        tenure_months: accountForm.loan_tenure_months === "" ? null : Number(accountForm.loan_tenure_months),
        emi_amount: accountForm.loan_emi_amount === "" ? null : Number(accountForm.loan_emi_amount),
        start_date: accountForm.loan_start_date,
        first_payment_date: accountForm.loan_first_payment_date || null,
        repayment_frequency: accountForm.loan_repayment_frequency,
      };
      const loanResponse = await apiFetch(`${API_BASE_URL}/api/loans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loanPayload),
      });
      const loanResult = await loanResponse.json();
      if (!loanResponse.ok) {
        throw new Error(loanResult?.detail || "Account was created, but loan setup failed. Open Loan Management and link or complete the loan record.");
      }
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
      credit_limit: "",
      loan_principal: "",
      loan_disbursed: "",
      loan_interest_rate: "",
      loan_tenure_months: "",
      loan_emi_amount: "",
      loan_start_date: new Date().toISOString().slice(0, 10),
      loan_first_payment_date: "",
      loan_interest_type: "reducing_balance",
      loan_repayment_frequency: "monthly",
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

    const response = await apiFetch(
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
    credit_limit: account.credit_limit ?? "",
    loan_principal: "",
    loan_disbursed: "",
    loan_interest_rate: "",
    loan_tenure_months: "",
    loan_emi_amount: "",
    loan_start_date: new Date().toISOString().slice(0, 10),
    loan_first_payment_date: "",
    loan_interest_type: "reducing_balance",
    loan_repayment_frequency: "monthly",
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
    const response = await apiFetch(
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

  const totalBalance = accounts.reduce((total, account) => {
    const tab = String(account.account_type || account.type || "").trim().toLowerCase().replace(/[ -]+/g, "_");
    if (["credit_card", "creditcard", "credit_card_account", "credit_line", "creditline", "credit_line_account", "cash_credit", "cash_credit_account", "overdraft", "od", "loan", "loan_account", "personal_loan", "home_loan", "term_loan"].includes(tab)) return total;
    return total + Number(account.balance || 0);
  }, 0);

  const accountTypeKey = (account) => String(account.account_type || account.type || "").trim().toLowerCase().replace(/[ -]+/g, "_");
  const accountTabs = [
    { id: "bank", label: "Banks", types: ["bank", "savings", "savings_account", "current", "current_account", "checking", "checking_account"] },
    { id: "cash", label: "Cash", types: ["cash", "cash_account"] },
    { id: "wallet", label: "Wallets", types: ["wallet", "digital_wallet", "payment_wallet"] },
    { id: "credit_card", label: "Credit Cards", types: ["credit_card", "creditcard", "credit_card_account"] },
    { id: "loan", label: "Loan Accounts", types: ["loan", "loan_account", "personal_loan", "home_loan", "term_loan"] },
    { id: "credit_line", label: "Credit Lines", types: ["credit_line", "creditline", "credit_line_account", "cash_credit", "cash_credit_account", "overdraft", "od"] },
    { id: "broker", label: "Broker Accounts", types: ["broker", "brokerage", "broker_account", "trading_account", "investment", "investment_account"] },
    { id: "other", label: "Others", types: [] },
  ];
  const categorizedAccountIds = new Set(accountTabs.filter((tab) => tab.id !== "other").flatMap((tab) =>
    accounts.filter((account) => tab.types.includes(accountTypeKey(account))).map((account) => account.id)
  ));
  const accountTabFor = (account) => accountTabs.find((tab) => tab.id !== "other" && tab.types.includes(accountTypeKey(account)))?.id || "other";
  const selectedAccountTab = accountTabs.find((tab) => tab.id === activeAccountTab) || accountTabs[0];
  const visibleAccounts = accounts.filter((account) => accountTabFor(account) === selectedAccountTab.id);

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (

    <div className="dashboard money-workspace money-accounts">

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

      {/* Contact details belong on the Accounts page as requested. */}
      <AccountContactSettings />

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

<div role="tablist" aria-label="Account categories" style={{ display: "flex", flexWrap: "wrap", gap: "8px", margin: "4px 0 16px" }}>
        {accountTabs.map((tab) => {
          const count = tab.id === "other"
            ? accounts.filter((account) => accountTabFor(account) === "other").length
            : accounts.filter((account) => tab.types.includes(accountTypeKey(account))).length;
          return (
            <button key={tab.id} type="button" role="tab" aria-selected={activeAccountTab === tab.id} onClick={() => setActiveAccountTab(tab.id)} className={activeAccountTab === tab.id ? "primary-button" : "secondary-button"} style={{ padding: "9px 13px", whiteSpace: "nowrap" }}>
              {tab.label} <span style={{ opacity: .75, marginLeft: "4px" }}>{count}</span>
            </button>
          );
        })}
      </div>

{!loading && (
  <div className={`account-list-grid${selectedAccountTab.id === "credit_card" ? " credit-card-grid" : " account-strip-list"}`}>
    {visibleAccounts.length > 0 ? visibleAccounts.map((account) => (

      <div
        key={account.id}
        className={["credit_card", "creditcard", "credit_card_account"].includes(accountTypeKey(account)) ? "account-strip-item account-credit-card" : "account-strip-item"}
      >

        {/* Realistic credit-card face; other account types retain their existing card layout. */}
        {["credit_card", "creditcard", "credit_card_account"].includes(String(account.account_type || account.type || "").trim().toLowerCase().replace(/[ -]+/g, "_")) && (
          <div style={{ position: "relative", overflow: "hidden", minHeight: "158px", padding: "17px 18px", borderRadius: "16px", color: "#fff", background: "linear-gradient(135deg, #172554 0%, #4338ca 52%, #7c3aed 100%)", boxShadow: "0 10px 24px rgba(49,46,129,.24)", boxSizing: "border-box", display: "flex", flexDirection: "column", justifyContent: "space-between", gap: "16px" }}>
            <div style={{ position: "absolute", width: "190px", height: "190px", borderRadius: "50%", right: "-62px", top: "-92px", background: "rgba(255,255,255,.10)", pointerEvents: "none" }} />
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px", position: "relative" }}>
              <div><div style={{ fontSize: "10px", letterSpacing: ".15em", textTransform: "uppercase", color: "rgba(255,255,255,.72)" }}>Credit Card</div><div style={{ fontSize: "13px", fontWeight: 750, marginTop: "4px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "220px" }}>{account.institution || "Financial Institution"}</div></div>
              <Landmark size={24} style={{ flexShrink: 0, opacity: .92 }} />
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", position: "relative" }}>
              <div style={{ width: "35px", height: "26px", borderRadius: "6px", background: "linear-gradient(135deg,#f5e7b2,#c7a96b)", border: "1px solid rgba(255,255,255,.35)", display: "grid", gridTemplateColumns: "1fr 1fr", overflow: "hidden", flexShrink: 0 }}><span style={{ borderRight: "1px solid rgba(90,70,30,.28)", borderBottom: "1px solid rgba(90,70,30,.28)" }} /><span style={{ borderBottom: "1px solid rgba(90,70,30,.28)" }} /><span style={{ borderRight: "1px solid rgba(90,70,30,.28)" }} /><span /></div>
              <span style={{ fontSize: "13px", letterSpacing: ".13em", color: "rgba(255,255,255,.92)" }}>{account.account_number ? "•••• •••• •••• " + String(account.account_number).replace(/\D/g, "").slice(-4) : "•••• •••• •••• ••••"}</span>
            </div>
            <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: "10px", position: "relative" }}>
              <div style={{ minWidth: 0 }}><div style={{ fontSize: "9px", letterSpacing: ".12em", textTransform: "uppercase", color: "rgba(255,255,255,.66)" }}>Cardholder</div><div style={{ fontSize: "12px", fontWeight: 700, marginTop: "3px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{account.name}</div></div>
              <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".08em", whiteSpace: "nowrap", opacity: .92 }}>CREDIT</div>
            </div>
          </div>
        )}

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
              background: "var(--finos-account-icon-bg, linear-gradient(135deg, rgba(168,85,247,.30), rgba(236,72,153,.20)))",
              border: "1px solid var(--finos-account-icon-border, rgba(255,255,255,.10))",
            }}
          >
            <Landmark size={21} />
          </div>

          {/* DETAILS */}

          <div className="account-strip-details" style={{ minWidth: 0 }}>
            <div className="account-strip-name">
              {account.name}
            </div>

            <div className="account-strip-institution">
              {account.institution || "Financial Account"}
              {" • "}
              {account.type}
            </div>

            {account.account_number && !["credit_card", "creditcard", "credit_card_account"].includes(String(account.account_type || account.type || "").trim().toLowerCase().replace(/[ -]+/g, "_")) && (
              <div className="account-strip-number">
                {account.account_number}
              </div>
            )}

            <div
              className={`account-strip-status ${account.is_active ? "is-active" : "is-inactive"}`}
              aria-label={account.is_active ? "Active account" : "Inactive account"}
              title={account.is_active ? "Active" : "Inactive"}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                marginTop: "6px",
                fontSize: "10px",
                color: account.is_active ? "#4ade80" : "#f87171",
              }}
            >
              <span
                aria-hidden="true"
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  background: account.is_active ? "#4ade80" : "#f87171",
                }}
              />
              {account.is_active ? "Active" : "Inactive"}
            </div>
          </div>

        </div>


        {/* BALANCE */}

        <div
          style={{
            textAlign: "left",
            minWidth: 0,
            paddingTop: ["credit_card", "creditcard", "credit_card_account"].includes(accountTypeKey(account)) ? "12px" : "0",
            borderTop: ["credit_card", "creditcard", "credit_card_account"].includes(accountTypeKey(account)) ? "1px solid var(--finos-border, rgba(167,139,250,.16))" : "none",
          }}
        >

          <div
            style={{
              fontSize: "10px",
              color: "var(--finos-account-muted, var(--finos-muted, rgba(255,255,255,.45)))",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              marginBottom: "5px",
            }}
          >
            {["credit_card", "credit_line", "credit line"].includes(String(account.account_type || "").toLowerCase()) ? "Outstanding" : String(account.account_type || "").toLowerCase() === "loan" ? "Loan Principal" : "Balance"}
          </div>

          <div
            style={{
              fontSize: "17px",
              fontWeight: 800,
              color: "var(--finos-account-title, var(--finos-text, #ffffff))",
              whiteSpace: "nowrap",
            }}
          >
            {formatCurrency(account.balance)}
          </div>
          {["credit_card", "credit_line", "credit line"].includes(String(account.account_type || "").toLowerCase()) && (
            <div style={{ marginTop: "6px", fontSize: "11px", color: "var(--finos-account-muted, var(--finos-muted, #94a3b8))", lineHeight: 1.45 }}>
              <div>Credit limit: {formatCurrency(account.credit_limit)}</div>
              <div>Available credit: {formatCurrency(Math.max(0, Number(account.credit_limit || 0) - Number(account.balance || 0)))}</div>
              <div style={{ marginTop: "3px" }}>Outstanding is a liability; available credit is not an asset.</div>
            </div>
          )}

        </div>


{/* ACCOUNT ACTIONS */}
<div
  style={{
    display: "flex",
    flexDirection: ["credit_card", "creditcard", "credit_card_account"].includes(accountTypeKey(account)) ? "column" : "row",
    flexWrap: "wrap",
    gap: "7px",
    alignItems: "stretch",
    minWidth: 0,
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

          )) : (
      <div className="empty-chart" style={{ padding: "24px 12px" }}>
        <strong>No {selectedAccountTab.label.toLowerCase()} found</strong>
        <span>Add an account in this category to see it here.</span>
      </div>
    )}
  </div>
)}

        {/* ==================================================
            ACCOUNT FORM MODAL — compact, responsive dialog
            Existing save/edit handlers and API payload are preserved.
        ================================================== */}
        {showAccountForm && (
          <div
            role="presentation"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget && !accountSaving) {
                setShowAccountForm(false);
                setEditingAccount(null);
              }
            }}
            className="account-form-overlay"
          >
            <section
              role="dialog"
              aria-modal="true"
              aria-labelledby="account-form-title"
              className="glass-card account-form-dialog"
            >
              <header className="account-form-header">
                <div>
                  <p className="card-label account-form-eyebrow">MONEY · ACCOUNTS</p>
                  <h3 id="account-form-title" className="account-form-title">
                    {editingAccount ? "Edit account" : "Add a new account"}
                  </h3>
                  <p className="account-form-description">
                    Enter the account details below. Fields marked * are required.
                  </p>
                </div>
                <button
                  type="button"
                  aria-label="Close account form"
                  onClick={() => { if (!accountSaving) { setShowAccountForm(false); setEditingAccount(null); } }}
                  disabled={accountSaving}
                  className="account-form-close"
                >×</button>
              </header>

              <div className="account-form-fields">
                {[
                  { key: "name", label: "Account name *", placeholder: "e.g. Salary Account", type: "text", required: true },
                  { key: "account_type", label: "Account type *", type: "select", required: true },
                  { key: "institution", label: "Bank / Institution", placeholder: "e.g. HDFC Bank", type: "text" },
                  { key: "account_number", label: "Account number", placeholder: "Enter account number (optional)", type: "text" },
                  ...(accountForm.account_type !== "loan" ? [{ key: "balance", label: ["credit_card", "credit_line"].includes(accountForm.account_type) ? "Opening outstanding amount (₹) *" : "Opening balance (₹) *", placeholder: "0.00", type: "number", required: true }] : []),
                  ...(["credit_card", "credit_line"].includes(accountForm.account_type) ? [
                    { key: "credit_limit", label: "Approved credit limit (₹) *", placeholder: "e.g. 100000", type: "number", required: true },
                  ] : []),
                  ...(accountForm.account_type === "loan" ? [
                    { key: "loan_principal", label: "Original loan principal (₹) *", placeholder: "e.g. 500000", type: "number", required: true },
                    { key: "loan_disbursed", label: "Amount disbursed (₹) *", placeholder: "e.g. 500000", type: "number", required: true },
                    { key: "loan_interest_rate", label: "Annual interest rate (%)", placeholder: "e.g. 8.5", type: "number" },
                    { key: "loan_tenure_months", label: "Tenure (months)", placeholder: "e.g. 240", type: "number" },
                    { key: "loan_emi_amount", label: "EMI amount (₹)", placeholder: "e.g. 42000", type: "number" },
                    { key: "loan_start_date", label: "Loan start date *", type: "date", required: true },
                    { key: "loan_first_payment_date", label: "First payment date", type: "date" },
                  ] : []),
                ].map((field) => (
                  <label key={field.key} className="account-form-field">
                    <span>{field.label}</span>
                    {field.type === "select" ? (
                      <StyledSelect value={accountForm.account_type}
                        onChange={(event) => setAccountForm({ ...accountForm, account_type: event.target.value })}
                        className="finos-select account-form-select"
                      >
                        <option value="bank">Bank Account</option>
                        <option value="cash">Cash in Hand</option>
                        <option value="petty_cash">Petty Cash</option>
                        <option value="wallet">Wallet</option>
                        <option value="credit_card">Credit Card</option>
                        <option value="credit_line">Credit Line</option>
                        <option value="loan">Loan Account</option>
                        <option value="receivable">Receivable</option>
                        <option value="payable">Payable</option>
                        <option value="investment">Investment / Broker Cash</option>
                        <option value="other">Other</option>
                      </StyledSelect>
                    ) : (
                      <input
                        type={field.type}
                        required={field.required || false}
                        min={field.type === "number" ? "0" : undefined}
                        step={field.type === "number" ? "0.01" : undefined}
                        placeholder={field.placeholder}
                        value={accountForm[field.key]}
                        onChange={(event) => setAccountForm({ ...accountForm, [field.key]: event.target.value })}
                        className="account-form-input"
                      />
                    )}
                  </label>
                ))}
              </div>

              {accountForm.account_type === "loan" && (
                <div className="account-form-fields account-form-loan-fields">
                  <label className="account-form-field">
                    <span>Interest calculation</span>
                    <StyledSelect value={accountForm.loan_interest_type} onChange={(event) => setAccountForm({ ...accountForm, loan_interest_type: event.target.value })}>
                      <option value="reducing_balance">Reducing balance</option>
                      <option value="flat">Flat rate</option>
                    </StyledSelect>
                  </label>
                  <label className="account-form-field">
                    <span>Repayment frequency</span>
                    <StyledSelect value={accountForm.loan_repayment_frequency} onChange={(event) => setAccountForm({ ...accountForm, loan_repayment_frequency: event.target.value })}>
                      <option value="monthly">Monthly</option>
                      <option value="weekly">Weekly</option>
                      <option value="quarterly">Quarterly</option>
                      <option value="annually">Annually</option>
                    </StyledSelect>
                  </label>
                </div>
              )}
              <footer className="account-form-footer">
                <button
                  type="button"
                  className="secondary-button account-form-cancel"
                  onClick={() => { setShowAccountForm(false); setEditingAccount(null); }}
                  disabled={accountSaving}
                >Cancel</button>
                <button
                  type="button"
                  className="primary-button account-form-submit"
                  onClick={handleAccountSubmit}
                  disabled={accountSaving || !accountForm.name.trim() || accountForm.balance === ""}
                >{accountSaving ? "Saving…" : editingAccount ? "Save changes" : "Save account"}</button>
              </footer>
            </section>
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
    "https://wealthmanager.duckdns.org";

  const USER_ID = getCurrentUserId();

  // ----------------------------------------------------------
  // LOAD BUDGETS
  // ----------------------------------------------------------

  async function loadBudgets() {

    try {

      setLoading(true);
      setError("");

      const response = await apiFetch(
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

    const response = await apiFetch(
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

      const response = await apiFetch(
        `${API_BASE_URL}/api/categories/?user_id=${USER_ID}`
      );

      if (!response.ok) {
        throw new Error("Unable to load categories.");
      }

      let data = await response.json();
      data = Array.isArray(data) ? data : [];

      // Seed missing defaults once per user; never overwrite or delete user data.
      const existingNames = new Set(data.map((item) => String(item.name || "").trim().toLowerCase()));
      const missingDefaults = TAX_READY_DEFAULT_CATEGORIES.filter(([, name]) => !existingNames.has(name.toLowerCase()));
      if (missingDefaults.length) {
        for (const [category_type, name, description] of missingDefaults) {
          try {
            const seedResponse = await apiFetch(`${API_BASE_URL}/api/categories/`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ user_id: USER_ID, name, category_type, description }),
            });
            if (seedResponse.ok) {
              const created = await seedResponse.json();
              data.push(created);
              existingNames.add(name.toLowerCase());
            }
          } catch (seedError) {
            console.warn("Could not seed starter category:", name, seedError);
          }
        }
      }

      setCategories(data);

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

      const response = await apiFetch(
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
    const response = await apiFetch(
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

    <div className="dashboard money-workspace money-budget">

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
    className="budget-list-grid"
  >

    {budgets.map((budget) => (

      <div
        key={budget.id}
        className="budget-list-card"
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
            background: "var(--finos-accent-soft, var(--t-inner-bg, transparent))",
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
                color: "var(--finos-muted-text, var(--finos-text))",
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
                color: "var(--finos-text)",
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
              background: "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
              border: "1px solid var(--finos-border)",
              fontSize: "11px",
              fontWeight: 700,
              color: "var(--finos-accent)",
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
            color: "var(--finos-muted-text, var(--finos-text))",
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
              color: "var(--finos-muted-text, var(--finos-text))",
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
              color: "var(--finos-muted-text, var(--finos-text))",
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
              background: "var(--t-inner-bg, var(--t-card-bg, var(--finos-surface)))",
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
                background: "var(--finos-accent)",
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
    color: "var(--finos-danger, var(--finos-text))",
    borderColor: "var(--finos-border)",
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
            color: "var(--finos-muted-text, var(--finos-text))",
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

        <div className="budget-form-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) setShowForm(false); }}>
          <div className="glass-card budget-form-modal" role="dialog" aria-modal="true" aria-labelledby="budget-form-title">

          <div className="card-header">

            <div>

              <p className="card-label">
                NEW BUDGET
              </p>

              <h3 id="budget-form-title">Create Budget</h3>
              <button type="button" className="budget-form-close" aria-label="Close budget form" onClick={() => setShowForm(false)}>×</button>

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

              <StyledSelect className="finos-select"
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

              </StyledSelect>

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
  const [activeTransactionTab, setActiveTransactionTab] = useState("all");
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
  const [showSalaryComponents, setShowSalaryComponents] = useState(false);
  const [salaryComponents, setSalaryComponents] = useState({ employer_name: "", gross_salary: "", salary_received: "", basic: "", da: "0", hra: "", allowances: "", bonus: "0", commission: "0", perquisites: "0", other: "0", deductions: "0", tds: "0" });
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [deletingTransaction, setDeletingTransaction] = useState(null);
  const [formData, setFormData] = useState({
    account_id: "",
    transfer_to_account_id: "",
    category_id: "",
    transaction_type: "income",
    amount: "",
    transaction_date: new Date().toISOString().split("T")[0],
    description: "",
    reference: "",
    party_name: "",
    due_date: "",
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

  // Only show categories that match the selected transaction type.
  const transactionCategories = categories.filter((category) => {
    const type = String(category.category_type || "").trim().toLowerCase();
    if (formData.transaction_type === "income" || formData.transaction_type === "receivable") return type === "income";
    if (formData.transaction_type === "expense" || formData.transaction_type === "payable") return type === "expense";
    return false;
  });
  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://wealthmanager.duckdns.org";

  const USER_ID = getCurrentUserId();

  const loanInputStyle = { width: "100%", boxSizing: "border-box", display: "block", marginTop: "6px", padding: "10px 11px", borderRadius: "9px", border: "1px solid rgba(255,255,255,0.14)", background: "#151525", color: "#fff", outline: "none" };

  // ----------------------------------------------------------
  // LOAD TRANSACTIONS
  // ----------------------------------------------------------

  useEffect(() => {

    const loadTransactions = async () => {

      try {

        setLoading(true);
        setError("");

        const response = await apiFetch(
          `${API_BASE_URL}/api/transactions/?user_id=${USER_ID}`
        );

        if (!response.ok) {
          throw new Error(
            `Transactions API error: ${response.status}`
          );
        }

        const data = await response.json();
        setTransactions(data);
        const accountsResponse = await apiFetch(`${API_BASE_URL}/api/accounts/?user_id=${USER_ID}`);
        if (accountsResponse.ok) {
          const accountsData = await accountsResponse.json();
          setAccounts(Array.isArray(accountsData) ? accountsData : []);
        }

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
    return ["income", "refund", "interest", "dividend"].includes(String(transaction.transaction_type || "").toLowerCase());
  };

  // Existing detailed transaction types stay intact but appear under the three
  // user-facing tabs: Income, Expense, and Transfer.
  const mainTransactionTab = (transaction) => {
    const type = String(transaction.transaction_type || "").toLowerCase();
    if (type === "transfer") return "transfer";
    if (["income", "refund", "interest", "dividend", "receivable"].includes(type)) return "income";
    return "expense";
  };

  // ----------------------------------------------------------
  // FORM HANDLERS
  // ----------------------------------------------------------

  const handleFormChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
      ...(name === "transaction_type" ? { category_id: "" } : {}),
    }));
    if (name === "category_id") {
      const selected = categories.find((item) => String(item.id) === String(value));
      if (String(selected?.name || "").trim().toLowerCase() === "salary") {
        const gross = Math.max(0, Number(formData.amount) || 0);
        const basic = Math.round(gross * 0.40 * 100) / 100;
        const hra = Math.round(basic * 0.40 * 100) / 100;
        setSalaryComponents((current) => ({
          ...current,
          salary_received: current.salary_received || String(Number(formData.amount) || 0),
          gross_salary: current.gross_salary || String(gross),
          basic: current.basic || String(basic),
          hra: current.hra || String(hra),
          allowances: current.allowances || String(Math.round((gross - basic - hra) * 100) / 100),
        }));
        setShowSalaryComponents(true);
      }
    }
  };

  // ----------------------------------------------------------
  // LOAD ACCOUNT & CATEGORY OPTIONS
  // ----------------------------------------------------------

  const loadFormOptions = async () => {
    try {
      const [accountsResponse, categoriesResponse] =
        await Promise.all([
          apiFetch(
            `${API_BASE_URL}/api/accounts/?user_id=${USER_ID}`
          ),
          apiFetch(
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

      let categoriesData = await categoriesResponse.json();
      categoriesData = Array.isArray(categoriesData) ? categoriesData : [];
      const existingNames = new Set(categoriesData.map((item) => String(item.name || "").trim().toLowerCase()));
      for (const [category_type, name, description] of TAX_READY_DEFAULT_CATEGORIES) {
        if (existingNames.has(name.toLowerCase())) continue;
        try {
          const seedResponse = await apiFetch(`${API_BASE_URL}/api/categories/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: USER_ID, name, category_type, description }),
          });
          if (seedResponse.ok) {
            const created = await seedResponse.json();
            categoriesData.push(created);
            existingNames.add(name.toLowerCase());
          }
        } catch (seedError) {
          console.warn("Could not seed starter category:", name, seedError);
        }
      }

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
      return { accounts: Array.isArray(accountsData) ? accountsData : [], categories: categoriesData };

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
    transfer_to_account_id: "",
    category_id: "",
    transaction_type: activeTransactionTab === "all" ? "expense" : activeTransactionTab,
    amount: "",
    transaction_date:
      new Date().toISOString().split("T")[0],
    description: "",
    reference: "",
    party_name: "",
    due_date: "",
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
      transfer_to_account_id: String(transaction.transfer_to_account_id || ""),
      category_id: String(transaction.category_id || ""),
      transaction_type: transaction.transaction_type || "expense",
      amount: transaction.amount ?? "",
      transaction_date:
        transaction.transaction_date ||
        new Date().toISOString().split("T")[0],
      description: transaction.description || "",
      reference: transaction.reference || "",
      party_name: transaction.party_name || "",
      due_date: transaction.due_date || "",
    });

    setError("");
    setFormMessage("");

    const options = await loadFormOptions();
    const category = (options?.categories || []).find((item) => String(item.id) === String(transaction.category_id));
    const isSalary = String(category?.name || transaction.category_name || "").trim().toLowerCase() === "salary";
    if (isSalary) {
      let saved = null;
      try {
        const raw = window.localStorage.getItem(`financial-os:salary-components:${USER_ID}`);
        const candidate = raw ? JSON.parse(raw) : null;
        if (candidate && candidate.user_id === USER_ID && (!candidate.transaction_id || String(candidate.transaction_id) === String(transaction.id))) saved = candidate;
      } catch (storageError) { console.warn("Unable to load saved salary components", storageError); }
      const amount = String(transaction.amount ?? "");
      const gross = saved?.gross_salary ?? amount;
      const basic = saved?.basic ?? Math.round((Number(gross) || 0) * 0.4 * 100) / 100;
      const hra = saved?.hra ?? Math.round((Number(basic) || 0) * 0.4 * 100) / 100;
      const otherKeys = ["da", "bonus", "commission", "perquisites", "other"];
      const otherSum = otherKeys.reduce((sum, key) => sum + (Number(saved?.[key]) || 0), 0);
      const allowances = saved?.allowances ?? Math.max(0, Math.round(((Number(gross) || 0) - (Number(basic) || 0) - (Number(hra) || 0) - otherSum) * 100) / 100);
      setSalaryComponents({
        employer_name: saved?.employer_name || "",
        gross_salary: String(gross), salary_received: amount,
        basic: String(basic), da: String(saved?.da ?? 0), hra: String(hra), allowances: String(allowances),
        bonus: String(saved?.bonus ?? 0), commission: String(saved?.commission ?? 0), perquisites: String(saved?.perquisites ?? 0), other: String(saved?.other ?? 0),
        deductions: String(saved?.payroll_deductions ?? saved?.deductions ?? 0), tds: String(saved?.tds ?? 0),
      });
      setShowSalaryComponents(true);
    }

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

    if (formData.transaction_type === "transfer" && (!formData.transfer_to_account_id || String(formData.transfer_to_account_id) === String(formData.account_id))) {
      setFormMessage("Please choose a different destination account.");
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
      category_id: formData.transaction_type === "transfer" || !formData.category_id || formData.category_id === "__loan_disbursement__" ? null : Number(formData.category_id),
      transaction_type: formData.transaction_type,
      ...(formData.transaction_type === "transfer" ? { transfer_to_account_id: Number(formData.transfer_to_account_id) } : {}),
      amount: Number(formData.amount),
      description: formData.description.trim(),
      transaction_date: formData.transaction_date,
      reference: formData.reference.trim(),
      ...(["receivable", "payable"].includes(formData.transaction_type) ? {
        party_name: (formData.party_name || "").trim() || null,
        due_date: formData.due_date || null,
      } : {}),
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

const response = await apiFetch(
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
    const refreshResponse = await apiFetch(
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
    // Link newly-created/updated salary breakdown to this transaction without creating another income entry.
    try {
      const rawSalary = window.localStorage.getItem(`financial-os:salary-components:${USER_ID}`);
      const salaryRecord = rawSalary ? JSON.parse(rawSalary) : null;
      const selectedCategoryName = categories.find((item) => String(item.id) === String(payload.category_id))?.name;
      if (salaryRecord && salaryRecord.user_id === USER_ID && (String(selectedCategoryName || "").toLowerCase() === "salary" || String(payload.description || "").includes("Salary details:"))) {
        salaryRecord.transaction_id = isEditing ? editingTransaction.id : (data?.id ?? data?.transaction?.id ?? salaryRecord.transaction_id);
        salaryRecord.transaction_date = payload.transaction_date;
        salaryRecord.salary_received = Number(payload.amount) || 0;
        salaryRecord.updated_at = new Date().toISOString();
        window.localStorage.setItem(`financial-os:salary-components:${USER_ID}`, JSON.stringify(salaryRecord));
        window.dispatchEvent(new Event("financial-os:salary-components-updated"));
      }
    } catch (salaryLinkError) { console.warn("Transaction saved but salary record could not be linked", salaryLinkError); }
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
      const response = await apiFetch(
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


      const transactionsResponse = await apiFetch(
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
      className="glass-card add-transaction-modal"
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
          gridTemplateColumns: "repeat(auto-fit, minmax(95px, 1fr))",
          gap: "8px",
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
        <button type="button" onClick={() => setFormData((previous) => ({ ...previous, transaction_type: "receivable", category_id: "" }))} style={{ padding: "12px 6px", borderRadius: "14px", border: formData.transaction_type === "receivable" ? "1px solid rgba(234,179,8,0.8)" : "1px solid rgba(255,255,255,0.10)", background: formData.transaction_type === "receivable" ? "rgba(234,179,8,0.16)" : "rgba(255,255,255,0.05)", color: "#fff", cursor: "pointer", fontWeight: 700 }}>Receivable</button>
        <button type="button" onClick={() => setFormData((previous) => ({ ...previous, transaction_type: "payable", category_id: "" }))} style={{ padding: "12px 6px", borderRadius: "14px", border: formData.transaction_type === "payable" ? "1px solid rgba(249,115,22,0.8)" : "1px solid rgba(255,255,255,0.10)", background: formData.transaction_type === "payable" ? "rgba(249,115,22,0.16)" : "rgba(255,255,255,0.05)", color: "#fff", cursor: "pointer", fontWeight: 700 }}>Payable</button>
        <button
          type="button"
          onClick={() => setFormData((previous) => ({ ...previous, transaction_type: "transfer", category_id: "" }))}
          style={{ padding: "12px 6px", borderRadius: "14px", border: formData.transaction_type === "transfer" ? "1px solid rgba(96,165,250,0.8)" : "1px solid rgba(255,255,255,0.10)", background: formData.transaction_type === "transfer" ? "rgba(96,165,250,0.16)" : "rgba(255,255,255,0.05)", color: "#fff", cursor: "pointer", fontWeight: 700 }}
        >Transfer</button>
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
          {["receivable", "payable"].includes(formData.transaction_type) ? "Related account (no cash movement yet)" : "Account"}
        </label>

        <StyledSelect className="finos-select"
          name="account_id"
          value={formData.account_id}
          onChange={handleFormChange}
          style={{ width: "100%", minWidth: 0 }}
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
        </StyledSelect>
      </div>

      {formData.transaction_type === "transfer" && (
        <div style={{ marginBottom: "16px" }}>
          <label style={{ display: "block", marginBottom: "7px", fontSize: "13px", color: "rgba(255,255,255,0.70)" }}>To Account</label>
          <StyledSelect name="transfer_to_account_id" value={formData.transfer_to_account_id} onChange={handleFormChange} style={{ width: "100%", minWidth: 0 }}>
            <option value="">Select destination account</option>
            {accounts.filter((account) => String(account.id) !== String(formData.account_id)).map((account) => <option key={account.id} value={account.id}>{account.name} ({account.account_type})</option>)}
          </StyledSelect>
        </div>
      )}

      {/* CATEGORY */}

      {formData.transaction_type !== "transfer" && <div style={{ marginBottom: "16px" }}>
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

        <StyledSelect className="finos-select"
          name="category_id"
          value={formData.category_id}
          onChange={handleFormChange}
          style={{ width: "100%", minWidth: 0 }}
        >
          <option value="">Select category</option>
          {formData.transaction_type === "income" && !categories.some((category) => String(category.name || "").trim().toLowerCase() === "loan disbursement" && String(category.category_type || "").toLowerCase() === "income") && (
            <option value="__loan_disbursement__">Loan Disbursement (non-taxable loan proceeds)</option>
          )}

{transactionCategories.map((category) => (
  <option
    key={category.id}
    value={category.id}
  >
    {category.name}
  </option>
))}
        </StyledSelect>
      </div>}

      {(formData.transaction_type === "receivable" || formData.transaction_type === "payable") && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "16px" }}>
          <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>
            {formData.transaction_type === "receivable" ? "Who owes you? (optional)" : "Who do you owe? (optional)"}
            <input name="party_name" value={formData.party_name || ""} onChange={handleFormChange} maxLength={150} placeholder={formData.transaction_type === "receivable" ? "Customer / person" : "Supplier / person"} style={loanInputStyle} />
          </label>
          <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>
            Due date (optional)
            <input type="date" name="due_date" value={formData.due_date || ""} onChange={handleFormChange} style={loanInputStyle} />
          </label>
        </div>
      )}

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
            <label style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>Loan Type *<StyledSelect required name="loan_type" value={formData.loan_type} onChange={handleFormChange} style={loanInputStyle}>{["Personal Loan","Home Loan","Car Loan","Education Loan","Business Loan","Gold Loan","Loan Against Property","Other"].map((x) => <option key={x} value={x}>{x}</option>)}</StyledSelect></label>
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

    <div className="dashboard money-workspace money-transactions">

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
                        (transaction.transaction_type || "").toLowerCase() === "expense"
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

      <div role="tablist" aria-label="Filter transaction history" style={{ display: "flex", flexWrap: "wrap", gap: "8px", margin: "12px 0" }}>
        {[
          { id: "all", label: "All" },
          { id: "income", label: "Income" },
          { id: "expense", label: "Expense" },
          { id: "transfer", label: "Transfer" },
        ].map((tab) => (
          <button key={tab.id} type="button" role="tab" aria-selected={activeTransactionTab === tab.id} onClick={() => setActiveTransactionTab(tab.id)} className={activeTransactionTab === tab.id ? "primary-button" : "secondary-button"} style={{ padding: "9px 14px" }}>
            {tab.label}
          </button>
        ))}
      </div>

      <section className="glass-card transaction-history-panel">

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
          transactions.filter((item) => activeTransactionTab === "all" || mainTransactionTab(item) === activeTransactionTab).length === 0 && (

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

              <button className="secondary-button" onClick={openTransactionForm}>
                Add Transaction
              </button>

            </div>

          )}


        {/* --------------------------------------------------
            TRANSACTION CARDS
        -------------------------------------------------- */}

        {!loading &&
          transactions.filter((item) => activeTransactionTab === "all" || mainTransactionTab(item) === activeTransactionTab).length > 0 && (

            <div className="transaction-history-list">

              {transactions.filter((item) => activeTransactionTab === "all" || mainTransactionTab(item) === activeTransactionTab).map(
                (transaction) => {

                  const income =
                    isIncome(transaction);

                  return (

                    <div
                      key={transaction.id}
                      className="transaction-history-card"
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
                              transaction.transaction_type === "transfer" ? "rgba(96,165,250,0.16)" : (income ? "rgba(34,197,94,0.16)" : "rgba(239,68,68,0.16)"),
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
                            className="transaction-history-title"
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
                            className="transaction-history-meta"
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
                              className="transaction-history-reference"
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
                          className="transaction-history-amount"
                          style={{
                            fontSize:
                              "16px",
                            fontWeight:
                              800,
                            color:
                              transaction.transaction_type === "transfer" ? "#93c5fd" : (income ? "#4ade80" : "#fb7185"),
                            whiteSpace:
                              "nowrap",
                          }}
                        >

                          {transaction.transaction_type === "transfer" ? "" : (income ? "+" : "-")}
                          {formatCurrency(transaction.amount)}

                        </div>
                        {transaction.transaction_type !== "transfer" && <button
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
                        </button>}
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

      {/* Salary components popup: component breakdown never changes the cash transaction amount. */}
      {showSalaryComponents && (
        <div role="dialog" aria-modal="true" aria-label="Salary components" onClick={() => setShowSalaryComponents(false)} style={{ position: "fixed", inset: 0, zIndex: 10020, display: "flex", alignItems: "center", justifyContent: "center", padding: 16, background: "rgba(0,0,0,.72)", backdropFilter: "blur(8px)" }}>
          <div className="glass-card" onClick={(event) => event.stopPropagation()} style={{ width: "100%", maxWidth: 560, maxHeight: "90vh", overflowY: "auto", padding: 22, border: "1px solid rgba(168,85,247,.35)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 8 }}>
              <div><h3 style={{ margin: 0 }}>Salary Components</h3><p style={{ margin: "6px 0 0", color: "rgba(255,255,255,.58)", fontSize: 12 }}>Suggested breakdown; adjust to match employer payroll/Form 16.</p></div>
              <button type="button" className="secondary-button" onClick={() => setShowSalaryComponents(false)}>Close</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))", gap: 12, marginTop: 16 }}>
              <label style={{ display: "block", color: "rgba(255,255,255,.76)", fontSize: 12 }}>Company / Employer Name<input type="text" value={salaryComponents.employer_name} onChange={(e) => setSalaryComponents((p) => ({ ...p, employer_name: e.target.value }))} placeholder="Employer name" style={{ width: "100%", boxSizing: "border-box", marginTop: 6, padding: "11px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,.14)", background: "#151525", color: "#fff" }} /></label>
              <label style={{ display: "block", color: "rgba(255,255,255,.76)", fontSize: 12 }}>Gross Salary (₹)<input type="number" min="0" step="0.01" value={salaryComponents.gross_salary} onChange={(e) => { const gross = Math.max(0, Number(e.target.value) || 0); const basic = Math.round(gross * .4 * 100) / 100; const hra = Math.round(basic * .4 * 100) / 100; setSalaryComponents((p) => ({ ...p, gross_salary: e.target.value, basic: String(basic), hra: String(hra), allowances: String(Math.round((gross - basic - hra - (Number(p.da) || 0) - (Number(p.bonus) || 0) - (Number(p.commission) || 0) - (Number(p.perquisites) || 0) - (Number(p.other) || 0)) * 100) / 100) })); }} style={{ width: "100%", boxSizing: "border-box", marginTop: 6, padding: "11px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,.14)", background: "#151525", color: "#fff" }} /></label>
              <label style={{ display: "block", color: "rgba(255,255,255,.76)", fontSize: 12 }}>Salary Received / Net Salary Credited (₹)<input id="salary-components-received" name="salary_received" type="text" inputMode="decimal" autoComplete="off" readOnly={false} aria-readonly="false" value={salaryComponents.salary_received ?? ""} onChange={(e) => { const value = e.target.value.replace(/[^0-9.]/g, ""); setSalaryComponents((p) => ({ ...p, salary_received: value })); }} placeholder="Type actual salary received" style={{ width: "100%", boxSizing: "border-box", marginTop: 6, padding: "11px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,.14)", background: "#151525", color: "#fff", pointerEvents: "auto", opacity: 1 }} /><span style={{ display: "block", marginTop: 4, color: "rgba(255,255,255,.58)", fontSize: 11 }}>Editable field. Enter the actual net salary credited. Applying components does not overwrite the transaction amount.</span></label>
              <div style={{ gridColumn: "1 / -1", marginTop: 4, padding: "12px 14px", borderRadius: 10, border: "1px solid rgba(34,197,94,.28)", background: "rgba(34,197,94,.07)" }}>
                <h4 style={{ margin: 0, color: "#86efac", fontSize: 13 }}>INCOME COMPONENTS</h4>
                <p style={{ margin: "5px 0 0", color: "rgba(255,255,255,.58)", fontSize: 11, lineHeight: 1.5 }}>Salary and benefit components. These may already be included in Gross Salary—enter each amount according to your payslip/Form 16 to avoid double counting.</p>
              </div>
              {[ ["basic", "Basic Salary"], ["da", "DA"], ["hra", "HRA"], ["allowances", "Other Allowances"], ["bonus", "Bonus"], ["commission", "Commission"], ["perquisites", "Perquisites (taxable value, if applicable)"], ["other", "Other Salary Components"] ].map(([key, label]) => <label key={key} style={{ display: "block", color: "rgba(255,255,255,.76)", fontSize: 12 }}>{label}<input type="number" min="0" step="0.01" value={salaryComponents[key]} onChange={(e) => setSalaryComponents((p) => { const next = { ...p, [key]: e.target.value }; if (["basic", "da", "hra", "bonus", "commission", "perquisites", "other"].includes(key)) { const gross = Number(p.gross_salary) || 0; const fixed = ["basic", "da", "hra", "bonus", "commission", "perquisites", "other"].reduce((sum, k) => sum + (Number(next[k]) || 0), 0); if (key !== "allowances") next.allowances = String(Math.round((gross - fixed) * 100) / 100); } return next; })} style={{ width: "100%", boxSizing: "border-box", marginTop: 6, padding: "11px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,.14)", background: "#151525", color: "#fff" }} /></label>)}
              <div style={{ gridColumn: "1 / -1", marginTop: 4, padding: "12px 14px", borderRadius: 10, border: "1px solid rgba(248,113,113,.28)", background: "rgba(248,113,113,.07)" }}>
                <h4 style={{ margin: 0, color: "#fca5a5", fontSize: 13 }}>DEDUCTIONS & RECONCILIATION</h4>
                <p style={{ margin: "5px 0 0", color: "rgba(255,255,255,.58)", fontSize: 11, lineHeight: 1.5 }}>Enter actual amounts from your payslip. TDS is part of total deductions where applicable—do not count it twice. An unexplained gross-to-net difference is not automatically a deduction.</p>
              </div>
              {[ ["deductions", "Total Payroll Deductions (reference)"], ["tds", "TDS (included in deductions if applicable)"] ].map(([key, label]) => <label key={key} style={{ display: "block", color: "rgba(255,255,255,.76)", fontSize: 12 }}>{label}<input type="number" min="0" step="0.01" value={salaryComponents[key]} onChange={(e) => setSalaryComponents((p) => ({ ...p, [key]: e.target.value }))} style={{ width: "100%", boxSizing: "border-box", marginTop: 6, padding: "11px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,.14)", background: "#151525", color: "#fff" }} /></label>)}
            </div>
            <div aria-live="polite" style={{ marginTop: 16, padding: 14, borderRadius: 12, border: "1px solid rgba(168,85,247,.25)", background: "rgba(168,85,247,.06)" }}>
              <strong style={{ display: "block", marginBottom: 10, fontSize: 13 }}>Live salary reconciliation</strong>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(135px,1fr))", gap: 10 }}>
                <div><div style={{ color: "rgba(255,255,255,.55)", fontSize: 11 }}>Gross salary</div><strong>{formatCurrency(Number(salaryComponents.gross_salary) || 0)}</strong></div>
                <div><div style={{ color: "rgba(255,255,255,.55)", fontSize: 11 }}>Net salary received</div><strong>{formatCurrency(Number(salaryComponents.salary_received) || 0)}</strong></div>
                <div><div style={{ color: "rgba(255,255,255,.55)", fontSize: 11 }}>Gross − net (to reconcile)</div><strong>{formatCurrency((Number(salaryComponents.gross_salary) || 0) - (Number(salaryComponents.salary_received) || 0))}</strong></div>
                <div><div style={{ color: "rgba(255,255,255,.55)", fontSize: 11 }}>Deductions entered</div><strong>{formatCurrency((Number(salaryComponents.deductions) || 0))}</strong></div>
              </div>
              <div style={{ marginTop: 10, fontSize: 12, color: (Number(salaryComponents.salary_received) > Number(salaryComponents.gross_salary)) ? "#fda4af" : "rgba(255,255,255,.72)" }}>
                {Number(salaryComponents.salary_received) > Number(salaryComponents.gross_salary)
                  ? "Validation: salary received exceeds gross salary. Check the amounts."
                  : Number(salaryComponents.gross_salary) < 0 || Number(salaryComponents.salary_received) < 0
                    ? "Salary amounts cannot be negative."
                    : Math.abs(((Number(salaryComponents.gross_salary) || 0) - (Number(salaryComponents.salary_received) || 0)) - (Number(salaryComponents.deductions) || 0)) < 0.01
                      ? "Reconciled: entered deductions match the gross-to-net difference."
                      : "Not yet reconciled: the gross-to-net difference is not necessarily all deductions. Enter actual payroll deductions from the payslip; the app will not assume the difference is TDS or PF."}
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginTop: 18, paddingTop: 14, borderTop: "1px solid rgba(255,255,255,.10)" }}>
              <div><div style={{ color: "rgba(255,255,255,.55)", fontSize: 12 }}>Salary component total</div><strong>{formatCurrency(["basic", "da", "hra", "allowances", "bonus", "commission", "perquisites", "other"].reduce((sum, key) => sum + (Number(salaryComponents[key]) || 0), 0))}</strong><div style={{ color: "rgba(255,255,255,.55)", fontSize: 11 }}>Gross less components: {formatCurrency((Number(salaryComponents.gross_salary) || 0) - ["basic", "da", "hra", "allowances", "bonus", "commission", "perquisites", "other"].reduce((sum, key) => sum + (Number(salaryComponents[key]) || 0), 0))}</div></div>
              <button type="button" className="primary-button" onClick={() => {
                const componentKeys = ["basic", "da", "hra", "allowances", "bonus", "commission", "perquisites", "other"];
                const componentTotal = componentKeys.reduce((sum, key) => sum + (Number(salaryComponents[key]) || 0), 0);
                const gross = Number(salaryComponents.gross_salary) || 0;
                const salaryReceived = Number(salaryComponents.salary_received) || 0;
                const deductions = Number(salaryComponents.deductions) || 0;
                const difference = Math.round((gross - salaryReceived) * 100) / 100;
                if (gross <= 0 || salaryReceived < 0 || salaryReceived > gross) { setError("Enter a valid gross salary and a salary received amount between ₹0 and gross salary."); return; }
                if (componentKeys.some((key) => (Number(salaryComponents[key]) || 0) < 0)) { setError("Salary components cannot be negative."); return; }
                if (componentTotal - gross > 0.009) { setError(`Salary components total (${formatCurrency(componentTotal)}) cannot exceed gross salary (${formatCurrency(gross)}). Reduce the components before saving.`); return; }
                if (deductions < 0 || deductions - difference > 0.009) { setError(`Payroll deductions cannot exceed the gross-to-net difference of ${formatCurrency(Math.max(0, difference))}. Check the payslip values.`); return; }
                const labels = { basic: "Basic Salary", da: "DA", hra: "HRA", allowances: "Other Allowances", bonus: "Bonus", commission: "Commission", perquisites: "Perquisites", other: "Other Salary Components" };
                const detail = componentKeys.filter((key) => Number(salaryComponents[key]) > 0).map((key) => `${labels[key]}: ₹${Number(salaryComponents[key]).toFixed(2)}`).join("; ");
                const originalAmount = Number(editingTransaction?.amount ?? formData.amount) || 0;
                const metadata = [`Employer: ${salaryComponents.employer_name || "Not entered"}`, `Gross salary: ₹${gross.toFixed(2)}`, `Salary received: ₹${salaryReceived.toFixed(2)}`, `Components total: ₹${componentTotal.toFixed(2)}`, `Unallocated gross salary: ₹${(gross - componentTotal).toFixed(2)}`, `Gross minus salary received: ₹${difference.toFixed(2)}`, `Payroll deductions reference: ₹${deductions.toFixed(2)}`, `TDS reference: ₹${(Number(salaryComponents.tds) || 0).toFixed(2)}`, detail].filter(Boolean).join("; ");
                const savedRecord = {
                  user_id: USER_ID,
                  transaction_id: editingTransaction?.id ?? null,
                  employer_name: salaryComponents.employer_name || "",
                  pay_period: "monthly",
                  transaction_date: formData.transaction_date || new Date().toISOString().slice(0, 10),
                  gross_salary: gross, salary_received: salaryReceived,
                  basic: Number(salaryComponents.basic) || 0, hra: Number(salaryComponents.hra) || 0, da: Number(salaryComponents.da) || 0,
                  allowances: Number(salaryComponents.allowances) || 0, bonus: Number(salaryComponents.bonus) || 0,
                  commission: Number(salaryComponents.commission) || 0, perquisites: Number(salaryComponents.perquisites) || 0,
                  other: Number(salaryComponents.other) || 0, payroll_deductions: deductions, tds: Number(salaryComponents.tds) || 0,
                  component_total: componentTotal, updated_at: new Date().toISOString(),
                };
                try {
                  window.localStorage.setItem(`financial-os:salary-components:${USER_ID}`, JSON.stringify(savedRecord));
                  window.dispatchEvent(new Event("financial-os:salary-components-updated"));
                } catch (storageError) { setError("Salary components could not be saved in this browser. Check browser storage settings and try again."); return; }
                setFormData((previous) => ({ ...previous, amount: salaryReceived !== originalAmount ? String(salaryReceived) : previous.amount, description: [previous.description.split(" | Salary details:")[0], `Salary details: ${metadata}`].filter(Boolean).join(" | ") }));
                setError("");
                setShowSalaryComponents(false);
              }}>Apply Components</button>
            </div>
            <p style={{ margin: "12px 0 0", color: "rgba(255,255,255,.48)", fontSize: 11, lineHeight: 1.5 }}>Basic 40% and HRA 40% of Basic are configurable suggestions, not statutory salary ratios. DA defaults to 0%. PF and professional tax depend on payroll facts and applicable rules. Components are saved separately for the current user. Editing Salary Received updates the transaction amount on the next Save; changing components alone preserves it.</p>
          </div>
        </div>
      )}

    </div>

  );

}

// ============================================================
// CATEGORIES
// ============================================================

// India-focused starter categories. Parent/subcategory paths are stored in the
  // existing category name field so this update remains compatible with the live API.
const TAX_READY_DEFAULT_CATEGORIES = [
  // Income: the five statutory heads are the primary tax classifications.
  ["income", "Salary", "Salary components are captured in a dedicated popup; tax treatment depends on the component and tax year"],
  ["income", "House Property > Rent", "Income from house property; map to applicable tax-year reporting rules"],
  ["income", "Business/Profession > Business Income", "Business or professional income"],
  ["income", "Business/Profession > Professional Fees", "Professional and consulting receipts"],
  ["income", "Business/Profession > Freelance Income", "Freelance receipts"],
  ["income", "Capital Gains > Stocks", "Sale of shares; classify holding period and applicable tax treatment"],
  ["income", "Capital Gains > Mutual Funds", "Redemption/sale; classify fund type and applicable tax treatment"],
  ["income", "Capital Gains > ETFs", "Sale/redemption; classify underlying asset and applicable tax treatment"],
  ["income", "Capital Gains > Property", "Sale of land/building; review cost and holding period"],
  ["income", "Capital Gains > Gold", "Sale of gold or related assets"],
  ["income", "Capital Gains > Digital Assets", "Virtual digital assets; special rules may apply"],
  ["income", "Other Sources > Savings Interest", "Interest income; review applicable tax treatment"],
  ["income", "Other Sources > FD Interest", "Fixed-deposit interest"],
  ["income", "Other Sources > RD Interest", "Recurring-deposit interest"],
  ["income", "Other Sources > Bond Interest", "Bond and securities interest"],
  ["income", "Other Sources > Dividends", "Dividend income"],
  ["income", "Other Sources > Family Pension", "Classify under applicable rules"],
  ["income", "Other Sources > Gifts", "Gift receipt; exemptions and reporting depend on circumstances"],
  ["income", "Other Sources > Winnings", "Lottery and other winnings; special tax rules may apply"],
  ["income", "Other Sources > Other Income", "Review and map before tax filing"],
  ["income", "Loan Disbursement", "Liability proceeds; not taxable income by default"],
  // Daily-use and personal categories are deliberately listed first.
  ["expense", "Food > Groceries", "Personal spending; not automatically deductible"],
  ["expense", "Food > Restaurant", "Restaurant and dining spend"],
  ["expense", "Food > Food Delivery", "Food delivery orders"],
  ["expense", "Food > Snacks", "Snacks and small food purchases"],
  ["expense", "Food > Miscellaneous", "Other food spending"],
  ["expense", "Housing > Rent", "Personal rent; tax treatment depends on circumstances"],
  ["expense", "Housing > Maintenance", "Housing maintenance"],
  ["expense", "Housing > Repairs", "Repairs and upkeep"],
  ["expense", "Utilities > Electricity", "Electricity and power"],
  ["expense", "Utilities > Water", "Water bills"],
  ["expense", "Utilities > Gas", "Gas bills"],
  ["expense", "Utilities > Internet", "Internet connectivity"],
  ["expense", "Utilities > Mobile", "Mobile and phone bills"],
  ["expense", "Transport > Fuel", "Fuel and charging"],
  ["expense", "Transport > Public Transport", "Bus, train and metro"],
  ["expense", "Transport > Taxi/Ride Share", "Taxi and ride sharing"],
  ["expense", "Transport > Parking/Tolls", "Parking and tolls"],
  ["expense", "Transport > Vehicle Repairs", "Vehicle maintenance and repairs"],
  ["expense", "Healthcare > Doctor", "Doctor and consultation expenses"],
  ["expense", "Healthcare > Medicines", "Medicines and pharmacy"],
  ["expense", "Healthcare > Hospital", "Hospital and treatment expenses"],
  ["expense", "Healthcare > Tests", "Medical tests and diagnostics"],
  ["expense", "Healthcare > Health Insurance", "Insurance payment; deduction eligibility must be assessed separately"],
  ["expense", "Shopping > Clothing", "Clothing and footwear"],
  ["expense", "Shopping > Electronics", "Electronics and accessories"],
  ["expense", "Shopping > Personal Care", "Personal care items"],
  ["expense", "Shopping > Household Items", "Household supplies and items"],
  ["expense", "Education > School/College Fees", "Education spending; deduction eligibility depends on applicable rules"],
  ["expense", "Education > Books", "Books and learning materials"],
  ["expense", "Education > Courses", "Courses and certifications"],
  ["expense", "Family > Childcare", "Childcare and child-related spending"],
  ["expense", "Family > Parents' Support", "Family support"],
  ["expense", "Entertainment > Movies/Events", "Movies, events and tickets"],
  ["expense", "Entertainment > Streaming", "Streaming and subscriptions"],
  ["expense", "Entertainment > Hobbies", "Hobbies and recreation"],
  ["expense", "Travel > Flights/Trains", "Travel tickets"],
  ["expense", "Travel > Hotels", "Accommodation"],
  ["expense", "Travel > Holidays", "Holiday spending"],
  ["expense", "Lifestyle > Gym/Sports", "Fitness and sports"],
  ["expense", "Lifestyle > Salon/Wellness", "Personal wellness and grooming"],
  ["expense", "Pets > Food/Supplies", "Pet food and supplies"],
  ["expense", "Pets > Veterinary", "Veterinary care"],
  ["expense", "Personal Services > Laundry/Cleaning", "Laundry and cleaning services"],
  ["expense", "Personal Services > Domestic Help", "Domestic help"],
  ["expense", "Gifts & Donations > Gifts", "Personal gifts"],
  ["expense", "Gifts & Donations > Donations", "Donation; deduction eligibility must be assessed separately"],
  ["expense", "Financial Costs > Bank Fees", "Bank and account fees"],
  ["expense", "Financial Costs > Card Fees", "Card fees and charges"],
  ["expense", "Miscellaneous > Other Personal Expense", "Unclassified personal spending"],
  // Tax-related/business categories: classifications do not guarantee deductibility.
  ["expense", "Business Expenses > Rent", "Business premises rent; deductibility depends on business and tax rules"],
  ["expense", "Business Expenses > Salaries Paid", "Payroll and wages"],
  ["expense", "Business Expenses > Professional Fees", "Accounting, legal and consulting fees"],
  ["expense", "Business Expenses > Advertising", "Advertising and marketing"],
  ["expense", "Business Expenses > Software", "Business software and subscriptions"],
  ["expense", "Business Expenses > Travel", "Business travel"],
  ["expense", "Business Expenses > Utilities", "Business utilities"],
  ["expense", "Tax Payments > Advance Tax", "Tax payment; reconcile with tax records"],
  ["expense", "Tax Payments > Self-Assessment Tax", "Tax payment; reconcile with tax records"],
  ["expense", "Tax Deductions > 80C", "Potential deduction for eligible tax years/regimes only"],
  ["expense", "Tax Deductions > 80D", "Potential deduction for eligible tax years/regimes only"],
  ["expense", "Tax Deductions > 80E", "Potential deduction for eligible tax years/regimes only"],
  ["expense", "Tax Deductions > 80G", "Potential deduction for eligible tax years/regimes only"],
  ["expense", "Home Loan > Principal", "Liability principal; eligibility depends on tax rules"],
  ["expense", "Home Loan > Interest", "Interest component; eligibility depends on tax rules"],
  ["expense", "Investment Costs > Brokerage", "Investment cost; tax treatment depends on transaction"],
  ["expense", "Investment Costs > Transaction Charges", "Investment transaction charges"],
  ["expense", "Loan Repayment > Principal", "Principal repayment reduces liability; not interest expense"],
  ["expense", "Loan Repayment > Interest", "Interest component; treatment depends on purpose and applicable rules"],
  ["expense", "Refunds > Purchase Refund", "Use to reverse/reconcile the original expense"],
  ["other", "Transfer Between Own Accounts", "Internal transfer; not income or expense"],
  ["other", "Credit Card Settlement", "Settlement of recorded credit-card liability; avoid double-counting"],
];


function Category() {


  // ----------------------------------------------------------
  // STATE
  // ----------------------------------------------------------

  const [categories, setCategories] = useState([]);
  const [activeCategoryTab, setActiveCategoryTab] = useState("income");
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
    parent_category: "",
    description: "",
  });

  // ----------------------------------------------------------
  // API CONFIGURATION
  // ----------------------------------------------------------

  const API_BASE_URL =
    "https://wealthmanager.duckdns.org";

  const USER_ID = getCurrentUserId();

  // ----------------------------------------------------------
  // LOAD CATEGORIES
  // ----------------------------------------------------------

  async function loadCategories() {

    try {

      setLoading(true);
      setError("");

      const response = await apiFetch(
        `${API_BASE_URL}/api/categories/?user_id=${USER_ID}`
      );

      if (!response.ok) {
        throw new Error(
          `Categories API error: ${response.status}`
        );
      }

      let data = await response.json();
      data = Array.isArray(data) ? data : [];
      const existingNames = new Set(data.map((item) => String(item.name || "").trim().toLowerCase()));
      for (const [category_type, name, description] of TAX_READY_DEFAULT_CATEGORIES) {
        if (existingNames.has(name.toLowerCase())) continue;
        try {
          const seedResponse = await apiFetch(`${API_BASE_URL}/api/categories/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: USER_ID, name, category_type, description }),
          });
          if (seedResponse.ok) {
            const created = await seedResponse.json();
            data.push(created);
            existingNames.add(name.toLowerCase());
          }
        } catch (seedError) {
          console.warn("Could not seed starter category:", name, seedError);
        }
      }
      // Display everyday/personal categories first while retaining all saved records.
      const categoryRank = (item) => {
        const name = String(item.name || "").toLowerCase();
        if (/^(food|housing|utilities|transport|healthcare|shopping|education|family|entertainment|travel|lifestyle|pets|personal services|gifts & donations|financial costs|miscellaneous)(\s*>|$)/.test(name)) return 0;
        if (/^(salary|house property|business\/profession|capital gains|other sources)/.test(name)) return 1;
        if (/^(business expenses|tax payments|tax deductions|home loan|investment costs|loan repayment)/.test(name)) return 2;
        return 3;
      };
      data.sort((a, b) => categoryRank(a) - categoryRank(b) || String(a.name || "").localeCompare(String(b.name || "")));
      setCategories(data);

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
      category_type: activeCategoryTab === "income" ? "income" : "expense",
      parent_category: "",
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

    const pathParts = String(category.name || "").split(" > ");
    setFormData({
      name: pathParts.pop() || "",
      category_type: category.category_type || "expense",
      parent_category: pathParts.join(" > "),
      description: category.description || "",
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

    const leafName = formData.name.trim();
    const name = formData.parent_category
      ? `${formData.parent_category} > ${leafName}`
      : leafName;

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

      const response = await apiFetch(

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
        parent_category: "",
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

      const response = await apiFetch(
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

  const visibleTypeCategories = categories.filter(
    (category) => category.category_type === activeCategoryTab
  );

  const favoriteNames = activeCategoryTab === "income"
    ? [
        "Salary",
        "Other Sources > Savings Interest",
        "Other Sources > Dividends",
        "House Property > Rent",
      ]
    : [
        "Food > Groceries",
        "Housing > Rent",
        "Transport > Fuel",
        "Utilities > Electricity",
      ];

  const favoriteCategories = favoriteNames
    .map((name) => visibleTypeCategories.find(
      (category) => String(category.name || "").toLowerCase() === name.toLowerCase()
    ))
    .filter(Boolean);

  const favoriteCategoryIds = new Set(favoriteCategories.map((category) => category.id));

  const isBusinessCategory = (category) => {
    const name = String(category.name || "").toLowerCase();
    const root = name.split(" > ")[0].trim();
    return root === "business/profession"
      || root === "business expenses"
      || /^(business income|business revenue|business sales|business services|business travel|business utilities)(\s*>|$)/.test(name);
  };

  const personalCategories = visibleTypeCategories.filter(
    (category) => !favoriteCategoryIds.has(category.id) && !isBusinessCategory(category)
  );

  const businessCategories = visibleTypeCategories.filter(
    (category) => !favoriteCategoryIds.has(category.id) && isBusinessCategory(category)
  );

  const otherCategories = categories.filter(
    (category) => !["income", "expense"].includes(String(category.category_type || "").toLowerCase())
  );

  const renderCategoryCard = (category) => (
    <div
      key={category.id}
      className="category-list-item"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "16px",
        padding: "16px",
        borderRadius: "16px",
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: "14px", fontWeight: 700, overflowWrap: "anywhere" }}>
          {category.name}
        </div>
        {category.description && (
          <div style={{ marginTop: "5px", fontSize: "12px" }}>
            {category.description}
          </div>
        )}
      </div>
      <div style={{ display: "flex", gap: "8px", flexShrink: 0 }}>
        <button
          type="button"
          className="secondary-button"
          onClick={() => openEditCategoryForm(category)}
          style={{ padding: "7px 12px", fontSize: "11px" }}
        >
          Edit
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={() => setCategoryToDelete(category)}
          style={{ padding: "7px 12px", fontSize: "11px" }}
        >
          Delete
        </button>
      </div>
    </div>
  );

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (

    <div className="dashboard categories-page">

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

      <section className="glass-card category-list-section">

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


        {!loading && (
          <>
            <div style={{ display: "flex", gap: "10px", marginTop: "20px", marginBottom: "22px" }}>
              {[
                { value: "income", label: "Income", icon: "↑" },
                { value: "expense", label: "Expense", icon: "↓" },
              ].map((tab) => {
                const selected = activeCategoryTab === tab.value;
                const count = categories.filter((category) => category.category_type === tab.value).length;
                return (
                  <button
                    key={tab.value}
                    type="button"
                    onClick={() => setActiveCategoryTab(tab.value)}
                    aria-pressed={selected}
                    style={{
                      flex: 1,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "9px",
                      padding: "14px 16px",
                      borderRadius: "14px",
                      border: selected ? "1px solid rgba(190,100,255,.55)" : "1px solid rgba(255,255,255,.10)",
                      background: selected ? "linear-gradient(135deg, rgba(168,85,247,.28), rgba(236,72,153,.16))" : "rgba(255,255,255,.035)",
                      color: "#fff",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    <span style={{ fontSize: "18px" }}>{tab.icon}</span>
                    <span>{tab.label}</span>
                    <span style={{ fontSize: "11px", color: "rgba(255,255,255,.62)", fontWeight: 600 }}>{count}</span>
                  </button>
                );
              })}
            </div>

            <section style={{ marginBottom: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <span style={{ fontSize: "18px" }}>⭐</span>
                <h4 style={{ margin: 0, color: "#fff", fontSize: "15px" }}>Favorite {activeCategoryTab === "income" ? "Income" : "Expense"} Categories</h4>
                <span style={{ fontSize: "11px", color: "rgba(255,255,255,.5)" }}>Top 4</span>
              </div>
              <div style={{ display: "grid", gap: "10px" }}>
                {favoriteCategories.length > 0
                  ? favoriteCategories.map(renderCategoryCard)
                  : <p style={{ color: "rgba(255,255,255,.55)", fontSize: "13px" }}>Favorite categories will appear here when available.</p>}
              </div>
            </section>

            {[
              { title: "Personal", items: personalCategories, icon: "👤" },
              { title: "Business", items: businessCategories, icon: "🏢" },
            ].map((group) => (
              <section key={group.title} style={{ marginBottom: "24px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                  <span style={{ fontSize: "17px" }}>{group.icon}</span>
                  <h4 style={{ margin: 0, color: "#fff", fontSize: "15px" }}>{group.title} {activeCategoryTab === "income" ? "Income" : "Expense"}</h4>
                  <span style={{ fontSize: "11px", color: "rgba(255,255,255,.5)" }}>{group.items.length}</span>
                </div>
                {group.items.length > 0
                  ? <div style={{ display: "grid", gap: "10px" }}>{group.items.map(renderCategoryCard)}</div>
                  : <p style={{ color: "rgba(255,255,255,.45)", fontSize: "12px", margin: "0 0 4px" }}>No categories in this section yet.</p>}
              </section>
            ))}


          </>
        )}

      </section>

      {!loading && otherCategories.length > 0 && (
        <section className="glass-card category-list-section" style={{ marginTop: "18px" }}>
          <div className="card-header">
            <div>
              <p className="card-label">ADDITIONAL CATEGORIES</p>
              <h3 style={{ margin: 0 }}>Other / Transfers</h3>
            </div>
            <span className="score">{otherCategories.length}</span>
          </div>
          <p style={{ color: "rgba(255,255,255,.55)", fontSize: "12px", marginTop: "10px" }}>
            Transfer and settlement categories stay separate from income and expense.
          </p>
          <div style={{ display: "grid", gap: "10px", marginTop: "14px" }}>
            {otherCategories.map(renderCategoryCard)}
          </div>
        </section>
      )}

      {/* ====================================================
          CATEGORY FORM
      ==================================================== */}

      {showForm && (

        <div
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !saving) {
              setShowForm(false);
            }
          }}
          className="category-form-overlay"
        >

        <div
          className="glass-card category-form-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="category-form-title"

        >

          <div className="card-header">

            <div>

              <p className="card-label">
                {editingCategory
                  ? "EDIT CATEGORY"
                  : "NEW CATEGORY"}
              </p>

              <h3 id="category-form-title">
                {editingCategory
                  ? "Update Category"
                  : "Create Category"}
              </h3>

            </div>

            <button
              type="button"
              aria-label="Close category form"
              onClick={() => !saving && setShowForm(false)}
              disabled={saving}
              className="secondary-button category-form-close"
            >
              ✕
            </button>
          </div>


          <form onSubmit={saveCategory}>

            {/* NAME */}

            <div className="category-form-field">

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
                className="category-form-input"
              />

            </div>


            {/* TYPE */}

            <div className="category-form-field">

              <label>
                Category Type
              </label>

              <StyledSelect className="category-form-select"
                value={
                  formData.category_type
                }
                onChange={(event) =>
                  updateForm(
                    "category_type",
                    event.target.value
                  )
                }
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

              </StyledSelect>

            </div>


            {/* OPTIONAL PARENT: selecting one creates a subcategory path */}
            <div className="category-form-field">
              <label>Parent Category (optional)</label>
              <StyledSelect className="category-form-select"
                value={formData.parent_category}
                onChange={(event) => updateForm("parent_category", event.target.value)}
              >
                <option value="">None — create a main category</option>
                {formData.category_type === "income" && <option value="Business/Profession">Business / Profession</option>}
                {formData.category_type === "expense" && <option value="Business Expenses">Business Expenses</option>}
                {categories
                  .filter((category) => category.category_type === formData.category_type && !String(category.name || "").includes(" > ") && (!editingCategory || category.id !== editingCategory.id))
                  .map((category) => <option key={category.id} value={category.name}>{category.name}</option>)}
              </StyledSelect>
              <p className="category-form-help">Choose a parent to create a subcategory. Existing categories and transaction records are preserved.</p>
            </div>

            {/* DESCRIPTION */}

            <div className="category-form-field">

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
                className="category-form-textarea"
              />

            </div>


            {/* ACTIONS */}

            <div className="category-form-actions">

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
                className="secondary-button category-form-cancel"
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
    "https://wealthmanager.duckdns.org/api/bills";

  const API_BASE_URL =
    "https://wealthmanager.duckdns.org";


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

      const response = await apiFetch(
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

      const response = await apiFetch(
        `${API_BASE_URL}/api/categories/?user_id=${USER_ID}`
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

      const response = await apiFetch(
        `${API_BASE_URL}/api/accounts/?user_id=${USER_ID}`
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


      const response = await apiFetch(

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

      const response = await apiFetch(
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
          className="bill-form-overlay"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              resetForm();
              setShowForm(false);
            }
          }}
        >
          <div
            className="glass-card bill-form-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="bill-form-heading"
            onClick={(event) => event.stopPropagation()}
          >

          <div className="bill-form-header">

            <div>

              <div
                className="card-label"
              >
                {editingBill
                  ? "EDIT BILL"
                  : "ADD BILL"}
              </div>

              <h3 id="bill-form-heading" className="bill-form-title">
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
  className="bill-form-grid"
>
  {/* BILL NAME */}
  <div className="bill-form-field">
    <label className="bill-form-label">
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
    />
  </div>

  {/* AMOUNT */}
  <div className="bill-form-field"
  >
    <label className="bill-form-label"
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
    />
  </div>

  {/* CATEGORY */}
  <div className="bill-form-field"
  >
    <label className="bill-form-label"
    >
      Category
    </label>

    <StyledSelect className="finos-select bill-form-select"
      value={formData.category_id}
      onChange={(event) =>
        handleChange(
          "category_id",
          event.target.value
        )
      }
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
    </StyledSelect>
  </div>

  {/* PAYMENT ACCOUNT */}
  <div className="bill-form-field"
  >
    <label className="bill-form-label"
    >
      Payment Account
    </label>

    <StyledSelect className="finos-select bill-form-select"
      value={formData.account_id}
      onChange={(event) =>
        handleChange(
          "account_id",
          event.target.value
        )
      }
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
    </StyledSelect>
  </div>

  {/* FREQUENCY */}
  <div className="bill-form-field"
  >
    <label className="bill-form-label"
    >
      Frequency
    </label>

    <StyledSelect className="finos-select bill-form-select"
      value={formData.frequency}
      onChange={(event) =>
        handleChange(
          "frequency",
          event.target.value
        )
      }
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
    </StyledSelect>
  </div>

  {/* NEXT DUE DATE */}
  <div className="bill-form-field"
  >
    <label className="bill-form-label"
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
    />
  </div>

  {/* STATUS */}
  <div className="bill-form-field"
  >
    <label className="bill-form-label"
    >
      Status
    </label>

    <StyledSelect className="finos-select bill-form-select"
      value={formData.status}
      onChange={(event) =>
        handleChange(
          "status",
          event.target.value
        )
      }
    >
      <option value="active">Active</option>
      <option value="paused">Paused</option>
      <option value="cancelled">
        Cancelled
      </option>
    </StyledSelect>
  </div>

  {/* NOTES */}
  <div className="bill-form-field"
  >
    <label className="bill-form-label"
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
    />
  </div>
</div>

          <div className="bill-form-actions">

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










