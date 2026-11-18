# Financial OS — Project Overview, Architecture & Delivery Status

**Document role:** Primary project reference  
**Repository:** `siinghniibandhan-wq/ai-finance-trading-os`  
**Default branch:** `main`  
**Last documentation review:** 13 November 2026  
**Status rule:** “Implemented in repository” does not automatically mean production-deployed, externally connected, or fully verified.

---

## 1. Executive overview

Financial OS is a personal-finance, wealth-management, investment, trading-support and Indian tax-planning application. The repository contains a React/Vite frontend and a FastAPI/Python backend. The backend uses SQLAlchemy and PostgreSQL-compatible configuration, exposes authenticated finance APIs, and integrates with external services including m.Stock market data and Google Gemini AI.


**Important operating distinction:** successful market REST responses establish only the tested REST path. Source code existing in a repository does not prove that a feature is deployed or production-ready. The current reviewed market integration is REST-only.

## 2. System architecture

### 2.1 Logical architecture

```text
User browser
  |
  | HTTPS — React 18 + Vite frontend
  v
Financial OS API — FastAPI / Uvicorn
  |             |                 |
  |             |                 +--> Google Gemini AI (server-side credentials)
  |             |
  |             +--> PostgreSQL via SQLAlchemy
  |
  +--> m.Stock Gateway (private/restricted HTTP service)
          |
          +--> m.Stock REST APIs (quotes, indices, movers,
               instrument master and historical data)
```

This is the repository-level logical flow. Actual DNS, TLS termination, reverse-proxy placement, frontend hosting, database hosting, backup configuration and production network rules must be confirmed against the live AWS/account configuration before they are described as deployed facts.

### 2.2 Frontend

- Location: `frontend/`
- Framework: React 18, Vite 6.
- Entry points: `frontend/src/main.jsx` and `frontend/src/App.jsx`.
- API wrapper: `frontend/src/api.js`.
- The browser must contain only public configuration. API keys, database credentials, broker credentials, AWS credentials, m.Stock access tokens and gateway secrets must remain server-side.

### 2.3 Backend

- Location: `backend/`
- Framework: FastAPI; application entry point: `backend/app/main.py`.
- Persistence: SQLAlchemy models and configured database engine in `backend/app/database/`.
- API modules: `backend/app/routes/`.
- Shared integrations/services: `backend/app/services/`.
- API routers are registered centrally in `main.py`. Most business/data routers are attached with the authenticated-user dependency; authentication routes are registered separately.
- The code contains startup table creation and legacy conditional schema alterations for non-Vercel execution. These are technical debt and must not be mistaken for a controlled migration pipeline. Review database migration strategy before adding schema changes.
- `/health` is an application health endpoint; verify its current implementation and database dependency before using it as the sole infrastructure health check.

### 2.4 Market-data architecture

The current backend exposes REST-based market capabilities through registered FastAPI routers:

| Capability | Repository implementation | Data path / notes |
|---|---|---|
| Market overview | `market_overview.py` | Combines indices and gainers/losers; partial results are supported |
| Quotes | `market_quote.py`, `market.py`, market-price service | Uses the m.Stock gateway; read-only |
| Instrument search | `market_search.py` | Reads and caches the gateway instrument master |
| Historical data | `market_history.py` | Resolves instruments and requests historical OHLCV data |
| Indices | `market_indices.py` | NIFTY 50, SENSEX, NIFTY BANK and INDIA VIX are configured; live provider support must be verified individually |
| Gainers / losers | `market_movers.py` | Uses the gateway's dedicated provider endpoint |
| Charts | `market_charts.py` | Registered market chart API module |
| Watchlist | `watchlist.py` | User market watchlist routes |

The backend market overview currently reports market status as `unknown/not_connected`; do not describe exchange market-hours/status detection as complete without a verified source.

**Market Flow / Order Flow / market-stream status — source review 18 November 2026:**
- `backend/app/main.py` registers the REST market routers above; no Market Flow, Order Flow or market-stream router is registered.
- The reviewed backend source has no Market Flow/Order Flow adapter and no consumer for `/market-stream/snapshot`.
- The latest uploaded Gateway `mstock-gateway-app.py` contains no Market Flow, `/market-stream/*`, snapshot or stream implementation. Its WebSocket mention is limited to a legacy index-test heading.
- Accordingly, the current documented market-data integration is REST-only. Historical WebSocket incident/deployment observations are not evidence of current code or runtime state.
- This removal does not remove existing REST market APIs or broker-order safeguards.


