# ============================================================
# FINANCIAL OS
# CONSOLIDATED HOLDINGS ENGINE
# ============================================================
#
# Purpose:
# - Calculate actual holdings from BUY / SELL transactions.
# - Consolidate the same market instrument across Portfolio
#   investment records.
# - Calculate current portfolio value.
# - Calculate weighted average cost.
# - Calculate cost basis.
# - Calculate realised and unrealised gain/loss and return.
# - Preserve individual Portfolio investment records.
# - Provide broker and investment drill-down information.
#
# IMPORTANT:
# - Does NOT modify existing investment records.
# - Does NOT modify investment transactions.
# - Does NOT replace the Portfolio API.
# - Implements weighted-average realised P&L.
# - Implements remaining cost basis after SELL.
# - FIFO/LIFO and other advanced methods are not implemented.
# - Instrument Master belongs to Stage #6.
#
# HOLDINGS MODEL:
#
# Portfolio positions
#       ↓
# BUY / SELL transaction ledger
#       ↓
# Consolidated instrument
#       ↓
# Current quantity
#       ↓
# Cost basis + market value
#       ↓
# Unrealised P&L
# ============================================================

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/holdings",
    tags=["Holdings"],
)


# ============================================================
# DECIMAL HELPER
# ============================================================

def to_decimal(value):
    """
    Safely convert database numeric values to Decimal.
    """

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


# ============================================================
# HOLDING IDENTITY
# ============================================================

def holding_key(investment):
    """
    Determine the consolidation key.

    Current stage:
    - Same non-empty symbol = same underlying instrument.
    - No symbol = keep individual investment separate.

    Instrument Master will provide canonical identity later.
    """

    symbol = (
        str(investment.get("symbol") or "")
        .strip()
        .upper()
    )

    if symbol:
        return (
            "SYMBOL",
            symbol,
        )

    return (
        "INVESTMENT",
        str(investment["id"]),
    )


# ============================================================
# CREATE EMPTY HOLDING
# ============================================================

def create_holding(investment):
    """
    Create the internal accumulator for one consolidated holding.
    """

    return {
        "symbol": (
            str(investment.get("symbol") or "")
            .strip()
            .upper()
            or None
        ),
        "name": (
            investment.get("name")
            or "Unknown"
        ),
        "investment_type": (
            investment.get("investment_type")
            or "Other"
        ),
        "investment_ids": set(),
        "broker_breakdown": {},
        "quantity": Decimal("0"),
        "remaining_cost_basis": Decimal("0"),
        "realised_gain_loss": Decimal("0"),
        "realised_cost_basis": Decimal("0"),
        "sell_value": Decimal("0"),
        "fees": Decimal("0"),
        "current_price": to_decimal(
            investment.get("current_price")
        ),
    }


# ============================================================
# ADD BROKER INFORMATION
# ============================================================

def add_broker_position(
    holding,
    investment,
    quantity,
    transaction_type,
):
    """
    Maintain broker-level quantity without creating a separate
    database table.
    """

    broker = (
        str(
            investment.get("broker")
            or "Unspecified"
        ).strip()
        or "Unspecified"
    )

    holding["broker_breakdown"].setdefault(
        broker,
        {
            "quantity": Decimal("0"),
            "investment_ids": set(),
        },
    )

    broker_data = holding[
        "broker_breakdown"
    ][broker]

    broker_data["investment_ids"].add(
        investment["id"]
    )

    if transaction_type == "BUY":
        broker_data["quantity"] += quantity

    elif transaction_type == "SELL":
        broker_data["quantity"] -= quantity


# ============================================================
# SERIALIZE HOLDING
# ============================================================

