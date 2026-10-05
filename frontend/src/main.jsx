import React from "react";
import ReactDOM from "react-dom/client";

const root = document.getElementById("root");

root.innerHTML = `
  <div style="padding:30px;font-family:Arial">
    <h2>Loading App...</h2>
  </div>
`;

import("./App.jsx")
  .then((module) => {
    ReactDOM.createRoot(root).render(
      React.createElement(module.default)
    );
  })
  .catch((error) => {
    root.innerHTML = `
      <div style="padding:30px;font-family:Arial;color:red">
        <h2>App.jsx Error ❌</h2>
        <pre style="white-space:pre-wrap">${String(error.stack || error)}</pre>
      </div>
    `;
  });
