# Financial OS — AWS Infrastructure, Security & Operations

**Document role:** Canonical infrastructure and security operations guide  
**Last review:** 19 November 2026  
**Scope:** Repository security controls and the known AWS-hosted market-data gateway. Verify live AWS resources before treating this document as a complete account inventory.

---

## 1. Infrastructure facts and verification boundary

### Confirmed from repository and recorded operational evidence

| Component | Current evidence | Status / caveat |
|---|---|---|
| Backend application | FastAPI + Uvicorn, SQLAlchemy | Repository implementation |
| Database | SQLAlchemy database engine; PostgreSQL driver installed | Actual hosting (RDS vs self-managed) must be confirmed |
| Market-data gateway | EC2-hosted Flask service, loopback Flask listener on port 8000 | Recorded host details below; verify live before operational changes |
| Gateway host region | `ap-southeast-2` (Sydney) | Recorded EC2 deployment |
| Gateway host public IP | `54.153.201.74` | Infrastructure identifier; verify current allocation |
| EC2 instance ID | `i-078b9cec176a0384d` | Recorded instance; verify current state |
| Gateway service | `mstock-gateway.service` | systemd service |
| Backend service | `financial-os-backend.service` | Recorded Gunicorn service on `127.0.0.1:8001`; verify current unit |
| Secrets integration | boto3 dependency and SSM Parameter Store configuration guidance | Actual IAM permissions and parameter names must be checked in AWS |
| Frontend hosting | AWS Amplify is configured as the public frontend target; production branch `main`, app root `frontend/` | User-provided Amplify configuration/screenshot; verify live deployment ID and deployed commit in Amplify |
| Historical m.Stock WebSocket response | Earlier provider response identified `awselb/2.0` | Historical incident evidence only; not a current application dependency |

Do not infer that the application uses AWS RDS, ALB, WAF, CloudFront, S3, Route 53, CloudWatch alarms or multi-AZ infrastructure until the live account configuration confirms those resources.

## 2. Logical AWS and service architecture

```text
Browser
  |
  | HTTPS
  v
AWS Amplify (public frontend; deployment record to be verified)
  |
  | HTTPS API requests to https://wealthmanager.duckdns.org
  v
Financial OS API (FastAPI / Gunicorn or Uvicorn)
  |                         |
  |                         +--> PostgreSQL (hosting to be confirmed)
  |
  +--> m.Stock Gateway EC2 (Sydney, ap-southeast-2)
          |
          +--> Flask gateway bound to 127.0.0.1:8000
          |
          +--> systemd: mstock-gateway.service
          |
          +--> m.Stock REST APIs
          |
          +--> (no application WebSocket stream is currently documented)
               wss://ws.mstock.trade
               Provider DNS/ELB observed in Mumbai (ap-south-1)
```

This is a logical representation of known components, not a complete network topology. Confirm the exact route between the Financial OS backend and gateway, security-group rules, public/private subnet placement, NAT/egress, TLS termination, DNS and database network path from AWS.

## 3. Known EC2 services

### m.Stock gateway host

Recorded deployment:
- Region: `ap-southeast-2` (Sydney).
- Instance: `i-078b9cec176a0384d`.
- Public IP at time of record: `54.153.201.74`.
- Gateway directory: `/home/ssm-user/mstock-gateway`.
- Python virtual environment: `/home/ssm-user/mstock-gateway/venv`.
- systemd unit: `mstock-gateway.service`.
- Flask listener: `127.0.0.1:8000` (loopback only).
- Environment file: `/etc/financial-os-gateway.env`.
- Shared-secret header: `X-Financial-OS-Gateway-Secret`; never publish its value.

### Financial OS backend host/service

Recorded service details:
- systemd unit: `financial-os-backend.service`.
- Gunicorn workers: 2.
- Listener: `127.0.0.1:8001`.
- The backend service is separate from the m.Stock gateway service.

**Change safety:** Do not restart, stop, edit or redeploy either service as a documentation task. Never modify the backend service while investigating a gateway-only issue unless evidence and explicit approval require it.

## 4. AWS services — purpose and current status