def serialize_holding(holding):
    """
    Convert internal Decimal/set structures into API-safe data.

    Stage 4:
    - Weighted-average cost basis.
    - Realised P&L on SELL.
    - Unrealised P&L on remaining quantity.
    - Total P&L = realised + unrealised.
    """

    quantity = holding["quantity"]

    if quantity <= 0:
        return None

    # --------------------------------------------------------
    # REMAINING COST BASIS
    # --------------------------------------------------------

    cost_basis = holding["remaining_cost_basis"]

    average_cost = (
        cost_basis / quantity
        if quantity > 0
        else Decimal("0")
    )

    # --------------------------------------------------------
    # CURRENT MARKET VALUE
    # --------------------------------------------------------

    current_price = holding["current_price"]

    current_value = quantity * current_price

    # --------------------------------------------------------
    # UNREALISED P&L
    # --------------------------------------------------------

    unrealised_gain_loss = (
        current_value - cost_basis
    )

    unrealised_return_percent = (
        (
            unrealised_gain_loss
            / cost_basis
        )
        * Decimal("100")
        if cost_basis > 0
        else Decimal("0")
    )

    # --------------------------------------------------------
    # REALISED P&L
    # --------------------------------------------------------

    realised_gain_loss = holding["realised_gain_loss"]
    realised_cost_basis = holding["realised_cost_basis"]

    realised_return_percent = (
        (
            realised_gain_loss
            / realised_cost_basis
        )
        * Decimal("100")
        if realised_cost_basis > 0
        else Decimal("0")
    )

    # --------------------------------------------------------
    # TOTAL P&L
    # --------------------------------------------------------

    total_gain_loss = (
        realised_gain_loss
        + unrealised_gain_loss
    )

    total_cost_basis = (
        realised_cost_basis
        + cost_basis
    )

    total_return_percent = (
        (
            total_gain_loss
            / total_cost_basis
        )
        * Decimal("100")
        if total_cost_basis > 0
        else Decimal("0")
    )

    # --------------------------------------------------------
    # BROKER BREAKDOWN
    # --------------------------------------------------------

    broker_breakdown = []

    for (
        broker,
        broker_data,
    ) in holding[
        "broker_breakdown"
    ].items():

        broker_quantity = (
            broker_data["quantity"]
        )

        # Don't show a broker whose complete position
        # has already been sold.
        if broker_quantity <= 0:
            continue

        broker_breakdown.append(
            {
                "broker": broker,
                "quantity": broker_quantity,
                "investment_ids": sorted(
                    broker_data[
                        "investment_ids"
                    ]
                ),
            }
        )

    return {
        "name": holding["name"],
        "symbol": holding["symbol"],
        "investment_type": holding[
            "investment_type"
        ],
        "quantity_held": quantity,
        "average_cost": average_cost,
        "cost_basis": cost_basis,
        "current_price": current_price,
        "current_value": current_value,
        "realised_gain_loss": realised_gain_loss,
        "realised_cost_basis": realised_cost_basis,
        "realised_return_percent": realised_return_percent,
        "unrealised_gain_loss": unrealised_gain_loss,
        "unrealised_return_percent": unrealised_return_percent,
        "total_gain_loss": total_gain_loss,
        "total_return_percent": total_return_percent,
        "sell_proceeds": holding["sell_value"],
        "total_fees": holding["fees"],
        "investment_count": len(
            holding["investment_ids"]
        ),
        "investment_ids": sorted(
            holding["investment_ids"]
        ),
        "broker_breakdown": broker_breakdown,
        "fees": holding["fees"],
        "price_source": "Portfolio current price",
    }


# ============================================================
# LOAD INVESTMENTS
# ============================================================

def load_investments(
    db: Session,
    user_id: int,
):
    """
    Load all Portfolio investment records for the user.
    """

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
                broker,
                fees
            FROM investments
            WHERE user_id = :user_id
            ORDER BY id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    return [
        dict(row._mapping)
        for row in result
    ]


# ============================================================
# LOAD TRANSACTIONS
# ============================================================

def load_transactions(
    db: Session,
    user_id: int,
):
    """
    Load the complete investment transaction ledger.
    """

    # Ensure status columns exist before filtering. The transaction API normally
    # performs this migration, but Holdings can be the first endpoint called.
    db.execute(text("ALTER TABLE investment_transactions ADD COLUMN IF NOT EXISTS status VARCHAR(12) NOT NULL DEFAULT 'ACTIVE'"))
    db.execute(text("ALTER TABLE investment_transactions ADD COLUMN IF NOT EXISTS void_reason TEXT"))
    db.execute(text("ALTER TABLE investment_transactions ADD COLUMN IF NOT EXISTS voided_at TIMESTAMP"))
    db.commit()

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                investment_id,
                transaction_type,
                quantity,
                price,
                fees,
                transaction_date
            FROM investment_transactions
            WHERE user_id = :user_id
              AND status = 'ACTIVE'
            ORDER BY transaction_date ASC, id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    return [
        dict(row._mapping)
        for row in result
    ]


# ============================================================
# BUILD HOLDINGS
# ============================================================

