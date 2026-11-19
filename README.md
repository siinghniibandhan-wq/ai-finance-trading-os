> **IMPORTANT NOTICE — PERSONAL USE ONLY**
>
> 1. This website and service are intended solely for individual, personal use.
> 2. Plans and pricing are displayed for presentation and to provide a complete, premium website experience; they do not represent a current offer of commercial services.
> 3. This application, website and service are not currently intended or permitted for commercial use. Any consideration of commercialisation would be no earlier than 3–5 years from now.
> 4. For licensing-related questions or concerns, please use the Contact Details section or submit the contact form.
>
> This notice is shown on the public homepage. It is not displayed after login or within authenticated areas.
>
# Financial OS

A unified personal-finance, wealth-management, investment, market-data, trading-support and Indian tax workspace.

> **Documentation rule:** repository implementation, automated test success, deployment and production verification are separate states. A feature is not production-ready merely because its source code exists.
>
> **Current hosting boundary (19 November 2026):** AWS Amplify is the public frontend target (`main` branch, app root `frontend/`). The browser calls the backend API at `https://wealthmanager.duckdns.org`; DuckDNS is the API origin, not the public website. PR #223 removed the GitHub workflow that force-published compiled frontend files to `frontend-dist` and aligned backend CORS with the Amplify origin. EC2/Nginx static-frontend retirement and live Amplify deployment verification remain separate operational checks; do not assume those host-side steps are complete.

## Project at a glance

| Area | Current repository implementation |
|---|---|
| Frontend | React 18 + Vite 6 |
| Backend | FastAPI + Python |
| Persistence | SQLAlchemy with PostgreSQL driver/configuration |
| Market-data integration | m.Stock REST gateway (quotes, search, indices, movers and historical data) |
| AI integration | Google Gemini and configurable AI gateway providers |
| Cloud/operations | Recorded AWS EC2 services for the market-data gateway and backend; live infrastructure inventory remains to be verified |

## Contents

