import React, { useState } from "react";

function App() {
  const [active, setActive] = useState("Dashboard");
  const [menuOpen, setMenuOpen] = useState(false);

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

  const cards = [
    ["Net Worth", "₹0", "Assets − liabilities"],
    ["Total Assets", "₹0", "Current asset value"],
    ["Liabilities", "₹0", "Outstanding amount"],
    ["Investments", "₹0", "Portfolio value"]
  ];

  function navigate(item) {
    setActive(item);
    setMenuOpen(false);
  }

  return React.createElement(
    React.Fragment,
    null,

    React.createElement(
      "style",
      null,
      `
      * {
        box-sizing: border-box;
      }

      html, body, #root {
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

      .finance-app {
        min-height: 100vh;
        display: flex;
        background: #f5f3fb;
      }

      /* SIDEBAR */

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

      /* MAIN */

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

      /* CONTENT */

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

      /* KPI */

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

      /* DASHBOARD BLOCKS */

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
        background:
          linear-gradient(
            to bottom,
            transparent 24%,
            #eeeaf6 25%,
            transparent 26%,
            transparent 49%,
            #eeeaf6 50%,
            transparent 51%,
            transparent 74%,
            #eeeaf6 75%,
            transparent 76%
          ),
          #faf9fd;
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

      /* QUICK ACTIONS */

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

      /* MOBILE BOTTOM NAV */

      .mobile-bottom {
        display: none;
      }

      .drawer {
        display: none;
      }

      /* TABLET */

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
      }

      /* MOBILE */

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

        /* DRAWER */

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

      @media (max-width: 420px) {
        .kpi-grid {
          grid-template-columns: 1fr;
        }

        .quick-grid {
          grid-template-columns: 1fr 1fr;
        }

        .kpi-value {
          font-size: 25px;
        }
      }
      `
    ),

    React.createElement(
      "div",
      { className: "finance-app" },

      /* DESKTOP SIDEBAR */

      React.createElement(
        "aside",
        { className: "finance-sidebar" },

        React.createElement(
          "div",
          { className: "brand" },
          "AI ",
          React.createElement("span", null, "Finance")
        ),

        menu.map(function(item) {
          return React.createElement(
            "button",
            {
              key: item,
              className:
                active === item
                  ? "side-item active"
                  : "side-item",
              onClick: function() {
                navigate(item);
              }
            },
            item
          );
        })
      ),

      /* MOBILE DRAWER */

      menuOpen &&
        React.createElement(
          React.Fragment,
          null,

          React.createElement(
            "div",
            {
              className: "drawer-overlay",
              onClick: function() {
                setMenuOpen(false);
              }
            }
          ),

          React.createElement(
            "aside",
            { className: "drawer" },

            React.createElement(
              "div",
              { className: "drawer-head" },

              React.createElement(
                "div",
                { className: "drawer-brand" },
                "AI Finance"
              ),

              React.createElement(
                "button",
                {
                  className: "drawer-close",
                  onClick: function() {
                    setMenuOpen(false);
                  }
                },
                "×"
              )
            ),

            menu.map(function(item) {
              return React.createElement(
                "div",
                {
                  key: item,
                  className:
                    active === item
                      ? "drawer-item active"
                      : "drawer-item",
                  onClick: function() {
                    navigate(item);
                  }
                },
                item
              );
            })
          )
        ),

      /* MAIN */

      React.createElement(
        "main",
        { className: "finance-main" },

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
                onClick: function() {
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
                "Personal Finance & Wealth"
              ),

              React.createElement(
                "strong",
                null,
                active
              )
            )
          ),

          React.createElement(
            "div",
            { className: "profile" },
            "N"
          )
        ),

        React.createElement(
          "section",
          { className: "page" },

          React.createElement(
            "div",
            { className: "page-heading" },

            React.createElement(
              "h2",
              null,
              "Financial Overview"
            ),

            React.createElement(
              "p",
              null,
              "Your complete financial picture in one place."
            )
          ),

          /* KPI */

          React.createElement(
            "div",
            { className: "kpi-grid" },

            cards.map(function(card) {
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

          /* MAIN PANELS */

          React.createElement(
            "div",
            { className: "dashboard-grid" },

            React.createElement(
              "div",
              { className: "panel" },

              React.createElement(
                "h3",
                null,
                "Cash Flow"
              ),

              React.createElement(
                "div",
                { className: "panel-subtitle" },
                "Income and expenses"
              ),

              React.createElement(
                "div",
                { className: "chart" },
                "Cash flow chart"
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
                "Ask about your finances, investments, portfolio, taxes, goals or trading."
              ),

              React.createElement(
                "button",
                { className: "primary-button" },
                "Open AI Chat"
              )
            )
          ),

          /* QUICK ACTIONS */

          React.createElement(
            "div",
            { className: "quick-grid" },

            [
              ["＋", "Add Transaction", "Record income or expense"],
              ["↔", "Transfer", "Move money between accounts"],
              ["＋", "Add Investment", "Record an investment"],
              ["AI", "Ask AI", "Ask your finance assistant"]
            ].map(function(item) {
              return React.createElement(
                "div",
                {
                  className: "quick",
                  key: item[1]
                },

                React.createElement(
                  "strong",
                  null,
                  item[0] + "  " + item[1]
                ),

                React.createElement(
                  "span",
                  null,
                  item[2]
                )
              );
            })
          )
        )
      ),

      /* MOBILE BOTTOM NAV */

      React.createElement(
        "nav",
        { className: "mobile-bottom" },

        [
          ["⌂", "Dashboard"],
          ["₹", "Accounts"],
          ["↕", "Transactions"],
          ["◈", "Investments"],
          ["AI", "AI Chat"]
        ].map(function(item) {
          return React.createElement(
            "button",
            {
              key: item[1],
              className:
                active === item[1]
                  ? "bottom-item active"
                  : "bottom-item",
              onClick: function() {
                navigate(item[1]);
              }
            },

            React.createElement(
              "span",
              { className: "bottom-icon" },
              item[0]
            ),

            item[1]
          );
        })
      )
    )
  );
}

export default App;
