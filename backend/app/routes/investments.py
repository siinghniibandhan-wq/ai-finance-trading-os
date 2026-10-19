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
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Account, InstrumentMaster, User
from app.routes.auth import get_current_user
from app.finance_diary import record_finance_event

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

    db.execute(text("ALTER TABLE investments ADD COLUMN IF NOT EXISTS current_price NUMERIC(18,4)"))
    db.execute(text("ALTER TABLE investments ADD COLUMN IF NOT EXISTS asset_class VARCHAR(80)"))
    db.execute(text("ALTER TABLE investments ADD COLUMN IF NOT EXISTS product_type VARCHAR(80)"))
    db.execute(text("ALTER TABLE investments ADD COLUMN IF NOT EXISTS instrument_id VARCHAR(150)"))
    db.execute(text("ALTER TABLE investments ADD COLUMN IF NOT EXISTS investment_account_id INTEGER"))
    db.execute(text("ALTER TABLE investments ADD COLUMN IF NOT EXISTS instrument_master_id INTEGER"))

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
    asset_class: str | None = None
    product_type: str | None = None
    instrument_id: str | None = None
    investment_account_id: int | None = None
    instrument_master_id: int | None = None
    exchange: str | None = None


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


def build_market_quote_symbol(
    symbol: str,
    exchange: str | None = None,
) -> str:
    """Qualify a quote symbol with its known exchange without guessing listings."""
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise MarketPriceError("Investment symbol is missing.")

    if ":" in cleaned:
        prefix, remainder = cleaned.split(":", 1)
        if prefix in {"NSE", "BSE"} and remainder:
            if exchange and exchange.strip().upper() in {"NSE", "BSE"} and prefix != exchange.strip().upper():
                raise MarketPriceError(
                    f"Investment symbol exchange {prefix} conflicts with instrument exchange {exchange.strip().upper()}."
                )
            return cleaned

    if exchange is None or not exchange.strip():
        # Legacy records without exchange metadata retain their existing symbol behavior.
        return cleaned

    normalized_exchange = exchange.strip().upper()
    if normalized_exchange not in {"NSE", "BSE"}:
        raise MarketPriceError(
            f"Unsupported instrument exchange: {normalized_exchange}."
        )
    return f"{normalized_exchange}:{cleaned}"


# ============================================================
# LIST INVESTMENTS
# ============================================================

