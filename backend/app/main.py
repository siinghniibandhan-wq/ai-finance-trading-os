# ============================================================
# FINANCIAL OS
# FASTAPI APPLICATION
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine

# Import models before create_all().
from app import models

# Import API routes.
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
    investment_transactions,
    holdings,
    investment_pnl,
    financial_summary,
    financial_analytics,
    financial_plan,
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

app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(budgets.router)
app.include_router(bills.router)
app.include_router(investments.router)
app.include_router(market.router)
app.include_router(investment_transactions.router)
app.include_router(holdings.router)
app.include_router(investment_pnl.router)
app.include_router(financial_summary.router)
app.include_router(financial_analytics.router)
app.include_router(financial_plan.router)
