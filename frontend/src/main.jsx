import React from "react";
import ReactDOM from "react-dom/client";

const root = document.getElementById("root");

root.innerHTML = "";

ReactDOM.createRoot(root).render(
  React.createElement(
    "div",
    {
      style: {
        padding: "40px",
        fontFamily: "Arial",
        background: "#f5f3ff",
        minHeight: "100vh"
      }
    },
    React.createElement("h1", null, "AI Finance Trading OS"),
    React.createElement("h2", null, "React Working ✅"),
    React.createElement("p", null, "React is rendering correctly.")
  )
);
