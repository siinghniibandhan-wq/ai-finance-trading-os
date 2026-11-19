# ============================================================
# FINANCIAL OS
# FASTAPI APPLICATION
# ============================================================

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.database.database import Base, engine

# Import models before create_all().
from app import models


# ============================================================
# IMPORT API ROUTES
# ============================================================

from app.routes import (
    auth,
    profile,
    ai_assistant,
    broker_orders,
    broker_reconciliation,
    users,
    loans,
    accounts,
    chart_of_accounts,
    ledger,
    categories,
    transactions,
    dashboard,
    budgets,
    bills,
    investments,
    market,
    market_overview,
    market_flow,
    options_hub,
    market_quote,
    market_search,
    mutual_fund_search,
    market_history,
    market_charts,
    watchlist,
    market_movers,
    market_indices,
    investment_transactions,
    holdings,
    investment_pnl,

    # Financial Data & Analytics
    financial_summary,
    financial_analytics,
    financial_plan,
    goals,

    # Tax Data
    tax_data,
    capital_gains,
    capital_gains_classification,
    asset_classification,
    tax_calculation,
    tax_context,

    # Tax Liability & Income Engines
    tax_liability,
    income_tax_loss_setoff,
    income_tax_aggregation,

    # Module 10
    deductions_exempt_income,

    # Module 11
    final_taxable_income,

    # Module 12
    final_tax_liability,

    # Module 13
    itr_ready_tax_report,
    tax_business_income,
    tax_house_property,
    tax_review,
    finance_diary,
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================
# Vercel may create multiple function instances concurrently. Never run
# create_all() or ad-hoc ALTER TABLE statements during serverless imports.
# Apply schema changes as a controlled, one-off database migration before
# deploying the new release. Local/non-Vercel deployments retain the legacy
# bootstrap behavior for backwards compatibility.
if os.getenv("VERCEL") != "1":
    
    Base.metadata.create_all(
        bind=engine
    )
    
    def _apply_account_credit_limit_migration():
        """Add account credit fields and loan-account linking to existing databases."""
        inspector = inspect(engine)
        with engine.begin() as connection:
            if inspector.has_table("accounts"):
                account_columns = {column["name"] for column in inspector.get_columns("accounts")}
                if "credit_limit" not in account_columns:
                    connection.execute(text("ALTER TABLE accounts ADD COLUMN credit_limit NUMERIC(18, 2)"))
            if inspector.has_table("loans"):
                loan_columns = {column["name"] for column in inspector.get_columns("loans")}
                if "linked_account_id" not in loan_columns:
                    connection.execute(text("ALTER TABLE loans ADD COLUMN linked_account_id INTEGER"))
                if engine.dialect.name == "postgresql":
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_loans_linked_account_id ON loans (linked_account_id)"))
    
    _apply_account_credit_limit_migration()
    
    
    def _apply_account_logical_delete_migration():
        """Add an account tombstone flag without deleting linked ledger rows."""
        inspector = inspect(engine)
        if not inspector.has_table("accounts"):
            return
        columns = {column["name"] for column in inspector.get_columns("accounts")}
        if "is_deleted" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE accounts ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE")
                )
    
    
    _apply_account_logical_delete_migration()
    
    
    def _apply_account_details_migration():
        """Add optional bank and broker identity fields to existing account rows."""
        inspector = inspect(engine)
        if not inspector.has_table("accounts"):
            return
        columns = {column["name"] for column in inspector.get_columns("accounts")}
        definitions = {
            "ifsc_code": "VARCHAR(20)",
            "nominee_name": "VARCHAR(150)",
            "bo_id": "VARCHAR(100)",
            "linked_mobile_number": "VARCHAR(25)",
            "linked_email": "VARCHAR(255)",
            "is_deleted": "BOOLEAN NOT NULL DEFAULT FALSE",
        }
        with engine.begin() as connection:
            for column_name, sql_type in definitions.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE accounts ADD COLUMN {column_name} {sql_type}"))
    
    
    _apply_account_details_migration()
    
    
    def _apply_user_phone_number_migration():
        """Add the optional unique phone number column to existing user tables."""
        table_name = "users"
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        with engine.begin() as connection:
            if "phone_number" not in existing_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(25)"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_number ON users (phone_number)"))
    
    
    _apply_user_phone_number_migration()
    
    
    
    
    def _apply_hra_eligibility_schema_migration():
        """Add HRA eligibility columns to existing databases safely.
    
        SQLAlchemy create_all() creates missing tables but does not add columns to
        existing tables. This idempotent startup migration repairs databases that
        predate the HRA eligibility fields without modifying existing records.
        """
        table_name = "tax_salary_income_records"
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            # The model/table may be unavailable in a minimal test configuration.
            return
    
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing_columns = {
            "accommodation_owned_by_taxpayer": "BOOLEAN NOT NULL DEFAULT FALSE",
            "rent_actually_paid": "BOOLEAN NOT NULL DEFAULT FALSE",
        }
    
        with engine.begin() as connection:
            for column_name, column_definition in missing_columns.items():
                if column_name not in existing_columns:
                    # Names and definitions are fixed constants, not user input.
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_definition}"
                        )
                    )
    
    
    _apply_hra_eligibility_schema_migration()
    
    
    def _apply_receivable_payable_schema_migration():
        """Add receivable/payable tracking fields to existing transactions safely."""
        table_name = "transactions"
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        additions = {
            "party_name": "VARCHAR(150)",
            "due_date": "DATE",
            "settled_amount": "NUMERIC(18, 2) NOT NULL DEFAULT 0",
            "status": "VARCHAR(20) NOT NULL DEFAULT 'open'",
            "settles_transaction_id": "INTEGER",
        }
        with engine.begin() as connection:
            for column_name, column_definition in additions.items():
                if column_name not in existing_columns:
                    connection.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
                    ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_transactions_settles_transaction_id "
                "ON transactions (settles_transaction_id)"
            ))
    
    
    _apply_receivable_payable_schema_migration()
    
    
    def _apply_tax_business_source_link_migration():
        """Add an optional explicit Money-transaction link to tax business records."""
        table_name = "tax_business_income_records"
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        with engine.begin() as connection:
            if "source_transaction_id" not in existing_columns:
                connection.execute(text(
                    f"ALTER TABLE {table_name} ADD COLUMN source_transaction_id INTEGER"
                ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_tax_business_income_records_source_transaction_id "
                "ON tax_business_income_records (source_transaction_id)"
            ))
    
    
    _apply_tax_business_source_link_migration()
    

