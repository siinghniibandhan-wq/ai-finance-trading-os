# ============================================================
# FINANCIAL OS
# INVESTMENT COST BASIS + P&L ENGINE
# ============================================================
#
# Purpose:
# - Calculate investment cost basis
# - Calculate realised P&L using WEIGHTED-AVERAGE
# - Calculate unrealised P&L
# - Calculate remaining quantity
# - Calculate remaining cost basis
# - Include transaction fees
#
# Accounting method:
# WEIGHTED-AVERAGE = First In, First Out
#
# IMPORTANT:
# - Does NOT modify investment records
# - Does NOT modify transaction records
# - Reads from investment_transactions
# - Uses existing investment.current_price
# ============================================================

from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.auth import get_current_user
from app.models import User


router = APIRouter(
    prefix="/api/investment-pnl",
    tags=["Investment P&L"],
)


# ============================================================
# DECIMAL HELPERS
# ============================================================

def money(value: Decimal) -> Decimal:
    """
    Round monetary values to 2 decimal places.
    """
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def quantity_value(value: Decimal) -> Decimal:
    """
    Keep quantity precision up to 6 decimal places.
    """
    return value.quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# WEIGHTED-AVERAGE CALCULATION
# ============================================================

def calculate_weighted_average(transactions):
    """
    Process ACTIVE BUY/SELL transactions using weighted-average cost.
    BUY fees increase acquisition cost; SELL fees reduce net proceeds.
    """
    quantity_held = Decimal("0")
    remaining_cost_basis = Decimal("0")
    realised_profit = Decimal("0")
    total_sell_value = Decimal("0")
    total_buy_fees = Decimal("0")
    total_sell_fees = Decimal("0")
    total_sold_quantity = Decimal("0")
    total_fees = Decimal("0")

    for transaction in transactions:
        transaction_type = str(transaction.transaction_type or "").upper()
        quantity = Decimal(str(transaction.quantity or 0))
        price = Decimal(str(transaction.price or 0))
        fees = Decimal(str(transaction.fees or 0))

        if quantity <= 0 or price <= 0 or fees < 0:
            raise ValueError("Transaction quantity, price, or fees are invalid.")

        total_fees += fees

        if transaction_type == "BUY":
            quantity_held += quantity
            remaining_cost_basis += quantity * price + fees
            total_buy_fees += fees
        elif transaction_type == "SELL":
            if quantity > quantity_held:
                raise ValueError(
                    "SELL quantity exceeds available holding. "
                    "Review the active transaction sequence."
                )
            average_cost = remaining_cost_basis / quantity_held
            released_cost = average_cost * quantity
            net_proceeds = quantity * price - fees
            realised_profit += net_proceeds - released_cost
            quantity_held -= quantity
            remaining_cost_basis -= released_cost
            total_sold_quantity += quantity
            total_sell_value += quantity * price
            total_sell_fees += fees
            if quantity_held == 0:
                remaining_cost_basis = Decimal("0")
        else:
            raise ValueError("Unsupported transaction type.")

    return {
        "remaining_quantity": quantity_value(quantity_held),
        "remaining_cost_basis": money(remaining_cost_basis),
        "realised_pnl": money(realised_profit),
        "total_sold_quantity": quantity_value(total_sold_quantity),
        "total_buy_fees": money(total_buy_fees),
        "total_sell_fees": money(total_sell_fees),
        "total_fees": money(total_fees),
        "total_sell_value": money(total_sell_value),
    }


def ensure_transaction_status(db: Session):
    """Ensure status exists before filtering voided transactions."""
    db.execute(text(
        "ALTER TABLE investment_transactions "
        "ADD COLUMN IF NOT EXISTS status VARCHAR(12) NOT NULL DEFAULT 'ACTIVE'"
    ))
    db.commit()


# ============================================================
# GET P&L FOR ONE INVESTMENT
# ============================================================

