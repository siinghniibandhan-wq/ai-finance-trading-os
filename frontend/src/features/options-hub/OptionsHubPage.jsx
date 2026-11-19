import React from "react";
import "./options-hub.css";

const planned = [
  ["Option chain by strike", "CE / PE bid, ask, LTP, volume and open interest"],
  ["Open-interest analytics", "OI change, PCR and verified writer positioning"],
  ["Volatility and Greeks", "IV, delta, gamma, theta and vega from provider-backed inputs"],
  ["Max Pain and levels", "Calculated only from a complete, correctly mapped option chain"],
  ["Strategy analysis", "Payoff and risk analysis using verified contract specifications"]
];

export default function OptionsHubPage() {
  return (
    <main className="options-hub-page">
      <header className="options-hub-header">
        <div>
          <small>FINANCIAL OS / MARKETS</small>
          <h1>Options Hub</h1>
          <p>Derivatives analysis workspace. Live analytics remain gated until the broker data contract is verified.</p>
        </div>
        <span className="options-hub-status">DATA SOURCE NOT CONNECTED</span>
      </header>
      <section className="options-hub-gate" role="status">
        <div className="options-hub-gate-mark">!</div>
        <div>
          <h2>Option-chain REST integration is not available in the current Financial OS API.</h2>
          <p>The current frontend has no verified option-chain endpoint or contract/expiry mapping. This workspace will not display simulated strikes, OI, PCR, Max Pain, IV or Greeks as market data.</p>
        </div>
      </section>
      <section className="options-hub-capabilities">
        <div className="options-hub-capabilities-heading">
          <small>PLANNED ANALYTICS · PROVIDER VERIFICATION REQUIRED</small>
          <h2>Options analysis modules</h2>
        </div>
        {planned.map(([title, detail]) => (
          <div className="options-hub-capability" key={title}>
            <div><strong>{title}</strong><span>{detail}</span></div>
            <span className="options-hub-unavailable">Awaiting verified data</span>
          </div>
        ))}
      </section>
      <footer>Read-only workspace · REST integration only · No order placement or broker credentials in the browser</footer>
    </main>
  );
}
