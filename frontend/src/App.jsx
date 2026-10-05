import React from "react";

function App() {
  const navItems = [
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
    ["Net Worth", "₹0", "Total assets minus liabilities"],
    ["Total Assets", "₹0", "Your current assets"],
    ["Total Liabilities", "₹0", "Outstanding liabilities"],
    ["Investments", "₹0", "Investment portfolio value"]
  ];

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
        padding: 0;
        width: 100%;
        min-height: 100%;
      }

      body {
        font-family: Arial, sans-serif;
      }

      .app-shell {
        min-height: 100vh;
        background: #f6f4fb;
        color: #171329;
        display: flex;
      }

      .sidebar {
        width: 240px;
        min-height: 100vh;
        flex-shrink: 0;
        background: #ffffff;
        border-right: 1px solid #e5e1f5;
        padding: 24px 16px;
      }

      .logo {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 30px;
        padding: 0 8px;
      }

      .nav-item {
        padding: 12px 14px;
        margin-bottom: 6px;
        border-radius: 10px;
        cursor: pointer;
      }

      .nav-item.active {
        background: #eee8ff;
        font-weight: 700;
      }

      .main {
        flex: 1;
        min-width: 0;
      }

      .topbar {
        background: #ffffff;
        border-bottom: 1px solid #e5e1f5;
        padding: 18px 28px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .content {
        padding: 28px;
      }

      .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
      }

      .lower-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 16px;
        margin-top: 20px;
      }

      .card {
        background: #ffffff;
        border: 1px solid #e5e1f5;
        border-radius: 16px;
        padding: 20px;
      }

      .chart-card,
      .assistant-card {
        min-height: 260px;
      }

      .chart-placeholder {
        margin-top: 45px;
        height: 90px;
        border-radius: 12px;
        background: #f6f4fb;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #8b859b;
      }

      .assistant-button {
        margin-top: 20px;
        border: none;
        border-radius: 10px;
        padding: 12px 18px;
        background: #6d4aff;
        color: white;
        font-weight: 700;
        cursor: pointer;
      }

      @media (max-width: 800px) {
        .app-shell {
          display: block;
        }

        .sidebar {
          width: 100%;
          min-height: auto;
          border-right: none;
          border-bottom: 1px solid #e5e1f5;
          padding: 16px;
        }

        .logo {
          margin-bottom: 14px;
        }

        .nav-list {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 6px;
        }

        .nav-item {
          margin: 0;
          padding: 10px 12px;
          font-size: 14px;
        }

        .topbar {
          padding: 16px;
        }

        .content {
          padding: 16px;
        }

        .kpi-grid {
          grid-template-columns: 1fr 1fr;
        }

        .lower-grid {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 480px) {
        .nav-list {
          grid-template-columns: 1fr 1fr;
        }

        .kpi-grid {
          grid-template-columns: 1fr;
        }

        .topbar h1 {
          font-size: 22px;
        }

        .content h2 {
          font-size: 21px;
        }

        .card {
          padding: 18px;
        }
      }
      `
    ),

    React.createElement(
      "div",
      { className: "app-shell" },

      React.createElement(
        "aside",
        { className: "sidebar" },

        React.createElement(
          "div",
          { className: "logo" },
          "AI Finance"
        ),

        React.createElement(
          "nav",
          { className: "nav-list" },

          navItems.map(function (item, index) {
            return React.createElement(
              "div",
              {
                key: item,
                className:
                  index === 0
                    ? "nav-item active"
                    : "nav-item"
              },
              item
            );
          })
        )
      ),

      React.createElement(
        "main",
        { className: "main" },

        React.createElement(
          "header",
          { className: "topbar" },

          React.createElement(
            "div",
            null,

            React.createElement(
              "div",
              {
                style: {
                  fontSize: "13px",
                  color: "#77718c",
                  marginBottom: "4px"
                }
              },
              "Personal Finance & Wealth"
            ),

            React.createElement(
              "h1",
              {
                style: {
                  margin: 0,
                  fontSize: "24px"
                }
              },
              "Dashboard"
            )
          ),

          React.createElement(
            "div",
            {
              style: {
                width: "42px",
                height: "42px",
                borderRadius: "50%",
                background: "#eee8ff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: "700"
              }
            },
            "N"
          )
        ),

        React.createElement(
          "section",
          { className: "content" },

          React.createElement(
            "div",
            { style: { marginBottom: "24px" } },

            React.createElement(
              "h2",
              {
                style: {
                  margin: "0 0 6px 0",
                  fontSize: "22px"
                }
              },
              "Financial Overview"
            ),

            React.createElement(
              "p",
              {
                style: {
                  margin: 0,
                  color: "#77718c"
                }
              },
              "Your complete financial picture in one place."
            )
          ),

          React.createElement(
            "div",
            { className: "kpi-grid" },

            cards.map(function (card) {
              return React.createElement(
                "div",
                {
                  key: card[0],
                  className: "card"
                },

                React.createElement(
                  "div",
                  {
                    style: {
                      color: "#77718c",
                      fontSize: "14px",
                      marginBottom: "12px"
                    }
                  },
                  card[0]
                ),

                React.createElement(
                  "div",
                  {
                    style: {
                      fontSize: "28px",
                      fontWeight: "700",
                      marginBottom: "8px"
                    }
                  },
                  card[1]
                ),

                React.createElement(
                  "div",
                  {
                    style: {
                      color: "#8b859b",
                      fontSize: "12px"
                    }
                  },
                  card[2]
                )
              );
            })
          ),

          React.createElement(
            "div",
            { className: "lower-grid" },

            React.createElement(
              "div",
              { className: "card chart-card" },

              React.createElement(
                "h3",
                { style: { margin: "0 0 8px 0" } },
                "Cash Flow"
              ),

              React.createElement(
                "p",
                { style: { color: "#77718c" } },
                "Income and expenses will appear here."
              ),

              React.createElement(
                "div",
                { className: "chart-placeholder" },
                "Chart area"
              )
            ),

            React.createElement(
              "div",
              { className: "card assistant-card" },

              React.createElement(
                "h3",
                { style: { margin: "0 0 8px 0" } },
                "AI Finance Assistant"
              ),

              React.createElement(
                "p",
                {
                  style: {
                    color: "#77718c",
                    lineHeight: "1.5"
                  }
                },
                "Ask questions about your money, investments, portfolio, taxes and financial goals."
              ),

              React.createElement(
                "button",
                { className: "assistant-button" },
                "Open AI Chat"
              )
            )
          )
        )
      )
    )
  );
}

export default App;