- [Product capabilities](#product-capabilities)
- [Architecture](#architecture)
- [Repository structure](#repository-structure)
- [Local development](#local-development)
- [Configuration and secrets](#configuration-and-secrets)
- [Testing and quality gates](#testing-and-quality-gates)
- [AWS architecture and operations](#aws-architecture-and-operations)
- [Deployment and release workflow](#deployment-and-release-workflow)
- [Database schema and migration governance](#database-schema-and-migration-governance)
- [Automation and scheduled operations](#automation-and-scheduled-operations)
- [Current implementation status and roadmap](#current-implementation-status-and-roadmap)
- [Security and financial safety](#security-and-financial-safety)
- [Documentation map](#documentation-map)

## Product capabilities

The application navigation and backend modules cover the following areas:

- **Personal finance:** Dashboard, Wealth Manager, Accounts, Transactions, Ledger, Chart of Accounts, Categories, Bills, Loans & Liabilities, Budgets, Goals and Finance Diary.
- **Investments:** Portfolio, Holdings, Investment Transactions, investment P&L, watchlists and broker reconciliation.
- **Markets:** Market overview, quotes, instrument search, indices, gainers/losers, historical market data and charts.
- **Indian tax:** income aggregation, deductions/exempt income, capital gains, house property, business income, loss set-off, tax liability and ITR-ready reporting.
- **AI and administration:** AI Assistant, account/profile settings and admin-only operations.
- **Themes:** central theme system and visual preferences.

This is a repository feature inventory, not a certification that every workflow is fully integrated, tested or deployed. Refer to [AUDIT_REPORT.md](AUDIT_REPORT.md) for status definitions, known gaps and prioritised work.

## Architecture

```text
Browser
  |
  | HTTPS
  v
React 18 + Vite frontend
  |
  | HTTPS API requests
  v
FastAPI backend
  |                 |                    |
  |                 |                    +--> AI provider integrations
  |                 |
  |                 +--> PostgreSQL-compatible database via SQLAlchemy
  |
  +--> m.Stock gateway (restricted HTTP service)
          |
          +--> m.Stock REST endpoints
```

### Frontend

- Application root: `frontend/`
- Entry files: `frontend/src/main.jsx`, `frontend/src/App.jsx`
- API client: `frontend/src/api.js`
- Build tool: Vite
- Public hosting target: AWS Amplify, production branch `main`, monorepo app root `frontend/`, build command `npm run build`, artifact directory `dist` (verify live Amplify settings before operational changes).
- Backend API origin: `https://wealthmanager.duckdns.org` via `VITE_API_BASE_URL`; DuckDNS remains backend/API-only and must not be treated as the public frontend origin.

### Backend

- Application root: `backend/`
- FastAPI entry point: `backend/app/main.py`
- Route modules: `backend/app/routes/`
- Models and persistence: `backend/app/models.py`, `backend/app/database/`
- Shared services and integrations: `backend/app/services/`
- Environment template: `backend/.env.example`

The backend is responsible for authentication, authorization, data ownership, persistence, external integrations and secrets. Do not place database, broker, m.Stock, AI-provider or AWS credentials in browser code or public `VITE_*` variables.

### Market data and m.Stock

The current Financial OS backend integrates with the m.Stock gateway through REST endpoints. The registered market capabilities are market overview, quotes, instrument search, indices, gainers/losers, historical data, charts and watchlists.

**Market data transport policy:**
- The application uses authenticated REST APIs for market overview, quotes, instrument search, indices, gainers/losers, historical data and charts.
- Market Flow chart work must remain REST-only. Do not add WebSocket, socket, event-stream or continuous streaming transports.
- Periodic refreshes must be bounded REST requests. Quote snapshots must not be represented as exchange ticks or continuous live feeds.
- Preserve existing authentication, gateway shared-secret validation, market routes and broker-order safeguards.

The REST market APIs and broker-order safeguards are separate existing functionality. Chart Flow is implemented as a read-only REST workspace backed by `GET /api/market-flow/`, with provider-returned cash-market movers, supported index snapshots and selected-sector mover/index requests. It reports partial provider responses and does not claim complete advance/decline breadth, full sector constituents, delivery statistics or historical market flow. Advanced Chart uses historical OHLCV and REST quote snapshots; quote retrieval time is not an exchange timestamp. No WebSocket/continuous market-data stream is part of the current Chart Flow/Advanced Chart design.



## Repository structure

```text
.
├── .github/
│   └── workflows/
│       ├── financial-os-ci.yml
│       └── package-aws-restored-source.yml
├── backend/
│   ├── app/
│   │   ├── database/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── main.py
│   │   └── models.py
│   ├── migrations/
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── src/
│   ├── scripts/
│   └── package.json
├── AUDIT_REPORT.md
├── SECURITY_OPERATIONS.md
└── THEME_SYSTEM_REDESIGN.md
```

This is a high-level map; consult the source tree for the complete file list. The repository currently has loose SQL migration files and startup schema logic. It does **not** currently contain a verified, dedicated migration runner, migration scheduler/timer, or a documented automated schema-application service.

## Local development

### Prerequisites

- Node.js 20 or a compatible supported release.
- Python 3.12.
- Access to a PostgreSQL database for backend workflows.
- Valid development configuration for any external integration being exercised.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Production build:

```bash
cd frontend
npm run build
```


```bash
cd frontend
```

Important Notice schedule tests:

```bash
cd frontend
npm run test:notice
```

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

Set valid local values in `.env` before starting the API. From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The backend requires a valid database configuration. External market-data, broker and AI workflows also require their respective provider configuration and credentials. Do not use production credentials for local development.

## Configuration and secrets

Use [backend/.env.example](backend/.env.example) as the variable-name reference. It contains placeholders, not working credentials.

Important configuration groups include:

- Database connection: `DATABASE_URL`.
- Authentication and administrator identity: `AUTH_SECRET_KEY`, `ADMIN_USER_ID`.
- Runtime environment and CORS: `APP_ENV`, `CORS_ALLOWED_ORIGINS`.
- Proxy trust: `TRUSTED_PROXY_COUNT` (set only for the exact trusted proxy chain).
- m.Stock gateway: `MSTOCK_GATEWAY_URL`, `MSTOCK_GATEWAY_SECRET`.
- AI provider configuration: Gemini parameter reference and optional provider gateway settings.
- AWS region/role configuration where server-side Parameter Store retrieval is enabled.

Never commit a real `.env`, API key, broker credential, access token, TOTP seed, private key or gateway shared secret. Prefer an attached IAM role and a managed secret store over static AWS credentials. See [SECURITY_OPERATIONS.md](SECURITY_OPERATIONS.md#secrets-and-identity).

## Testing and quality gates

The repository CI workflow is `.github/workflows/financial-os-ci.yml`. It runs on pushes and pull requests targeting `main`, and supports manual dispatch.

| Job | Current checks |
|---|---|
| Backend | Python 3.12, dependency installation, pip-audit and pytest |
| Secrets | Gitleaks repository-history scan |

Run the same core checks locally:

```bash
# Frontend
cd frontend
npm install
npm run build

# Backend (from repository root)
cd backend
python -m pip install -r requirements.txt -r requirements-dev.txt
PYTHONPATH=. pytest -q
```

A green CI run validates only the checks in that workflow and the commit it tested. It does not prove a production deployment, live AWS health, broker execution safety or live m.Stock streaming.

## AWS architecture and operations

The known recorded AWS deployment includes an EC2-hosted m.Stock gateway in `ap-southeast-2` (Sydney). The gateway has been recorded as a Flask service bound to `127.0.0.1:8000`, managed by `mstock-gateway.service`. A separate Financial OS backend service has been recorded as `financial-os-backend.service`, Gunicorn with two workers on `127.0.0.1:8001`.

These host details are historical operational evidence and must be checked against the live account before use. The database hosting type, active frontend hosting provider, application-owned load balancers, WAF, CloudFront, S3, Route 53, CloudWatch alarms and multi-AZ configuration are not confirmed by the repository alone.

AWS capabilities to inventory and govern:

- EC2 instances, regions, volumes, instance profiles and service units.
- IAM roles and least-privilege policies.
- Systems Manager Session Manager and Parameter Store/Secrets Manager configuration.
- Security groups, subnet routing, NACLs, egress and private service connectivity.
- Database hosting, encryption, backup retention and restore tests.
- DNS, TLS certificate ownership/renewal and the active frontend/API edge.
- CloudWatch log groups, retention, metrics and alarms.
- WAF or equivalent edge protections where deployed.

Do not expose backend or gateway listeners publicly. Restrict database access to the backend. Keep secrets server-side.

The detailed inventory, safeguards and operational checklist live in [SECURITY_OPERATIONS.md](SECURITY_OPERATIONS.md).

## Deployment and release workflow

Current repository automation and hosting boundary (19 November 2026):

1. Pull requests and pushes to `main` run `.github/workflows/financial-os-ci.yml` (frontend build and regression tests, backend regression tests, dependency audits and repository secret scan).
2. The `frontend-build.yml` workflow builds the frontend and uploads a CI artifact; the former `publish-frontend` job that force-pushed compiled files to `frontend-dist` has been removed by PR #223.
3. AWS Amplify is configured by the user as the public frontend host, connected to `main` with app root `frontend/`; the frontend build uses `npm run build` and `dist` output. Confirm the live Amplify deployment record before claiming a particular commit is deployed.
4. `VITE_API_BASE_URL=https://wealthmanager.duckdns.org` points the browser to the backend API. Backend CORS includes `https://main.d1qcu4l3dz9f9e.amplifyapp.com`.
5. The source-archive workflow is **not** an application deployment workflow. The CI artifact is not an Amplify deployment confirmation.
6. PR #223 does not change EC2/Nginx. Any EC2 static frontend root, frontend deploy timer/runner or redirect must be inspected and retired separately while preserving DuckDNS API routing, HTTPS, Bearer authentication and gateway connectivity.

Recommended release sequence:

1. Review and merge the intended change.
2. Confirm required CI jobs passed on the exact merge commit.
3. Confirm the deployment target and release artifact.
4. Apply any approved database migration separately, with a verified backup and rollback plan.
5. Deploy using the confirmed hosting mechanism.
6. Run safe smoke tests for health, login, account/transaction reads, market REST and gateway connectivity.
7. Verify m.Stock REST responses and gateway authentication using safe read-only checks.
8. Keep broker kill switches and live-order safeguards in the approved state.
9. Record commit SHA, CI run, deployment identifier, environment, smoke-test results and rollback reference.

Production deployment, database migration, IAM/network changes, credential rotation and live broker execution require the appropriate explicit approval. A documentation PR does not authorize these actions.

## Database schema and migration governance

The repository currently contains `backend/migrations/` with dated SQL files, additional standalone SQL migration files and startup schema/table logic in the backend. These are not yet one unified, verified migration system.

**Current facts and constraints:**

- SQL files are present, but no dedicated migration runner or scheduled schema-application workflow was found in the repository tree reviewed for this documentation update.
- Do not assume that a SQL file is automatically applied merely because it is committed or merged.
- Do not run schema changes against production without explicit approval.
- Before a migration: inspect the exact SQL and target environment, confirm unique migration identity/order, take and verify a restorable database backup, assess locking/data impact, define rollback/recovery, and record the applied version.
- Keep schema changes separate from application/service/tooling changes.
- Do not create duplicate migration identifiers or silently reuse an identifier for different SQL.
- Startup `create_all` or ad-hoc ALTER logic is not a substitute for a controlled migration history.

**Recommended future implementation (not currently implemented):** introduce a single migration framework/runner with a migration ledger, checksum validation, ordered execution, dry-run/status modes, backup gate, transaction policy, failure log and explicit environment targeting. Add scheduling only after the runner has been reviewed and approved. Production execution must remain separately gated. The exact runner, backup mechanism, rollback semantics and scheduler are design decisions requiring implementation and approval.

See [SECURITY_OPERATIONS.md](SECURITY_OPERATIONS.md#database-migrations-and-automation) for operational controls.

## Automation and scheduled operations

Automation currently visible in the repository:

| Automation | Trigger | Actual effect | What it does not do |
|---|---|---|---|
| Financial OS CI | Push/PR to `main`, manual dispatch | Builds/tests/audits frontend and backend; scans repository history | Does not deploy application or apply database migrations |
| AWS-restored source packaging | Manual dispatch; change to its workflow file on `main` | Produces a downloadable source ZIP artifact, 30-day retention | Does not deploy to EC2 or restart services |
| systemd services (recorded runtime) | Host service manager | Runs the gateway and backend services | Not a schema migration scheduler |

No repository-defined systemd timer, cron migration job, database migration runner or automatic production deploy workflow was identified in the reviewed branch. Live host timers/cron entries must be inspected on the server before claiming none exist operationally.

Any future scheduled task must document owner, trigger/cadence, target environment, permissions, logs, alerting, retry/timeout policy, idempotency and a disable/rollback procedure. Database automation must never bypass the backup gate or production approval.

## Current implementation status and roadmap

### Current market integration status

- The current application code documents and registers the m.Stock REST integration only.
- Market Flow, Order Flow and the application-level market-stream consumer are absent from the reviewed current backend source.
- Historical WebSocket incident and deployment records are retained in the security log as history, not as current blockers or active features.

### Prioritised roadmap

1. **P1 — Infrastructure truth:** complete live AWS inventory; confirm database hosting, frontend hosting, network boundaries, secrets store, monitoring, backups and restore procedure.
2. **P1 — Release assurance:** verify the real production deployment path and rollback; record test/deployment evidence per commit.
3. **P2 — Database governance:** implement a controlled migration runner and migration ledger; remove ad-hoc schema mutation only through a separately tested migration project.
4. **P2 — Maintainability:** modularise oversized frontend/tax modules without breaking existing workflows; improve structured logs, metrics and alerting.
5. **P3 — Security lifecycle:** evaluate MFA, email verification, password reset, CSP and safer session handling with coordinated backend/frontend changes.

The roadmap is a prioritised engineering view, not a claim that every item is approved or scheduled. Detailed status and feature definitions are maintained in [AUDIT_REPORT.md](AUDIT_REPORT.md).

## Security and financial safety

- Enforce authentication, user-data ownership and admin authorization on protected routes.
- Keep broker execution disabled unless explicitly approved and verified; preserve the kill switch and gateway restrictions.
- Do not test live orders as part of routine CI or smoke testing.
- Do not treat AI-generated tax or investment output as regulated advice or a substitute for reviewing source records and applicable Indian law.
- Validate tax year, regime, source documents and calculation rules before filing or making a financial decision.
- Log operational evidence without credentials, access tokens, account secrets or unnecessary personal financial data.
- Backups are only useful when restore procedures are tested.
- Infrastructure, database, broker and production changes require change review, explicit approval and rollback planning.

## Documentation map

| Document | Canonical responsibility |
|---|---|
| `README.md` | Project entry point, setup, high-level architecture, workflows and links |
| [AUDIT_REPORT.md](AUDIT_REPORT.md) | Product overview, feature inventory, implementation status, gaps and roadmap |
| [SECURITY_OPERATIONS.md](SECURITY_OPERATIONS.md) | AWS infrastructure, security, secrets, deployment, migrations, automation and incident response |
| [THEME_SYSTEM_REDESIGN.md](THEME_SYSTEM_REDESIGN.md) | Theme-system architecture and design decisions |
| [backend/app/services/AI_PROVIDERS.md](backend/app/services/AI_PROVIDERS.md) | AI provider configuration and integration details |

## Contribution and change-control expectations

- Make focused changes and preserve existing user workflows and API contracts.
- Add or update tests for behaviour changes.
- Keep documentation aligned with actual code and workflows.
- Never commit secrets or production data.
- Use pull requests and verify CI before merging.
- Treat production infrastructure, database migrations, credentials and broker execution as separately controlled changes.
