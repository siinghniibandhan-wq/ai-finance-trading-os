import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import Base, engine
from database import models


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