| AWS capability | Intended/known use | Current documentation status |
|---|---|---|
| EC2 | Hosts the m.Stock gateway; backend service host is recorded separately but live placement needs confirmation | Partially confirmed |
| IAM roles | Grant EC2 least-privilege access to required AWS resources such as SSM parameters | Must inspect attached roles and policies |
| Systems Manager (SSM) | Secure administration/parameter retrieval; boto3 dependency is present | Capability/configuration referenced; verify live use and permissions |
| Parameter Store / Secrets Manager | Store database, broker, AI and gateway credentials outside source control | Required security design; verify which store is actually used |
| Security Groups | Restrict HTTPS, SSH/SSM, backend-to-gateway and database traffic | Must inspect live rules |
| CloudWatch | Logs, metrics, alarms and EC2/service monitoring | Recommended; live configuration unverified |
| AWS WAF | Rate-based and managed protections at a supported edge/load-balancer layer | Recommended; not confirmed deployed |
| Application Load Balancer | TLS termination/routing if selected for this architecture | Not confirmed for this application |
| RDS | Managed PostgreSQL option | Not confirmed; do not assume |
| S3 | Backup/artifact/object storage option | Not confirmed |
| Route 53 / ACM | DNS and managed TLS option | Not confirmed |

The m.Stock endpoint's AWS load-balancer response is controlled by the provider. It must not be counted as one of this application's AWS resources.

## 5. Network boundaries

- Public traffic should enter through HTTPS on port 443 at the verified frontend/API edge.
- Backend application and gateway listeners should remain on loopback or private interfaces; do not expose ports 8000 or 8001 directly to the public internet.
- Permit gateway access only from the Financial OS backend's known security group or fixed private source where possible.
- PostgreSQL should accept traffic only from the backend security group/private source.
- Restrict SSH to a controlled administrator source, or use Systems Manager Session Manager where configured.
- Do not trust arbitrary `X-Forwarded-For` headers. Set `TRUSTED_PROXY_COUNT` only to the exact number of trusted reverse proxies.
- Confirm outbound egress policy and DNS resolution for external market-data and AI services.
- Review IPv4 and IPv6 rules separately.

## 6. Secrets and identity

### Secrets that must remain server-side

- `DATABASE_URL`
- `AUTH_SECRET_KEY`
- m.Stock API key, access token and TOTP seed/value
- `MSTOCK_GATEWAY_SECRET` / gateway shared secret
- Broker credentials and signing secrets
- Google Gemini API key
- AWS access credentials, if any (prefer instance roles over static keys)

Never put secrets in frontend `VITE_*` variables, source files, GitHub issues, screenshots, shell output, logs or documentation. The gateway shared secret must match on the backend and gateway, but its value must never be printed.

### Required production configuration

Use the current `backend/.env.example` as the variable-name reference and validate the actual runtime configuration. At minimum review:
- `APP_ENV=production`
- Strong randomly generated `AUTH_SECRET_KEY`
- Stable `ADMIN_USER_ID`
- `DATABASE_URL`
- Exact `CORS_ALLOWED_ORIGINS`
- Gateway URL and shared-secret configuration
- AI provider key configuration

Store production values in SSM Parameter Store or Secrets Manager with least-privilege IAM. Do not assume that adding boto3 alone configures secure secret retrieval.

Rotate any credential that may have been exposed. Removing a value from the latest commit does not remove it from Git history or invalidate it.

## 7. Application security controls in the repository

- Authenticated-user dependencies are applied to most business/data routers; authentication routes are registered separately.
- Admin-only operations use explicit admin authorization.
- CORS is intended to use exact allowed origins; localhost is development-only.
- API documentation/OpenAPI is restricted by environment and configuration.
- Process-local rate limits exist for API, login, registration, AI and broker order paths. These are not distributed WAF controls and reset on process restart.
- Broker orders have admin-only protection, a kill switch defaulting OFF, loopback gateway restrictions and a secret header according to the existing audit.
- Market instrument gateway requests reject unsafe remote HTTP gateway URLs; use the configured trusted endpoint.
- Frontend bearer tokens are currently stored in `sessionStorage`. JavaScript can read them if an XSS vulnerability exists. Moving to HttpOnly cookies requires coordinated same-site and CSRF handling.
- CI runs frontend/backend checks, dependency audits and repository-history secret scanning as configured in `.github/workflows/financial-os-ci.yml`.

