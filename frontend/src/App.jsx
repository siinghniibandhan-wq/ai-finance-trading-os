import React, { useEffect, useState } from "react";

/*
=====================================================
AI FINANCE TRADING OS
APP.JSX
=====================================================

NAVIGATION RULES
-----------------------------------------------------
1. Overview is the global homepage.

2. Finance itself opens Finance Overview.
   Finance does NOT contain "Finance Overview"
   as a separate submenu item.

3. Wealth itself opens Wealth Overview.

4. Investments itself opens Investment Overview.

5. Trading itself opens Trading Overview.

6. AI itself opens AI Overview.

7. Clicking the section NAME:
   - opens its overview
   - expands its submenu

8. Clicking the ARROW:
   - only expands/collapses the submenu
   - does NOT change the current page

9. Only ONE major section can be expanded at a time.

10. Accounts API is preserved.
=====================================================
*/

function App() {
  // =====================================================
  // BASIC APP STATE
  // =====================================================

  const [active, setActive] = useState("Overview");
  const [menuOpen, setMenuOpen] = useState(false);

  // =====================================================
  // EXPANDED SECTION
  // null = everything collapsed
  // =====================================================

  const [expandedSection, setExpandedSection] = useState(null);

  // =====================================================
  // ACCOUNTS STATE
  // EXISTING FUNCTIONALITY PRESERVED
  // =====================================================

  const [accounts, setAccounts] = useState([]);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [accountsError, setAccountsError] = useState("");

  // =====================================================
  // ADD ACCOUNT STATE
  // =====================================================

  const [showAddAccount, setShowAddAccount] = useState(false);

  const [accountForm, setAccountForm] = useState({
    name: "",
    account_type: "bank",
    institution: "",
    account_number: "",
    currency: "INR",
    opening_balance: ""
  });

  const [accountSaving, setAccountSaving] = useState(false);

  // =====================================================
  // NAVIGATION STRUCTURE
  // IMPORTANT:
  // OVERVIEW ITEMS ARE NOT SUBMENU ITEMS.
  // THE MAIN SECTION ITSELF IS THE OVERVIEW.
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
  // =====================================================

  const overviewCards = [
    ["Net Worth", "₹0", "Assets − liabilities"],
    ["Total Assets", "₹0", "Current asset value"],
    ["Liabilities", "₹0", "Outstanding amount"],
    ["Investments", "₹0", "Portfolio value"]
  ];

  // =====================================================
  // SECTION OVERVIEW TITLES
  // =====================================================

  const sectionOverviewTitles = {
    Finance: "Finance Overview",
    Wealth: "Wealth Overview",
    Investments: "Investment Overview",
    Trading: "Trading Overview",
    AI: "AI Overview"
  };

  // =====================================================
  // SECTION OVERVIEW DESCRIPTIONS
  // =====================================================

  const sectionDescriptions = {
    Finance:
      "Accounts, transactions, cash flow, budgets and everyday finances.",

    Wealth:
      "Assets, liabilities, net worth, insurance and long-term wealth.",

    Investments:
      "Your investment portfolio, holdings and investment performance.",

    Trading:
      "Markets, strategies, positions, orders, risk and trading activity.",

    AI:
      "Your AI-powered financial assistant, research, analysis and reports."
  };

  // =====================================================
  // FIND PARENT SECTION
  // =====================================================

  function findParentSection(page) {
    for (let i = 0; i < navigation.length; i += 1) {
      const item = navigation[i];

      if (
        item.type === "section" &&
        item.children.indexOf(page) !== -1
      ) {
        return item.name;
      }
    }

    return null;
  }

  // =====================================================
  // OPEN MAIN SECTION
  //
  // Example:
  // Click Finance
  // -> Finance Overview
  // -> Finance expands
  // =====================================================

  function openMainSection(sectionName) {
    setActive(sectionName);
    setExpandedSection(sectionName);
    setMenuOpen(false);
  }

  // =====================================================
  // TOGGLE ONLY THE ARROW
  //
  // IMPORTANT:
  // This does NOT change active page.
  // =====================================================

  function toggleSection(sectionName) {
    setExpandedSection(function (current) {
      if (current === sectionName) {
        return null;
      }

      return sectionName;
    });
  }

  // =====================================================
  // OPEN SINGLE PAGE
  //
  // Overview / Reports / Settings
  // collapse all major sections.
  // =====================================================

  function openSinglePage(page) {
    setActive(page);
    setExpandedSection(null);
    setMenuOpen(false);
  }

  // =====================================================
  // OPEN SUBPAGE
  // =====================================================

  function openSubPage(page, parentSection) {
    setActive(page);
    setExpandedSection(parentSection);
    setMenuOpen(false);
  }

  // =====================================================
  // LOAD ACCOUNTS
  //
  // EXISTING API URL PRESERVED
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
  // LOAD ACCOUNTS WHEN ACCOUNTS PAGE OPENS
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
  // ADD ACCOUNT — FORM FIELD HANDLER
  // =====================================================

  function updateAccountForm(field, value) {
    setAccountForm(function (current) {
      return {
        ...current,
        [field]: value
      };
    });
  }

  // =====================================================
  // ADD ACCOUNT — RESET FORM
  // =====================================================

  function resetAccountForm() {
    setAccountForm({
      name: "",
      account_type: "bank",
      institution: "",
      account_number: "",
      currency: "INR",
      opening_balance: ""
    });

    setAccountsError("");
  }

  // =====================================================
  // ADD ACCOUNT — SUBMIT
  //
  // Uses the existing Accounts API.
  // =====================================================

  async function createAccount() {
    setAccountsError("");

    if (!accountForm.name.trim()) {
      setAccountsError("Account name is required.");
      return;
    }

    const openingBalance =
      accountForm.opening_balance === ""
        ? 0
        : Number(accountForm.opening_balance);

    if (!Number.isFinite(openingBalance)) {
      setAccountsError("Opening balance must be a valid number.");
      return;
    }

    setAccountSaving(true);

    try {
      const response = await fetch(
        "https://ai-finance-trading-os-api.onrender.com/api/accounts/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            name: accountForm.name.trim(),
            account_type: accountForm.account_type,
            institution: accountForm.institution.trim() || null,
            account_number: accountForm.account_number.trim() || null,
            currency: accountForm.currency,
            opening_balance: openingBalance
          })
        }
      );

      const data = await response.json().catch(function () {
        return null;
      });

      if (!response.ok) {
        throw new Error(
          data?.detail ||
          data?.message ||
          "Unable to create account."
        );
      }

      resetAccountForm();
      setShowAddAccount(false);

      // Reload from the database so the UI shows the saved record.
      await loadAccounts();
    } catch (error) {
      setAccountsError(
        error?.message || "Unable to create account."
      );
    } finally {
      setAccountSaving(false);
    }
  }

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
    if (!type) {
      return "Account";
    }

    return String(type)
      .replaceAll("_", " ")
      .replace(/\b\w/g, function (letter) {
        return letter.toUpperCase();
      });
  }

  // =====================================================
  // DETERMINE CURRENT OVERVIEW SECTION
  // =====================================================

  function getCurrentOverviewSection() {
    if (
      active === "Finance" ||
      active === "Wealth" ||
      active === "Investments" ||
      active === "Trading" ||
      active === "AI"
    ) {
      return active;
    }

    return null;
  }

  // =====================================================
  // PAGE TITLE
  // =====================================================

  function getPageTitle() {
    const overviewSection = getCurrentOverviewSection();

    if (overviewSection) {
      return sectionOverviewTitles[overviewSection];
    }

    if (active === "Overview") {
      return "Overview";
    }

    return active;
  }

  // =====================================================
  // PAGE DESCRIPTION
  // =====================================================

  function getPageDescription() {
    const overviewSection = getCurrentOverviewSection();

    if (overviewSection) {
      return sectionDescriptions[overviewSection];
    }

    const descriptions = {
      Accounts:
        "Manage your bank accounts, cash, credit cards and wallets.",

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
        "Track gold holdings.",

      Crypto:
        "Track cryptocurrency investments.",

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
        "Record and analyze trading decisions.",

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
      width: 275px;
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

    /* =================================================
       MAIN NAVIGATION BUTTON
       ================================================= */

    .main-nav-row {
      display: flex;
      width: 100%;
      margin-bottom: 3px;
    }

    .main-nav-button {
      flex: 1;
      min-width: 0;
      border: 0;
      background: transparent;
      border-radius: 10px 0 0 10px;
      padding: 11px 12px;
      display: flex;
      align-items: center;
      gap: 9px;
      cursor: pointer;
      color: #514c61;
      font-size: 14px;
      text-align: left;
    }

    .main-nav-button:hover {
      background: #f5f1ff;
    }

    .main-nav-button.active-main {
      background: #eee8ff;
      color: #5530d9;
      font-weight: 700;
    }

    .nav-arrow-button {
      width: 42px;
      border: 0;
      background: transparent;
      border-radius: 0 10px 10px 0;
      color: #817b91;
      cursor: pointer;
      font-size: 11px;
    }

    .nav-arrow-button:hover {
      background: #f5f1ff;
      color: #5530d9;
    }

    .main-nav-row.active-row .nav-arrow-button {
      background: #eee8ff;
      color: #5530d9;
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

    /* =================================================
       SUB NAVIGATION
       ================================================= */

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
       MAIN AREA
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
       ADD ACCOUNT FORM
       ================================================= */

    .accounts-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 20px;
    }

    .add-account-button {
      border: 0;
      background: #7048ff;
      color: #ffffff;
      border-radius: 10px;
      padding: 11px 17px;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
    }

    .add-account-button:hover {
      background: #5f38e8;
    }

    .account-form-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 20px;
    }

    .account-form-title {
      margin: 0 0 16px;
      font-size: 18px;
      font-weight: 800;
    }

    .account-form-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .account-field {
      min-width: 0;
    }

    .account-field.full {
      grid-column: 1 / -1;
    }

    .account-field label {
      display: block;
      margin-bottom: 6px;
      color: #625c70;
      font-size: 12px;
      font-weight: 700;
    }

    .account-field input,
    .account-field select {
      width: 100%;
      min-height: 44px;
      border: 1px solid #ddd7ea;
      border-radius: 10px;
      background: #ffffff;
      color: #18152b;
      padding: 10px 12px;
      font-size: 14px;
      outline: none;
    }

    .account-field input:focus,
    .account-field select:focus {
      border-color: #7048ff;
      box-shadow: 0 0 0 3px rgba(112, 72, 255, 0.10);
    }

    .account-form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 18px;
    }

    .account-cancel-button {
      border: 1px solid #ddd7ea;
      background: #ffffff;
      color: #5d566a;
      border-radius: 10px;
      padding: 10px 16px;
      font-weight: 700;
      cursor: pointer;
    }

    .account-save-button {
      border: 0;
      background: #7048ff;
      color: #ffffff;
      border-radius: 10px;
      padding: 10px 18px;
      font-weight: 700;
      cursor: pointer;
    }

    .account-save-button:disabled,
    .account-cancel-button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    /* =================================================
       MODULE PAGE
       ================================================= */

    .module-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 28px;
      min-height: 220px;
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
    }

    /* =================================================
       MOBILE
       ================================================= */

    .mobile-bottom {
      display: none;
    }

    .drawer {
      display: none;
    }

    @media (max-width: 1050px) {
      .finance-sidebar {
        width: 240px;
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

      .account-form-grid {
        grid-template-columns: 1fr;
      }

      .account-field.full {
        grid-column: auto;
      }

      .accounts-toolbar {
        align-items: flex-start;
      }

      .add-account-button {
        flex-shrink: 0;
      }

      /* =============================================
         MOBILE BOTTOM NAV
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
         MOBILE DRAWER
         ============================================= */

      .drawer-overlay {
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
        box-shadow: 8px 0 30px rgba(0,0,0,0.14);
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

      .drawer-main-row {
        display: flex;
        width: 100%;
        margin-bottom: 3px;
      }

      .drawer-main-button {
        flex: 1;
        border: 0;
        background: transparent;
        border-radius: 10px 0 0 10px;
        padding: 12px 10px;
        display: flex;
        align-items: center;
        gap: 8px;
        text-align: left;
        cursor: pointer;
        color: #514c61;
        font-size: 14px;
      }

      .drawer-main-button.active {
        background: #eee8ff;
        color: #5535d9;
        font-weight: 700;
      }

      .drawer-arrow-button {
        width: 42px;
        border: 0;
        background: transparent;
        border-radius: 0 10px 10px 0;
        cursor: pointer;
        color: #817b91;
      }

      .drawer-arrow-button:hover {
        background: #f5f1ff;
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
        color: #5535d9;
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
  // DESKTOP NAVIGATION
  // =====================================================

  function renderDesktopNavigation() {
    return navigation.map(function (item) {
      // -------------------------------------------------
      // SINGLE ITEM
      // -------------------------------------------------

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
              openSinglePage(item.name);
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

      // -------------------------------------------------
      // MAIN SECTION
      // -------------------------------------------------

      const sectionIsActive =
        active === item.name ||
        findParentSection(active) === item.name;

      return React.createElement(
        React.Fragment,
        { key: item.name },

        React.createElement(
          "div",
          {
            className:
              sectionIsActive
                ? "main-nav-row active-row"
                : "main-nav-row"
          },

          // ---------------------------------------------
          // SECTION NAME
          // ---------------------------------------------

          React.createElement(
            "button",
            {
              className:
                sectionIsActive
                  ? "main-nav-button active-main"
                  : "main-nav-button",

              onClick: function () {
                openMainSection(item.name);
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
          ),

          // ---------------------------------------------
          // ARROW
          // ONLY COLLAPSES / EXPANDS
          // ---------------------------------------------

          React.createElement(
            "button",
            {
              className: "nav-arrow-button",

              onClick: function (event) {
                event.stopPropagation();
                toggleSection(item.name);
              },

              "aria-label":
                expandedSection === item.name
                  ? `Collapse ${item.name}`
                  : `Expand ${item.name}`
            },

            expandedSection === item.name
              ? "▲"
              : "▼"
          )
        ),

        // -----------------------------------------------
        // CHILDREN
        // -----------------------------------------------

        expandedSection === item.name &&
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
                    openSubPage(child, item.name);
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
  // MOBILE NAVIGATION
  // =====================================================

  function renderMobileNavigation() {
    return navigation.map(function (item) {
      // -------------------------------------------------
      // SINGLE ITEM
      // -------------------------------------------------

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
              openSinglePage(item.name);
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

      // -------------------------------------------------
      // SECTION
      // -------------------------------------------------

      const sectionIsActive =
        active === item.name ||
        findParentSection(active) === item.name;

      return React.createElement(
        React.Fragment,
        { key: item.name },

        React.createElement(
          "div",
          {
            className:
              sectionIsActive
                ? "drawer-main-row active-row"
                : "drawer-main-row"
          },

          // ---------------------------------------------
          // SECTION NAME
          // ---------------------------------------------

          React.createElement(
            "button",
            {
              className:
                sectionIsActive
                  ? "drawer-main-button active"
                  : "drawer-main-button",

              onClick: function () {
                openMainSection(item.name);
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
          ),

          // ---------------------------------------------
          // MOBILE ARROW
          // ---------------------------------------------

          React.createElement(
            "button",
            {
              className: "drawer-arrow-button",

              onClick: function (event) {
                event.stopPropagation();
                toggleSection(item.name);
              }
            },

            expandedSection === item.name
              ? "▲"
              : "▼"
          )
        ),

        // -----------------------------------------------
        // MOBILE CHILDREN
        // -----------------------------------------------

        expandedSection === item.name &&
          React.createElement(
            "div",
            { className: "drawer-sub" },

            item.children.map(function (child) {
              return React.createElement(
                "button",
                {
                  key: child,

                  className:
                    active === child
                      ? "active"
                      : "",

                  onClick: function () {
                    openSubPage(child, item.name);
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
  // GLOBAL OVERVIEW
  // =====================================================

  function renderOverview() {
    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },

        React.createElement(
          "h2",
          null,
          "Overview"
        ),

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
            {
              className: "kpi",
              key: card[0]
            },

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
            "Your combined financial picture will appear here."
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
              openMainSection("Finance");
            }
          },

          React.createElement(
            "strong",
            null,
            "Finance"
          ),

          React.createElement(
            "span",
            null,
            "Accounts, transactions and cash flow"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              openMainSection("Wealth");
            }
          },

          React.createElement(
            "strong",
            null,
            "Wealth"
          ),

          React.createElement(
            "span",
            null,
            "Assets, liabilities and net worth"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              openMainSection("Investments");
            }
          },

          React.createElement(
            "strong",
            null,
            "Investments"
          ),

          React.createElement(
            "span",
            null,
            "Portfolio and investments"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              openMainSection("AI");
            }
          },

          React.createElement(
            "strong",
            null,
            "AI"
          ),

          React.createElement(
            "span",
            null,
            "AI financial assistant"
          )
        )
      )
    );
  }

  // =====================================================
  // SECTION OVERVIEW PAGE
  // =====================================================

  function renderSectionOverview(sectionName) {
    const iconMap = {
      Finance: "💰",
      Wealth: "💎",
      Investments: "📊",
      Trading: "📈",
      AI: "🤖"
    };

    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },

        React.createElement(
          "h2",
          null,
          sectionOverviewTitles[sectionName]
        ),

        React.createElement(
          "p",
          null,
          sectionDescriptions[sectionName]
        )
      ),

      React.createElement(
        "div",
        { className: "module-card" },

        React.createElement(
          "div",
          { className: "module-icon" },
          iconMap[sectionName]
        ),

        React.createElement(
          "h3",
          null,
          sectionOverviewTitles[sectionName]
        ),

        React.createElement(
          "p",
          null,
          "This is the main overview for the ",
          sectionName,
          " section. Its dashboard, analytics and real data will be connected here as we build the individual modules."
        )
      )
    );
  }

  // =====================================================
  // ACCOUNTS PAGE
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

      // ===================================================
      // ACCOUNTS HEADER
      // ===================================================

      React.createElement(
        "div",
        { className: "accounts-toolbar" },

        React.createElement(
          "div",
          null,

          React.createElement(
            "div",
            { className: "page-heading", style: { marginBottom: 0 } },

            React.createElement(
              "h2",
              null,
              "Accounts"
            ),

            React.createElement(
              "p",
              null,
              "Manage your bank accounts, cash, credit cards and wallets."
            )
          )
        ),

        React.createElement(
          "button",
          {
            className: "add-account-button",
            onClick: function () {
              setAccountsError("");
              setShowAddAccount(function (current) {
                return !current;
              });
            }
          },
          showAddAccount ? "Close" : "+ Add Account"
        )
      ),

      // ===================================================
      // ACCOUNT ERROR
      // ===================================================

      accountsError &&
        React.createElement(
          "div",
          { className: "account-error" },
          accountsError
        ),

      // ===================================================
      // ADD ACCOUNT FORM
      // ===================================================

      showAddAccount &&
        React.createElement(
          "div",
          { className: "account-form-card" },

          React.createElement(
            "h3",
            { className: "account-form-title" },
            "Add Account"
          ),

          React.createElement(
            "div",
            { className: "account-form-grid" },

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Account Name *"
              ),

              React.createElement("input", {
                type: "text",
                placeholder: "e.g. HDFC Salary Account",
                value: accountForm.name,
                onChange: function (event) {
                  updateAccountForm("name", event.target.value);
                }
              })
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Account Type *"
              ),

              React.createElement(
                "select",
                {
                  value: accountForm.account_type,
                  onChange: function (event) {
                    updateAccountForm(
                      "account_type",
                      event.target.value
                    );
                  }
                },

                React.createElement(
                  "option",
                  { value: "bank" },
                  "Bank Account"
                ),

                React.createElement(
                  "option",
                  { value: "cash" },
                  "Cash"
                ),

                React.createElement(
                  "option",
                  { value: "credit_card" },
                  "Credit Card"
                ),

                React.createElement(
                  "option",
                  { value: "wallet" },
                  "Wallet"
                )
              )
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Institution"
              ),

              React.createElement("input", {
                type: "text",
                placeholder: "e.g. HDFC Bank",
                value: accountForm.institution,
                onChange: function (event) {
                  updateAccountForm(
                    "institution",
                    event.target.value
                  );
                }
              })
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Account Number"
              ),

              React.createElement("input", {
                type: "text",
                placeholder: "Optional",
                value: accountForm.account_number,
                onChange: function (event) {
                  updateAccountForm(
                    "account_number",
                    event.target.value
                  );
                }
              })
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Currency"
              ),

              React.createElement(
                "select",
                {
                  value: accountForm.currency,
                  onChange: function (event) {
                    updateAccountForm(
                      "currency",
                      event.target.value
                    );
                  }
                },

                React.createElement(
                  "option",
                  { value: "INR" },
                  "INR — Indian Rupee"
                ),

                React.createElement(
                  "option",
                  { value: "USD" },
                  "USD — US Dollar"
                ),

                React.createElement(
                  "option",
                  { value: "EUR" },
                  "EUR — Euro"
                ),

                React.createElement(
                  "option",
                  { value: "GBP" },
                  "GBP — British Pound"
                )
              )
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Opening Balance"
              ),

              React.createElement("input", {
                type: "number",
                step: "0.01",
                placeholder: "0.00",
                value: accountForm.opening_balance,
                onChange: function (event) {
                  updateAccountForm(
                    "opening_balance",
                    event.target.value
                  );
                }
              })
            )
          ),

          React.createElement(
            "div",
            { className: "account-form-actions" },

            React.createElement(
              "button",
              {
                className: "account-cancel-button",
                disabled: accountSaving,
                onClick: function () {
                  resetAccountForm();
                  setShowAddAccount(false);
                }
              },
              "Cancel"
            ),

            React.createElement(
              "button",
              {
                className: "account-save-button",
                disabled: accountSaving,
                onClick: createAccount
              },
              accountSaving ? "Saving..." : "Save Account"
            )
          )
        ),

      // ===================================================
      // ACCOUNT SUMMARY
      // ===================================================

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

      // ===================================================
      // ACCOUNT LIST
      // ===================================================

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
                "Use + Add Account above to create your first account."
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
                  { className: "account-name" },
                  account.name
                ),

                React.createElement(
                  "div",
                  { className: "account-type" },
                  accountTypeLabel(account.account_type)
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
      active === "Transactions" ||
      active === "Accounts" ||
      active === "Budget" ||
      active === "Cash Flow" ||
      active === "Categories"
    ) {
      icon = "💰";
    }

    if (
      active === "Assets" ||
      active === "Liabilities" ||
      active === "Net Worth" ||
      active === "Insurance" ||
      active === "Real Estate"
    ) {
      icon = "💎";
    }

    if (
      active === "Portfolio" ||
      active === "Stocks" ||
      active === "Mutual Funds" ||
      active === "ETFs" ||
      active === "Bonds" ||
      active === "Gold" ||
      active === "Crypto"
    ) {
      icon = "📊";
    }

    if (
      active === "Markets" ||
      active === "Watchlist" ||
      active === "Screener" ||
      active === "Charts" ||
      active === "Strategies" ||
      active === "Backtesting" ||
      active === "Paper Trading" ||
      active === "Live Trading" ||
      active === "Positions" ||
      active === "Orders"
    ) {
      icon = "📈";
    }

    if (
      active === "AI Chat" ||
      active === "AI Research" ||
      active === "AI Analysis" ||
      active === "AI Predictions" ||
      active === "AI Reports"
    ) {
      icon = "🤖";
    }

    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },

        React.createElement(
          "h2",
          null,
          active
        ),

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
          "This module is part of the Finance OS architecture and will be connected to its full functionality without affecting the other modules."
        )
      )
    );
  }

  // =====================================================
  // PAGE ROUTER
  // =====================================================

  function renderPage() {
    // Global overview
    if (active === "Overview") {
      return renderOverview();
    }

    // Main section overview
    if (
      active === "Finance" ||
      active === "Wealth" ||
      active === "Investments" ||
      active === "Trading" ||
      active === "AI"
    ) {
      return renderSectionOverview(active);
    }

    // Existing Accounts page
    if (active === "Accounts") {
      return renderAccounts();
    }

    // Everything else for now
    return renderModulePage();
  }

  // =====================================================
  // MOBILE QUICK NAVIGATION
  // =====================================================

  const mobileShortcuts = [
    ["Overview", "🏠"],
    ["Finance", "💰"],
    ["Investments", "📊"],
    ["Trading", "📈"],
    ["AI", "🤖"]
  ];

  // =====================================================
  // MAIN RETURN
  // =====================================================

  return React.createElement(
    React.Fragment,
    null,

    // ===================================================
    // GLOBAL STYLES
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
                {
                  style: {
                    color: "#7048ff"
                  }
                },
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
      // MAIN CONTENT
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
        // PAGE CONTENT
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
              active === item[0] ||
              findParentSection(active) === item[0]
                ? "bottom-item active"
                : "bottom-item",

            onClick: function () {
              openMainSection(item[0]);
            }
          },

          React.createElement(
            "span",
            { className: "bottom-icon" },
            item[1]
          ),

          item[0]
        );
      })
    )
  );
}

export default App;
