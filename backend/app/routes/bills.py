# =====================================================
# BILLS & SUBSCRIPTIONS API
# AI FINANCE TRADING OS
# =====================================================

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Account, Category


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/api/bills",
    tags=["Bills & Subscriptions"],
)


# =====================================================
# DATABASE TABLE
# =====================================================

def ensure_bills_table(db: Session):
    """
    Create the bills table if it does not already exist.
    This keeps Bills independent from the existing
    transaction/category/account tables.
    """

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS bills (
                id SERIAL PRIMARY KEY,

                name VARCHAR(255) NOT NULL,

                category_id INTEGER NULL,

                account_id INTEGER NULL,

               
