# Financial OS — AWS Infrastructure, Security & Operations

**Document role:** Canonical infrastructure and security operations guide  
**Last review:** 13 November 2026  
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
| Frontend hosting | Vite build and CI present; historical deployment references are mixed | Confirm active production host from deployment records |
| AWS load balancer for m.Stock WebSocket | Provider response identified `awselb/2.0` | This is the remote m.Stock endpoint path; not evidence of an application-owned ALB |

Do not infer that the application uses AWS RDS, ALB, WAF, CloudFront, S3, Route 53, CloudWatch alarms or multi-AZ infrastructure until the live account configuration confirms those resources.

## 2. Logical AWS and service architecture

```text
Browser
  |
  | HTTPS
  v
Frontend hosting (active provider to be confirmed)
  |
  | HTTPS API requests
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
          +--> m.Stock WebSocket endpoint
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

## 8. m.Stock WebSocket incident and operational response

**Latest diagnostic evidence:** 13 November 2026, approximately 15:08–15:12 UTC, from the user's SSM session on the Sydney EC2 gateway host.

### Confirmed gateway and authentication state

- mstock-gateway.service was active (PID 76459) and the Flask listener was bound to 127.0.0.1:8000.
- The gateway application registers the market_stream Flask blueprint. The stream worker is a background thread in the Flask process; it is not expected to appear as a separate market_stream.py OS process.
- The required header is X-Financial-OS-Gateway-Secret; the gateway validates it against FINANCIAL_OS_GATEWAY_SECRET.
- An earlier pair of curl diagnostics omitted the header and correctly returned HTTP 403 GATEWAY_SECRET_INVALID.
- A subsequent diagnostic read the secret from the running process environment without printing it and sent it in the required header. Both /market-stream/status and /market-stream/snapshot then returned HTTP 200. This verifies the gateway's own shared-secret guard for that diagnostic. Both FINANCIAL_OS_GATEWAY_SECRET and MSTOCK_GATEWAY_SECRET variable names were present in the process environment; their values were not disclosed. This test alone does not prove that the Financial OS backend is configured with the same value.

### Current WebSocket state

The authenticated /market-stream/status response reported:

| Field | Observed value |
|---|---|
| Worker running | true |
| WebSocket connected | false |
| stale | true |
| cached_instruments | 0 |
| last_tick_at / age | null |
| reconnect_count | 933 |
| Mode | 3 (full) |
| Subscribed token | 2885 (instrument identity not verified) |
| last_error | HTTP 502 during WebSocket handshake |

The authenticated /market-stream/snapshot endpoint returned HTTP 200 with an empty ticks array. The worker thread is active and retrying; this is not a connected feed.

### Network and handshake evidence

- WebSocket endpoint: wss://ws.mstock.trade.
- DNS resolved the host to provider AWS load-balancer addresses 13.200.68.179 and 15.206.54.73, associated with Mumbai (ap-south-1).
- The EC2 gateway host is in Sydney (ap-southeast-2).
- TCP/TLS connectivity succeeded; the certificate for ws.mstock.trade verified successfully with TLS 1.3.
- No outbound proxy environment variables were configured.
- Installed client library: websocket-client 1.9.0.
- The worker constructs a credential-bearing WebSocket URL server-side, then sends LOGIN, subscribe and mode messages only after create_connection succeeds. The observed HTTP 502 happens during the handshake, before those messages are sent.
- The HTTP response identified awselb/2.0. This indicates a provider-side load-balancer response path; it does not independently prove the exact failed upstream component or root cause.

**Current diagnosis:** gateway service, internal shared-secret authentication, DNS and TLS are working. The m.Stock WebSocket HTTP upgrade is failing with HTTP 502. No live ticks have been received. This is not evidence that the m.Stock API key/access token is invalid, that the Type A decoder is wrong, or that the subscription was rejected: the handshake has not reached LOGIN or subscription.

### Current support and next actions

The user has already emailed m.Stock and elected to wait for its response rather than send duplicate requests immediately. No provider response has yet been recorded in this incident log.

1. Wait for m.Stock's technical response. If requested, provide sanitized UTC/IST timestamps, source region, DNS/TLS results and HTTP 502 response details. Never provide API keys, access tokens, TOTP or gateway secrets.
2. After provider feedback, repeat a controlled WebSocket handshake test and record the result. An India-origin comparison may help distinguish provider-wide failure from source-region/network routing, but region difference alone is not a proven cause.
3. Once the handshake succeeds, verify LOGIN response, subscription acknowledgement, heartbeat, packet receipt, Type A decoding, exchange timestamps, cache population and stale/reconnect behaviour.
4. Verify the instrument master and expiry/token mapping before adding NIFTY futures/options subscriptions. Token 2885 is observed in the current status but its instrument identity has not been independently verified.
5. Separately implement and test the adapter from raw /market-stream/snapshot ticks to the Financial OS normalized /order-flow/snapshot futures/options contract.
6. Verify the backend's gateway URL and shared-secret configuration against the gateway without displaying either secret, then verify frontend freshness display.

### Safeguards

- Do not expose credentials, access tokens, TOTP or gateway secrets in diagnostics, logs, screenshots or documentation.
- Do not change trading, order execution, broker integration, database state or migrations to fix a pre-authentication WebSocket 502.
- Do not restart services, alter systemd configuration, change credentials, move the EC2 host/region or rewrite the decoder without evidence and explicit approval.
- Keep REST market-data health, WebSocket transport health and market-data freshness as separate signals.
- Do not mark the feed LIVE until fresh ticks and the full normalized application path are verified end-to-end.


## 9. Deployment and release workflow

The repository currently provides GitHub Actions workflows:
- `financial-os-ci.yml`: frontend dependency installation/audit, Order Flow tests, Vite production build, backend dependency installation/audit, pytest and secret scanning.
- `package-aws-restored-source.yml`: creates a source archive on workflow dispatch and on changes to that workflow.

These workflows do not, by themselves, prove that production deploys automatically from `main`. Confirm the active deployment provider, branch mapping, build settings, environment variables, artifact promotion and rollback process from the live hosting configuration.

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
- Separate operational dashboards for backend API, m.Stock REST and m.Stock WebSocket.

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
- [ ] Confirm active frontend hosting provider and deployment branch/workflow.
- [ ] Confirm TLS termination, certificate renewal and DNS ownership.
- [ ] Confirm CloudWatch log groups, retention, metrics and alarms.
- [ ] Confirm WAF/edge rate limiting or document the compensating controls.
- [ ] Verify log rotation and backup restoration.
- [ ] Complete the India-origin m.Stock WebSocket handshake comparison.



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
| `.github/workflows/financial-os-ci.yml` | Push/PR to `main`; manual dispatch | Frontend install/audit, Order Flow tests, Vite build, backend install/audit, pytest and Gitleaks scan | No production deployment; no schema application |
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


## Addendum — Type A market-stream deployment evidence (13 November 2026)

The user inspected the existing EC2 gateway directory through an authorized Session Manager session and supplied these deployed-host files for review:

- `mstock_stream.py`: Type A binary-frame decoder.
- `market_stream.py`: persistent WebSocket worker with token subscriptions, tick cache, reconnect backoff and stale status.
- `market_stream_routes.py`: Flask blueprint exposing read-only `/market-stream/start`, `/stop`, `/status` and `/snapshot`.
- EC2 `app.py` imports and registers `create_market_stream_blueprint` at lines 917–924.
- `mstock-gateway.service` was observed active under systemd.

This is evidence from the deployed EC2 host, not proof that the same files are committed to this GitHub repository. An active systemd process and registered blueprint do not prove the worker itself has been started or has received live ticks.

A request to the stream status route returned `GATEWAY_SECRET_INVALID`. This indicates the request failed the gateway's internal shared-secret validation. It does not establish that m.Stock API credentials are invalid. The user reports that existing REST market data remains available; keep REST and WebSocket health separate. Resolve the internal secret mismatch using the existing server-side configuration without exposing or regenerating credentials.

The gateway blueprint's `/market-stream/snapshot` route returns cached decoded ticks and stream status. The repository Order Flow adapter expects a different endpoint, `/order-flow/snapshot`, with normalized futures/options data. The adapter/route mapping and the Order Flow connection have not yet been verified. Do not report Order Flow as LIVE until authentication, worker startup, token subscriptions, fresh tick receipt, normalized snapshot delivery and frontend freshness display have all been tested.

The prior Sydney-host HTTP 502 WebSocket-upgrade result is historical. It occurred before LOGIN/subscription and does not establish the current worker's connection state.

**Safety:** Do not modify existing REST market-data routes, broker/order execution, production service configuration or database state during this verification. Database migrations and migration automation remain out of scope and untouched.
