# Financial OS audit (static review, no tests executed)

Sandbox had no network, so dependencies could not be installed and pytest/vite build were NOT run.
All Python compiles. Run `pip install -r requirements.txt -r requirements-dev.txt && pytest -q` in backend/ and `npm ci && npm run build` in frontend/.

## Fixed in this zip
- CORS: broken/over-broad `amplifyapp.com` regex removed (double-escaped, never matched; would trust any Amplify site). Exact origins only.
- /health now really checks the DB (503 if down); removed hardcoded public /api/database-status.
- Login: PBKDF2 raised 310k -> 600k with auto-upgrade at next login; cap on stored rounds; dummy hash so unknown accounts take equal time (no user enumeration by timing).
- /api/ai/status now requires login.
- Security headers added (nosniff, frame deny, HSTS, no-store, referrer).
- Logout now clears salary details kept in localStorage.
- Removed 9 unused imports, duplicate if/else, stray blank lines, __pycache__ folders; added requirements-dev.txt (pytest, httpx).

## Round 2 (security only; broker, market and portfolio code untouched)
- Registration is now throttled (20/hour per address); stricter email check; password may not equal the email.
- Rate-limit memory is bounded; limits can use the real client address behind a proxy via TRUSTED_PROXY_COUNT=1 (set it only if nginx/load balancer is in front).
- /docs, /redoc and /openapi.json are OFF unless ENABLE_API_DOCS=1 is set on the server.
- AI chat limited to 30 messages per 10 minutes per user (protects your AI key from cost abuse).

## IMPORTANT server setting (no code change)
Admin is identified by ADMIN_EMAIL unless ADMIN_USER_ID is set. If the admin ever changes their email, the old address becomes free and anyone could register with it and become admin. Set ADMIN_USER_ID=<your user id> on the server now.

## Round 3 (error messages, go-live)
- Plain-language errors everywhere: login, registration, order placement and all save/delete forms now show real sentences
  (e.g. "Password: String should have at least 12 characters", "Cannot reach the server...") instead of "Request failed (400)".
  A broker message such as "Insufficient balance" is shown exactly as the gateway sends it.
- Unexpected server errors (500) now say what kind of problem it was (database / connected service timeout / unexpected)
  plus a reference code; the full technical error is written to the server log under that same code.
- Checked all frontend API paths against backend routes and all menu pages: no broken links found.
- Added backend/.env.example and .gitignore (the zip had none, so .env files could have been committed).

## Go-live checklist
1. Server env: AUTH_SECRET_KEY (48+ random chars), ADMIN_USER_ID, DATABASE_URL, CORS_ALLOWED_ORIGINS; see backend/.env.example.
2. HTTPS only (nginx + Let's Encrypt); run uvicorn behind it; set TRUSTED_PROXY_COUNT=1.
3. Run the tests (pytest) and `npm ci && npm run build`; fix anything red before launch.
4. Run the broker .sql files in backend/migrations once, by hand, on a backup first.
5. Back up the database daily and test a restore. Rotate AUTH_SECRET_KEY if it was ever shared (this logs everyone out).
6. Verify fastapi==0.157.0 installs from your package index; pin boto3 and google-genai to exact versions.
7. Log rotation for gateway.log / orders.log.jsonl (they contain order data).

## More recommendations
- Add CSP and cache headers at nginx for the frontend; consider httpOnly cookies instead of sessionStorage tokens.
- Add error monitoring (Sentry) so reference codes alert you.
- Split App.jsx (16k lines) and tax route files (2k lines each) into smaller modules; add a CI job running pytest and build.
- Add Alembic migrations instead of startup ALTER TABLE code.
- Email verification and password reset before opening registration publicly.

## Verified OK
- Every user-data route uses require_matching_user_id / get_current_user / get_current_admin (ownership enforced).
- Broker orders: admin-only, kill switch default OFF, loopback-only gateway, secret header. Not modified.
- No hardcoded secrets, no eval/exec/subprocess, SQL is parameterised (f-string SQL uses constants only).

## Needs your decision
1. Market routes (/api/market*, search, mutual-funds) are public and proxy upstream APIs: add login or rate limit?
2. instrument_master.py is never registered in main.py: delete it or register it?
3. Login rate limit is per-process and keyed on request.client.host: behind nginx/proxy all users share one IP. Needs proxy-header handling or Redis.
4. Schema changes run at startup in main.py plus loose .sql files: move to Alembic.
5. No password reset, email verification, or MFA. Registration reveals if an email exists (409).
6. Tokens are in sessionStorage (XSS-exposed); consider httpOnly cookies. No CSP set.
7. App.jsx is 16k lines: split into modules.
8. Localhost origins and the Amplify URL are hardcoded in CORS; move to env.
