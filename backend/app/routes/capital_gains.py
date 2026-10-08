# ============================================================
# FINANCIAL OS
# CAPITAL GAINS DATA ENGINE v1.1
# ============================================================
#
# Purpose:
# - Calculate realised capital gains from BUY / SELL ledger
# - Use FIFO matching
# - Track individual BUY lots
# - Calculate holding period
# - Calculate sale proceeds
# - Calculate cost of units sold
# - Allocate BUY and SELL fees
# - Provide financial-year capital-gain data
#
# IMPORTANT:
# - READ-ONLY ENGINE
# - Does NOT modify investments
# - Does NOT modify investment_transactions
# - Does NOT modify holdings
# - Does NOT calculate final income tax liability
# - Does NOT apply STCG/LTCG tax rates
#
# ============================================================


from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/capital-gains",
    tags=["Capital Gains"],
)


# ============================================================
# DECIMAL HELPER
# ============================================================

def to_decimal(value):
    """
    Safely convert database values to Decimal.
    """

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


# ============================================================
# FINANCIAL YEAR HELPER
# ============================================================

def get_financial_year_dates(financial_year):
    """
    Convert Indian financial year format:

        2026-27

    into:

        2026-04-01
        2027-03-31
    """

    if not financial_year:
        financial_year = "2026-27"

    parts = financial_year.split("-")

    if len(parts) != 2:
        raise HTTPException(
            status_code=400,
            detail="Financial year must use format YYYY-YY.",
        )

    try:
        start_year = int(parts[0])
        end_short = int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Financial year must use format YYYY-YY.",
        )

    if end_short != (start_year + 1) % 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid financial year.",
        )

    start_date = date(
        start_year,
        4,
        1,
    )

    end_date = date(
        start_year + 1,
        3,
        31,
    )

    return (
        financial_year,
        start_date,
        end_date,
    )


# ============================================================
# LOAD INVESTMENT TRANSACTIONS
# ============================================================

