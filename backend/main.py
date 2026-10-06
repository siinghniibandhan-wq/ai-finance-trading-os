import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import Base, engine
from database import models

from backend.routes.accounts import router as accounts_router
from backend.routes.categories import router as categories_router
from backend.routes.transactions import router as transactions_router
from backend.routes.assets import router as assets_router
from backend.routes.liabilities import router as liabilities_router
from backend.routes.dashboard import router as dashboard_router

# =====================================================
# BUDGET ROUTES
# =====================================================

from backend import budgets

# =====================================================
# BILLS & SUBSCRIPTIONS ROUTES
# =====================================================

from backend import bills

# =====================================================
# STATEMENTS / IMPORT ROUTES
# =====================================================

from backend import statements

# =====================================================
# WEALTH - ASSETS ROUTES
# =====================================================

from backend import assets

app = FastAPI(
    title="AI Finance Trading OS",
    description="AI-powered personal finance, wealth management, investment and trading platform.",
    version="1.0.0",
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
# DATABASE INITIALIZATION
# ============================================================

if engine is not None:
    Base.metadata.create_all(bind=engine)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(assets_router)
app.include_router(liabilities_router)
app.include_router(dashboard_router)
# =====================================================
# BUDGET ROUTES
# =====================================================

app.include_router(budgets.router)

# =====================================================
# BILLS & SUBSCRIPTIONS ROUTES
# =====================================================

app.include_router(bills.router)

# =====================================================
# STATEMENTS / IMPORT ROUTES
# =====================================================

app.include_router(statements.router)

# =====================================================
# WEALTH - ASSETS ROUTES
# =====================================================

app.include_router(assets.router)

# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "name": "AI Finance Trading OS",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database_configured": bool(os.getenv("DATABASE_URL")),
    }


@app.get("/api")
def api_root():
    return {
        "message": "AI Finance Trading OS API",
        "status": "online",
    }