# ============================================================
# CREATE APPLICATION
# ============================================================

# Interactive API docs list every endpoint to anyone who can reach the server.
# They are off unless ENABLE_API_DOCS=1 is set (for example on a dev machine).
APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
_docs_enabled = APP_ENV in {"development", "local", "test"} and os.getenv("ENABLE_API_DOCS", "").strip() == "1"

app = FastAPI(
    title="Financial OS API",
    version="1.0.0",
    description="Backend API for Financial OS",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)


# ============================================================
# PLAIN-LANGUAGE SERVER ERRORS
# Unexpected failures return a readable reason plus a reference code.
# The full technical error (never shown to users) is written to the
# server log under the same reference so it can be found quickly.
# ============================================================

import logging
import socket
import uuid

from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from fastapi import Request
from fastapi.responses import JSONResponse

_error_logger = logging.getLogger("financial_os.errors")


def _plain_reason(exc: Exception) -> str:
    if isinstance(exc, (DBAPIError, SQLAlchemyError)):
        return "The database had a problem saving or reading your data."
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "A connected service took too long to respond."
    if isinstance(exc, (ConnectionError, OSError)):
        return "The server could not reach a connected service."
    return "An unexpected problem occurred on the server."


# Registered before CORSMiddleware so the CORS layer wraps this response too;
# otherwise the browser hides the message behind a generic "Failed to fetch".
@app.middleware("http")
async def plain_language_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        reference = uuid.uuid4().hex[:8].upper()
        _error_logger.error(
            "Unhandled error ref=%s %s %s", reference, request.method, request.url.path, exc_info=exc
        )
        return JSONResponse(
            status_code=500,
            content={"detail": f"{_plain_reason(exc)} Please try again. If it keeps happening, quote reference {reference}."},
        )



# ============================================================
# CORS
# Set CORS_ALLOWED_ORIGINS in the backend environment to a
# comma-separated list of exact trusted frontend origins, e.g.
# https://your-frontend.onrender.com
# Do not use "*" with credentialed requests in production.
# ============================================================


_raw_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
CORS_ALLOWED_ORIGINS = [origin.strip().rstrip("/") for origin in _raw_cors_origins.split(",") if origin.strip()]
CORS_ALLOWED_ORIGINS.append("https://main.d1qcu4l3dz9f9e.amplifyapp.com")
if APP_ENV in {"development", "local", "test"}:
    CORS_ALLOWED_ORIGINS.extend(["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"])
CORS_ALLOWED_ORIGINS = list(dict.fromkeys(CORS_ALLOWED_ORIGINS))
if "*" in CORS_ALLOWED_ORIGINS:
    raise RuntimeError("CORS_ALLOWED_ORIGINS must contain exact origins; wildcard origins are forbidden.")


# API RATE LIMITING — process-local first layer; add AWS WAF/shared proxy limits for multi-worker deployments.
_RATE_LIMIT_DEFAULT_MAX = 120
_RATE_LIMIT_DEFAULT_WINDOW = 60
_RATE_LIMIT_MAX_KEYS = 50000
_rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = threading.Lock()
_RATE_LIMIT_POLICIES = {"/api/auth/login": (10, 60), "/api/auth/register": (5, 3600)}
_RATE_LIMIT_PREFIX_POLICIES = (("/api/ai/", (20, 600)), ("/api/broker-orders", (10, 60)))


