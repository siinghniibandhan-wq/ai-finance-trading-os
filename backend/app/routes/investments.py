# ============================================================
# FINANCIAL OS
# INVESTMENTS API
# ============================================================
#
# Portfolio flow:
#
# Portfolio
#     ↓
# Investments API
#     ↓
# Market Price Service
#     ↓
# AWS m.Stock Gateway
#     ↓
# m.Stock
#     ↓
# NSE / BSE market price
#
# IMPORTANT:
# - m.Stock API credentials are NOT stored here.
# - TOTP is NOT stored here.
# - Access token is NOT stored here.
# - Authentication remains inside the AWS m.Stock Gateway.
#
# Supported automatic market refresh:
# - Stocks
# - ETFs
#
# Other investment types continue to use their stored current_price.
# ============================================================


from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.services.market_price import (
    MarketPriceError,
    get_market_price,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/investments",
    tags=["Investments"],
)


# ============================================================
# DATABASE TABLE
# ============================================================

def ensure_investments_table(db: Session):
    """
    Create the investments table if it does not exist.

    Existing databases are preserved.
    """

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS investments (

                id SERIAL PRIMARY KEY,

                user_id INTEGER NOT NULL,

                name VARCHAR(255) NOT NULL,

                investment_type VARCHAR(50) NOT NULL,

                symbol VARCHAR(100),

                quantity NUMERIC(18,6) NOT NULL,

                buy_price NUMERIC(18,4) NOT NULL,

                current_price NUMERIC(18,4),

                buy_date DATE NOT NULL,

                broker VARCHAR(255),

                fees NUMERIC(18,2) DEFAULT 0,

                notes TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    # --------------------------------------------------------
    # Safety migration for existing databases
    # --------------------------------------------------------

    db.execute(
        text(
            """
            ALTER TABLE investments
            ADD COLUMN IF NOT EXISTS current_price
            NUMERIC(18,4)
            """
        )
    )

    db.commit()


# ============================================================
# PYDANTIC SCHEMA
# ============================================================

class InvestmentCreate(BaseModel):

    user_id: int

    name: str = Field(
        min_length=1,
        max_length=255
    )

    investment_type: str = Field(
        min_length=1,
        max_length=50
    )

    symbol: str | None = None

    quantity: Decimal = Field(
        gt=0
    )

    buy_price: Decimal = Field(
        gt=0
    )

    current_price: Decimal | None = None

    buy_date: date

    broker: str = Field(min_length=1, max_length=255)

    fees: Decimal = Field(
        default=Decimal("0"),
        ge=0
    )

    notes: str | None = None


# ============================================================
# HELPER — SERIALIZE INVESTMENT
# ============================================================

def investment_response(row):
    """
    Convert database row into a portfolio response.

    Also calculates:
    - invested_value
    - current_value
    - gain_loss
    - return_percent
    """

    data = dict(row._mapping)

    quantity = Decimal(
        str(data.get("quantity") or 0)
    )

    buy_price = Decimal(
        str(data.get("buy_price") or 0)
    )

    current_price = data.get("current_price")

    if current_price is None:
        current_price = buy_price
    else:
        current_price = Decimal(
            str(current_price)
        )

    invested_value = quantity * buy_price

    current_value = quantity * current_price

    gain_loss = (
        current_value - invested_value
    )

    if invested_value > 0:

        return_percent = (
            gain_loss / invested_value
        ) * Decimal("100")

    else:

        return_percent = Decimal("0")

    data["invested_value"] = invested_value

    data["current_value"] = current_value

    data["gain_loss"] = gain_loss

    data["return_percent"] = return_percent

    return data


# ============================================================
# HELPER — MARKET ELIGIBLE INVESTMENT
# ============================================================

def is_market_investment(
    investment_type: str | None,
) -> bool:
    """
    Determine whether an investment should use
    the m.Stock equity market-price API.
    """

    if not investment_type:
        return False

    normalized = (
        investment_type
        .strip()
        .lower()
    )

    return normalized in {
        "stock",
        "stocks",
        "etf",
    }


# ============================================================
# LIST INVESTMENTS
# ============================================================

@router.get("/")
def list_investments(
    user_id: int,
    db: Session = Depends(get_db),
):

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at

            FROM investments

            WHERE user_id = :user_id

            ORDER BY id DESC
            """
        ),
        {
            "user_id": user_id
        },
    )

    return [
        investment_response(row)
        for row in result
    ]


# ============================================================
# CREATE INVESTMENT
# ============================================================

@router.post("/", status_code=201)
def create_investment(
    data: InvestmentCreate,
    db: Session = Depends(get_db),
):

    # Mandatory broker validation; reject whitespace-only values.
    if not data.broker.strip():
        raise HTTPException(status_code=422, detail="Broker is required.")

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            INSERT INTO investments (

                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes

            )

            VALUES (

                :user_id,
                :name,
                :investment_type,
                :symbol,
                :quantity,
                :buy_price,
                :current_price,
                :buy_date,
                :broker,
                :fees,
                :notes

            )

            RETURNING

                id,
                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at
            """
        ),
        {
            "user_id": data.user_id,

            "name": data.name.strip(),

            "investment_type":
                data.investment_type.strip(),

            "symbol":
                data.symbol.strip().upper()
                if data.symbol
                else None,

            "quantity": data.quantity,

            "buy_price": data.buy_price,

            "current_price":
                data.current_price,

            "buy_date": data.buy_date,

            "broker":
                data.broker.strip()
                if data.broker
                else None,

            "fees": data.fees,

            "notes": data.notes,
        },
    )

    db.commit()

    investment = result.first()

    if not investment:

        raise HTTPException(
            status_code=500,
            detail="Unable to create investment.",
        )

    return investment_response(
        investment
    )