def load_transactions(
    db: Session,
    user_id: int,
    end_date: date,
):
    """
    Load all BUY / SELL transactions up to the end of
    the requested financial year.

    Earlier BUY transactions are required because a SELL
    in the current FY may use a BUY lot from an earlier FY.
    """

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
              AND transaction_date <= :end_date
            ORDER BY
                transaction_date ASC,
                id ASC
            """
        ),
        {
            "user_id": user_id,
            "end_date": end_date,
        },
    )

    return [
        dict(row._mapping)
        for row in result
    ]


# ============================================================
# FIFO CAPITAL GAINS ENGINE
# ============================================================

def calculate_fifo_gains(
    transactions,
    start_date,
    end_date,
):
    """
    Calculate realised gains using FIFO.

    FIFO is maintained separately for each investment_id.

    Every SELL is matched against the oldest available BUY
    lots.

    Each matched lot records its own holding period.
    """

    # --------------------------------------------------------
    # FIFO BUY LOTS
    # --------------------------------------------------------

    buy_lots = {}

    realised_gains = []

    total_sale_proceeds = Decimal("0")
    total_cost_basis = Decimal("0")
    total_realised_gain_loss = Decimal("0")
    total_sell_fees = Decimal("0")
    total_buy_fees_allocated = Decimal("0")

    unmatched_quantity = Decimal("0")

    # --------------------------------------------------------
    # PROCESS TRANSACTIONS CHRONOLOGICALLY
    # --------------------------------------------------------

    for transaction in transactions:

        investment_id = transaction[
            "investment_id"
        ]

        transaction_type = (
            str(
                transaction[
                    "transaction_type"
                ]
            )
            .strip()
            .upper()
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

        transaction_date = transaction[
            "transaction_date"
        ]

        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if transaction_type == "BUY":

            gross_buy_value = (
                quantity * price
            )

            buy_lots.setdefault(
                investment_id,
                [],
            )

            buy_lots[
                investment_id
            ].append(
                {
                    "buy_transaction_id": (
                        transaction["id"]
                    ),
                    "buy_date": (
                        transaction_date
                    ),
                    "quantity_remaining": (
                        quantity
                    ),
                    "unit_price": (
                        price
                    ),
                    "total_buy_fee": (
                        fees
                    ),
                    "gross_buy_value": (
                        gross_buy_value
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # SELL
        # ----------------------------------------------------

        if transaction_type != "SELL":
            continue

        remaining_quantity = quantity

        lots = buy_lots.setdefault(
            investment_id,
            [],
        )

        matched_lots = []

        total_matched_quantity = (
            Decimal("0")
        )

        total_allocated_cost = (
            Decimal("0")
        )

        total_allocated_buy_fees = (
            Decimal("0")
        )

        # ----------------------------------------------------
        # FIFO LOT CONSUMPTION
        # ----------------------------------------------------

        while (
            remaining_quantity > 0
            and lots
        ):

            lot = lots[0]

            lot_quantity = lot[
                "quantity_remaining"
            ]

            matched_quantity = min(
                remaining_quantity,
                lot_quantity,
            )

            # ------------------------------------------------
            # ALLOCATE BUY FEE
            # ------------------------------------------------

            if lot_quantity > 0:

                allocated_buy_fee = (
                    lot["total_buy_fee"]
                    * (
                        matched_quantity
                        / lot_quantity
                    )
                )

            else:

                allocated_buy_fee = (
                    Decimal("0")
                )

            # ------------------------------------------------
            # ACQUISITION COST
            # ------------------------------------------------

            gross_acquisition_cost = (
                matched_quantity
                * lot["unit_price"]
            )

            acquisition_cost = (
                gross_acquisition_cost
                + allocated_buy_fee
            )

            # ------------------------------------------------
            # HOLDING PERIOD
            # ------------------------------------------------

            holding_days = (
                transaction_date
                - lot["buy_date"]
            ).days

            matched_lots.append(
                {
                    "buy_transaction_id": (
                        lot[
                            "buy_transaction_id"
                        ]
                    ),
                    "buy_date": (
                        lot["buy_date"]
                    ),
                    "quantity": (
                        matched_quantity
                    ),
                    "buy_price": (
                        lot["unit_price"]
                    ),
                    "allocated_buy_fee": (
                        allocated_buy_fee
                    ),
                    "cost_basis": (
                        acquisition_cost
                    ),
                    "holding_days": (
                        holding_days
                    ),
                }
            )

            total_matched_quantity += (
                matched_quantity
            )

            total_allocated_cost += (
                acquisition_cost
            )

            total_allocated_buy_fees += (
                allocated_buy_fee
            )

            lot[
                "quantity_remaining"
            ] -= matched_quantity

            remaining_quantity -= (
                matched_quantity
            )

            # ------------------------------------------------
            # REMOVE FULLY CONSUMED LOT
            # ------------------------------------------------

            if lot[
                "quantity_remaining"
            ] <= 0:

                lots.pop(0)

        # ----------------------------------------------------
        # UNMATCHED SELL QUANTITY
        # ----------------------------------------------------

        if remaining_quantity > 0:

            unmatched_quantity += (
                remaining_quantity
            )

        # ----------------------------------------------------
        # ONLY REPORT SALES INSIDE REQUESTED FY
        # ----------------------------------------------------

        if (
            transaction_date < start_date
            or transaction_date > end_date
        ):
            continue

        # ----------------------------------------------------
        # MATCHED SALE
        # ----------------------------------------------------

        if total_matched_quantity <= 0:
            continue

        # ----------------------------------------------------
        # SALE PROCEEDS
        # ----------------------------------------------------

        gross_sale_proceeds = (
            total_matched_quantity
            * price
        )

        # Allocate SELL fee only to the matched quantity.
        if quantity > 0:

            allocated_sell_fee = (
                fees
                * (
                    total_matched_quantity
                    / quantity
                )
            )

        else:

            allocated_sell_fee = (
                Decimal("0")
            )

        net_sale_proceeds = (
            gross_sale_proceeds
            - allocated_sell_fee
        )

        # ----------------------------------------------------
        # REALISED GAIN / LOSS
        # ----------------------------------------------------

        realised_gain_loss = (
            net_sale_proceeds
            - total_allocated_cost
        )

        # ----------------------------------------------------
        # WEIGHTED AVERAGE HOLDING DAYS
        # ----------------------------------------------------

        weighted_holding_days = (
            Decimal("0")
        )

        if total_matched_quantity > 0:

            for lot in matched_lots:

                weighted_holding_days += (
                    Decimal(
                        str(
                            lot[
                                "holding_days"
                            ]
                        )
                    )
                    * lot["quantity"]
                )

            weighted_holding_days = (
                weighted_holding_days
                / total_matched_quantity
            )

        # ----------------------------------------------------
        # TOTALS
        # ----------------------------------------------------

        total_sale_proceeds += (
            net_sale_proceeds
        )

        total_cost_basis += (
            total_allocated_cost
        )

        total_realised_gain_loss += (
            realised_gain_loss
        )

        total_sell_fees += (
            allocated_sell_fee
        )

        total_buy_fees_allocated += (
            total_allocated_buy_fees
        )

        # ----------------------------------------------------
        # TRANSACTION RESULT
        # ----------------------------------------------------

        realised_gains.append(
            {
                "sell_transaction_id": (
                    transaction["id"]
                ),
                "investment_id": (
                    investment_id
                ),
                "sale_date": (
                    transaction_date
                ),
                "quantity_sold": (
                    total_matched_quantity
                ),
                "sale_price": price,
                "gross_sale_proceeds": (
                    gross_sale_proceeds
                ),
                "sell_fees": (
                    allocated_sell_fee
                ),
                "net_sale_proceeds": (
                    net_sale_proceeds
                ),
                "cost_basis": (
                    total_allocated_cost
                ),
                "realised_gain_loss": (
                    realised_gain_loss
                ),
                "holding_days": (
                    weighted_holding_days
                ),
                "matched_lots": matched_lots,
            }
        )

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "transactions": realised_gains,
        "summary": {
            "sale_count": len(
                realised_gains
            ),
            "total_sale_proceeds": (
                total_sale_proceeds
            ),
            "total_cost_basis": (
                total_cost_basis
            ),
            "total_realised_gain_loss": (
                total_realised_gain_loss
            ),
            "total_sell_fees": (
                total_sell_fees
            ),
            "total_buy_fees_allocated": (
                total_buy_fees_allocated
            ),
            "unmatched_quantity": (
                unmatched_quantity
            ),
        },
    }


# ============================================================
# CAPITAL GAINS API
# ============================================================

@router.get("/")
def capital_gains(
    user_id: int,
    financial_year: str = "2026-27",
    db: Session = Depends(get_db),
):
    """
    Return FY-wise realised capital-gain data.

    This endpoint is READ-ONLY.
    """

    # --------------------------------------------------------
    # FINANCIAL YEAR
    # --------------------------------------------------------

    (
        resolved_financial_year,
        start_date,
        end_date,
    ) = get_financial_year_dates(
        financial_year
    )

    # --------------------------------------------------------
    # LOAD LEDGER
    # --------------------------------------------------------

    transactions = load_transactions(
        db=db,
        user_id=user_id,
        end_date=end_date,
    )

    # --------------------------------------------------------
    # CALCULATE FIFO GAINS
    # --------------------------------------------------------

    result = calculate_fifo_gains(
        transactions=transactions,
        start_date=start_date,
        end_date=end_date,
    )

    summary = result[
        "summary"
    ]

    # --------------------------------------------------------
    # TAX CLASSIFICATION
    # --------------------------------------------------------

    return {
        "status": "success",
        "user_id": user_id,

        "capital_gains_engine": {
            "name": (
                "Capital Gains Data Engine"
            ),
            "version": "1.1",
            "read_only": True,
        },

        "financial_year": (
            resolved_financial_year
        ),

        "start_date": start_date,

        "end_date": end_date,

        "data_source": (
            "investment_transactions"
        ),

        "method": "FIFO",

        "tax_classification": {
            "status": "not_calculated",
            "message": (
                "STCG/LTCG classification and "
                "tax liability are not calculated "
                "by Capital Gains Data Engine v1.1."
            ),
        },

        "summary": summary,

        "realised_transactions": (
            result[
                "transactions"
            ]
        ),

        "transaction_count": len(
            transactions
        ),
    }