@router.get("/")
def list_investments(
    user_id: int | None = None,  # Legacy query parameter is ignored for security.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            SELECT
                investments.id,
                investments.user_id,
                investments.name,
                investments.investment_type,
                investments.symbol,
                (SELECT im.exchange FROM instrument_master im
                 WHERE im.id = investments.instrument_master_id) AS exchange,
                CASE
                    WHEN COALESCE(tx.ledger_count, 0) > 0
                    THEN COALESCE(tx.active_quantity, 0)
                    ELSE investments.quantity
                END AS quantity,

                CASE
                    WHEN COALESCE(tx.buy_quantity, 0) > 0
                    THEN tx.weighted_buy_price
                    ELSE investments.buy_price
                END AS buy_price,

                current_price,
                buy_date,
                broker,
                fees,
                notes,
                asset_class,
                product_type,
                instrument_id,
                investment_account_id,
                instrument_master_id,
                created_at,
                updated_at

            FROM investments

            LEFT JOIN (
                SELECT
                    investment_id,
                    COUNT(*) AS ledger_count,
                    COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) - COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'SELL'
                             THEN quantity ELSE 0 END
                    ), 0) AS active_quantity,
                    COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) AS buy_quantity,
                    CASE WHEN COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) > 0
                    THEN SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity * price + COALESCE(fees, 0) ELSE 0 END
                    ) / SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    )
                    ELSE NULL END AS weighted_buy_price
                FROM investment_transactions
                WHERE user_id = :user_id
                GROUP BY investment_id
            ) tx ON tx.investment_id = investments.id

            WHERE investments.user_id = :user_id

            ORDER BY investments.id DESC
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
    current_user: User = Depends(get_current_user),
):
    # Never trust user_id supplied in the request body.
    user_id = current_user.id

    ensure_investments_table(db)

    # The selected account ID is authoritative; broker names are display-only.
    if not data.investment_account_id:
        raise HTTPException(status_code=409, detail="Select an active Investment / Broker Cash account from Money → Accounts.")
    broker_account = db.query(Account).filter(
        Account.id == data.investment_account_id,
        Account.user_id == user_id,
        Account.account_type == "investment",
        Account.is_active.is_(True),
    ).with_for_update().first()
    if broker_account is None:
        raise HTTPException(status_code=409, detail="Selected account must be an active Investment account owned by the logged-in user.")
    broker_name = (broker_account.institution or broker_account.name).strip()
    purchase_cost = ((data.quantity * data.buy_price) + data.fees).quantize(Decimal("0.01"))
    if Decimal(str(broker_account.balance or 0)) < purchase_cost:
        raise HTTPException(status_code=409, detail=f"Insufficient cash in {broker_account.name}. Transfer funds into this Investment account before buying.")

    normalized_type = data.investment_type.strip().lower()
    if normalized_type in {"stocks", "stock", "etfs", "etf", "equity mutual funds"}:
        asset_class = data.asset_class or "Equity"
    elif normalized_type in {"bonds", "fixed deposits", "debt mutual funds"}:
        asset_class = data.asset_class or "Fixed Income"
    elif normalized_type in {"gold", "silver", "commodities"}:
        asset_class = data.asset_class or "Commodities"
    elif normalized_type in {"crypto", "cryptocurrency", "digital assets"}:
        asset_class = data.asset_class or "Digital Assets"
    else:
        asset_class = data.asset_class or "Other"
    product_type = data.product_type or data.investment_type.strip()
    master = None
    if data.instrument_master_id is not None:
        master = db.query(InstrumentMaster).filter(
            InstrumentMaster.id == data.instrument_master_id
        ).first()
        if master is None:
            raise HTTPException(status_code=422, detail="Selected instrument does not exist.")
        exchange = (master.exchange or data.exchange or "").strip().upper() or None
        symbol = (data.symbol or master.symbol or "").strip().upper() or None
        if data.symbol and master.symbol and data.symbol.strip().upper() != master.symbol.strip().upper():
            raise HTTPException(status_code=422, detail="Symbol does not match the selected instrument.")
        if data.exchange and exchange and data.exchange.strip().upper() != exchange:
            raise HTTPException(status_code=422, detail="Exchange does not match the selected instrument.")
    else:
        exchange = (data.exchange or ("NSE" if data.symbol else "")).strip().upper() or None
        symbol = data.symbol.strip().upper() if data.symbol else None
        if exchange and exchange not in {"NSE", "BSE"}:
            raise HTTPException(status_code=422, detail="Exchange must be NSE or BSE.")
        instrument_id = data.instrument_id or (symbol if symbol else data.name.strip().upper())
        canonical_key = f"{instrument_id}::{exchange or 'UNSPECIFIED'}::{product_type.strip().lower()}"
        master = db.query(InstrumentMaster).filter(InstrumentMaster.canonical_key == canonical_key).first()
        if master is None:
            master = InstrumentMaster(
                canonical_key=canonical_key,
                name=data.name.strip(),
                symbol=symbol,
                exchange=exchange,
                asset_class=asset_class,
                product_type=product_type,
            )
            db.add(master)
            db.flush()
    instrument_id = data.instrument_id or (symbol if symbol else data.name.strip().upper())

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
                notes,
                asset_class,
                product_type,
                instrument_id,
                investment_account_id,
                instrument_master_id

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
                :notes,
                :asset_class,
                :product_type,
                :instrument_id,
                :investment_account_id,
                :instrument_master_id

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
                asset_class,
                product_type,
                instrument_id,
                investment_account_id,
                instrument_master_id,
                created_at,
                updated_at
            """
        ),
        {
            "user_id": user_id,

            "name": data.name.strip(),

            "investment_type":
                data.investment_type.strip(),

            "symbol": symbol,

            "quantity": data.quantity,

            "buy_price": data.buy_price,

            "current_price":
                data.current_price,

            "buy_date": data.buy_date,

            "broker": broker_name,

            "fees": data.fees,
            "notes": data.notes,
            "asset_class": asset_class,
            "product_type": product_type,
            "instrument_id": instrument_id,
            "investment_account_id": broker_account.id,
            "instrument_master_id": master.id,
        },
    )

    # The frontend immediately creates the initial BUY ledger row. Cash is
    # deducted exactly once by /api/investment-transactions/ after that row is
    # validated, avoiding duplicate debits for the same purchase.
    db.commit()

    investment = result.first()

    if not investment:

        raise HTTPException(
            status_code=500,
            detail="Unable to create investment.",
        )

    record_finance_event(db, user_id=user_id, event_type="created", entity_type="investment", entity_id=investment.id, description=f"Investment position created: {data.name.strip()}", snapshot={"id": investment.id, "name": data.name.strip(), "asset_class": asset_class, "product_type": product_type, "instrument_id": instrument_id, "instrument_master_id": master.id, "broker": broker_name, "investment_account_id": broker_account.id, "quantity": data.quantity, "buy_price": data.buy_price, "fees": data.fees, "cash_deduction_handled_by_initial_buy_ledger": True})
    db.commit()
    return investment_response(investment)


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
    user_id: int | None = None,  # Legacy query parameter is ignored for security.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    ensure_investments_table(db)

    result = db.execute(
        text(
            """
            SELECT
                investments.id,
                investments.user_id,
                investments.name,
                investments.investment_type,
                investments.symbol,
                investments.instrument_master_id,
                instrument_master.exchange AS instrument_exchange,
                instrument_master.symbol AS master_symbol,
                CASE
                    WHEN COALESCE(tx.ledger_count, 0) > 0
                    THEN COALESCE(tx.active_quantity, 0)
                    ELSE investments.quantity
                END AS quantity,
                CASE
                    WHEN COALESCE(tx.buy_quantity, 0) > 0
                    THEN tx.weighted_buy_price
                    ELSE investments.buy_price
                END AS buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at

            FROM investments
            LEFT JOIN instrument_master ON instrument_master.id = investments.instrument_master_id
            LEFT JOIN (
                SELECT
                    investment_id,
                    COUNT(*) AS ledger_count,
                    COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) - COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'SELL'
                             THEN quantity ELSE 0 END
                    ), 0) AS active_quantity,
                    COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) AS buy_quantity,
                    CASE WHEN COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) > 0
                    THEN SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity * price + COALESCE(fees, 0) ELSE 0 END
                    ) / SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    )
                    ELSE NULL END AS weighted_buy_price
                FROM investment_transactions
                WHERE user_id = :user_id
                GROUP BY investment_id
            ) tx ON tx.investment_id = investments.id
            WHERE investments.user_id = :user_id

            ORDER BY investments.id ASC
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

        symbol = investment.get("symbol") or investment.get("master_symbol")
        exchange = investment.get("instrument_exchange")

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

            quote_symbol = build_market_quote_symbol(symbol, exchange)
            market_price = get_market_price(quote_symbol)

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
    current_user: User = Depends(get_current_user),
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
                instrument_master_id,
                instrument_master.exchange AS instrument_exchange,
                instrument_master.symbol AS master_symbol,
                CASE
                    WHEN COALESCE(tx.ledger_count, 0) > 0
                    THEN COALESCE(tx.active_quantity, 0)
                    ELSE investments.quantity
                END AS quantity,
                CASE
                    WHEN COALESCE(tx.buy_quantity, 0) > 0
                    THEN tx.weighted_buy_price
                    ELSE investments.buy_price
                END AS buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes,
                created_at,
                updated_at

            FROM investments
            LEFT JOIN instrument_master ON instrument_master.id = investments.instrument_master_id
            LEFT JOIN (
                SELECT
                    investment_id,
                    COUNT(*) AS ledger_count,
                    COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) - COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'SELL'
                             THEN quantity ELSE 0 END
                    ), 0) AS active_quantity,
                    COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) AS buy_quantity,
                    CASE WHEN COALESCE(SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    ), 0) > 0
                    THEN SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity * price + COALESCE(fees, 0) ELSE 0 END
                    ) / SUM(
                        CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                             THEN quantity ELSE 0 END
                    )
                    ELSE NULL END AS weighted_buy_price
                FROM investment_transactions
                WHERE user_id = :user_id
                GROUP BY investment_id
            ) tx ON tx.investment_id = investments.id
            WHERE investments.id = :investment_id AND investments.user_id = :user_id
            """
        ),
        {
            "investment_id": investment_id,
            "user_id": current_user.id
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

    symbol = investment.get("symbol") or investment.get("master_symbol")
    exchange = investment.get("instrument_exchange")

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

        quote_symbol = build_market_quote_symbol(symbol, exchange)
        market_price = get_market_price(quote_symbol)

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
                AND user_id = :user_id
            """
        ),
        {
            "current_price": market_price,
            "investment_id": investment_id,
            "user_id": current_user.id,
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
    current_user: User = Depends(get_current_user),
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

            WHERE id = :investment_id AND user_id = :user_id
            """
        ),
        {
            "investment_id": investment_id,
            "user_id": current_user.id
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
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

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
            SELECT id, investment_type, symbol, buy_date, broker, investment_account_id
            FROM investments
            WHERE id = :investment_id AND user_id = :user_id
            """
        ),
        {
            "investment_id": investment_id,
            "user_id": user_id,
        },
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Investment not found.")

    selected_account_id = data.investment_account_id or existing.investment_account_id
    if not selected_account_id:
        raise HTTPException(status_code=409, detail="Select an active Investment / Broker Cash account to link this position.")
    selected_account = db.query(Account).filter(
        Account.id == selected_account_id,
        Account.user_id == user_id,
        Account.account_type == "investment",
        Account.is_active.is_(True),
    ).with_for_update().first()
    if selected_account is None:
        raise HTTPException(status_code=409, detail="Selected account must be an active Investment account owned by the logged-in user.")
    if existing.investment_account_id is not None and existing.investment_account_id != selected_account_id:
        raise HTTPException(status_code=409, detail="A linked investment cannot be reassigned to another cash account. Keep its original broker-account linkage.")

    # A ledger-backed position is derived from its BUY/SELL history. Do not
    # silently overwrite its quantity/cost basis or change the broker/security
    # identity through the legacy position form; those changes must go through
    # the transaction ledger so history and holdings remain consistent.
    if inspect(db.get_bind()).has_table("investment_transactions"):
        ledger = db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_count,
                COALESCE(SUM(CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                                  THEN quantity ELSE 0 END), 0)
                  - COALESCE(SUM(CASE WHEN status = 'ACTIVE' AND transaction_type = 'SELL'
                                      THEN quantity ELSE 0 END), 0) AS active_quantity,
                COALESCE(SUM(CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                                  THEN quantity ELSE 0 END), 0) AS buy_quantity,
                CASE WHEN COALESCE(SUM(CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                                            THEN quantity ELSE 0 END), 0) > 0
                     THEN SUM(CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                                   THEN quantity * price + COALESCE(fees, 0) ELSE 0 END)
                          / SUM(CASE WHEN status = 'ACTIVE' AND transaction_type = 'BUY'
                                     THEN quantity ELSE 0 END)
                     ELSE NULL END AS weighted_buy_price
            FROM investment_transactions
            WHERE user_id = :user_id AND investment_id = :investment_id
        """), {"user_id": user_id, "investment_id": investment_id}).first()

        if ledger and ledger.active_count:
            ledger_quantity = Decimal(str(ledger.active_quantity or 0))
            ledger_buy_price = Decimal(str(ledger.weighted_buy_price or 0))
            quantity_changed = abs(Decimal(str(data.quantity)) - ledger_quantity) > Decimal("0.000001")
            cost_changed = bool(ledger.buy_quantity) and abs(Decimal(str(data.buy_price)) - ledger_buy_price) > Decimal("0.0001")
            identity_changed = (
                data.investment_type.strip() != (existing.investment_type or "").strip()
                or (data.symbol or "").strip().upper() != (existing.symbol or "").strip().upper()
                or (
                    data.broker.strip() != (existing.broker or "").strip()
                    and existing.investment_account_id is not None
                )
                or data.buy_date != existing.buy_date
            )
            if quantity_changed or cost_changed or identity_changed:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This holding is controlled by its BUY/SELL transaction history. "
                        "Edit the transaction from Portfolio → History to change quantity or cost basis. "
                        "Broker, instrument, and opening-date changes are blocked to protect position identity."
                    ),
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

                investment_account_id = :investment_account_id,

                fees = :fees,

                notes = :notes,

                updated_at =
                    CURRENT_TIMESTAMP

            WHERE
                id = :investment_id AND user_id = :user_id

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
                investment_account_id,
                fees,
                notes,
                created_at,
                updated_at
            """
        ),
        {
            "investment_id": investment_id,
            "user_id": user_id,

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

            "investment_account_id": selected_account_id,

            "fees":
                data.fees,

            "notes":
                data.notes,
        },
    )

    investment = result.first()

    if not investment:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to update investment.")

    record_finance_event(db, user_id=user_id, event_type="updated", entity_type="investment", entity_id=investment.id, description=f"Investment record updated: {data.name.strip()}", snapshot={"id": investment.id, "name": data.name.strip(), "investment_type": data.investment_type, "symbol": data.symbol, "quantity": data.quantity, "buy_price": data.buy_price, "broker": data.broker, "notes": data.notes})
    db.commit()
    return investment_response(investment)


