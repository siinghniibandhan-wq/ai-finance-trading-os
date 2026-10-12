# Financial OS — Phase 2: Authentication and Admin Foundation

## Included in this update
- Registered the existing `/api/auth` router with FastAPI.
- Kept registration and login endpoints, password hashing, and signed bearer tokens.
- Added `/api/auth/admin/users` to list accounts for the configured administrator.
- Added `/api/auth/admin/users/{user_id}/status` to activate/deactivate an account.
- Admin identity is configured on the backend with `ADMIN_EMAIL`; the client cannot grant itself admin privileges.
- Existing m.Stock market-data routes were not changed.

## Required backend environment variables
- `AUTH_SECRET_KEY`: random secret with at least 32 characters. Use a secure secret manager/environment variable; do not commit it.
- `ADMIN_EMAIL`: email address of the administrator account. Register this email through `/api/auth/register` if the user row does not already exist, then log in normally.

## Endpoints
- `POST /api/auth/register` — creates an account; password must be at least 12 characters.
- `POST /api/auth/login` — returns a bearer token.
- `GET /api/auth/me` — returns the authenticated user's basic profile.
- `GET /api/auth/admin/users` — admin-only account listing.
- `PATCH /api/auth/admin/users/{user_id}/status` — admin-only activation status change. JSON body: `{"is_active": false}` or `{"is_active": true}`.

## Important scope / safety note
This is the authentication/admin foundation only. It does NOT yet enforce authenticated ownership on every financial endpoint, nor does it remove the frontend's hardcoded user IDs. Do not treat the application as safe for multi-customer production until the subsequent data-isolation phase is complete and tested. Open registration is currently enabled. Subscription/billing and email verification are not implemented.
