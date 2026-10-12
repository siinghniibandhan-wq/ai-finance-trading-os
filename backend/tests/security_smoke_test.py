#!/usr/bin/env python3
"""Read-only smoke tests for Financial OS auth and user_id isolation.

Required environment:
  FINOS_API_BASE_URL=https://your-backend.example
  FINOS_USER_A_EMAIL=...
  FINOS_USER_A_PASSWORD=...
  FINOS_USER_B_EMAIL=...
  FINOS_USER_B_PASSWORD=...

This script makes GET requests only. It does not create, update, or delete data.
It tests a representative set of routes; it is not a complete penetration test.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.getenv("FINOS_API_BASE_URL", "").rstrip("/")
EMAIL_A = os.getenv("FINOS_USER_A_EMAIL", "")
PASSWORD_A = os.getenv("FINOS_USER_A_PASSWORD", "")
EMAIL_B = os.getenv("FINOS_USER_B_EMAIL", "")
PASSWORD_B = os.getenv("FINOS_USER_B_PASSWORD", "")

def request(method, path, token=None, payload=None):
    url = BASE + path
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8", "replace")
            try:
                body = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                body = raw
            return response.status, body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = raw
        return exc.code, body
    except Exception as exc:
        return None, str(exc)

def login(email, password):
    status, body = request(
        "POST",
        "/api/auth/login",
        payload={"email": email, "password": password},
    )
    if status != 200 or not isinstance(body, dict) or not body.get("access_token"):
        raise RuntimeError(f"Login failed for {email!r}: HTTP {status}; response={body!r}")
    return body["access_token"], body.get("user", {}).get("id")

def main():
    missing = [
        name for name, value in [
            ("FINOS_API_BASE_URL", BASE),
            ("FINOS_USER_A_EMAIL", EMAIL_A),
            ("FINOS_USER_A_PASSWORD", PASSWORD_A),
            ("FINOS_USER_B_EMAIL", EMAIL_B),
            ("FINOS_USER_B_PASSWORD", PASSWORD_B),
        ] if not value
    ]
    if missing:
        print("Missing environment variables: " + ", ".join(missing), file=sys.stderr)
        return 2
    if EMAIL_A.strip().lower() == EMAIL_B.strip().lower():
        print("User A and User B must be two different test accounts.", file=sys.stderr)
        return 2

    token_a, id_a = login(EMAIL_A, PASSWORD_A)
    token_b, id_b = login(EMAIL_B, PASSWORD_B)
    if not id_a or not id_b or id_a == id_b:
        print("FAIL: login responses did not identify two distinct users.")
        return 1

    failures = []
    passes = 0

    # Protected endpoints must reject requests without a Bearer token.
    protected_paths = [
        "/api/accounts/",
        "/api/transactions/",
        "/api/investments/",
        "/api/investment-transactions/",
        "/api/loans",
        "/api/loan-receivables",
        "/api/liabilities",
        "/api/bills/",
        "/api/watchlist/",
        f"/api/dashboard/summary?user_id={id_a}",
        f"/api/financial-summary/?user_id={id_a}",
        f"/api/financial-plan/?user_id={id_a}",
        f"/api/tax-data/?user_id={id_a}",
        f"/api/tax-calculation/?user_id={id_a}",
        f"/api/tax-context/?user_id={id_a}",
        f"/api/capital-gains/?user_id={id_a}",
        f"/api/itr-ready-tax-report/?user_id={id_a}",
    ]
    for path in protected_paths:
        status, body = request("GET", path)
        if status in (401, 403):
            print(f"PASS unauthenticated rejected: GET {path} -> {status}")
            passes += 1
        else:
            failures.append(f"Unauthenticated GET {path} expected 401/403, got {status}: {body!r}")

    # A valid User A token must not authorize a request scoped to User B.
    # These GET routes explicitly use the shared require_matching_user_id dependency.
    cross_user_paths = [
        f"/api/dashboard/summary?user_id={id_b}",
        f"/api/capital-gains/?user_id={id_b}",
        f"/api/capital-gains-classification/?user_id={id_b}",
        f"/api/deductions-exempt-income/claims?user_id={id_b}",
        f"/api/deductions-exempt-income/?user_id={id_b}",
        f"/api/final-tax-liability/credits?user_id={id_b}",
        f"/api/final-tax-liability/compare-regimes?user_id={id_b}",
        f"/api/final-tax-liability/?user_id={id_b}",
        f"/api/financial-analytics/expenses-by-category?user_id={id_b}",
        f"/api/financial-analytics/monthly-cash-flow?user_id={id_b}",
        f"/api/financial-analytics/period-summary?user_id={id_b}",
        f"/api/financial-plan/?user_id={id_b}",
        f"/api/financial-summary/?user_id={id_b}",
        f"/api/financial-summary/loan-movements?user_id={id_b}",
        f"/api/income-tax-aggregation/?user_id={id_b}",
        f"/api/income-tax-loss-setoff/?user_id={id_b}",
        f"/api/itr-ready-tax-report/?user_id={id_b}",
        f"/api/tax-calculation/?user_id={id_b}",
        f"/api/tax-context/?user_id={id_b}",
        f"/api/tax-data/?user_id={id_b}",
        f"/api/tax-liability/?user_id={id_b}",
        f"/api/watchlist/?user_id={id_b}",
    ]
    for path in cross_user_paths:
        status, body = request("GET", path, token=token_a)
        if status == 403:
            print(f"PASS cross-user request denied: GET {path} -> 403")
            passes += 1
        else:
            failures.append(f"Cross-user GET {path} expected 403, got {status}: {body!r}")

    # User B's own access should still work for their own user-scoped routes.
    own_user_paths = [
        f"/api/dashboard/summary?user_id={id_b}",
        f"/api/financial-summary/?user_id={id_b}",
        f"/api/tax-data/?user_id={id_b}",
    ]
    for path in own_user_paths:
        status, body = request("GET", path, token=token_b)
        if status == 200:
            print(f"PASS own-user request allowed: GET {path} -> 200")
            passes += 1
        else:
            failures.append(f"Own-user GET {path} expected 200, got {status}: {body!r}")

    print(f"\nRESULT: {passes} checks passed; {len(failures)} failed.")
    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
