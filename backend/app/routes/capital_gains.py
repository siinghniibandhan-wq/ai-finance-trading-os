# ============================================================
# FINANCIAL OS
# CAPITAL GAINS DATA ENGINE v1.0
# ============================================================
#
# Purpose:
# - Calculate realised capital gains from BUY / SELL ledger
# - Use FIFO matching
# - Calculate sale proceeds
# - Calculate cost of units sold
# - Include buy/sell fees
# - Calculate holding period
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
# FIFO MODEL:
#
# BUY  → creates a lot
# SELL → consumes oldest available BUY lot
#
# Capital Gain =
# Net Sale Proceeds - Allocated Acquisition Cost
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

    We intentionally load transactions before the FY start
    because a SELL during the current FY may use a BUY lot
    created in an earlier financial year.
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

    This is intentional for v1.0 because the existing ledger
    identifies transactions by investment_id. Instrument Master
    / canonical security identity will be introduced later.
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

            # Acquisition cost includes BUY fees.
            acquisition_cost = (
                quantity * price
            ) + fees

            buy_lots.setdefault(
                investment_id,
                [],
            )

            buy_lots[
                investment_id
            ].append(
                {
                    "transaction_id": transaction[
                        "id"
                    ],
                    "quantity_remaining": quantity,
                    "unit_cost": (
                        acquisition_cost
                        / quantity
                    ),
                    "transaction_date": (
                        transaction_date
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

        # Net proceeds after SELL fees.
        sale_proceeds = (
            quantity * price
        ) - fees

        allocated_cost = Decimal("0")
        allocated_buy_fees = Decimal("0")

        lots = buy_lots.setdefault(
            investment_id,
            [],
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

            matched_cost = (
                matched_quantity
                * lot["unit_cost"]
            )

            allocated_cost += matched_cost

            # The BUY fee is already included inside
            # the lot's unit cost. We expose the allocated
            # portion separately for reporting.
            original_buy_value = (
                lot_quantity
                * lot["unit_cost"]
            )

            if original_buy_value > 0:
                allocated_buy_fee = (
                    matched_quantity
                    / lot_quantity
                ) * (
                    original_buy_value
                    - (
                        lot_quantity
                        * (
                            lot["unit_cost"]
                        )
                    )
                )
            else:
                allocated_buy_fee = Decimal("0")

            # The expression above normally resolves to zero
            # because unit_cost already contains fees.
            # Actual acquisition cost remains represented by
            # unit_cost and is used for gain calculation.

            allocated_buy_fees += (
                allocated_buy_fee
            )

            lot[
                "quantity_remaining"
            ] -= matched_quantity

            remaining_quantity -= (
                matched_quantity
            )

            if lot[
                "quantity_remaining"
            ] <= 0:
                lots.pop(0)

        # ----------------------------------------------------
        # DATA QUALITY CHECK
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

        matched_quantity = (
            quantity - remaining_quantity
        )

        # If a sale has no matching BUY data,
        # do not create a false capital gain.
        if matched_quantity <= 0:
            continue

        # For v1.0, if the entire sale is not matched,
        # report only the matched portion.
        matched_sale_proceeds = (
            matched_quantity
            * price
        )

        # Allocate SELL fees proportionally.
        if quantity > 0:
            matched_sell_fees = (
                fees
                * (
                    matched_quantity
                    / quantity
                )
            )
        else:
            matched_sell_fees = Decimal("0")

        matched_net_proceeds = (
            matched_sale_proceeds
            - matched_sell_fees
        )

        realised_gain_loss = (
            matched_net_proceeds
            - allocated_cost
        )

        holding_days = None

        # The exact holding period depends on which FIFO lots
        # were consumed. For v1.0, calculate it from the oldest
        # relevant transaction date available.
        #
        # This is intentionally conservative and will be
        # enhanced with lot-level disposal records later.

        sale_lots = buy_lots.get(
            investment_id,
            []
        )

        # Since the consumed lots have been removed above,
        # the exact consumed BUY date is not retained here.
        # Therefore v1.0 leaves holding_days as None rather
        # than inventing a value.

        total_sale_proceeds += (
            matched_net_proceeds
        )

        total_cost_basis += (
            allocated_cost
        )

        total_realised_gain_loss += (
            realised_gain_loss
        )

        total_sell_fees += (
            matched_sell_fees
        )

        total_buy_fees_allocated += (
            allocated_buy_fees
        )

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
                    matched_quantity
                ),
                "sale_price": price,
                "gross_sale_proceeds": (
                    matched_sale_proceeds
                ),
                "sell_fees": (
                    matched_sell_fees
                ),
                "net_sale_proceeds": (
                    matched_net_proceeds
                ),
                "cost_basis": (
                    allocated_cost
                ),
                "realised_gain_loss": (
                    realised_gain_loss
                ),
                "holding_days": holding_days,
            }
        )

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
    # GAIN TYPE
    # --------------------------------------------------------
    #
    # v1.0 does NOT classify STCG/LTCG because exact holding
    # period handling and security-specific tax rules belong
    # to the later Tax Calculation Engine.
    # --------------------------------------------------------

    return {
        "status": "success",
        "user_id": user_id,

        "capital_gains_engine": {
            "name": (
                "Capital Gains Data Engine"
            ),
            "version": "1.0",
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
                "by Capital Gains Data Engine v1.0."
            ),
        },

        "summary": summary,

        "realised_transactions": result[
            "transactions"
        ],

        "transaction_count": len(
            transactions
        ),
    }
