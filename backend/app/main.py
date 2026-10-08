# ============================================================
# FINANCIAL OS
# FASTAPI APPLICATION
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine

# Import models before create_all().
from app import models


# ============================================================
# IMPORT API ROUTES
# ============================================================

from app.routes import (
    users,
    accounts,
    categories,
    transactions,
    dashboard,
    budgets,
    bills,
    investments,
    market,
    market_overview,
    investment_transactions,
    holdings,
    investment_pnl,

    # Financial Data & Analytics
    financial_summary,
    financial_analytics,
    financial_plan,

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
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


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
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(budgets.router)
app.include_router(bills.router)
app.include_router(investments.router)
app.include_router(market.router)
app.include_router(market_overview.router)
app.include_router(investment_transactions.router)
app.include_router(holdings.router)
app.include_router(investment_pnl.router)


# ------------------------------------------------------------
# FINANCIAL DATA & ANALYTICS
# ------------------------------------------------------------

app.include_router(financial_summary.router)
app.include_router(financial_analytics.router)
app.include_router(financial_plan.router)


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
