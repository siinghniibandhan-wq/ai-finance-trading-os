# Financial OS security operations

## Application controls in this repository

- Business/data routers require a valid bearer session by default. Registration and login are the only intentionally public API actions; `/` and `/health` are minimal operational endpoints.
- API documentation and OpenAPI are disabled in production. They can be enabled only when `APP_ENV` is `development`, `local`, or `test` and `ENABLE_API_DOCS=1`.
- CORS accepts exact configured origins and the deployed Amplify origin. Localhost origins are development-only. Credentialed CORS and wildcard origins are disabled.
- API limits: default 120/minute/IP, login 10/minute/IP (plus existing 5 failures/15 minutes per IP+identifier), registration 5/hour/IP, AI 20/10 minutes/IP, broker orders 10/minute/IP.
- Application rate limiting is process-local and resets on restart. It is not a distributed WAF control.
- Market instrument requests reject remote HTTP gateway URLs; configure HTTPS or a same-host loopback service.
- CI audits npm/Python dependencies and scans repository history for committed secrets. Dependabot checks npm, pip and GitHub Actions weekly.

## Mandatory AWS production configuration

1. Set `APP_ENV=production`, `AUTH_SECRET_KEY` to a newly generated random value of at least 48 characters, `ADMIN_USER_ID`, `DATABASE_URL`, and exact `CORS_ALLOWED_ORIGINS`.
2. Keep database, broker, AWS and AI-provider credentials in SSM Parameter Store or Secrets Manager. Never put secrets in Vite `VITE_*` variables. Set the same random `MSTOCK_GATEWAY_SECRET` (at least 32 characters) on the backend and gateway; market-data calls fail closed if it is absent.
3. Terminate TLS at nginx/ALB with modern TLS settings. Bind Uvicorn to loopback/private interfaces; do not expose the application or gateway port directly to the internet.
4. Security groups: expose 443 publicly; restrict SSH to a controlled administrator IP or use Systems Manager Session Manager; allow PostgreSQL only from the backend security group.
5. Add AWS WAF rate-based rules or nginx/shared-proxy limits for `/api/*`. The in-process limiter is per worker and does not protect against distributed traffic.
6. Set `TRUSTED_PROXY_COUNT` only to the exact number of trusted proxies. Never trust arbitrary client-supplied `X-Forwarded-For` values.
7. Enable GitHub secret scanning/push protection and Dependabot alerts; protect `main` with required CI checks and restrict direct push access.
8. Rotate any credential that may ever have been committed or exposed. Deleting a secret from the current tree does not invalidate Git-history copies. Verify backups and test restores.

## Frontend exposure boundary

The API hostname and request paths are necessarily visible in browser network traffic. A Vite `VITE_*` value is public after build and must never contain a credential. The API URL remains public configuration; database, broker, AWS and AI-provider secrets must stay server-side. A same-origin reverse proxy can remove the hardcoded API hostname from the bundle, but browser requests remain inspectable. The current bearer token is stored in `sessionStorage`: it is not a bundled API key, but JavaScript can read it if an XSS vulnerability is introduced. Moving to HttpOnly cookies requires a coordinated same-site/CSRF design and is not a safe one-file change.

## Verification boundary

CI checks source-level controls, dependency advisories and committed-secret patterns. The repository currently has no committed npm or Python dependency lockfile, so dependency resolution is audited on each CI run but is not fully reproducible between installs. CI cannot verify live EC2 security groups, nginx/ALB TLS, WAF rules, SSM values, database network exposure or deployed CORS headers. Those require an AWS-side deployment audit.