Verify current source and live settings before treating each control as effective in production.

## 8. Chart Flow, REST market data and streaming boundary

**Current source review — 19 November 2026**

- `backend/app/routes/market_flow.py` defines the read-only `GET /api/market-flow/` endpoint. `backend/app/main.py` imports and registers `market_flow.router` through the authenticated-user router helper.
- The market snapshot fetches m.Stock Type A provider-ranked cash-market gainers and losers for NSE and BSE (`SecurityIdCode=0`) and the supported market-index snapshots.
- The optional sector-index snapshot mode requests the configured sector index quotes. A sector-specific request returns provider-ranked movers for that sector and the associated sector-index quote.
- The provider returns ranked movers, not every listed instrument or every sector constituent. The API explicitly reports that full advance/decline breadth, full sector constituent breadth, delivery statistics and historical market flow are unavailable. Do not describe the returned mover counts as complete exchange breadth.
- Provider request pacing, bounded caching, partial-result reporting and read-only/no-database-write behaviour are implemented in the route.
- Chart Flow and Advanced Chart use REST data paths. Periodic refreshes are bounded HTTP requests; quote retrieval time is not an exchange timestamp. No WebSocket/continuous market-data stream is part of the current Chart Flow/Advanced Chart runtime.
- The latest uploaded Gateway source reviewed in the earlier source audit had no Market Flow or `/market-stream/*` implementation. This is a source-file observation, not proof of the current live EC2 deployment.

### Historical incident record — 13 November 2026

Earlier SSM observations about a Gateway WebSocket worker, `/market-stream/*` routes, `GATEWAY_SECRET_INVALID`, and provider handshake failures are retained as historical audit evidence only. They do not establish current repository code, deployed Gateway files, live service state or current provider connectivity.

### Operational boundaries

- Preserve m.Stock REST routes, quote contracts, market history, charts, indices, movers, search, watchlists and broker-order safeguards.
- Preserve existing Bearer authentication and gateway shared-secret validation. Chart Flow is a private read-only API route and does not replace these controls.
- Do not reintroduce WebSocket market streaming or `/market-stream/*` dependencies into Chart Flow/Advanced Chart unless separately requested and reviewed.
- Never include API keys, access tokens, TOTP values or gateway shared secrets in diagnostics or documentation.

## 9. Deployment and release workflow

The repository currently provides GitHub Actions workflows:
- `financial-os-ci.yml`: runs frontend production build/regression checks, backend regression tests, dependency audits and repository secret scanning on pushes/PRs to `main` and manual dispatch.
- `frontend-build.yml`: builds the frontend and uploads a CI artifact. The former `publish-frontend` job that force-pushed compiled assets to `frontend-dist` was removed by PR #223.
- `package-aws-restored-source.yml`: creates a source archive on workflow dispatch and on changes to that workflow.

AWS Amplify is configured as the public frontend target on branch `main`, with app root `frontend/`, `npm run build` and `dist` output. The browser API origin remains `https://wealthmanager.duckdns.org`, and backend CORS includes `https://main.d1qcu4l3dz9f9e.amplifyapp.com`. This configuration does not prove which commit is currently deployed. PR #223 did not change EC2/Nginx, DNS, TLS, backend services or Gateway services. Inspect and retire any EC2 static frontend root, redirect or frontend deploy timer/runner separately; preserve DuckDNS API reverse-proxy routes and backend/Gateway connectivity.

### Release checklist

1. Merge only reviewed changes to the intended branch.
2. Confirm all required CI jobs pass on the exact merge commit.
3. Confirm the intended hosting workflow and target environment.
4. Apply database migrations separately, with verified backup and rollback plan.
5. Deploy application artifact.
6. Run safe smoke tests: health, login, account read, transaction read, market REST, gateway connectivity and frontend route loading.
7. Verify broker kill switch remains in the intended state; never place a live test order without explicit approval.
8. Record commit SHA, workflow run, deployment ID, environment, smoke-test results and rollback reference.

## 10. Monitoring, logs, backup and recovery

