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
        grid-template-columns: 1fr;
      }

      .accounts-list {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    /* =================================================
       MOBILE
       ================================================= */

    @media (max-width: 700px) {
      .finance-app {
        display: block;
        padding-bottom: 70px;
      }

      .finance-sidebar {
        display: none;
      }

      .topbar {
        height: 64px;
        padding: 0 15px;
      }

      .mobile-menu {
        display: flex;
        width: 40px;
        height: 40px;
        border: 0;
        border-radius: 11px;
        background: #f0ebff;
        color: #5935d9;
        align-items: center;
        justify-content: center;
        font-size: 21px;
        margin-right: 10px;
        cursor: pointer;
      }

      .top-title small {
        display: none;
      }

      .top-title strong {
        font-size: 18px;
      }

      .profile {
        width: 36px;
        height: 36px;
      }

      .page {
        padding: 18px 15px 25px;
      }

      .page-heading h2 {
        font-size: 21px;
      }

      .kpi-grid {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }

      .kpi {
        padding: 15px;
      }

      .kpi-value {
        font-size: 22px;
      }

      .dashboard-grid {
        grid-template-columns: 1fr;
        gap: 10px;
      }

      .panel {
        padding: 17px;
      }

      .chart-placeholder {
        height: 150px;
      }

      .quick-grid {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }

      .accounts-summary {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }

      .accounts-list {
        grid-template-columns: 1fr;
        gap: 10px;
      }

      .account-card {
        padding: 17px;
      }

      /* =============================================
         MOBILE BOTTOM
         ============================================= */

      .mobile-bottom {
        position: fixed;
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        bottom: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: #ffffff;
        border-top: 1px solid #e5e1f0;
        z-index: 40;
      }

      .bottom-item {
        border: 0;
        background: transparent;
        color: #77718c;
        font-size: 10px;
        cursor: pointer;
      }

      .bottom-item.active {
        color: #6040dc;
        font-weight: 700;
      }

      .bottom-icon {
        display: block;
        font-size: 18px;
        margin-bottom: 3px;
      }

      /* =============================================
         DRAWER
         ============================================= */

      .drawer-overlay {
        display: block;
        position: fixed;
        inset: 0;
        background: rgba(20, 16, 35, 0.38);
        z-index: 80;
      }

      .drawer {
        display: block;
        position: fixed;
        top: 0;
        left: 0;
        width: 300px;
        max-width: 86vw;
        height: 100vh;
        overflow-y: auto;
        background: #ffffff;
        z-index: 90;
        padding: 20px 15px;
        box-shadow: 8px 0 30px rgba(0, 0, 0, 0.14);
      }

      .drawer-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 5px 8px 20px;
      }

      .drawer-brand {
        font-size: 20px;
        font-weight: 800;
      }

      .drawer-close {
        width: 36px;
        height: 36px;
        border: 0;
        border-radius: 10px;
        background: #f2eff8;
        font-size: 20px;
        cursor: pointer;
      }

      .drawer-main-button {
        width: 100%;
        border: 0;
        background: transparent;
        border-radius: 10px;
        padding: 12px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        text-align: left;
        cursor: pointer;
        color: #514c61;
        font-size: 14px;
      }

      .drawer-main-button.active {
        background: #eee8ff;
        color: #5530d9;
        font-weight: 700;
      }

      .drawer-sub {
        padding-left: 26px;
        padding-bottom: 5px;
      }

      .drawer-sub button {
        width: 100%;
        border: 0;
        background: transparent;
        color: #777184;
        border-radius: 8px;
        padding: 10px;
        text-align: left;
        cursor: pointer;
        font-size: 13px;
      }

      .drawer-sub button.active {
        background: #eee8ff;
        color: #5530d9;
        font-weight: 700;
      }
    }

    @media (max-width: 420px) {
      .kpi-grid {
        grid-template-columns: 1fr;
      }

      .accounts-summary {
        grid-template-columns: 1fr;
      }
    }
  `;

  // =====================================================
  // DESKTOP SIDEBAR RENDERER
  // =====================================================

  function renderDesktopNavigation() {
    return navigation.map(function (item) {
      if (item.type === "single") {
        return React.createElement(
          "button",
          {
            key: item.name,
            className:
              active === item.name
                ? "main-nav-button active-main"
                : "main-nav-button",
            onClick: function () {
              navigate(item.name);
            }
          },
          React.createElement(
            "span",
            { className: "nav-left" },
            React.createElement(
              "span",
              { className: "nav-icon" },
              item.icon
            ),
            item.name
          )
        );
      }

      const isSectionActive =
        active === item.children[0] ||
        item.children.indexOf(active) !== -1;

      return React.createElement(
        React.Fragment,
        { key: item.name },

        React.createElement(
          "button",
          {
            className:
              isSectionActive
                ? "main-nav-button active-main"
                : "main-nav-button",
            onClick: function () {
              openSection(item.name);
            }
          },
          React.createElement(
            "span",
            { className: "nav-left" },
            React.createElement(
              "span",
              { className: "nav-icon" },
              item.icon
            ),
            item.name
          ),
          React.createElement(
            "span",
            { className: "nav-arrow" },
            expanded[item.name] ? "▲" : "▼"
          )
        ),

        expanded[item.name] &&
          React.createElement(
            "div",
            { className: "sub-nav" },
            item.children.map(function (child) {
              return React.createElement(
                "button",
                {
                  key: child,
                  className:
                    active === child
                      ? "sub-nav-button active"
                      : "sub-nav-button",
                  onClick: function () {
                    navigate(child);
                  }
                },
                child
              );
            })
          )
      );
    });
  }

  // =====================================================
  // MOBILE DRAWER RENDERER
  // =====================================================

  function renderMobileNavigation() {
    return navigation.map(function (item) {
      if (item.type === "single") {
        return React.createElement(
          "button",
          {
            key: item.name,
            className:
              active === item.name
                ? "drawer-main-button active"
                : "drawer-main-button",
            onClick: function () {
              navigate(item.name);
            }
          },
          React.createElement(
            "span",
            { className: "nav-left" },
            React.createElement(
              "span",
              { className: "nav-icon" },
              item.icon
            ),
            item.name
          )
        );
      }

      return React.createElement(
        React.Fragment,
        { key: item.name },

        React.createElement(
          "button",
          {
            className:
              item.children.indexOf(active) !== -1
                ? "drawer-main-button active"
                : "drawer-main-button",
            onClick: function () {
              toggleSection(item.name);
            }
          },
          React.createElement(
            "span",
            { className: "nav-left" },
            React.createElement(
              "span",
              { className: "nav-icon" },
              item.icon
            ),
            item.name
          ),
          expanded[item.name] ? "▲" : "▼"
        ),

        expanded[item.name] &&
          React.createElement(
            "div",
            { className: "drawer-sub" },
            item.children.map(function (child) {
              return React.createElement(
                "button",
                {
                  key: child,
                  className:
                    active === child ? "active" : "",
                  onClick: function () {
                    navigate(child);
                  }
                },
                child
              );
            })
          )
      );
    });
  }

  // =====================================================
  // OVERVIEW PAGE
  // =====================================================

  function renderOverview() {
    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },
        React.createElement("h2", null, "Overview"),
        React.createElement(
          "p",
          null,
          "Everything at a glance across your financial life."
        )
      ),

      React.createElement(
        "div",
        { className: "kpi-grid" },
        overviewCards.map(function (card) {
          return React.createElement(
            "div",
            { className: "kpi", key: card[0] },
            React.createElement(
              "div",
              { className: "kpi-label" },
              card[0]
            ),
            React.createElement(
              "div",
              { className: "kpi-value" },
              card[1]
            ),
            React.createElement(
              "div",
              { className: "kpi-note" },
              card[2]
            )
          );
        })
      ),

      React.createElement(
        "div",
        { className: "dashboard-grid" },

        React.createElement(
          "div",
          { className: "panel" },
          React.createElement(
            "h3",
            null,
            "Financial Overview"
          ),
          React.createElement(
            "div",
            { className: "panel-subtitle" },
            "Your financial activity will appear here."
          ),
          React.createElement(
            "div",
            { className: "chart-placeholder" },
            "Financial chart will be connected to real data."
          )
        ),

        React.createElement(
          "div",
          { className: "panel ai-panel" },
          React.createElement(
            "div",
            { className: "ai-icon" },
            "AI"
          ),
          React.createElement(
            "h3",
            null,
            "AI Finance Assistant"
          ),
          React.createElement(
            "div",
            { className: "ai-text" },
            "Your AI assistant will eventually analyze your finances, investments, markets and trading activity from one place."
          )
        )
      ),

      React.createElement(
        "div",
        { className: "quick-grid" },

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              navigate("Accounts");
            }
          },
          React.createElement("strong", null, "Accounts"),
          React.createElement(
            "span",
            null,
            "Manage your financial accounts"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              navigate("Transactions");
            }
          },
          React.createElement("strong", null, "Transactions"),
          React.createElement(
            "span",
            null,
            "Track income and expenses"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              navigate("Portfolio");
            }
          },
          React.createElement("strong", null, "Portfolio"),
          React.createElement(
            "span",
            null,
            "View investments"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              navigate("AI Chat");
            }
          },
          React.createElement("strong", null, "AI Chat"),
          React.createElement(
            "span",
            null,
            "Ask your financial AI"
          )
        )
      )
    );
  }

  // =====================================================
  // ACCOUNTS PAGE
  // EXISTING BACKEND FUNCTIONALITY PRESERVED
  // =====================================================

  function renderAccounts() {
    const totalBalance = accounts.reduce(
      function (total, account) {
        return total + Number(account.current_balance || 0);
      },
      0
    );

    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },
        React.createElement("h2", null, "Accounts"),
        React.createElement(
          "p",
          null,
          "Manage your bank accounts, cash, credit cards and wallets."
        )
      ),

      accountsError &&
        React.createElement(
          "div",
          { className: "account-error" },
          accountsError
        ),

      React.createElement(
        "div",
        { className: "accounts-summary" },

        React.createElement(
          "div",
          { className: "summary-card" },
          React.createElement(
            "div",
            { className: "summary-label" },
            "Total Accounts"
          ),
          React.createElement(
            "div",
            { className: "summary-value" },
            accounts.length
          )
        ),

        React.createElement(
          "div",
          { className: "summary-card" },
          React.createElement(
            "div",
            { className: "summary-label" },
            "Total Balance"
          ),
          React.createElement(
            "div",
            { className: "summary-value" },
            formatMoney(totalBalance, "INR")
          )
        ),

        React.createElement(
          "div",
          { className: "summary-card" },
          React.createElement(
            "div",
            { className: "summary-label" },
            "Status"
          ),
          React.createElement(
            "div",
            { className: "summary-value" },
            accountsLoading ? "Loading..." : "Connected"
          )
        )
      ),

      React.createElement(
        "div",
        { className: "accounts-list" },

        accountsLoading
          ? React.createElement(
              "div",
              { className: "account-empty" },
              "Loading accounts..."
            )
          : accounts.length === 0
          ? React.createElement(
              "div",
              { className: "account-empty" },
              React.createElement(
                "strong",
                null,
                "No active accounts yet."
              ),
              React.createElement(
                "div",
                { style: { marginTop: "8px" } },
                "Your Accounts section is connected to the backend. Add Account functionality will be built next."
              )
            )
          : accounts.map(function (account) {
              return React.createElement(
                "div",
                {
                  className: "account-card",
                  key: account.id
                },

                React.createElement(
                  "div",
                  { className: "account-top" },

                  React.createElement(
                    "div",
                    null,

                    React.createElement(
                      "div",
                      { className: "account-name" },
                      account.name
                    ),

                    React.createElement(
                      "div",
                      { className: "account-type" },
                      accountTypeLabel(account.account_type)
                    )
                  )
                ),

                React.createElement(
                  "div",
                  { className: "account-balance" },
                  formatMoney(
                    account.current_balance,
                    account.currency
                  )
                ),

                React.createElement(
                  "div",
                  { className: "account-meta" },
                  account.institution
                    ? `Institution: ${account.institution}`
                    : "Institution: —",
                  React.createElement("br"),
                  account.account_number
                    ? `Account: ${account.account_number}`
                    : "Account: —"
                )
              );
            })
      )
    );
  }

  // =====================================================
  // GENERIC MODULE PAGE
  // =====================================================

  function renderModulePage() {
    let icon = "📁";

    if (
      active.toLowerCase().includes("finance") ||
      active === "Transactions" ||
      active === "Accounts" ||
      active === "Budget"
    ) {
      icon = "💰";
    } else if (
      active.toLowerCase().includes("wealth") ||
      active === "Assets" ||
      active === "Liabilities" ||
      active === "Net Worth"
    ) {
      icon = "💎";
    } else if (
      active.toLowerCase().includes("investment") ||
      active === "Portfolio" ||
      active === "Stocks" ||
      active === "Crypto"
    ) {
      icon = "📊";
    } else if (
      active.toLowerCase().includes("trading") ||
      active === "Markets" ||
      active === "Charts" ||
      active === "Backtesting"
    ) {
      icon = "📈";
    } else if (active.toLowerCase().includes("ai")) {
      icon = "🤖";
    }

    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },
        React.createElement("h2", null, active),
        React.createElement(
          "p",
          null,
          getPageDescription()
        )
      ),

      React.createElement(
        "div",
        { className: "module-card" },

        React.createElement(
          "div",
          { className: "module-icon" },
          icon
        ),

        React.createElement(
          "h3",
          null,
          active
        ),

        React.createElement(
          "p",
          null,
          "The navigation structure is now ready. This module will be connected to its real functionality without changing the rest of the application."
        )
      )
    );
  }

  // =====================================================
  // PAGE CONTENT ROUTER
  // =====================================================

  function renderPage() {
    if (active === "Overview") {
      return renderOverview();
    }

    if (active === "Accounts") {
      return renderAccounts();
    }

    return renderModulePage();
  }

  // =====================================================
  // MOBILE BOTTOM NAVIGATION
  // =====================================================

  const mobileShortcuts = [
    ["Overview", "🏠"],
    ["Finance Overview", "💰"],
    ["Investment Overview", "📊"],
    ["Trading Overview", "📈"],
    ["AI Chat", "🤖"]
  ];

  // =====================================================
  // MAIN RETURN
  // =====================================================

  return React.createElement(
    React.Fragment,
    null,

    // ===================================================
    // GLOBAL CSS
    // ===================================================

    React.createElement(
      "style",
      null,
      styles
    ),

    // ===================================================
    // MOBILE DRAWER
    // ===================================================

    menuOpen &&
      React.createElement(
        React.Fragment,
        null,

        React.createElement("div", {
          className: "drawer-overlay",
          onClick: function () {
            setMenuOpen(false);
          }
        }),

        React.createElement(
          "aside",
          { className: "drawer" },

          React.createElement(
            "div",
            { className: "drawer-head" },

            React.createElement(
              "div",
              { className: "drawer-brand" },
              "AI ",
              React.createElement(
                "span",
                { style: { color: "#7048ff" } },
                "Finance"
              )
            ),

            React.createElement(
              "button",
              {
                className: "drawer-close",
                onClick: function () {
                  setMenuOpen(false);
                }
              },
              "×"
            )
          ),

          renderMobileNavigation()
        )
      ),

    // ===================================================
    // APPLICATION
    // ===================================================

    React.createElement(
      "div",
      { className: "finance-app" },

      // =================================================
      // DESKTOP SIDEBAR
      // =================================================

      React.createElement(
        "aside",
        { className: "finance-sidebar" },

        React.createElement(
          "div",
          { className: "brand" },
          "AI ",
          React.createElement(
            "span",
            null,
            "Finance"
          )
        ),

        renderDesktopNavigation()
      ),

      // =================================================
      // MAIN AREA
      // =================================================

      React.createElement(
        "main",
        { className: "finance-main" },

        // ===============================================
        // TOP BAR
        // ===============================================

        React.createElement(
          "header",
          { className: "topbar" },

          React.createElement(
            "div",
            { className: "top-left" },

            React.createElement(
              "button",
              {
                className: "mobile-menu",
                onClick: function () {
                  setMenuOpen(true);
                }
              },
              "☰"
            ),

            React.createElement(
              "div",
              { className: "top-title" },

              React.createElement(
                "small",
                null,
                "AI Finance Trading OS"
              ),

              React.createElement(
                "strong",
                null,
                getPageTitle()
              )
            )
          ),

          React.createElement(
            "div",
            { className: "profile" },
            "N"
          )
        ),

        // ===============================================
        // PAGE
        // ===============================================

        React.createElement(
          "section",
          { className: "page" },
          renderPage()
        )
      )
    ),

    // ===================================================
    // MOBILE BOTTOM NAV
    // ===================================================

    React.createElement(
      "nav",
      { className: "mobile-bottom" },

      mobileShortcuts.map(function (item) {
        return React.createElement(
          "button",
          {
            key: item[0],
            className:
              active === item[0]
                ? "bottom-item active"
                : "bottom-item",
            onClick: function () {
              navigate(item[0]);
            }
          },

          React.createElement(
            "span",
            { className: "bottom-icon" },
            item[1]
          ),

          item[0]
            .replace(" Overview", "")
            .replace(" Chat", "")
        );
      })
    )
  );
}

export default App;