@router.get("/{investment_id}")
def get_investment_pnl(
    investment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Always derive ownership from the verified token, never a request parameter.
    user_id = current_user.id
    """
    Calculate WEIGHTED-AVERAGE cost basis and P&L
    for one investment.
    """

    ensure_transaction_status(db)

    # --------------------------------------------------------
    # GET INVESTMENT
    # --------------------------------------------------------

    investment_result = db.execute(
        text(
            """
            SELECT
                id,
                name,
                symbol,
                investment_type,
                current_price
            FROM investments
            WHERE id = :investment_id
              AND user_id = :user_id
            """
        ),
        {
            "investment_id": investment_id,
            "user_id": user_id,
        },
    )

    investment = investment_result.first()

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found.",
        )

    # --------------------------------------------------------
    # GET TRANSACTIONS
    # --------------------------------------------------------

    transaction_result = db.execute(
        text(
            """
            SELECT
                id,
                transaction_type,
                quantity,
                price,
                fees,
                transaction_date
            FROM investment_transactions
            WHERE investment_id = :investment_id
              AND user_id = :user_id
              AND status = 'ACTIVE'
            ORDER BY
                transaction_date ASC,
                id ASC
            """
        ),
        {
            "investment_id": investment_id,
            "user_id": user_id,
        },
    )

    transactions = transaction_result.fetchall()

    # --------------------------------------------------------
    # NO TRANSACTIONS
    # --------------------------------------------------------

    if not transactions:
        return {
            "status": "success",
            "investment_id": investment.id,
            "name": investment.name,
            "symbol": investment.symbol,
            "investment_type": investment.investment_type,
            "quantity_held": Decimal("0"),
            "average_cost": Decimal("0"),
            "cost_basis": Decimal("0"),
            "current_price": Decimal(
                str(investment.current_price or 0)
            ),
            "current_value": Decimal("0"),
            "unrealised_pnl": Decimal("0"),
            "realised_pnl": Decimal("0"),
            "total_pnl": Decimal("0"),
            "return_percent": Decimal("0"),
        }

    # --------------------------------------------------------
    # WEIGHTED-AVERAGE ENGINE
    # --------------------------------------------------------

    try:
        pnl = calculate_weighted_average(transactions)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    quantity_held = pnl[
        "remaining_quantity"
    ]

    cost_basis = pnl[
        "remaining_cost_basis"
    ]

    current_price = Decimal(
        str(investment.current_price or 0)
    )

    # --------------------------------------------------------
    # CURRENT VALUE
    # --------------------------------------------------------

    current_value = (
        quantity_held * current_price
    )

    current_value = money(current_value)

    # --------------------------------------------------------
    # UNREALISED P&L
    # --------------------------------------------------------

    unrealised_pnl = (
        current_value
        - cost_basis
    )

    unrealised_pnl = money(
        unrealised_pnl
    )

    # --------------------------------------------------------
    # REALISED P&L
    # --------------------------------------------------------

    realised_pnl = pnl[
        "realised_pnl"
    ]

    # --------------------------------------------------------
    # TOTAL P&L
    # --------------------------------------------------------

    total_pnl = money(
        realised_pnl
        + unrealised_pnl
    )

    # --------------------------------------------------------
    # AVERAGE COST
    # --------------------------------------------------------

    if quantity_held > 0:

        average_cost = (
            cost_basis
            / quantity_held
        )

        average_cost = money(
            average_cost
        )

    else:
        average_cost = Decimal("0")

    # --------------------------------------------------------
    # RETURN %
    # --------------------------------------------------------

    total_invested_for_return = (
        cost_basis
    )

    if total_invested_for_return > 0:

        return_percent = (
            unrealised_pnl
            / total_invested_for_return
        ) * Decimal("100")

        return_percent = money(
            return_percent
        )

    else:
        return_percent = Decimal("0")

    return {
        "status": "success",
        "investment_id": investment.id,
        "name": investment.name,
        "symbol": investment.symbol,
        "investment_type": investment.investment_type,

        "quantity_held": quantity_held,

        "average_cost": average_cost,

        "cost_basis": cost_basis,

        "current_price": current_price,

        "current_value": current_value,

        "unrealised_pnl": unrealised_pnl,

        "realised_pnl": realised_pnl,

        "total_pnl": total_pnl,

        "return_percent": return_percent,

        "total_sold_quantity": pnl[
            "total_sold_quantity"
        ],

        "total_sell_value": pnl[
            "total_sell_value"
        ],

        "buy_fees": pnl[
            "total_buy_fees"
        ],

        "sell_fees": pnl["total_sell_fees"],
        "total_fees": pnl["total_fees"],
    }


# ============================================================
# GET P&L FOR ALL INVESTMENTS
# ============================================================