Recommended controls to implement/verify:
- CloudWatch or equivalent central logs for EC2 and application services.
- Alarms for EC2 status checks, disk/memory pressure, service restarts, API 5xx, gateway failures, stale market data and database availability.
- Structured logs with request/correlation IDs and sanitized provider errors.
- Log rotation and retention for application, gateway and order logs. Order logs may contain sensitive financial information.
- Daily database backups, documented retention and periodic restore tests.
- EC2 recovery procedure and tested service restart steps.
- Credential rotation and incident escalation contacts.
- Monitor the backend API and m.Stock REST gateway independently; no application market-stream health dashboard is currently in scope.

Do not record secrets or full authentication headers in logs. A successful backup job is not sufficient: restore testing is required.

## 11. Change control and access

- Use least-privilege IAM and separate human/operator access from application runtime roles.
- Prefer SSM Session Manager over publicly exposed SSH where feasible.
- Protect `main` with pull-request review and required CI checks.
- Production database migrations, network/security-group edits, IAM changes, broker execution changes and credential rotation require explicit approval and a rollback plan.
- Documentation-only changes must not restart services, alter AWS resources or change production configuration.

## 12. AWS audit items still requiring live verification

- [ ] Enumerate EC2 instances, regions, AMIs, attached roles, volumes and public IPs.
- [ ] Confirm backend and gateway host placement and service unit definitions.
- [ ] Inspect security groups, subnet routing, NACLs and outbound egress.
- [ ] Confirm actual database host/type, subnet access, encryption, backups and restore procedure.
- [ ] Confirm SSM Parameter Store vs Secrets Manager use and IAM policies.
- [x] Record AWS Amplify as the public frontend target (`main`, app root `frontend/`) and DuckDNS as backend API origin only.
- [ ] Verify the live Amplify deployment ID/commit and smoke-test the public frontend against the DuckDNS API.
- [ ] Inspect EC2/Nginx static frontend root, redirects and frontend deploy timer/runner; retire only frontend serving while preserving API proxy routes.
- [ ] Confirm TLS termination, certificate renewal and DNS ownership.
- [ ] Confirm CloudWatch log groups, retention, metrics and alarms.
- [ ] Confirm WAF/edge rate limiting or document the compensating controls.
- [ ] Verify log rotation and backup restoration.
- [x] Reconcile Market Flow / market-stream documentation with the current backend and latest uploaded Gateway source (18 November 2026).



## 13. Database migrations and automation

### 13.1 Current repository evidence

The reviewed repository contains:

- Dated SQL files under `backend/migrations/`.
- Additional standalone SQL migration files under `backend/`.
- Application startup table/schema logic in the backend.
- GitHub Actions CI and source-archive workflows described in Section 9.

The reviewed repository tree does **not** contain a dedicated migration runner, migration ledger implementation, schema-application systemd unit/timer, cron migration definition or automatic production migration workflow. This is a repository finding only; it does not prove that no manually configured timer or script exists on a live EC2 host.

Do not assume a committed SQL file is automatically applied. Do not run it against production without separate explicit approval.

### 13.2 Current automation — actual behaviour

| Mechanism | Trigger | Confirmed effect | Not confirmed / does not do |
|---|---|---|---|
| `.github/workflows/package-aws-restored-source.yml` | Manual dispatch; workflow-file change on `main` | Packages source ZIP and uploads a 30-day GitHub Actions artifact | No EC2 deployment, service restart or database migration |
| `mstock-gateway.service` | systemd service manager | Runs the recorded Flask gateway service | Not a schema runner or scheduler |
| `financial-os-backend.service` | systemd service manager | Runs the recorded backend service | Not a schema runner or scheduler |

No repository-defined systemd timer or scheduled schema runner was found in the reviewed branch. Inspect live `systemctl list-timers --all`, `systemctl list-units --type=service` and the applicable user's crontab before documenting the host's actual scheduled operations. Review output carefully and redact sensitive environment values.

### 13.3 Migration controls required before implementation

Any future migration mechanism should provide:

1. Unique, immutable migration identity and deterministic ordering.
2. Migration ledger recording file identity, checksum, execution timestamp, environment and result.
3. Checksum mismatch detection; never silently rerun modified SQL.
4. Dry-run and status inspection before execution.
5. Verified backup gate before any production write.
6. Explicit transaction/partial-failure policy and recovery instructions.
7. Locking to prevent concurrent migration processes.
8. Restricted execution identity and explicit environment targeting.
9. Sanitised logs and alerting on failure.
10. A tested restore/recovery path.

