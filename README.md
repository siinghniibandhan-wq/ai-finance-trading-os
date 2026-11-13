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

## Project at a glance

| Area | Current repository implementation |
|---|---|
| Frontend | React 18 + Vite 6 |
| Backend | FastAPI + Python |
| Persistence | SQLAlchemy with PostgreSQL driver/configuration |
| Market-data integration | m.Stock REST gateway and WebSocket stream path |
| AI integration | Google Gemini and configurable AI gateway providers |
| Cloud/operations | Recorded AWS EC2 services for the market-data gateway and backend; live infrastructure inventory remains to be verified |
| CI | GitHub Actions for frontend build, Order Flow tests, backend tests, dependency audits and secret scanning |

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
- **Order Flow:** order-flow workspace and broker-order service boundaries. Live execution remains subject to explicit operational safeguards and verification.
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
          |
          +--> m.Stock WebSocket endpoint
               wss://ws.mstock.trade
```

### Frontend

- Application root: `frontend/`
- Entry files: `frontend/src/main.jsx`, `frontend/src/App.jsx`
- API client: `frontend/src/api.js`
- Build tool: Vite
- Order Flow workspace: `frontend/src/order-flow/`

### Backend

- Application root: `backend/`
- FastAPI entry point: `backend/app/main.py`
- Route modules: `backend/app/routes/`
- Models and persistence: `backend/app/models.py`, `backend/app/database/`
- Shared services and integrations: `backend/app/services/`
- Environment template: `backend/.env.example`

The backend is responsible for authentication, authorization, data ownership, persistence, external integrations and secrets. Do not place database, broker, m.Stock, AI-provider or AWS credentials in browser code or public `VITE_*` variables.

### Market data and m.Stock

REST and WebSocket are separate service paths and must have separate health indicators. The user reports that existing REST market data remains available; this does not establish WebSocket health.

**Latest EC2 gateway check — 13 November 2026:**
- mstock-gateway.service is active and the Flask app/stream blueprint are running.
- The stream worker's authenticated status reports running=true, but connected=false, stale=true, zero cached instruments, no last tick and 933 reconnect attempts. The current status lists token 2885; its instrument identity is not independently verified.
- The required gateway secret header works when supplied with the value read server-side from the running gateway process. The earlier 403 was caused by diagnostic curl requests omitting that header.
- DNS and TLS verification for ws.mstock.trade succeed, but the WebSocket HTTP upgrade returns HTTP 502 from a provider AWS load-balancer response. The failure occurs before LOGIN or subscription messages. No live ticks have been received.
- The user has already contacted m.Stock and is waiting for its response. The feed must remain labelled NOT LIVE.

The EC2 blueprint exposes /market-stream/start|stop|status|snapshot. Its snapshot returns raw decoded tick-cache data, while the repository Order Flow adapter expects normalized /order-flow/snapshot futures/options data. The bridge between these contracts remains unimplemented/unverified. Do not infer instrument identity, expiry, option OI or other undocumented fields.

Do not mark Order Flow live until the WebSocket handshake, LOGIN, subscriptions, fresh decoded ticks, normalized backend response, backend-to-gateway authentication and frontend freshness display all pass end-to-end. See AUDIT_REPORT.md Section 2.5, SECURITY_OPERATIONS.md Section 8 and frontend/src/order-flow/README.md.
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
│   │   └── order-flow/
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

Order Flow data-model tests:

```bash
cd frontend
npm run test:market-flow
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
| Frontend | Node 20, dependency installation, npm audit, Order Flow tests and Vite production build |
| Backend | Python 3.12, dependency installation, pip-audit and pytest |
| Secrets | Gitleaks repository-history scan |

Run the same core checks locally:

```bash
# Frontend
cd frontend
npm install
npm run test:market-flow
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

Do not expose backend or gateway listeners publicly. Restrict database access to the backend. Keep secrets server-side. Never treat the provider's `awselb/2.0` WebSocket response as evidence that this application owns an AWS load balancer.

The detailed inventory, safeguards and operational checklist live in [SECURITY_OPERATIONS.md](SECURITY_OPERATIONS.md).

## Deployment and release workflow

Current repository automation:

1. Pull requests and pushes to `main` run the CI workflow described above.
2. The `package-aws-restored-source.yml` workflow can be manually dispatched and also runs when that workflow file changes on `main`. It packages the source into a ZIP artifact retained for 30 days.
3. The source-archive workflow is **not** an application deployment workflow.
4. No automatic production deployment from `main` is established by these two workflow files. Confirm the actual hosting provider, connected branch, build settings, environment variables, deployment history and rollback path in the live hosting account.

Recommended release sequence:

1. Review and merge the intended change.
2. Confirm required CI jobs passed on the exact merge commit.
3. Confirm the deployment target and release artifact.
4. Apply any approved database migration separately, with a verified backup and rollback plan.
5. Deploy using the confirmed hosting mechanism.
6. Run safe smoke tests for health, login, account/transaction reads, market REST and gateway connectivity.
7. Verify WebSocket tick freshness separately from REST health.
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

### Current known blocker

- m.Stock WebSocket handshake from the recorded Sydney host returns HTTP 502 before authentication/subscription. India-origin comparison and provider-side investigation are pending.
- Market REST checks passed in the recorded test; this does not establish live streaming health.

### Prioritised roadmap

1. **P0 — Market streaming:** run India-origin and independent-network handshake tests; obtain provider-side LB/target health evidence; only then validate login, subscriptions, ticks, heartbeat and stale/reconnect handling.
2. **P1 — Infrastructure truth:** complete live AWS inventory; confirm database hosting, frontend hosting, network boundaries, secrets store, monitoring, backups and restore procedure.
3. **P1 — Release assurance:** verify the real production deployment path and rollback; record test/deployment evidence per commit.
4. **P2 — Database governance:** implement a controlled migration runner and migration ledger; remove ad-hoc schema mutation only through a separately tested migration project.
5. **P2 — Maintainability:** modularise oversized frontend/tax modules without breaking existing workflows; improve structured logs, metrics and alerting.
6. **P3 — Security lifecycle:** evaluate MFA, email verification, password reset, CSP and safer session handling with coordinated backend/frontend changes.

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
| [frontend/src/order-flow/README.md](frontend/src/order-flow/README.md) | Order Flow implementation-specific notes |

## Contribution and change-control expectations

- Make focused changes and preserve existing user workflows and API contracts.
- Add or update tests for behaviour changes.
- Keep documentation aligned with actual code and workflows.
- Never commit secrets or production data.
- Use pull requests and verify CI before merging.
- Treat production infrastructure, database migrations, credentials and broker execution as separately controlled changes.