# ============================================================
# REFRESH ALL MARKET PRICES
# ============================================================
#
# Example:
#
# POST
# /api/investments/refresh?user_id=1
#
# This refreshes Stocks and ETFs only.
#
# ============================================================

@router.post("/refresh")
def refresh_market_prices(
    user_id: int,
    db: Session = Depends(get_db),
):

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at

            FROM investments

            WHERE user_id = :user_id

            ORDER BY id ASC
            """
        ),
        {
            "user_id": user_id
        },
    )

    investments = list(result)

    refreshed = []

    skipped = []

    failed = []

    # --------------------------------------------------------
    # Process each investment
    # --------------------------------------------------------

    for row in investments:

        investment = dict(
            row._mapping
        )

        investment_type = (
            investment.get(
                "investment_type"
            )
        )

        symbol = investment.get(
            "symbol"
        )

        # ----------------------------------------------------
        # Skip unsupported investment types
        # ----------------------------------------------------

        if not is_market_investment(
            investment_type
        ):

            skipped.append(
                {
                    "id":
                        investment["id"],

                    "name":
                        investment["name"],

                    "reason":
                        "Market refresh is currently "
                        "supported for Stocks and ETFs only.",
                }
            )

            continue

        # ----------------------------------------------------
        # Skip missing symbols
        # ----------------------------------------------------

        if not symbol:

            failed.append(
                {
                    "id":
                        investment["id"],

                    "name":
                        investment["name"],

                    "symbol":
                        None,

                    "error":
                        "Investment symbol is missing.",
                }
            )

            continue

        # ----------------------------------------------------
        # Get latest market price
        # ----------------------------------------------------

        try:

            market_price = get_market_price(
                symbol
            )

        except MarketPriceError as exc:

            failed.append(
                {
                    "id":
                        investment["id"],

                    "name":
                        investment["name"],

                    "symbol":
                        symbol,

                    "error":
                        str(exc),
                }
            )

            continue

        # ----------------------------------------------------
        # Save current market price
        # ----------------------------------------------------

        db.execute(
            text(
                """
                UPDATE investments

                SET
                    current_price = :current_price,
                    updated_at = CURRENT_TIMESTAMP

                WHERE
                    id = :investment_id
                    AND user_id = :user_id
                """
            ),
            {
                "current_price":
                    market_price,

                "investment_id":
                    investment["id"],

                "user_id":
                    user_id,
            },
        )

        # ----------------------------------------------------
        # Calculate portfolio values
        # ----------------------------------------------------

        quantity = Decimal(
            str(
                investment.get(
                    "quantity"
                ) or 0
            )
        )

        buy_price = Decimal(
            str(
                investment.get(
                    "buy_price"
                ) or 0
            )
        )

        invested_value = (
            quantity * buy_price
        )

        current_value = (
            quantity * market_price
        )

        gain_loss = (
            current_value -
            invested_value
        )

        if invested_value > 0:

            return_percent = (
                gain_loss /
                invested_value
            ) * Decimal("100")

        else:

            return_percent = Decimal("0")

        refreshed.append(
            {
                "id":
                    investment["id"],

                "name":
                    investment["name"],

                "symbol":
                    symbol,

                "previous_price":
                    investment.get(
                        "current_price"
                    ),

                "current_price":
                    market_price,

                "quantity":
                    quantity,

                "invested_value":
                    invested_value,

                "current_value":
                    current_value,

                "gain_loss":
                    gain_loss,

                "return_percent":
                    return_percent,
            }
        )

    # --------------------------------------------------------
    # Commit all updated prices
    # --------------------------------------------------------

    db.commit()

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "status": "success",

        "message":
            "Market prices refreshed.",

        "user_id":
            user_id,

        "refreshed":
            refreshed,

        "refreshed_count":
            len(refreshed),

        "skipped":
            skipped,

        "skipped_count":
            len(skipped),

        "failed":
            failed,

        "failed_count":
            len(failed),
    }


# ============================================================
# REFRESH SINGLE INVESTMENT
# ============================================================
#
# Example:
#
# POST
# /api/investments/1/refresh
#
# ============================================================

@router.post("/{investment_id}/refresh")
def refresh_single_investment(
    investment_id: int,
    db: Session = Depends(get_db),
):

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at

            FROM investments

            WHERE id = :investment_id
            """
        ),
        {
            "investment_id":
                investment_id
        },
    )

    row = result.first()

    if not row:

        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    investment = dict(
        row._mapping
    )

    if not is_market_investment(
        investment.get(
            "investment_type"
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Market price refresh is currently "
                "supported for Stocks and ETFs only."
            ),
        )

    symbol = investment.get(
        "symbol"
    )

    if not symbol:

        raise HTTPException(
            status_code=400,
            detail=(
                "Investment symbol is missing."
            ),
        )

    # --------------------------------------------------------
    # Get market price
    # --------------------------------------------------------

    try:

        market_price = get_market_price(
            symbol
        )

    except MarketPriceError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # --------------------------------------------------------
    # Save market price
    # --------------------------------------------------------

    db.execute(
        text(
            """
            UPDATE investments

            SET
                current_price = :current_price,
                updated_at = CURRENT_TIMESTAMP

            WHERE
                id = :investment_id
            """
        ),
        {
            "current_price":
                market_price,

            "investment_id":
                investment_id,
        },
    )

    db.commit()

    # --------------------------------------------------------
    # Return updated investment
    # --------------------------------------------------------

    updated_result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at

            FROM investments

            WHERE id = :investment_id
            """
        ),
        {
            "investment_id":
                investment_id
        },
    )

    updated = updated_result.first()

    return investment_response(
        updated
    )


# ============================================================
# GET SINGLE INVESTMENT
# ============================================================

@router.get("/{investment_id}")
def get_investment(
    investment_id: int,
    db: Session = Depends(get_db),
):

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at

            FROM investments

            WHERE id = :investment_id
            """
        ),
        {
            "investment_id":
                investment_id
        },
    )

    investment = result.first()

    if not investment:

        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    return investment_response(
        investment
    )