def build_holdings(
    investments,
    transactions,
):
    """
    Build consolidated Holdings without modifying the database.
    """

    investment_map = {
        investment["id"]: investment
        for investment in investments
    }

    grouped = {}

    # Investment records that already have ledger activity.
    ledger_investment_ids = set()

    # --------------------------------------------------------
    # PROCESS TRANSACTION LEDGER
    # --------------------------------------------------------

    for transaction in transactions:

        investment = investment_map.get(
            transaction["investment_id"]
        )

        if not investment:
            continue

        ledger_investment_ids.add(
            transaction["investment_id"]
        )

        key = holding_key(
            investment
        )

        if key not in grouped:
            grouped[key] = create_holding(
                investment
            )

        holding = grouped[key]

        holding["investment_ids"].add(
            investment["id"]
        )

        quantity = to_decimal(
            transaction["quantity"]
        )

        price = to_decimal(
            transaction["price"]
        )

        fees = to_decimal(
            transaction["fees"]
        )

        gross_value = (
            quantity * price
        )

        holding["fees"] += fees

        transaction_type = (
            str(
                transaction[
                    "transaction_type"
                ]
            )
            .strip()
            .upper()
        )

        if transaction_type == "BUY":

            acquisition_cost = (
                gross_value + fees
            )

            holding["quantity"] += (
                quantity
            )

            # BUY fees are part of acquisition cost.
            holding["remaining_cost_basis"] += (
                acquisition_cost
            )

        elif transaction_type == "SELL":

            # ------------------------------------------------
            # REALISED P&L USING WEIGHTED-AVERAGE COST
            # ------------------------------------------------
            #
            # The average cost immediately before the sale
            # determines the cost released from the holding.
            # ------------------------------------------------

            available_quantity = holding["quantity"]

            if available_quantity <= 0:
                # Defensive handling for malformed legacy data.
                released_cost = Decimal("0")
                sell_quantity = Decimal("0")
            else:
                sell_quantity = min(
                    quantity,
                    available_quantity,
                )

                average_cost_before_sell = (
                    holding["remaining_cost_basis"]
                    / available_quantity
                )

                released_cost = (
                    average_cost_before_sell
                    * sell_quantity
                )

            net_sale_proceeds = (
                (sell_quantity * price)
                - fees
            )

            realised_gain_loss = (
                net_sale_proceeds
                - released_cost
            )

            holding["quantity"] -= (
                sell_quantity
            )

            holding["remaining_cost_basis"] -= (
                released_cost
            )

            # Defensive rounding/oversell protection.
            if holding["quantity"] < 0:
                holding["quantity"] = Decimal("0")

            if holding["remaining_cost_basis"] < 0:
                holding["remaining_cost_basis"] = Decimal("0")

            holding["realised_gain_loss"] += (
                realised_gain_loss
            )

            holding["realised_cost_basis"] += (
                released_cost
            )

            holding["sell_value"] += (
                net_sale_proceeds
            )

        add_broker_position(
            holding,
            investment,
            quantity,
            transaction_type,
        )

    # --------------------------------------------------------
    # LEGACY PORTFOLIO FALLBACK
    # --------------------------------------------------------
    #
    # Existing investments created before the transaction
    # ledger existed must still appear in Holdings.
    #
    # We treat their stored Portfolio quantity as the original
    # position. We do NOT create fake transactions.
    # --------------------------------------------------------

    for investment in investments:

        if investment["id"] in ledger_investment_ids:
            continue

        key = holding_key(
            investment
        )

        if key not in grouped:
            grouped[key] = create_holding(
                investment
            )

        holding = grouped[key]

        holding["investment_ids"].add(
            investment["id"]
        )

        quantity = to_decimal(
            investment.get("quantity")
        )

        buy_price = to_decimal(
            investment.get("buy_price")
        )

        fees = to_decimal(
            investment.get("fees")
        )

        acquisition_cost = (
            quantity * buy_price
            + fees
        )

        holding["quantity"] += (
            quantity
        )

        holding["remaining_cost_basis"] += (
            acquisition_cost
        )

        holding["fees"] += fees

        add_broker_position(
            holding,
            investment,
            quantity,
            "BUY",
        )

    # --------------------------------------------------------
    # SERIALIZE ACTIVE HOLDINGS
    # --------------------------------------------------------

    holdings = []

    for holding in grouped.values():

        serialized = serialize_holding(
            holding
        )

        if serialized is not None:
            holdings.append(
                serialized
            )

    # Largest market value first.
    holdings.sort(
        key=lambda item: (
            item["current_value"]
        ),
        reverse=True,
    )

    return holdings


# ============================================================
# GET ALL CONSOLIDATED HOLDINGS
# ============================================================

