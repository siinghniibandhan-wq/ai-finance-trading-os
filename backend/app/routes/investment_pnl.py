# ============================================================
# FINANCIAL OS
# INVESTMENT COST BASIS + P&L ENGINE
# ============================================================
#
# Purpose:
# - Calculate investment cost basis
# - Calculate realised P&L using FIFO
# - Calculate unrealised P&L
# - Calculate remaining quantity
# - Calculate remaining cost basis
# - Include transaction fees
#
# Accounting method:
# FIFO = First In, First Out
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
# FIFO CALCULATION
# ============================================================

def calculate_fifo(transactions):
    """
    Process BUY / SELL transactions using FIFO.

    Each BUY creates a lot:

        {
            quantity,
            remaining_quantity,
            price,
            fee,
            cost_per_unit
        }

    SELL transactions consume the oldest BUY lots first.
    """

    lots = []

    realised_profit = Decimal("0")
    total_sell_value = Decimal("0")
    total_sell_fees = Decimal("0")
    total_buy_fees = Decimal("0")

    total_sold_quantity = Decimal("0")

    for transaction in transactions:

        transaction_type = str(
            transaction.transaction_type
        ).upper()

        quantity = Decimal(
            str(transaction.quantity or 0)
        )

        price = Decimal(
            str(transaction.price or 0)
        )

        fees = Decimal(
            str(transaction.fees or 0)
        )

        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if transaction_type == "BUY":

            total_buy_fees += fees

            # Total acquisition cost including fees.
            total_cost = (
                quantity * price
            ) + fees

            # Allocate the BUY fee across the quantity.
            cost_per_unit = (
                total_cost / quantity
            )

            lots.append(
                {
                    "quantity": quantity,
                    "remaining_quantity": quantity,
                    "price": price,
                    "fees": fees,
                    "cost_per_unit": cost_per_unit,
                }
            )

        # ----------------------------------------------------
        # SELL
        # ----------------------------------------------------

        elif transaction_type == "SELL":

            remaining_to_sell = quantity

            total_sell_value += (
                quantity * price
            )

            total_sell_fees += fees
            total_sold_quantity += quantity

            # Selling without sufficient BUY lots.
            available_quantity = sum(
                lot["remaining_quantity"]
                for lot in lots
            )

            if remaining_to_sell > available_quantity:
                raise ValueError(
                    "SELL quantity exceeds available "
                    "FIFO holding."
                )

            # ------------------------------------------------
            # FIFO LOT CONSUMPTION
            # ------------------------------------------------

            while remaining_to_sell > 0:

                current_lot = lots[0]

                lot_quantity = current_lot[
                    "remaining_quantity"
                ]

                consumed_quantity = min(
                    remaining_to_sell,
                    lot_quantity,
                )

                # Cost assigned to this SELL portion.
                allocated_cost = (
                    consumed_quantity
                    * current_lot["cost_per_unit"]
                )

                # Allocate selling fees proportionally.
                allocated_sell_fee = (
                    fees
                    * (
                        consumed_quantity
                        / quantity
                    )
                )

                # Net proceeds for this portion.
                net_proceeds = (
                    consumed_quantity * price
                ) - allocated_sell_fee

                # Realised P&L.
                realised_profit += (
                    net_proceeds
                    - allocated_cost
                )

                # Reduce BUY lot.
                current_lot[
                    "remaining_quantity"
                ] -= consumed_quantity

                remaining_to_sell -= (
                    consumed_quantity
                )

                # Remove fully consumed lot.
                if (
                    current_lot[
                        "remaining_quantity"
                    ] <= 0
                ):
                    lots.pop(0)

    # ========================================================
    # REMAINING HOLDINGS
    # ========================================================

    remaining_quantity = sum(
        lot["remaining_quantity"]
        for lot in lots
    )

    remaining_cost_basis = sum(
        lot["remaining_quantity"]
        * lot["cost_per_unit"]
        for lot in lots
    )

    return {
        "remaining_quantity": quantity_value(
            remaining_quantity
        ),
        "remaining_cost_basis": money(
            remaining_cost_basis
        ),
        "realised_pnl": money(
            realised_profit
        ),
        "total_sold_quantity": quantity_value(
            total_sold_quantity
        ),
        "total_buy_fees": money(
            total_buy_fees
        ),
        "total_sell_fees": money(
            total_sell_fees
        ),
        "total_sell_value": money(
            total_sell_value
        ),
        "lots": lots,
    }


# ============================================================
# GET P&L FOR ONE INVESTMENT
# ============================================================

@router.get("/{investment_id}")
def get_investment_pnl(
    investment_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Calculate FIFO cost basis and P&L
    for one investment.
    """

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
    # FIFO ENGINE
    # --------------------------------------------------------

    try:
        fifo = calculate_fifo(transactions)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    quantity_held = fifo[
        "remaining_quantity"
    ]

    cost_basis = fifo[
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

    realised_pnl = fifo[
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

        "total_sold_quantity": fifo[
            "total_sold_quantity"
        ],

        "total_sell_value": fifo[
            "total_sell_value"
        ],

        "buy_fees": fifo[
            "total_buy_fees"
        ],

        "sell_fees": fifo[
            "total_sell_fees"
        ],
    }


# ============================================================
# GET P&L FOR ALL INVESTMENTS
# ============================================================

@router.get("/")
def get_all_investment_pnl(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Calculate P&L for every investment
    belonging to the user.
    """

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
                fifo = calculate_fifo(
                    transactions
                )

            except ValueError:
                continue

            quantity_held = fifo[
                "remaining_quantity"
            ]

            cost_basis = fifo[
                "remaining_cost_basis"
            ]

            realised_pnl = fifo[
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
