"""
Financial OS — Watchlist Engine v1.0

Purpose:
- Store a user's market watchlist.
- Add market instruments to a watchlist.
- List watchlist instruments.
- Remove instruments from a watchlist.
- Keep watchlist data separate from investment holdings.
- Read/write only to the watchlist table.
- No changes to investments or transactions.
"""


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User
from app.routes.auth import get_current_user
from app.routes.ownership import require_matching_user_id


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/watchlist",
    tags=["Watchlist"],
)


# ============================================================
# DATABASE TABLE
# ============================================================

def ensure_watchlist_table(db: Session):
    """
    Create the watchlist table if it does not already exist.

    This keeps Watchlist independent from the existing
    investments and investment_transactions tables.
    """

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS watchlist (
                id SERIAL PRIMARY KEY,

                user_id INTEGER NOT NULL,

                symbol VARCHAR(100) NOT NULL,

                exchange VARCHAR(20) NOT NULL
                    DEFAULT 'NSE',

                name VARCHAR(255),

                instrument_token BIGINT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    # Prevent duplicate symbols for the same user/exchange.
    db.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_watchlist_user_exchange_symbol
            ON watchlist (
                user_id,
                exchange,
                symbol
            )
            """
        )
    )

    db.commit()


# ============================================================
# PYDANTIC SCHEMA
# ============================================================

class WatchlistCreate(BaseModel):

    user_id: int

    symbol: str = Field(
        min_length=1,
        max_length=100,
    )

    exchange: str = Field(
        default="NSE",
        min_length=1,
        max_length=20,
    )

    name: str | None = Field(
        default=None,
        max_length=255,
    )

    instrument_token: int | None = None


# ============================================================
# LIST WATCHLIST
# ============================================================

@router.get("/", dependencies=[Depends(require_matching_user_id)])
def list_watchlist(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Return all watchlist instruments for a user.
    """

    ensure_watchlist_table(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                symbol,
                exchange,
                name,
                instrument_token,
                created_at
            FROM watchlist
            WHERE user_id = :user_id
            ORDER BY id DESC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    watchlist = [dict(row._mapping) for row in result]
    return {
        "status": "success",
        "engine": "Watchlist Engine",
        "version": "1.0",
        "read_only": True,
        "user_id": user_id,
        # SELECT rowcount is driver-dependent (often -1); count the fetched rows.
        "count": len(watchlist),
        "watchlist": watchlist,
        "database_write": False,
    }


# ============================================================
# ADD TO WATCHLIST
# ============================================================

@router.post("/", status_code=201)
def add_to_watchlist(
    data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a market instrument to the user's watchlist.
    """

    if data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="The requested user_id does not match the authenticated user.")

    ensure_watchlist_table(db)

    symbol = data.symbol.strip().upper()
    exchange = data.exchange.strip().upper()

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Market symbol is required.",
        )

    if not exchange:
        raise HTTPException(
            status_code=400,
            detail="Exchange is required.",
        )

    # --------------------------------------------------------
    # Prevent duplicates
    # --------------------------------------------------------

    existing = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                symbol,
                exchange,
                name,
                instrument_token,
                created_at
            FROM watchlist
            WHERE user_id = :user_id
              AND exchange = :exchange
              AND symbol = :symbol
            """
        ),
        {
            "user_id": current_user.id,
            "exchange": exchange,
            "symbol": symbol,
        },
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Symbol is already in the watchlist.",
        )

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    try:
        result = db.execute(
            text(
                """
                INSERT INTO watchlist (
                    user_id,
                    symbol,
                    exchange,
                    name,
                    instrument_token
                )
                VALUES (
                    :user_id,
                    :symbol,
                    :exchange,
                    :name,
                    :instrument_token
                )
                RETURNING
                    id,
                    user_id,
                    symbol,
                    exchange,
                    name,
                    instrument_token,
                    created_at
                """
            ),
            {
                "user_id": current_user.id,
                "symbol": symbol,
                "exchange": exchange,
                "name": data.name.strip() if data.name else None,
                "instrument_token": data.instrument_token,
            },
        )
        # A concurrent request may pass the pre-insert SELECT too. The unique
        # index is authoritative; translate its conflict into a stable 409.
        watchlist_item = result.first()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = db.execute(
            text(
                """
                SELECT id FROM watchlist
                WHERE user_id = :user_id AND exchange = :exchange AND symbol = :symbol
                """
            ),
            {"user_id": current_user.id, "exchange": exchange, "symbol": symbol},
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Symbol is already in the watchlist.") from exc
        raise HTTPException(status_code=503, detail="Unable to save watchlist item safely.") from exc

    if not watchlist_item:
        raise HTTPException(
            status_code=500,
            detail="Unable to add instrument to watchlist.",
        )

    return {
        "status": "success",
        "engine": "Watchlist Engine",
        "version": "1.0",
        "action": "added",
        "item": dict(
            watchlist_item._mapping
        ),
        "database_write": True,
    }


# ============================================================
# REMOVE FROM WATCHLIST
# ============================================================

@router.delete("/{watchlist_id}", dependencies=[Depends(require_matching_user_id)])
def remove_from_watchlist(
    watchlist_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Remove one watchlist item belonging to the user.
    """

    ensure_watchlist_table(db)

    result = db.execute(
        text(
            """
            DELETE FROM watchlist
            WHERE id = :watchlist_id
              AND user_id = :user_id
            RETURNING id
            """
        ),
        {
            "watchlist_id": watchlist_id,
            "user_id": user_id,
        },
    )

    deleted = result.first()

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Watchlist item not found.",
        )

    db.commit()

    return {
        "status": "success",
        "engine": "Watchlist Engine",
        "version": "1.0",
        "action": "removed",
        "watchlist_id": watchlist_id,
        "database_write": True,
    }
