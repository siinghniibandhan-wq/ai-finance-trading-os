# ============================================================
# FINANCIAL OS
# FASTAPI APPLICATION
# ============================================================

from fastapi import FastAPI
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
    vibe_trading,
    users,
    loans,
    accounts,
    categories,
    transactions,
    dashboard,
    budgets,
    bills,
    investments,
    market,
    market_overview,
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
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


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


# ============================================================
# CREATE APPLICATION
# ============================================================

app = FastAPI(
    title="Financial OS API",
    version="1.0.0",
    description="Backend API for Financial OS",
)


# ============================================================
# CORS
# Set CORS_ALLOWED_ORIGINS in the backend environment to a
# comma-separated list of exact trusted frontend origins, e.g.
# https://your-frontend.onrender.com
# Do not use "*" with credentialed requests in production.
# ============================================================

import os

_raw_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
if _raw_cors_origins:
    CORS_ALLOWED_ORIGINS = [
        origin.strip().rstrip("/")
        for origin in _raw_cors_origins.split(",")
        if origin.strip()
    ]
else:
    # Fail closed to local development origins if not configured.
    # Production deployments must explicitly set CORS_ALLOWED_ORIGINS.
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
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
    return {
        "status": "healthy",
        "database": "connected",
    }


# ============================================================
# DATABASE STATUS
# ============================================================

@app.get("/api/database-status")
def database_status():
    return {
        "status": "connected",
        "database": "Financial OS PostgreSQL",
        "tables": [
            "users",
            "accounts",
            "categories",
            "transactions",
        ],
    }


# ============================================================
# API ROUTES
# ============================================================

# ------------------------------------------------------------
# CORE FINANCIAL OS
# ------------------------------------------------------------
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(ai_assistant.router)
app.include_router(vibe_trading.router)

app.include_router(users.router)
app.include_router(loans.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(budgets.router)
app.include_router(bills.router)
app.include_router(investments.router)
app.include_router(market.router)
app.include_router(market_overview.router)
app.include_router(market_quote.router)
app.include_router(market_search.router)
app.include_router(mutual_fund_search.router)
app.include_router(market_history.router)
app.include_router(market_charts.router)
app.include_router(watchlist.router)
app.include_router(market_movers.router)
app.include_router(market_indices.router)
app.include_router(investment_transactions.router)
app.include_router(holdings.router)
app.include_router(investment_pnl.router)


# ------------------------------------------------------------
# FINANCIAL DATA & ANALYTICS
# ------------------------------------------------------------

app.include_router(financial_summary.router)
app.include_router(financial_analytics.router)
app.include_router(financial_plan.router)
app.include_router(goals.router)


# ------------------------------------------------------------
# TAX DATA & CAPITAL GAINS
# ------------------------------------------------------------

app.include_router(tax_data.router)
app.include_router(capital_gains.router)
app.include_router(capital_gains_classification.router)
app.include_router(asset_classification.router)
app.include_router(tax_calculation.router)
app.include_router(tax_context.router)


# ------------------------------------------------------------
# TAX LIABILITY & INCOME ENGINES
# ------------------------------------------------------------

app.include_router(tax_liability.router)
app.include_router(income_tax_loss_setoff.router)
app.include_router(income_tax_aggregation.router)


# ------------------------------------------------------------
# MODULE 10
# DEDUCTIONS & EXEMPT INCOME
# ------------------------------------------------------------

app.include_router(
    deductions_exempt_income.router
)

# ------------------------------------------------------------
# MODULE 11
# FINAL TAXABLE INCOME
# ------------------------------------------------------------
app.include_router(
    final_taxable_income.router
)

# ------------------------------------------------------------
# MODULE 12
# FINAL TAXABLE LIABILITY
# ------------------------------------------------------------
app.include_router(final_tax_liability.router)


# ------------------------------------------------------------
# MODULE 13
# ITR READY TAX REPORT
# ------------------------------------------------------------
app.include_router(itr_ready_tax_report.router)
app.include_router(tax_business_income.router)
