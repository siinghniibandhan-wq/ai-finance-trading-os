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
    "div",
    {
      style: {
        minHeight: "100vh",
        background: "#f6f4fb",
        color: "#171329",
        fontFamily: "Arial, sans-serif",
        display: "flex"
      }
    },

    /* Sidebar */
    React.createElement(
      "aside",
      {
        style: {
          width: "240px",
          minHeight: "100vh",
          background: "#ffffff",
          borderRight: "1px solid #e5e1f5",
          padding: "24px 16px",
          boxSizing: "border-box"
        }
      },

      React.createElement(
        "div",
        {
          style: {
            fontSize: "20px",
            fontWeight: "700",
            marginBottom: "30px",
            padding: "0 8px"
          }
        },
        "AI Finance"
      ),

      React.createElement(
        "div",
        null,

        navItems.map(function (item, index) {
          return React.createElement(
            "div",
            {
              key: item,
              style: {
                padding: "12px 14px",
                marginBottom: "6px",
                borderRadius: "10px",
                background: index === 0 ? "#eee8ff" : "transparent",
                fontWeight: index === 0 ? "700" : "400",
                cursor: "pointer"
              }
            },
            item
          );
        })
      )
    ),

    /* Main */
    React.createElement(
      "main",
      {
        style: {
          flex: 1,
          minWidth: 0
        }
      },

      /* Topbar */
      React.createElement(
        "header",
        {
          style: {
            background: "#ffffff",
            borderBottom: "1px solid #e5e1f5",
            padding: "18px 28px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between"
          }
        },

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

      /* Content */
      React.createElement(
        "section",
        {
          style: {
            padding: "28px"
          }
        },

        React.createElement(
          "div",
          {
            style: {
              marginBottom: "24px"
            }
          },

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

        /* KPI cards */
        React.createElement(
          "div",
          {
            style: {
              display: "grid",
              gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
              gap: "16px"
            }
          },

          cards.map(function (card) {
            return React.createElement(
              "div",
              {
                key: card[0],
                style: {
                  background: "#ffffff",
                  border: "1px solid #e5e1f5",
                  borderRadius: "16px",
                  padding: "20px",
                  minHeight: "125px",
                  boxSizing: "border-box"
                }
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

        /* Lower dashboard */
        React.createElement(
          "div",
          {
            style: {
              display: "grid",
              gridTemplateColumns: "2fr 1fr",
              gap: "16px",
              marginTop: "20px"
            }
          },

          React.createElement(
            "div",
            {
              style: {
                background: "#ffffff",
                border: "1px solid #e5e1f5",
                borderRadius: "16px",
                padding: "22px",
                minHeight: "260px"
              }
            },

            React.createElement(
              "h3",
              {
                style: {
                  margin: "0 0 8px 0"
                }
              },
              "Cash Flow"
            ),

            React.createElement(
              "p",
              {
                style: {
                  color: "#77718c"
                }
              },
              "Income and expenses will appear here."
            ),

            React.createElement(
              "div",
              {
                style: {
                  marginTop: "45px",
                  height: "90px",
                  borderRadius: "12px",
                  background: "#f6f4fb",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#8b859b"
                }
              },
              "Chart area"
            )
          ),

          React.createElement(
            "div",
            {
              style: {
                background: "#ffffff",
                border: "1px solid #e5e1f5",
                borderRadius: "16px",
                padding: "22px",
                minHeight: "260px"
              }
            },

            React.createElement(
              "h3",
              {
                style: {
                  margin: "0 0 8px 0"
                }
              },
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
              {
                style: {
                  marginTop: "20px",
                  border: "none",
                  borderRadius: "10px",
                  padding: "12px 18px",
                  background: "#6d4aff",
                  color: "#ffffff",
                  fontWeight: "700",
                  cursor: "pointer"
                }
              },
              "Open AI Chat"
            )
          )
        )
      )
    )
  );
}

export default App;
