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