The exact tool, transaction boundary, backup mechanism, rollback strategy, runner interface and scheduling cadence remain design decisions. Do not represent this recommended design as implemented.

### 13.4 Safe operating sequence

1. Review the migration SQL and its data/locking impact.
2. Confirm the target environment and current migration ledger.
3. Verify a fresh database backup and a tested restore path.
4. Run validation/dry-run in a non-production environment.
5. Apply to staging and run application regression tests.
6. Obtain separate production approval.
7. Apply in a controlled window and verify schema state and application health.
8. Record migration identifier, checksum, commit, environment, backup reference and result.
9. If execution fails, stop subsequent migrations and follow the approved recovery plan; do not blindly rerun.

Keep schema files limited to schema/data migration intent. Do not embed service management, runner installation, timer creation or deployment-tool changes inside SQL files.

## 14. Automation governance

Every scheduled or event-driven automation must document:

- Owner and purpose.
- Trigger, cadence and timezone.
- Target environment and execution identity.
- Required permissions and secret references (never secret values).
- Timeout, retry, idempotency and concurrency behaviour.
- Logs, metrics, alert recipient and failure escalation.
- Disable procedure and rollback/recovery method.

A timer or cron job must not bypass backup verification, migration ledger checks or production approval. CI success is not deployment success. Artifact creation is not deployment. A running systemd service is not proof that a scheduled job or migration runner exists.

## 15. AWS architecture implementation status

The AWS architecture table in Section 4 describes purpose and verification status. Use these status labels consistently:

- **Confirmed from repository/recorded evidence:** code or a dated operational record supports the statement.
- **Partially confirmed:** some configuration is known, but live state or dependencies remain unverified.
- **Recommended, not confirmed:** proposed architecture/control only.
- **Not confirmed:** do not describe as deployed until verified in the AWS account.

For the next live infrastructure audit, capture resource IDs, region, account/environment, tags, security-group references, subnet placement, IAM role, backup policy and last-verified timestamp. Never copy secret values or credential-bearing environment output into documentation.

The application-owned AWS topology remains incomplete until the active frontend host, backend host, database host, network path, IAM/SSM secret retrieval, DNS/TLS edge, logging/alarms and backup/restore configuration have all been checked against the live account.


## Historical deployment note — Type A market stream (13 November 2026)

An earlier EC2 inspection documented a Type A decoder, a persistent WebSocket worker and Flask market-stream routes. That evidence belongs to the 13 November deployment snapshot only. The latest uploaded Gateway `mstock-gateway-app.py` reviewed on 18 November no longer contains those routes or worker references. Do not use this historical addendum as a current deployment inventory.

The Financial OS Order Flow adapter and Market Flow integration are absent from the reviewed current backend source. The current application market-data integration is REST-based. Existing REST and broker-order functionality must remain unchanged.


---

## Operational status addendum — 20 November 2026

### Authentication incident closure

The HTTP 401 `Authentication is required` issue reported after OTP sign-in is **resolved per the latest user confirmation**. This is an incident-status update, not a claim that a new authentication mechanism was introduced. Preserve the existing Financial OS authentication flow and the gateway-owned m.Stock provider session. Do not create a parallel OTP/login flow or duplicate provider-token lifecycle.

For release verification, test the complete sequence: OTP sign-in, access to an authenticated API route, continued session use beyond the previously observed short interval, explicit logout and sign-in again. Record the environment, timestamp and tested commit. Never include bearer tokens, OTP values, TOTP seeds or gateway secrets in the evidence.

### BSE integration status

The BSE market-data issue is **resolved per the latest user confirmation**. Current repository code includes BSE in the cash-market mover exchange mapping and accepts NSE/BSE in the Options Hub master and option-chain routes. The 19 November 2026 gateway discovery session returned NSE Futures 685, NSE Options 92,283, BSE Futures 661 and BSE Options 45,318 (138,947 observed contracts total). These counts are a dated observation only. LTP quote retrieval was tested; optional provider fields such as volume and open interest remain coverage-dependent.

Continue to treat market requests as read-only REST operations. Do not infer complete exchange breadth from ranked movers or present missing provider fields as real values. The BSE issue is no longer an active incident in the latest user-confirmed status.
