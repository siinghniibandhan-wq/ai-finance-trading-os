# ============================================================
# FINANCIAL OS
# INVESTMENTS API
# ============================================================

from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db


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

# ============================================================
# CURRENT PRICE + PRICE TRACKING FIELDS
# ============================================================

db.execute(
    text(
        """
        ALTER TABLE investments
        ADD COLUMN IF NOT EXISTS current_price NUMERIC(18,4)
        """
    )
)

db.execute(
    text(
        """
        ALTER TABLE investments
        ADD COLUMN IF NOT EXISTS price_source VARCHAR(20)
        DEFAULT 'Manual'
        """
    )
)

db.execute(
    text(
        """
        ALTER TABLE investments
        ADD COLUMN IF NOT EXISTS price_updated_at TIMESTAMP
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
    
    price_source: str | None = "Manual"

    price_updated_at: datetime | None = None
    
    buy_date: date

    broker: str | None = None

    fees: Decimal = Field(
        default=Decimal("0"),
        ge=0
    )

    notes: str | None = None


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
                price_source,
                price_updated_at,
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
        dict(row._mapping)
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
                data.symbol.strip()
                if data.symbol
                else None,
            "quantity": data.quantity,
            "buy_price": data.buy_price,
            "current_price": data.current_price,
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

    return dict(investment._mapping)


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
            "investment_id": investment_id
        },
    )

    investment = result.first()

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    return dict(investment._mapping)


# ============================================================
# UPDATE INVESTMENT
# ============================================================

@router.put("/{investment_id}")
def update_investment(
    investment_id: int,
    data: InvestmentCreate,
    db: Session = Depends(get_db),
):

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            UPDATE investments
            SET
                name = :name,
                investment_type = :investment_type,
                symbol = :symbol,
                quantity = :quantity,
                buy_price = :buy_price,
                current_price = :current_price,
                buy_date = :buy_date,
                broker = :broker,
                fees = :fees,
                notes = :notes,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :investment_id
            AND user_id = :user_id
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
            "investment_id": investment_id,
            "user_id": data.user_id,
            "name": data.name.strip(),
            "investment_type": data.investment_type.strip(),
            "symbol": data.symbol.strip()
                if data.symbol
                else None,
            "quantity": data.quantity,
            "buy_price": data.buy_price,
            "current_price": data.current_price,
            "buy_date": data.buy_date,
            "broker": data.broker.strip()
                if data.broker
                else None,
            "fees": data.fees,
            "notes": data.notes,
        },
    )

    investment = result.first()

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    db.commit()

    return dict(investment._mapping)

# ============================================================
# DELETE INVESTMENT
# ============================================================

@router.delete("/{investment_id}")
def delete_investment(
    investment_id: int,
    db: Session = Depends(get_db),
):

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            DELETE FROM investments
            WHERE id = :investment_id
            RETURNING id
            """
        ),
        {
            "investment_id": investment_id
        },
    )

    deleted = result.first()

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    db.commit()

    return {
        "status": "deleted",
        "investment_id": investment_id,
  }