## 3. Existing feature inventory

The following is a repository-level inventory derived from the current navigation and registered backend modules. It is not a production acceptance certificate.

### 3.1 Personal finance and money management

- Dashboard and financial summary.
- Wealth Manager.
- Accounts and account profile/contact settings.
- Transactions, ledger and chart of accounts.
- Categories and bills.
- Loans and liabilities.
- Budgets and goals.
- Finance Diary.
- Dashboard summary, alerts, recent transactions and financial trend data are implemented in the frontend/backend code paths.

### 3.2 Investments and portfolio

- Portfolio and holdings.
- Investment transactions and investment P&L.
- Broker order and broker reconciliation API modules.
- Instrument master and watchlist routes.
- Market data: overview, quotes, search, historical data, charts, movers and indices.
- Broker execution is a high-risk capability: verify kill switch, gateway restrictions, credentials, reconciliation and explicit user approval before any live order workflow is enabled.

### 3.3 Indian tax workspace

Repository modules cover tax data, capital gains, asset/capital-gains classification, tax calculation, tax context, deductions/exempt income, taxable income, tax liability, loss set-off, income aggregation, business income, house property, tax review and ITR-ready reporting.

Tax calculations and reports require validation against the applicable financial year, tax regime, user-provided evidence and current Indian tax law. A feature being present in code is not a substitute for CA review or statutory validation. Review-only candidate data must not be treated as verified taxable income without the intended verification step.

### 3.4 AI and administration

- AI Assistant integration with Google Gemini.
- Administration panel and admin-only API routes.
- User/profile and authentication routes.
- Account security and settings.

### 3.5 Themes and UI

The frontend contains a central theme system and multiple selectable visual themes. The theme redesign document is `THEME_SYSTEM_REDESIGN.md`. Theme changes must preserve business logic, data flows, API calls and interactions.

## 4. Feature status and release truth

Use these status definitions in all project documents:

| Status | Meaning |
|---|---|
| Implemented in repository | Relevant frontend/backend code is present |
| Integrated | UI, API and required service path are connected |
| Tested | Automated or documented manual tests passed for the stated scope |
| Deployed | A deployment record confirms the version is live in the named environment |
| Production-verified | The live workflow was exercised safely and its result recorded |
| Blocked / degraded | A known dependency or operational issue prevents expected behaviour |
| Planned | Approved or prioritised work not yet implemented |
| Proposed | Candidate work requiring prioritisation/approval |

Do not upgrade a status based on source files alone. Record test run, commit SHA, environment and date for deployment/production verification.

## 5. Current known gaps and upcoming work

The Market Flow, Order Flow and application-level market-stream integration are not part of the reviewed current source. They are not active roadmap blockers in this audit. Existing market REST capabilities remain separate.


### Priority 1 — infrastructure and release assurance
- Verify the actual frontend hosting target and custom-domain routing. Repository configuration and historical references mention more than one hosting platform; document the active production target only after checking its deployment configuration.
- Produce an AWS inventory from the live account: EC2 instances, regions, security groups, IAM roles, SSM/Secrets Manager usage, storage, database, backups, DNS, TLS and monitoring.
- Confirm whether the PostgreSQL database is RDS or self-managed; do not assume either from the SQLAlchemy connection alone.
- Confirm reverse proxy/TLS termination and whether any ALB belongs to this application. The `awselb/2.0` response observed for the m.Stock endpoint identifies the provider-side response path, not an application-owned load balancer.
- Verify CI checks and deployment workflows before declaring a release complete.

### Priority 2 — architecture and maintainability
- Replace ad-hoc startup schema alterations with a controlled migration process and documented backup/rollback procedure.
- Split oversized frontend and tax modules incrementally without changing existing behaviour.
- Introduce reproducible dependency lockfiles and pin critical integrations.
- Add structured application/gateway health metrics, log rotation, alerting and correlation IDs.
- Evaluate distributed rate limiting/WAF controls where multiple workers or instances make process-local limits insufficient.

