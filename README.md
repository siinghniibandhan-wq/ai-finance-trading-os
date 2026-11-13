# Financial OS

Financial OS is a trading and investment application with market-data, broker-order, portfolio, reconciliation, holdings, and watchlist workflows.

## m.Stock integration status

The agreed m.Stock integration review covers **five steps, all marked complete by the owner**:

1. Original REST integration
2. Broker authentication and session management
3. BUY/SELL order integration
4. Trade reconciliation and Portfolio
5. Watchlist (intentional device-local storage)

## Investment workflow

The application provides four related but distinct investment views:

- **Portfolio** — individual investment records and portfolio-level overview; users can start a purchase through **Add Investment**.
- **Holdings** — consolidated current positions by instrument, derived from investment BUY/SELL activity; users can buy/add to an existing holding.
- **Market** — instrument discovery and detail pages; selecting BUY/SELL routes the chosen instrument and action into the Portfolio transaction form.
- **Investment Transaction History** — the BUY/SELL ledger inside the Invest/Portfolio workflow. This is separate from Account/Money transaction history.

All supported BUY/SELL entry points converge on the common investment transaction workflow. Completed activity is reflected in the relevant Portfolio, Holdings and investment-history views after refresh. See **[MSTOCK_INTEGRATION_STATUS.md](./MSTOCK_INTEGRATION_STATUS.md)** for the detailed distinctions, HDFC example, diagrams, code references and change-control rules.

The historical static review is available in **[AUDIT_REPORT.md](./AUDIT_REPORT.md)**. Its historical recommendations are not automatically approved work or current requirements.

## Change-control

- Preserve existing user-facing workflows and accepted design decisions.
- Do not reopen an owner-confirmed complete integration step without a requested re-audit or concrete regression evidence.
- Documentation/audit work does not authorise application-code changes, database migrations, broker configuration changes, AWS changes, or production deployment. Obtain separate explicit approval for those actions.
- Report tests, CI, deployments, and migrations only with directly verified results.

## Repository areas

- `backend/` — application API and services.
- `frontend/` — application user interface.
