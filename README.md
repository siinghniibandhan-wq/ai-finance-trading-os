# Financial OS

Financial OS is a trading and investment application with market-data, broker-order, portfolio, reconciliation, and watchlist workflows.

## m.Stock integration status

The agreed m.Stock integration review covers **five steps, all marked complete by the owner**:

1. Original REST integration
2. Broker authentication and session management
3. BUY/SELL order integration
4. Trade reconciliation and Portfolio
5. Watchlist (intentional device-local storage)

See **[MSTOCK_INTEGRATION_STATUS.md](./MSTOCK_INTEGRATION_STATUS.md)** for the accepted scope, owner decisions, five-step overview, review workflow, and change-control boundaries.

The historical static review is available in **[AUDIT_REPORT.md](./AUDIT_REPORT.md)**. It records the findings and recommendations from that review; those historical recommendations are not automatically approved work or current requirements.

## Change-control

- Preserve existing user-facing workflows and accepted design decisions.
- Do not reopen an owner-confirmed complete integration step without a requested re-audit or concrete regression evidence.
- Documentation/audit work does not authorise application-code changes, database migrations, broker configuration changes, AWS changes, or production deployment. Obtain separate explicit approval for those actions.
- Report tests, CI, deployments, and migrations only with directly verified results.

## Repository areas

- `backend/` — application API and services.
- `frontend/` — application user interface.
