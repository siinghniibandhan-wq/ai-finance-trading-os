import React, { useEffect, useState } from "react";

function App() {
  // =====================================================
  // BASIC APP STATE
  // =====================================================

  const [active, setActive] = useState("Dashboard");
  const [menuOpen, setMenuOpen] = useState(false);

  // =====================================================
  // ACCOUNTS STATE
  // =====================================================

  const [accounts, setAccounts] = useState([]);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [accountsError, setAccountsError] = useState("");

  // =====================================================
  // NAVIGATION MENU
  // EDIT MENU ITEMS HERE
  // =====================================================

  const menu = [
    "Dashboard",
    "Accounts",
    "Transactions",
    "Investments",
    "Assets",
    "Liabilities",
    "Trading",
    "AI Chat",
    "Reports",
    "Settings"
  ];

  // =====================================================
  // DASHBOARD KPI DATA
  // WILL BE CONNECTED TO REAL DATA LATER
  // =====================================================

  const cards = [
    ["Net Worth", "₹0", "Assets − liabilities"],
    ["Total Assets", "₹0", "Current asset value"],
    ["Liabilities", "₹0", "Outstanding amount"],
    ["Investments", "₹0", "Portfolio value"]
  ];

  // =====================================================
  // NAVIGATION FUNCTION
  // =====================================================

  function navigate(item) {
    setActive(item);
    setMenuOpen(false);
  }

  // =====================================================
  // LOAD ACCOUNTS FROM BACKEND
  //
  // EDIT API URL HERE IF BACKEND URL EVER CHANGES
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
  // HELPER: FORMAT MONEY
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
  // MAIN APP
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
      `
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
         APP LAYOUT
         ================================================= */

      .finance-app {
        min-height: 100vh;
        display: flex;
        background: #f5f3fb;
      }

      /* =================================================
         DESKTOP SIDEBAR
         ================================================= */

      .finance-sidebar {
        width: 245px;
        min-height: 100vh;
        flex-shrink: 0;
        background: #ffffff;
        border-right: 1px solid #e8e3f4;
        padding: 22px 14px;
      }

      .brand {
        padding: 4px 12px 25px;
        font-size: 21px;
        font-weight: 800;
      }

      .brand span {
        color: #7048ff;
      }

      .side-item {
        width: 100%;
        padding: 12px 14px;
        margin-bottom: 4px;
        border: 0;
        background: transparent;
        border-radius: 10px;
        text-align: left;
        font-size: 14px;
        color: #514c61;
        cursor: pointer;
      }

      .side-item:hover {
        background: #f4f0ff;
      }

      .side-item.active {
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
         GENERAL PAGE
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
         DASHBOARD KPI
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
        min-width: 0;
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
         DASHBOARD PANELS
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
        min-width: 0;
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

      .chart {
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
        background: linear-gradient(
          145deg,
          #ffffff,
          #f8f5ff
        );
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

      .primary-button {
        border: 0;
        background: #7048ff;
        color: white;
        padding: 11px 17px;
        border-radius: 10px;
        font-weight: 700;
        cursor: pointer;
        margin-top: 15px;
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
         ACCOUNTS PAGE
         ================================================= */

      .accounts-toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 20px;
      }

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

      .add-account-button {
        border: 0;
        background: #7048ff;
        color: #ffffff;
        padding: 11px 18px;
        border-radius: 10px;
        font-weight: 700;
        cursor: pointer;
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
        min-width: 0;
      }

      .account-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
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
         MOBILE BOTTOM NAV
         ================================================= */

      .mobile-bottom {
        display: none;
      }

      .drawer {
        display: none;
      }

      /* =================================================
         TABLET
         ================================================= */

      @media (max-width: 1000px) {
        .finance-sidebar {
          width: 210px;
        }

        .kpi-grid {
          grid-template-columns: repeat(2, 1fr);
        }

        .dashboard-grid {
          grid-template-columns: 1fr;
        }

        .quick-grid {
          grid-template-columns: repeat(2, 1fr);
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
          position: sticky;
          top: 0;
          z-index: 20;
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

        .top-left {
          display: flex;
          align-items: center;
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

        .page-heading {
          margin-bottom: 16px;
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
          border-radius: 14px;
        }

        .kpi-label {
          font-size: 12px;
        }

        .kpi-value {
          font-size: 22px;
        }

        .kpi-note {
          font-size: 11px;
        }

        .dashboard-grid {
          grid-template-columns: 1fr;
          gap: 10px;
          margin-top: 10px;
        }

        .panel {
          padding: 17px;
          border-radius: 14px;
        }

        .chart {
          height: 150px;
        }

        .quick-grid {
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }

        .quick {
          padding: 13px;
        }

        /* =============================================
           ACCOUNTS MOBILE
           ============================================= */

        .accounts-toolbar {
          align-items: flex-start;
          flex-direction: column;
        }

        .accounts-summary {
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }

        .summary-card:last-child {
          grid-column: 1 / -1;
        }

        .accounts-list {
          grid-template-columns: 1fr;
          gap: 10px;
        }

        .account-card {
          padding: 17px;
          border-radius: 14px;
        }

        .account-balance {
          font-size: 22px;
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
          width: 285px;
          max-width: 84vw;
          height: 100vh;
          background: #ffffff;
          z-index: 90;
          padding: 20px 15px;
          box-shadow: 8px 0 30px rgba(0,0,0,0.14);
        }

        .drawer-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 5px 8px 22px;
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
        }

        .drawer-item {
          padding: 13px 14px;
          border-radius: 10px;
          margin-bottom: 3px;
          font-size: 14px;
        }

        .drawer-item.active {
          background: #eee8ff;
          color: #5935d9;
          font-weight: 700;
        }
      }

      /* =================================================
         VERY SMALL MOBILE
         ================================================= */

      @media (max-width: 420px) {
        .kpi-grid {
          grid-template-columns: 1fr;
        }

        .quick-grid {
          grid-template-columns: 1fr 1fr;
        }

        .accounts-summary {
          grid-template-columns: 1fr;
        }

        .summary-card:last-child {
          grid-column: auto;
        }

        .kpi-value {
          font-size: 25px;
        }
      }
      `
    ),

    // ===================================================
    // APP CONTAINER
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
          React.createElement("span", null, "Finance")
        ),

        menu.map(function (item) {
          return React.createElement(
            "button",
            {
              key: item,
              className:
                active === item
                  ? "side-item active"
                  : "side-item",
              onClick: function () {
                navigate(item);
              }
            },
            item
          );
        })
      ),

      // =================================================
      // MOBILE DRAWER
      // =================================================

      menuOpen &&
        React.createElement(
          React.Fragment,
          null,

          React.createElement(
            "div",
            {
              
