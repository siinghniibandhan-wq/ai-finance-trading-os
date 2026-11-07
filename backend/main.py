"""Vercel Services entrypoint for the existing FastAPI application.

The application and all route modules remain in app.main; this shim only
exposes the existing ASGI app from the backend service root.
"""
from app.main import app

__all__ = ["app"]