def _rate_limit_client_ip(request: Request) -> str:
    try:
        trusted_proxy_count = max(0, int(os.getenv("TRUSTED_PROXY_COUNT", "0") or 0))
    except ValueError:
        trusted_proxy_count = 0
    forwarded = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
    # X-Forwarded-For is ordered client -> nearest proxy. Ignore the
    # configured trusted proxy hops from the right before selecting the
    # last address supplied before that trusted chain.
    if trusted_proxy_count and len(forwarded) > trusted_proxy_count:
        return forwarded[-(trusted_proxy_count + 1)]
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def enforce_api_rate_limits(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/api/") or request.method == "OPTIONS":
        return await call_next(request)
    scope = "api"
    limit, window = _RATE_LIMIT_DEFAULT_MAX, _RATE_LIMIT_DEFAULT_WINDOW
    if path in _RATE_LIMIT_POLICIES:
        scope = path
        limit, window = _RATE_LIMIT_POLICIES[path]
    else:
        for prefix, policy in _RATE_LIMIT_PREFIX_POLICIES:
            if path.startswith(prefix):
                scope = prefix
                limit, window = policy
                break
    now = time.monotonic()
    bucket_key = f"{_rate_limit_client_ip(request)}:{scope}"
    with _rate_limit_lock:
        if len(_rate_limit_buckets) >= _RATE_LIMIT_MAX_KEYS:
            for key, events in list(_rate_limit_buckets.items()):
                if not events or now - events[-1] >= 3600:
                    _rate_limit_buckets.pop(key, None)
        events = _rate_limit_buckets[bucket_key]
        while events and now - events[0] >= window:
            events.popleft()
        if len(events) >= limit:
            retry_after = max(1, int(window - (now - events[0])))
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please wait before trying again."}, headers={"Retry-After": str(retry_after), "Cache-Control": "no-store"})
        events.append(now)
    return await call_next(request)


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("Content-Security-Policy", "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Financial OS API",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    return {"status": "healthy"}


# ============================================================
# API ROUTES
# ============================================================

# ------------------------------------------------------------
# CORE FINANCIAL OS
# ------------------------------------------------------------
# Business/data routers are private by default; auth registration/login remain public.
def _include_private_router(router):
    app.include_router(router, dependencies=[Depends(auth.get_current_user)])

app.include_router(auth.router)
_include_private_router(profile.router)
_include_private_router(ai_assistant.router)
_include_private_router(broker_orders.router)
_include_private_router(broker_reconciliation.router)

_include_private_router(users.router)
_include_private_router(loans.router)
_include_private_router(accounts.router)
_include_private_router(chart_of_accounts.router)
_include_private_router(ledger.router)
_include_private_router(categories.router)
_include_private_router(transactions.router)
_include_private_router(dashboard.router)
_include_private_router(budgets.router)
_include_private_router(bills.router)
_include_private_router(investments.router)
_include_private_router(market.router)
_include_private_router(market_overview.router)
_include_private_router(market_flow.router)
_include_private_router(options_hub.router)
_include_private_router(market_quote.router)
_include_private_router(market_search.router)
_include_private_router(mutual_fund_search.router)
_include_private_router(market_history.router)
_include_private_router(market_charts.router)
_include_private_router(watchlist.router)
_include_private_router(market_movers.router)
_include_private_router(market_indices.router)
_include_private_router(investment_transactions.router)
_include_private_router(holdings.router)
_include_private_router(investment_pnl.router)
_include_private_router(finance_diary.router)


# ------------------------------------------------------------
# FINANCIAL DATA & ANALYTICS
# ------------------------------------------------------------

_include_private_router(financial_summary.router)
_include_private_router(financial_analytics.router)
_include_private_router(financial_plan.router)
_include_private_router(goals.router)


# ------------------------------------------------------------
# TAX DATA & CAPITAL GAINS
# ------------------------------------------------------------

_include_private_router(tax_data.router)
_include_private_router(capital_gains.router)
_include_private_router(capital_gains_classification.router)
_include_private_router(asset_classification.router)
_include_private_router(tax_calculation.router)
_include_private_router(tax_context.router)


# ------------------------------------------------------------
# TAX LIABILITY & INCOME ENGINES
# ------------------------------------------------------------

_include_private_router(tax_liability.router)
_include_private_router(income_tax_loss_setoff.router)
_include_private_router(income_tax_aggregation.router)


# ------------------------------------------------------------
# MODULE 10
# DEDUCTIONS & EXEMPT INCOME
# ------------------------------------------------------------

_include_private_router(
    deductions_exempt_income.router
)

# ------------------------------------------------------------
# MODULE 11
# FINAL TAXABLE INCOME
# ------------------------------------------------------------
_include_private_router(
    final_taxable_income.router
)

# ------------------------------------------------------------
# MODULE 12
# FINAL TAXABLE LIABILITY
# ------------------------------------------------------------
_include_private_router(final_tax_liability.router)


# ------------------------------------------------------------
# MODULE 13
# ITR READY TAX REPORT
# ------------------------------------------------------------
_include_private_router(itr_ready_tax_report.router)
_include_private_router(tax_business_income.router)
_include_private_router(tax_house_property.router)
_include_private_router(tax_review.router)