@router.get("/")
def get_all_investment_pnl(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Always derive ownership from the verified token, never a request parameter.
    user_id = current_user.id
    """
    Calculate P&L for every investment
    belonging to the user.
    """

    ensure_transaction_status(db)

    investments_result = db.execute(
        text(
            """
            SELECT id
            FROM investments
            WHERE user_id = :user_id
            ORDER BY id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    investments = investments_result.fetchall()

    results = []

    for investment in investments:

        # Reuse the same calculation logic
        transaction_result = db.execute(
            text(
                """
                SELECT
                    id,
                    transaction_type,
                    quantity,
                    price,
                    fees,
                    transaction_date
                FROM investment_transactions
                WHERE investment_id = :investment_id
                  AND user_id = :user_id
                  AND status = 'ACTIVE'
                ORDER BY
                    transaction_date ASC,
                    id ASC
                """
            ),
            {
                "investment_id": investment.id,
                "user_id": user_id,
            },
        )

        transactions = transaction_result.fetchall()

        investment_result = db.execute(
            text(
                """
                SELECT
                    id,
                    name,
                    symbol,
                    investment_type,
                    current_price
                FROM investments
                WHERE id = :investment_id
                  AND user_id = :user_id
                """
            ),
            {
                "investment_id": investment.id,
                "user_id": user_id,
            },
        )

        investment_data = investment_result.first()

        if not investment_data:
            continue

        if transactions:

            try:
                pnl = calculate_weighted_average(
                    transactions
                )

            except ValueError:
                continue

            quantity_held = pnl[
                "remaining_quantity"
            ]

            cost_basis = pnl[
                "remaining_cost_basis"
            ]

            realised_pnl = pnl[
                "realised_pnl"
            ]

        else:

            quantity_held = Decimal("0")
            cost_basis = Decimal("0")
            realised_pnl = Decimal("0")

        current_price = Decimal(
            str(
                investment_data.current_price
                or 0
            )
        )

        current_value = money(
            quantity_held
            * current_price
        )

        unrealised_pnl = money(
            current_value
            - cost_basis
        )

        total_pnl = money(
            realised_pnl
            + unrealised_pnl
        )

        if quantity_held > 0:

            average_cost = money(
                cost_basis
                / quantity_held
            )

        else:

            average_cost = Decimal("0")

        if cost_basis > 0:

            return_percent = money(
                (
                    unrealised_pnl
                    / cost_basis
                )
                * Decimal("100")
            )

        else:

            return_percent = Decimal("0")

        results.append(
            {
                "investment_id": investment_data.id,
                "name": investment_data.name,
                "symbol": investment_data.symbol,
                "investment_type": investment_data.investment_type,

                "quantity_held": quantity_held,

                "average_cost": average_cost,

                "cost_basis": cost_basis,

                "current_price": current_price,

                "current_value": current_value,

                "unrealised_pnl": unrealised_pnl,

                "realised_pnl": realised_pnl,

                "total_pnl": total_pnl,

                "return_percent": return_percent,
                "buy_fees": pnl["total_buy_fees"] if transactions else Decimal("0"),
                "sell_fees": pnl["total_sell_fees"] if transactions else Decimal("0"),
                "total_fees": pnl["total_fees"] if transactions else Decimal("0"),
            }
        )

    # ========================================================
    # PORTFOLIO TOTALS
    # ========================================================

    total_cost_basis = sum(
        (
            item["cost_basis"]
            for item in results
        ),
        Decimal("0"),
    )

    total_current_value = sum(
        (
            item["current_value"]
            for item in results
        ),
        Decimal("0"),
    )

    total_unrealised_pnl = sum(
        (
            item["unrealised_pnl"]
            for item in results
        ),
        Decimal("0"),
    )

    total_realised_pnl = sum(
        (
            item["realised_pnl"]
            for item in results
        ),
        Decimal("0"),
    )

    total_pnl = sum(
        (
            item["total_pnl"]
            for item in results
        ),
        Decimal("0"),
    )

    if total_cost_basis > 0:

        portfolio_return_percent = money(
            (
                total_unrealised_pnl
                / total_cost_basis
            )
            * Decimal("100")
        )

    else:

        portfolio_return_percent = Decimal("0")

    return {
        "status": "success",
        "user_id": user_id,

        "investments": results,

        "summary": {
            "total_cost_basis": money(
                total_cost_basis
            ),
            "total_current_value": money(
                total_current_value
            ),
            "total_unrealised_pnl": money(
                total_unrealised_pnl
            ),
            "total_realised_pnl": money(
                total_realised_pnl
            ),
            "total_pnl": money(
                total_pnl
            ),
            "portfolio_return_percent": (
                portfolio_return_percent
            ),
        },
      }