### Priority 3 — security and user lifecycle
- Complete email verification, password reset and MFA design.
- Evaluate HttpOnly cookie authentication with a coordinated CSRF design; do not make a one-sided token-storage change.
- Add a tested Content Security Policy and browser security headers at the correct serving layer.
- Validate admin identity configuration using a stable admin user ID.
- Verify backup restoration, retention and access controls.

These items are a prioritised backlog based on current repository findings and known operational gaps. They are not represented as already approved delivery commitments unless separately approved.

## 6. Quality gates

Before a release is called complete:

2. Backend: `cd backend && python -m pip install -r requirements.txt -r requirements-dev.txt && PYTHONPATH=. pytest -q`.
3. Review dependency audit and secret-scan results.
5. Verify deployment workflow and target environment.
6. Record commit SHA, CI run, deployment identifier, smoke-test results and rollback path.
7. Production changes involving database migrations, broker orders, credentials or infrastructure require separate explicit approval.

## 7. Historical audit notes

The earlier static audit identified security and maintainability work including exact-origin CORS, password hashing upgrades, authenticated AI status, security headers, logout cleanup, registration throttling, API-docs restrictions, AI rate limits, and plain-language error handling. These are historical audit findings; re-check current source and deployment configuration before treating every item as a live production guarantee.

The historical audit also identified unresolved design decisions: public market-route access/rate limiting, unused instrument-master route registration, proxy-aware rate limiting, migration management, password reset/email verification/MFA, sessionStorage token exposure, CSP, large frontend/tax modules and environment-driven CORS configuration.

## 8. Documentation ownership and update rules

- This file is the primary product, architecture, feature inventory and roadmap index.
- `SECURITY_OPERATIONS.md` owns AWS operations, security controls, secrets, network boundaries, deployment and incident procedures.
- `THEME_SYSTEM_REDESIGN.md` owns theme architecture and visual-system decisions.
- Keep one canonical explanation for each subject; link to it rather than creating near-duplicate files.
- Every status update must distinguish repository evidence, test evidence, deployment evidence and production evidence.
- Never document secrets, TOTP values, access tokens, private keys or full credential-bearing URLs.


## 9. Architecture and automation implementation boundary

The root `README.md` is the repository entry point and links to this report for product/feature status and to `SECURITY_OPERATIONS.md` for AWS and operational controls.

The reviewed repository structure confirms a React/Vite frontend, FastAPI backend, SQLAlchemy persistence layer, market-data gateway integration, AI provider integrations, dated SQL files under `backend/migrations/`, additional standalone SQL files, and startup schema logic. The repository review did not identify a dedicated database migration runner, migration ledger/automation service, cron definition or systemd timer definition.

Do not describe a migration runner, automated schema deployment, scheduled database job or production deployment pipeline as implemented until its executable code/configuration and successful run evidence exist. The current CI workflow validates builds/tests/audits; the source-packaging workflow creates an archive. Neither applies database migrations nor deploys the application.

### Proposed implementation sequence

1. Inventory every existing schema file and startup schema mutation; assign unique migration identities without renumbering/replaying already-applied production changes.
2. Select and document one migration mechanism and migration ledger.
3. Implement dry-run/status/checksum validation and safe ordered execution in a non-production environment.
4. Add a verified backup gate and explicit failure/rollback procedure.
5. Add environment-scoped execution permissions and audit logs.
6. Test against a production-like database snapshot and verify restore before requesting production approval.
7. Add a scheduler only after manual runner operation is proven safe; keep production application approval separate.

These are proposed steps, not current implementation claims. Production migration or deployment is not authorised by this documentation update.

## 10. Documentation cross-reference

- `README.md`: entry point, setup, high-level architecture, CI/deployment distinction and roadmap links.
- `SECURITY_OPERATIONS.md`: AWS architecture, service boundaries, security, deployment, migration governance and operational automation.
- `THEME_SYSTEM_REDESIGN.md`: theme system only.

Maintain one canonical document per subject and link to it rather than creating duplicate topic files.
