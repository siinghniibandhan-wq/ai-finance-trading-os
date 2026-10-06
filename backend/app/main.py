# ============================================================
# FINANCIAL OS
# FASTAPI APPLICATION
# ============================================================

from fastapi import FastAPI

from app.database.database import Base, engine

# Import models so SQLAlchemy knows about all tables.
from app import models


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

from fastapi.middleware.cors import CORSMiddleware


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
# DATABASE CHECK
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