@router.get("/")
def get_holdings(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Return consolidated current Holdings.

    Example:

        Portfolio:
            HDFC Bank / Position 1 / 100
            HDFC Bank / Position 2 / 100

        Holdings:
            HDFC Bank / 200
    """

    investments = load_investments(
        db,
        user_id,
    )

    transactions = load_transactions(
        db,
        user_id,
    )

    holdings = build_holdings(
        investments,
        transactions,
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_cost_basis = sum(
        (
            item["cost_basis"]
            for item in holdings
        ),
        Decimal("0"),
    )

    total_current_value = sum(
        (
            item["current_value"]
            for item in holdings
        ),
        Decimal("0"),
    )

    total_unrealised_gain_loss = (
        total_current_value
        - total_cost_basis
    )

    total_unrealised_return_percent = (
        (
            total_unrealised_gain_loss
            / total_cost_basis
        )
        * Decimal("100")
        if total_cost_basis > 0
        else Decimal("0")
    )

    total_realised_gain_loss = sum(
        (
            item["realised_gain_loss"]
            for item in holdings
        ),
        Decimal("0"),
    )

    total_realised_cost_basis = sum(
        (
            item["realised_cost_basis"]
            for item in holdings
        ),
        Decimal("0"),
    )

    total_realised_return_percent = (
        (
            total_realised_gain_loss
            / total_realised_cost_basis
        )
        * Decimal("100")
        if total_realised_cost_basis > 0
        else Decimal("0")
    )

    total_gain_loss = (
        total_realised_gain_loss
        + total_unrealised_gain_loss
    )

    total_cost_basis_for_return = (
        total_realised_cost_basis
        + total_cost_basis
    )

    total_return_percent = (
        (
            total_gain_loss
            / total_cost_basis_for_return
        )
        * Decimal("100")
        if total_cost_basis_for_return > 0
        else Decimal("0")
    )

    total_sell_proceeds = sum(
        (
            item["sell_proceeds"]
            for item in holdings
        ),
        Decimal("0"),
    )

    total_fees = sum(
        (
            item["total_fees"]
            for item in holdings
        ),
        Decimal("0"),
    )

    return {
        "status": "success",
        "user_id": user_id,
        "count": len(holdings),
        "holdings": holdings,
        "summary": {
            "holding_count": len(
                holdings
            ),
            "total_cost_basis": (
                total_cost_basis
            ),
            "total_current_value": (
                total_current_value
            ),
            "total_realised_gain_loss": (
                total_realised_gain_loss
            ),
            "total_realised_cost_basis": (
                total_realised_cost_basis
            ),
            "total_realised_return_percent": (
                total_realised_return_percent
            ),
            "total_unrealised_gain_loss": (
                total_unrealised_gain_loss
            ),
            "total_unrealised_return_percent": (
                total_unrealised_return_percent
            ),
            "total_gain_loss": (
                total_gain_loss
            ),
            "total_return_percent": (
                total_return_percent
            ),
            "total_sell_proceeds": (
                total_sell_proceeds
            ),
            "total_fees": (
                total_fees
            ),
        },
    }


# ============================================================
# GET HOLDING FOR ONE PORTFOLIO INVESTMENT
# ============================================================

@router.get("/{investment_id}")
def get_holding(
    investment_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Return the consolidated Holding containing a specific
    Portfolio investment.

    This preserves the old endpoint while making it consistent
    with the new consolidated Holdings engine.
    """

    investments = load_investments(
        db,
        user_id,
    )

    target = next(
        (
            investment
            for investment in investments
            if investment["id"]
            == investment_id
        ),
        None,
    )

    if not target:
        return {
            "status": "error",
            "message": "Investment not found.",
        }

    transactions = load_transactions(
        db,
        user_id,
    )

    holdings = build_holdings(
        investments,
        transactions,
    )

    key = holding_key(
        target
    )

    # Rebuild a lookup using the same identity rule.
    matching = []

    for holding in holdings:

        if (
            target.get("symbol")
            and holding.get("symbol")
            == str(
                target.get("symbol")
            ).strip().upper()
        ):
            matching.append(
                holding
            )

        elif (
            not target.get("symbol")
            and investment_id
            in holding.get(
                "investment_ids",
                [],
            )
        ):
            matching.append(
                holding
            )

    if not matching:
        return {
            "status": "success",
            "investment_id": investment_id,
            "holding": None,
            "message": "No active holding found.",
        }

    return {
        "status": "success",
        "investment_id": investment_id,
        "holding": matching[0],
    }
