# Financial OS — Project Overview, Architecture & Delivery Status

**Document role:** Primary project reference  
**Repository:** `siinghniibandhan-wq/ai-finance-trading-os`  
**Default branch:** `main`  
**Last documentation review:** 19 November 2026  
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

This is the repository-level logical flow. Public frontend hosting is configured for AWS Amplify (`main`, app root `frontend/`); the browser API origin is `https://wealthmanager.duckdns.org`. The exact live Amplify deployment and EC2/Nginx static-site state still require runtime verification. Database hosting, backup configuration and production network rules must be confirmed against the live AWS/account configuration.

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

**Chart Flow implementation — current source review 19 November 2026:**
- `backend/app/routes/market_flow.py` defines the read-only `GET /api/market-flow/` endpoint and is registered in `backend/app/main.py` behind the authenticated-user dependency.
- The unfiltered snapshot requests m.Stock Type A cash-market gainer/loser lists for NSE and BSE (`SecurityIdCode=0`) and supported index snapshots. Optional sector-index snapshots are separately requested.
- A `sector` query selects one of the provider-coded NSE sector universes and returns provider-ranked sector gainers/losers plus its sector-index quote. These rows are not the complete sector constituent universe.
- Provider calls are rate-limited and sector responses are cached. Partial responses include errors; the endpoint is read-only and reports no database writes.
- The payload explicitly marks full advance/decline breadth, full sector constituent breadth, delivery statistics and historical market flow as unavailable. Do not infer those metrics from top-mover lists.
- Frontend Chart Flow displays the market distribution/zero-centred flow and sector/mover views from REST-returned data. The UI can show partial data when provider requests fail; this is not a complete exchange-wide breadth feed.
- No WebSocket or continuous streaming transport is used for Chart Flow. Refreshes are bounded REST requests.

**Order Flow / market-stream boundary — source review 19 November 2026:**
- The application has a REST-backed Chart Flow market workspace through `market_flow.py`; do not describe Chart Flow itself as absent.
- The current Financial OS frontend/backend Chart Flow path does not consume `/market-stream/snapshot` and does not use a WebSocket market-data feed.
- The latest uploaded Gateway `mstock-gateway-app.py` reviewed in the earlier source audit contains no Market Flow, `/market-stream/*`, snapshot or stream implementation. Its WebSocket mention is limited to a legacy index-test heading. This is a source-file finding, not a live EC2 inspection.
- Historical WebSocket incident/deployment observations remain audit history only and are not evidence of current code or runtime connectivity.
- Existing REST market APIs and broker-order safeguards remain separate and must be preserved.


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
- Verify the AWS Amplify production deployment record, connected `main` branch, app root `frontend/`, build settings, environment variables and rollback path. The repository now documents Amplify as the public frontend target; the live deployment for a specific commit remains unverified.
- Inspect EC2/Nginx and any frontend deploy timer/runner before retiring static frontend serving. Preserve DuckDNS HTTPS/API routing, backend authentication and gateway connectivity.
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

The reviewed repository structure confirms a React/Vite frontend, FastAPI backend, SQLAlchemy persistence layer, m.Stock REST gateway integration, provider-backed Chart Flow REST route, AI provider integrations, dated SQL files under `backend/migrations/`, additional standalone SQL files, and startup schema logic. The repository review did not identify a dedicated database migration runner, migration ledger/automation service, cron definition or systemd timer definition.

Do not describe a migration runner, automated schema deployment, scheduled database job or production deployment pipeline as implemented until its executable code/configuration and successful run evidence exist. The current CI workflow validates builds/tests/audits; the source-packaging workflow creates an archive. The frontend build workflow uploads a CI artifact but no longer force-publishes to `frontend-dist`. These workflow runs do not themselves prove that Amplify deployed the commit or that EC2/Nginx frontend serving has been retired. None applies database migrations.

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


---

## Status addendum — 20 November 2026

This addendum supersedes older status statements where they conflict with the current source review or the latest user-confirmed operational result.

### BSE market and derivatives coverage

- The backend Market Flow implementation requests cash-market gainers and losers for both NSE and BSE using the m.Stock Type A exchange/segment mapping.
- The Options Hub REST adapter accepts both `NSE` and `BSE` for derivatives master and option-chain requests.
- The 19 November 2026 gateway discovery test returned the following observed contract counts: NSE Futures **685**, NSE Options **92,283**, BSE Futures **661**, and BSE Options **45,318** (combined **138,947**). These are time-specific provider master results, not fixed totals or a guarantee of current market availability.
- Futures/options quote requests returned LTP data in the recorded test session. Optional fields, including volume and open interest, remain dependent on provider response coverage. Missing fields must not be synthesized or presented as available.
- **BSE integration issue: resolved** according to the latest user confirmation. Keep this as a resolved incident, not an open blocker; continue ordinary regression coverage for exchange-qualified symbols and BSE requests.

### Authentication incident

- **HTTP 401 `Authentication is required` after OTP sign-in: resolved** according to the latest user confirmation on 20 November 2026.
- Preserve the existing OTP/login and token/session architecture. Provider authentication remains gateway-owned; do not add a second provider login, duplicate token store or parallel authentication mechanism as a workaround.
- The incident is considered user-confirmed resolved. This statement is not a substitute for a CI result or a timestamped production smoke-test record. Include login, authenticated API access and session continuity in release smoke tests.

### Current market transport boundary

- Chart Flow, Advanced Chart and the current market analytics path remain REST-based with bounded refreshes.
- Do not document WebSocket or continuous exchange-tick streaming as implemented in these workspaces.
- Provider-ranked mover lists are not complete exchange breadth; partial provider responses and unavailable analytics must remain explicit.
