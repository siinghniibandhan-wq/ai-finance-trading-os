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

**Last recorded evidence:** 13 November 2026.

- Endpoint: `wss://ws.mstock.trade`.
- From the Sydney EC2 gateway host, TCP 443 and TLS 1.3 succeeded, but WebSocket upgrade repeatedly returned HTTP 502 from a server identified as `awselb/2.0`.
- Provider DNS resolved to AWS load-balancer IPs in Mumbai (`ap-south-1`); the tested client host was in Sydney (`ap-southeast-2`).
- The failure occurred before LOGIN or subscription messages. The last captured worker was disconnected/stale and repeatedly reconnecting, with no ticks.
- REST endpoints for quotes, index quotes, gainers/losers, instruments and historical data returned HTTP 200 in the recorded checks.
- An India-origin WebSocket test has not yet been recorded. Region difference is a lead, not a proven root cause.

### Diagnostic sequence

1. Test the handshake from India and a second independent network. Record timestamp (IST), source network, DNS answer, TLS result, HTTP status and sanitized response headers.
2. Ask m.Stock to inspect WebSocket listener, target-group and upstream health for those exact timestamps.
3. Compare results to distinguish provider-wide failure from source-network/geographic routing.
4. Once handshake succeeds, test authentication, subscription acknowledgement, heartbeat, tick delivery and stale/reconnect handling.
5. Keep REST health, WebSocket transport health and market-data freshness as separate monitoring signals.

### Safeguards

- Do not expose credentials, access tokens, TOTP or gateway secrets in diagnostics.
- Do not change trading, order execution, broker integration or database state to fix a pre-authentication WebSocket 502.
- Do not move the EC2 host, rewrite the protocol or repeatedly restart production services without evidence and approval.
- Do not claim live streaming is healthy until ticks are received and freshness/reconnect checks pass.

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