# ============================================================
# UPDATE INVESTMENT
# ============================================================

@router.put("/{investment_id}")
def update_investment(
    investment_id: int,
    data: InvestmentCreate,
    db: Session = Depends(get_db),
):

    # Existing records may be incomplete, but an edit must supply a valid broker.
    if not data.broker.strip():
        raise HTTPException(status_code=422, detail="Broker is required.")

    ensure_investments_table(db)

    # --------------------------------------------------------
    # Check investment exists
    # --------------------------------------------------------

    existing = db.execute(
        text(
            """
            SELECT id
            FROM investments
            WHERE id = :investment_id
            """
        ),
        {
            "investment_id":
                investment_id
        },
    ).first()

    if not existing:

        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    # --------------------------------------------------------
    # Update investment
    # --------------------------------------------------------

    result = db.execute(
        text(
            """
            UPDATE investments

            SET

                user_id = :user_id,

                name = :name,

                investment_type =
                    :investment_type,

                symbol = :symbol,

                quantity = :quantity,

                buy_price = :buy_price,

                current_price =
                    :current_price,

                buy_date = :buy_date,

                broker = :broker,

                fees = :fees,

                notes = :notes,

                updated_at =
                    CURRENT_TIMESTAMP

            WHERE
                id = :investment_id

            RETURNING

                id,
                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at
            """
        ),
        {
            "investment_id":
                investment_id,

            "user_id":
                data.user_id,

            "name":
                data.name.strip(),

            "investment_type":
                data.investment_type.strip(),

            "symbol":
                data.symbol.strip().upper()
                if data.symbol
                else None,

            "quantity":
                data.quantity,

            "buy_price":
                data.buy_price,

            "current_price":
                data.current_price,

            "buy_date":
                data.buy_date,

            "broker":
                data.broker.strip()
                if data.broker
                else None,

            "fees":
                data.fees,

            "notes":
                data.notes,
        },
    )

    db.commit()

    investment = result.first()

    if not investment:

        raise HTTPException(
            status_code=500,
            detail="Unable to update investment.",
        )

    return investment_response(
        investment
    )


