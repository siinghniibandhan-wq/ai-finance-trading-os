import React, { useEffect, useState } from "react";

/*
=====================================================
AI FINANCE TRADING OS
MAIN APPLICATION SHELL
=====================================================

IMPORTANT:
- This file controls the frontend navigation and pages.
- Backend/API URLs are intentionally unchanged.
- Accounts still use the existing backend endpoint.
- Placeholder pages are intentionally lightweight.
- React.createElement is used to preserve the current
  working frontend setup.
=====================================================
*/

function App() {
  // =====================================================
  // BASIC APP STATE
  // =====================================================

  const [active, setActive] = useState("Overview");
  const [menuOpen, setMenuOpen] = useState(false);

  // =====================================================
  // EXPANDED MAIN SECTIONS
  // EDIT HERE IF YOU WANT DEFAULT OPEN SECTIONS
  // =====================================================

  const [expanded, setExpanded] = useState({
    Finance: true,
    Wealth: false,
    Investments: false,
    Trading: false,
    AI: false
  });

  // =====================================================
  // ACCOUNTS STATE
  // EXISTING FUNCTIONALITY PRESERVED
  // =====================================================

  const [accounts, setAccounts] = useState([]);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [accountsError, setAccountsError] = useState("");

  // =====================================================
  // MAIN NAVIGATION STRUCTURE
  // DO NOT CHANGE API ROUTES HERE
  // =====================================================

  const navigation = [
    {
      name: "Overview",
      icon: "🏠",
      type: "single"
    },

    {
      name: "Finance",
      icon: "💰",
      type: "section",
      children: [
        "Finance Overview",
        "Accounts",
        "Transactions",
        "Categories",
        "Cash Flow",
        "Budget",
        "Bills & Subscriptions",
        "Statements / Import"
      ]
    },

    {
      name: "Wealth",
      icon: "💎",
      type: "section",
      children: [
        "Wealth Overview",
        "Assets",
        "Liabilities",
        "Net Worth",
        "Insurance",
        "Real Estate",
        "Retirement",
        "Financial Goals"
      ]
    },

    {
      name: "Investments",
      icon: "📊",
      type: "section",
      children: [
        "Investment Overview",
        "Portfolio",
        "Stocks",
        "Mutual Funds",
        "ETFs",
        "Bonds",
        "Gold",
        "Crypto"
      ]
    },

    {
      name: "Trading",
      icon: "📈",
      type: "section",
      children: [
        "Trading Overview",
        "Markets",
        "Watchlist",
        "Screener",
        "Charts",
        "Strategies",
        "Backtesting",
        "Paper Trading",
        "Live Trading",
        "Positions",
        "Orders",
        "Risk Management",
        "Trading Journal"
      ]
    },

    {
      name: "AI",
      icon: "🤖",
      type: "section",
      children: [
        "AI Chat",
        "AI Research",
        "AI Analysis",
        "AI Predictions",
        "AI Reports"
      ]
    },

    {
      name: "Reports",
      icon: "📑",
      type: "single"
    },

    {
      name: "Settings",
      icon: "⚙️",
      type: "single"
    }
  ];

  // =====================================================
  // OVERVIEW KPI DATA
  // REAL DATA WILL BE CONNECTED LATER
  // =====================================================

  const overviewCards = [
    ["Net Worth", "₹0", "Assets − liabilities"],
    ["Total Assets", "₹0", "Current asset value"],
    ["Liabilities", "₹0", "Outstanding amount"],
    ["Investments", "₹0", "Portfolio value"]
  ];

  // =====================================================
  // NAVIGATION HELPERS
  // =====================================================

  function navigate(page) {
    setActive(page);
    setMenuOpen(false);
  }

  function toggleSection(section) {
    setExpanded(function (previous) {
      return {
        ...previous,
        [section]: !previous[section]
      };
    });
  }

  function openSection(section) {
    const item = navigation.find(function (nav) {
      return nav.name === section;
    });

    if (!item) return;

    if (item.children && item.children.length > 0) {
      navigate(item.children[0]);

      setExpanded(function (previous) {
        return {
          ...previous,
          [section]: true
        };
      });

      return;
    }

    navigate(section);
  }

  // =====================================================
  // LOAD ACCOUNTS FROM EXISTING BACKEND
  // IMPORTANT: EXISTING API PRESERVED
  // =====================================================

  async function loadAccounts() {
    setAccountsLoading(true);
    setAccountsError("");

    try {
      const response = await fetch(
        "https://ai-finance-trading-os-api.onrender.com/api/accounts/"
      );

      if (!response.ok) {
        throw new Error("Unable to load accounts.");
      }

      const data = await response.json();

      setAccounts(Array.isArray(data) ? data : []);
    } catch (error) {
      setAccountsError(
        error?.message || "Unable to load accounts."
      );
    } finally {
      setAccountsLoading(false);
    }
  }

  // =====================================================
  // LOAD ACCOUNTS WHEN ACCOUNTS PAGE IS OPENED
  // =====================================================

  useEffect(
    function () {
      if (active === "Accounts") {
        loadAccounts();
      }
    },
    [active]
  );

  // =====================================================
  // MONEY FORMATTER
  // =====================================================

  function formatMoney(value, currency) {
    const amount = Number(value || 0);

    return `${currency || "INR"} ${amount.toLocaleString(
      "en-IN",
      {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }
    )}`;
  }

  // =====================================================
  // ACCOUNT TYPE LABEL
  // =====================================================

  function accountTypeLabel(type) {
    if (!type) return "Account";

    return String(type)
      .replaceAll("_", " ")
      .replace(/\b\w/g, function (letter) {
        return letter.toUpperCase();
      });
  }

  // =====================================================
  // GET CURRENT PAGE TITLE
  // =====================================================

  function getPageTitle() {
    if (active === "Overview") {
      return "Overview";
    }

    return active;
  }

  // =====================================================
  // GET CURRENT PAGE DESCRIPTION
  // =====================================================

  function getPageDescription() {
    const descriptions = {
      Overview:
        "Your complete financial, wealth, investment and trading picture.",

      "Finance Overview":
        "Accounts, cash flow, transactions and everyday finances.",

      Accounts:
        "Manage your bank accounts, cash, cards and wallets.",

      Transactions:
        "View and manage your financial transactions.",

      Categories:
        "Organize your income and expense categories.",

      "Cash Flow":
        "Understand money coming in and going out.",

      Budget:
        "Plan and control your spending.",

      "Bills & Subscriptions":
        "Track recurring bills and subscriptions.",

      "Statements / Import":
        "Import and reconcile financial statements.",

      "Wealth Overview":
        "Your assets, liabilities and overall net worth.",

      Assets:
        "Manage everything you own.",

      Liabilities:
        "Manage loans, credit cards and other obligations.",

      "Net Worth":
        "Track your total wealth over time.",

      Insurance:
        "Track insurance policies and coverage.",

      "Real Estate":
        "Manage property and real estate holdings.",

      Retirement:
        "Plan and track retirement assets.",

      "Financial Goals":
        "Set and track your long-term financial goals.",

      "Investment Overview":
        "Your complete investment portfolio.",

      Portfolio:
        "Track investment holdings and performance.",

      Stocks:
        "Manage and analyze stock investments.",

      "Mutual Funds":
        "Manage mutual fund investments.",

      ETFs:
        "Manage exchange-traded funds.",

      Bonds:
        "Track fixed-income investments.",

      Gold:
        "Track physical and financial gold holdings.",

      Crypto:
        "Track cryptocurrency investments.",

      "Trading Overview":
        "Trading activity, positions, performance and risk.",

      Markets:
        "Market intelligence and market data.",

      Watchlist:
        "Track instruments you are watching.",

      Screener:
        "Find instruments using custom filters.",

      Charts:
        "Analyze price charts and technical indicators.",

      Strategies:
        "Build and manage trading strategies.",

      Backtesting:
        "Test trading strategies against historical data.",

      "Paper Trading":
        "Practice trading without real money.",

      "Live Trading":
        "Manage connected live trading activity.",

      Positions:
        "Monitor open and closed trading positions.",

      Orders:
        "Track trading orders.",

      "Risk Management":
        "Monitor exposure and trading risk.",

      "Trading Journal":
        "Record and analyze your trading decisions.",

      "AI Chat":
        "Talk to your AI financial assistant.",

      "AI Research":
        "AI-powered financial and market research.",

      "AI Analysis":
        "AI-powered analysis of your financial data.",

      "AI Predictions":
        "AI-generated predictions and scenarios.",

      "AI Reports":
        "Generate intelligent financial reports.",

      Reports:
        "Financial, investment, trading and tax reporting.",

      Settings:
        "Configure your Finance OS."
    };

    return (
      descriptions[active] ||
      "This module will be connected to the Finance OS engine."
    );
  }

  // =====================================================
  // GLOBAL STYLES
  // =====================================================

  const styles = `
    * {
      box-sizing: border-box;
    }

    html,
    body,
    #root {
      margin: 0;
      min-height: 100%;
      width: 100%;
    }

    body {
      font-family: Arial, sans-serif;
      background: #f5f3fb;
      color: #18152b;
    }

    button {
      font-family: inherit;
    }

    /* =================================================
       APP
       ================================================= */

    .finance-app {
      min-height: 100vh;
      display: flex;
      background: #f5f3fb;
    }

    /* =================================================
       SIDEBAR
       ================================================= */

    .finance-sidebar {
      width: 270px;
      min-height: 100vh;
      flex-shrink: 0;
      background: #ffffff;
      border-right: 1px solid #e8e3f4;
      padding: 20px 13px;
      overflow-y: auto;
    }

    .brand {
      padding: 5px 13px 23px;
      font-size: 21px;
      font-weight: 800;
    }

    .brand span {
      color: #7048ff;
    }

    .main-nav-button {
      width: 100%;
      border: 0;
      background: transparent;
      border-radius: 10px;
      padding: 11px 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      cursor: pointer;
      color: #514c61;
      font-size: 14px;
      text-align: left;
      margin-bottom: 3px;
    }

    .main-nav-button:hover {
      background: #f5f1ff;
    }

    .main-nav-button.active-main {
      background: #eee8ff;
      color: #5530d9;
      font-weight: 700;
    }

    .nav-left {
      display: flex;
      align-items: center;
      gap: 9px;
      min-width: 0;
    }

    .nav-icon {
      width: 22px;
      text-align: center;
      flex-shrink: 0;
    }

    .nav-arrow {
      color: #9992aa;
      font-size: 12px;
    }

    .sub-nav {
      padding: 2px 0 7px 30px;
    }

    .sub-nav-button {
      width: 100%;
      border: 0;
      background: transparent;
      color: #777184;
      border-radius: 8px;
      padding: 9px 10px;
      text-align: left;
      cursor: pointer;
      font-size: 13px;
      margin-bottom: 2px;
    }

    .sub-nav-button:hover {
      background: #f7f4ff;
      color: #5530d9;
    }

    .sub-nav-button.active {
      background: #eee8ff;
      color: #5530d9;
      font-weight: 700;
    }

    /* =================================================
       MAIN
       ================================================= */

    .finance-main {
      flex: 1;
      min-width: 0;
    }

    .topbar {
      height: 72px;
      background: #ffffff;
      border-bottom: 1px solid #e8e3f4;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 26px;
      position: sticky;
      top: 0;
      z-index: 20;
    }

    .top-left {
      display: flex;
      align-items: center;
    }

    .top-title small {
      display: block;
      color: #8b859b;
      font-size: 12px;
      margin-bottom: 3px;
    }

    .top-title strong {
      font-size: 21px;
    }

    .profile {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #eee8ff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: #5c3bdd;
    }

    .mobile-menu {
      display: none;
    }

    /* =================================================
       PAGE
       ================================================= */

    .page {
      padding: 26px;
      max-width: 1500px;
    }

    .page-heading {
      margin-bottom: 20px;
    }

    .page-heading h2 {
      margin: 0 0 5px;
      font-size: 24px;
    }

    .page-heading p {
      margin: 0;
      color: #817b91;
      font-size: 14px;
    }

    /* =================================================
       KPI
       ================================================= */

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 15px;
    }

    .kpi {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 19px;
    }

    .kpi-label {
      color: #858092;
      font-size: 13px;
      margin-bottom: 10px;
    }

    .kpi-value {
      font-size: 27px;
      font-weight: 800;
      margin-bottom: 6px;
    }

    .kpi-note {
      color: #9993a4;
      font-size: 12px;
    }

    /* =================================================
       PANELS
       ================================================= */

    .dashboard-grid {
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
      gap: 15px;
      margin-top: 15px;
    }

    .panel {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 20px;
    }

    .panel h3 {
      margin: 0 0 6px;
      font-size: 17px;
    }

    .panel-subtitle {
      color: #858092;
      font-size: 13px;
      margin-bottom: 20px;
    }

    .chart-placeholder {
      height: 190px;
      border-radius: 12px;
      background: #faf9fd;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #9993a4;
      font-size: 13px;
    }

    .ai-panel {
      background: linear-gradient(145deg, #ffffff, #f8f5ff);
    }

    .ai-icon {
      width: 44px;
      height: 44px;
      border-radius: 13px;
      background: #eee8ff;
      color: #6940ed;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      margin-bottom: 15px;
    }

    .ai-text {
      color: #716b7d;
      font-size: 13px;
      line-height: 1.55;
    }

    /* =================================================
       QUICK ACTIONS
       ================================================= */

    .quick-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-top: 15px;
    }

    .quick {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 13px;
      padding: 15px;
      cursor: pointer;
    }

    .quick strong {
      display: block;
      margin-bottom: 5px;
    }

    .quick span {
      font-size: 12px;
      color: #8b859b;
    }

    /* =================================================
       ACCOUNTS
       ================================================= */

    .accounts-summary {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin-bottom: 20px;
    }

    .summary-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 18px;
    }

    .summary-label {
      color: #858092;
      font-size: 13px;
      margin-bottom: 8px;
    }

    .summary-value {
      font-size: 23px;
      font-weight: 800;
    }

    .accounts-list {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 15px;
    }

    .account-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 19px;
    }

    .account-top {
      display: flex;
      justify-content: space-between;
      gap: 10px;
    }

    .account-name {
      font-size: 17px;
      font-weight: 700;
      word-break: break-word;
    }

    .account-type {
      display: inline-block;
      margin-top: 6px;
      padding: 5px 9px;
      border-radius: 8px;
      background: #f0ecff;
      color: #6040dc;
      font-size: 11px;
      font-weight: 700;
    }

    .account-balance {
      margin-top: 22px;
      font-size: 24px;
      font-weight: 800;
    }

    .account-meta {
      margin-top: 9px;
      color: #858092;
      font-size: 12px;
      line-height: 1.6;
    }

    .account-empty {
      background: #ffffff;
      border: 1px dashed #d9d2e9;
      border-radius: 16px;
      padding: 45px 20px;
      text-align: center;
      color: #858092;
      grid-column: 1 / -1;
    }

    .account-error {
      background: #fff1f1;
      border: 1px solid #f1caca;
      color: #a33333;
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 15px;
    }

    /* =================================================
       PLACEHOLDER MODULE
       ================================================= */

    .module-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 28px;
      min-height: 220px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .module-icon {
      font-size: 36px;
      margin-bottom: 12px;
    }

    .module-card h3 {
      margin: 0 0 8px;
      font-size: 20px;
    }

    .module-card p {
      color: #817b91;
      font-size: 14px;
      line-height: 1.6;
      max-width: 700px;
      margin: 0;
    }

    /* =================================================
       MOBILE BOTTOM NAV
       ================================================= */

    .mobile-bottom {
      display: none;
    }

    /* =================================================
       MOBILE DRAWER
       ================================================= */

    .drawer-overlay {
      display: none;
    }

    .drawer {
      display: none;
    }

    /* =================================================
       TABLET
       ================================================= */

    @media (max-width: 1050px) {
      .finance-sidebar {
        width: 235px;
      }

      .kpi-grid {
        grid-template-columns: repeat(2, 1fr);
      }

      .dashboard-grid {
        grid-template-columns: 1fr
