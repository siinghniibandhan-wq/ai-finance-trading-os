import React from "react";
import ReactDOM from "react-dom/client";

const root = document.getElementById("root");

window.addEventListener("error", (event) => {
  root.innerHTML = `
    <div style="padding:30px;font-family:Arial;color:red">
      <h2>Runtime Error ❌</h2>
      <pre style="white-space:pre-wrap">${event.error?.stack || event.message}</pre>
    </div>
  `;
});

window.addEventListener("unhandledrejection", (event) => {
  root.innerHTML = `
    <div style="padding:30px;font-family:Arial;color:red">
      <h2>Promise Error ❌</h2>
      <pre style="white-space:pre-wrap">${event.reason?.stack || event.reason}</pre>
    </div>
  `;
});

import("./App.jsx").then((module) => {
  const App = module.default;

  ReactDOM.createRoot(root).render(
    React.createElement(App)
  );
});