# ============================================================
# DELETE INVESTMENT
# ============================================================

@router.delete("/{investment_id}")
def delete_investment(
    investment_id: int,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Safely remove one investment record, never an entire instrument.

    Records with linked BUY/SELL transactions are protected so their
    transaction ledger and capital-gains history cannot be orphaned.
    """
    ensure_investments_table(db)

    # Locate exactly one record by its unique investment ID. When user_id
    # is supplied by the frontend, also scope the operation to that user.
    where_sql = "id = :investment_id"
    params = {"investment_id": investment_id}
    if user_id is not None:
        where_sql += " AND user_id = :user_id"
        params["user_id"] = user_id

    investment = db.execute(
        text(f"SELECT id, user_id, name FROM investments WHERE {where_sql}"),
        params,
    ).first()

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    # Only check for linked transactions if that ledger table exists.
    transaction_table_exists = db.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                  AND table_name = 'investment_transactions'
            )
        """)
    ).scalar()

    if transaction_table_exists:
        linked_transaction = db.execute(
            text("""
                SELECT id
                FROM investment_transactions
                WHERE user_id = :user_id
                  AND investment_id = :investment_id
                LIMIT 1
            """),
            {
                "user_id": investment.user_id,
                "investment_id": investment_id,
            },
        ).first()

        if linked_transaction:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This investment has linked BUY/SELL transaction history. "
                    "It was not deleted to protect your transaction and tax records."
                ),
            )

    # Delete only this individual row, never rows matched by name or symbol.
    result = db.execute(
        text("DELETE FROM investments WHERE id = :investment_id RETURNING id"),
        {"investment_id": investment_id},
    )
    deleted = result.first()
    if not deleted:
        db.rollback()
        raise HTTPException(status_code=404, detail="Investment not found.")

    db.commit()
    return {"status": "deleted", "investment_id": investment_id}