# ============================================================
# DELETE INVESTMENT
# ============================================================

@router.delete("/{investment_id}")
def delete_investment(
    investment_id: int,
    user_id: int | None = None,  # Legacy query parameter is ignored for security.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Safely remove one investment record, never an entire instrument.

    Records with linked BUY/SELL transactions are protected so their
    transaction ledger and capital-gains history cannot be orphaned.
    """
    ensure_investments_table(db)

    # Always scope deletion to the authenticated user; never trust query user_id.
    investment = db.execute(
        text("SELECT id, user_id, name FROM investments WHERE id = :investment_id AND user_id = :user_id"),
        {"investment_id": investment_id, "user_id": current_user.id},
    ).first()

    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found.")

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
        text("DELETE FROM investments WHERE id = :investment_id AND user_id = :user_id RETURNING id"),
        {"investment_id": investment_id, "user_id": current_user.id},
    )
    deleted = result.first()
    if not deleted:
        db.rollback()
        raise HTTPException(status_code=404, detail="Investment not found.")

    record_finance_event(db, user_id=investment.user_id, event_type="deleted", entity_type="investment", entity_id=investment_id, description=f"Investment record deleted: {investment.name}; original identity preserved in Finance Diary", snapshot={"id": investment.id, "user_id": investment.user_id, "name": investment.name})
    db.commit()
    return {"status": "deleted", "investment_id": investment_id, "history_preserved": True}
