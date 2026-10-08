"""
============================================================
FINANCIAL OS
INCOME AGGREGATION & TAXABLE INCOME ENGINE
============================================================

Version: 1.1

Purpose:
- Aggregate verified income transactions.
- Calculate current-year capital gains/losses.
- Apply current-year capital-loss set-off.
- Provide a provisional income aggregation layer.
- Keep final taxable income separate until deductions,
  exemptions and all income heads are available.

IMPORTANT:
- Read-only.
- Does NOT modify the database.
- Does NOT calculate final tax liability.
- Does NOT depend on helper functions from the
  Income Tax & Loss Set-off Engine.
============================================================
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/income-tax-aggregation",
    tags=["Income Tax Aggregation"],
)


ENGINE_VERSION = "1.1"


# ============================================================
# TAX / CAPITAL-GAIN RULES
# ============================================================

STCG_THRESHOLD_DAYS = {
    "listed_equity": 365,
    "equity_oriented_mf": 365,
    "listed_other_security": 365,
    "unlisted_equity": 730,
    "unlisted_other_security": 730,
}


# ============================================================
# MONEY HELPER
# ============================================================

def money(value):
    """
    Round monetary values to two decimal places.
    """

    return float(
        Decimal(str(value or 0)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    )


# ============================================================
# DECIMAL HELPER
# ============================================================

def decimal(value):
    """
    Safely convert a value to Decimal.
    """

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


# ============================================================
# FINANCIAL YEAR
# ============================================================

def get_financial_year_dates(financial_year):
    """
    Convert YYYY-YY into Indian financial-year dates.

    Example:

        2026-27
        01-Apr-2026
        31-Mar-2027
    """

    parts = financial_year.split("-")

    if len(parts) != 2:
        raise ValueError(
            "financial_year must use YYYY-YY format."
        )

    start_year = int(parts[0])

    return (
        date(
            start_year,
            4,
            1,
        ),
        date(
            start_year + 1,
            3,
            31,
        ),
    )


# ============================================================
# ASSET CLASSIFICATION
# ============================================================

def resolve_asset_class(investment_type):
    """
    Resolve investment_type into the tax asset class used
    by the Financial OS.

    Unknown types remain unclassified.
    """

    value = str(
        investment_type or ""
    ).strip().lower()

    mapping = {

        "stock": "listed_equity",
        "stocks": "listed_equity",
        "equity": "listed_equity",
        "share": "listed_equity",
        "shares": "listed_equity",
        "listed equity": "listed_equity",
        "listed stock": "listed_equity",
        "listed shares": "listed_equity",

        "equity mutual fund":
            "equity_oriented_mf",

        "equity mutual funds":
            "equity_oriented_mf",

        "equity mf":
            "equity_oriented_mf",

        "equity-oriented mutual fund":
            "equity_oriented_mf",

        "equity-oriented mutual funds":
            "equity_oriented_mf",

        "unlisted equity":
            "unlisted_equity",

        "unlisted stock":
            "unlisted_equity",

        "unlisted shares":
            "unlisted_equity",

        "listed security":
            "listed_other_security",

        "listed securities":
            "listed_other_security",

        "bond":
            "listed_other_security",

        "bonds":
            "listed_other_security",

        "unlisted security":
            "unlisted_other_security",

        "unlisted securities":
            "unlisted_other_security",
    }

    return mapping.get(value)


# ============================================================
# LOAD INVESTMENTS
# ============================================================

def load_investments(
    db: Session,
    user_id: int,
):
    """
    Load investment master records.
    """

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                name,
                investment_type,
                symbol
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
# LOAD INVESTMENT TRANSACTIONS
# ============================================================

def load_investment_transactions(
    db: Session,
    user_id: int,
    end_date: date,
):
    """
    Load the investment transaction ledger up to FY end.

    Earlier BUY transactions are required because a current
    FY SELL can consume a BUY from a previous financial year.
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
                investment_id ASC,
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
# FIFO CAPITAL-GAIN CALCULATION
# ============================================================

def calculate_capital_gains(
    investments,
    transactions,
    start_date,
    end_date,
):
    """
    Calculate current-FY realised capital gains/losses using FIFO.

    BUY transactions create FIFO lots.

    SELL transactions consume the oldest available lots.

    Only SELL transactions occurring inside the requested
    financial year are reported as current-year realised gains.
    """

    investment_map = {
        investment["id"]: investment
        for investment in investments
    }

    lots_by_investment = {}

    current_year_sales = []

    unmatched_quantity = Decimal("0")

    # --------------------------------------------------------
    # PROCESS TRANSACTIONS
    # --------------------------------------------------------

    for transaction in transactions:

        investment_id = transaction[
            "investment_id"
        ]

        investment = investment_map.get(
            investment_id
        )

        if not investment:
            continue

        transaction_type = str(
            transaction[
                "transaction_type"
            ]
            or ""
        ).upper()

        quantity = decimal(
            transaction["quantity"]
        )

        price = decimal(
            transaction["price"]
        )

        fees = decimal(
            transaction.get("fees")
        )

        transaction_date = transaction[
            "transaction_date"
        ]

        if quantity <= 0:
            continue

        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if transaction_type == "BUY":

            lots_by_investment.setdefault(
                investment_id,
                [],
            )

            lots_by_investment[
                investment_id
            ].append(
                {
                    "transaction_id":
                        transaction["id"],

                    "buy_date":
                        transaction_date,

                    "quantity":
                        quantity,

                    "unit_price":
                        price,

                    "fees":
                        fees,
                }
            )

            continue

        # ----------------------------------------------------
        # SELL
        # ----------------------------------------------------

        if transaction_type != "SELL":
            continue

        # Current-year sale?
        if (
            transaction_date < start_date
            or transaction_date > end_date
        ):
            continue

        remaining_quantity = quantity

        matched_lots = []

        sale_proceeds = (
            quantity * price
        )

        sale_fee = fees

        sale_cost_basis = Decimal("0")

        holding_days_total = Decimal("0")

        holding_quantity_total = Decimal("0")

        lots = lots_by_investment.setdefault(
            investment_id,
            [],
        )

        # ----------------------------------------------------
        # FIFO
        # ----------------------------------------------------

        while (
            remaining_quantity > 0
            and lots
        ):

            lot = lots[0]

            available_quantity = decimal(
                lot["quantity"]
            )

            matched_quantity = min(
                remaining_quantity,
                available_quantity,
            )

            # ------------------------------------------------
            # BUY FEE ALLOCATION
            # ------------------------------------------------

            buy_fee_allocated = Decimal("0")

            if available_quantity > 0:
                buy_fee_allocated = (
                    lot["fees"]
                    * (
                        matched_quantity
                        / available_quantity
                    )
                )

            matched_cost = (
                matched_quantity
                * lot["unit_price"]
            )

            matched_cost += (
                buy_fee_allocated
            )

            sale_cost_basis += matched_cost

            # ------------------------------------------------
            # HOLDING PERIOD
            # ------------------------------------------------

            buy_date = lot[
                "buy_date"
            ]

            if buy_date:
                holding_days = (
                    transaction_date
                    - buy_date
                ).days

                holding_days_total += (
                    Decimal(
                        str(holding_days)
                    )
                    * matched_quantity
                )

                holding_quantity_total += (
                    matched_quantity
                )

            matched_lots.append(
                {
                    "buy_transaction_id":
                        lot[
                            "transaction_id"
                        ],

                    "buy_date":
                        (
                            buy_date.isoformat()
                            if buy_date
                            else None
                        ),

                    "quantity":
                        money(matched_quantity),

                    "buy_price":
                        money(
                            lot[
                                "unit_price"
                            ]
                        ),

                    "buy_fee_allocated":
                        money(
                            buy_fee_allocated
                        ),
                }
            )

            lot["quantity"] = (
                available_quantity
                - matched_quantity
            )

            remaining_quantity -= (
                matched_quantity
            )

            if lot["quantity"] <= 0:
                lots.pop(0)

        # ----------------------------------------------------
        # UNMATCHED SELL QUANTITY
        # ----------------------------------------------------

        if remaining_quantity > 0:

            unmatched_quantity += (
                remaining_quantity
            )

        matched_quantity_total = (
            quantity
            - remaining_quantity
        )

        matched_sale_proceeds = (
            matched_quantity_total
            * price
        )

        # Allocate sale fee only to matched quantity.
        allocated_sale_fee = Decimal("0")

        if quantity > 0:
            allocated_sale_fee = (
                sale_fee
                * (
                    matched_quantity_total
                    / quantity
                )
            )

        realised_gain_loss = (
            matched_sale_proceeds
            - allocated_sale_fee
            - sale_cost_basis
        )

        weighted_holding_days = None

        if holding_quantity_total > 0:

            weighted_holding_days = (
                holding_days_total
                / holding_quantity_total
            )

        asset_class = resolve_asset_class(
            investment.get(
                "investment_type"
            )
        )

        classification = "UNCLASSIFIED"

        threshold_days = None

        if asset_class:

            threshold_days = (
                STCG_THRESHOLD_DAYS.get(
                    asset_class
                )
            )

            if (
                weighted_holding_days
                is not None
                and threshold_days is not None
            ):

                if (
                    weighted_holding_days
                    < Decimal(
                        str(
                            threshold_days
                        )
                    )
                ):
                    classification = "STCG"

                else:
                    classification = "LTCG"

        current_year_sales.append(
            {
                "sale_transaction_id":
                    transaction["id"],

                "investment_id":
                    investment_id,

                "name":
                    investment.get(
                        "name"
                    ),

                "symbol":
                    investment.get(
                        "symbol"
                    ),

                "investment_type":
                    investment.get(
                        "investment_type"
                    ),

                "asset_class":
                    asset_class,

                "classification":
                    classification,

                "sale_date":
                    (
                        transaction_date.isoformat()
                        if transaction_date
                        else None
                    ),

                "quantity":
                    money(quantity),

                "matched_quantity":
                    money(
                        matched_quantity_total
                    ),

                "unmatched_quantity":
                    money(
                        remaining_quantity
                    ),

                "sale_price":
                    money(price),

                "sale_proceeds":
                    money(
                        matched_sale_proceeds
                    ),

                "cost_basis":
                    money(
                        sale_cost_basis
                    ),

                "sale_fee":
                    money(
                        allocated_sale_fee
                    ),

                "realised_gain_loss":
                    money(
                        realised_gain_loss
                    ),

                "holding_days":
                    (
                        float(
                            weighted_holding_days
                        )
                        if weighted_holding_days
                        is not None
                        else None
                    ),

                "threshold_days":
                    threshold_days,

                "matched_lots":
                    matched_lots,
            }
        )

    # --------------------------------------------------------
    # TOTALS
    # --------------------------------------------------------

    stcg = Decimal("0")
    ltcg = Decimal("0")
    unclassified = Decimal("0")

    for sale in current_year_sales:

        gain = decimal(
            sale[
                "realised_gain_loss"
            ]
        )

        classification = sale[
            "classification"
        ]

        if classification == "STCG":

            stcg += gain

        elif classification == "LTCG":

            ltcg += gain

        else:

            unclassified += gain

    return {
        "sales": current_year_sales,
        "stcg": stcg,
        "ltcg": ltcg,
        "unclassified": unclassified,
        "unmatched_quantity":
            unmatched_quantity,
    }


# ============================================================
# CURRENT-YEAR LOSS SET-OFF
# ============================================================

def apply_loss_setoff(
    stcg,
    ltcg,
):
    """
    Apply current-year capital-loss set-off.

    Rules:

    STCL:
        First against STCG.
        Remaining STCL against LTCG.

    LTCL:
        Only against LTCG.

    Gains and losses are represented as signed values.
    """

    stcg = decimal(stcg)
    ltcg = decimal(ltcg)

    current_stcg_gain = max(
        stcg,
        Decimal("0"),
    )

    current_stcg_loss = max(
        -stcg,
        Decimal("0"),
    )

    current_ltcg_gain = max(
        ltcg,
        Decimal("0"),
    )

    current_ltcg_loss = max(
        -ltcg,
        Decimal("0"),
    )

    # --------------------------------------------------------
    # STCL → STCG
    # --------------------------------------------------------

    stcl_to_stcg = min(
        current_stcg_loss,
        current_stcg_gain,
    )

    remaining_stcl = (
        current_stcg_loss
        - stcl_to_stcg
    )

    remaining_stcg = (
        current_stcg_gain
        - stcl_to_stcg
    )

    # --------------------------------------------------------
    # STCL → LTCG
    # --------------------------------------------------------

    stcl_to_ltcg = min(
        remaining_stcl,
        current_ltcg_gain,
    )

    remaining_stcl -= (
        stcl_to_ltcg
    )

    remaining_ltcg = (
        current_ltcg_gain
        - stcl_to_ltcg
    )

    # --------------------------------------------------------
    # LTCL → LTCG
    # --------------------------------------------------------

    ltcl_to_ltcg = min(
        current_ltcg_loss,
        remaining_ltcg,
    )

    remaining_ltcg -= (
        ltcl_to_ltcg
    )

    remaining_ltcl = (
        current_ltcg_loss
        - ltcl_to_ltcg
    )

    return {
        "stcg_before_setoff":
            current_stcg_gain,

        "ltcg_before_setoff":
            current_ltcg_gain,

        "stcl_before_setoff":
            current_stcg_loss,

        "ltcl_before_setoff":
            current_ltcg_loss,

        "stcl_setoff_against_stcg":
            stcl_to_stcg,

        "stcl_setoff_against_ltcg":
            stcl_to_ltcg,

        "ltcl_setoff_against_ltcg":
            ltcl_to_ltcg,

        "remaining_stcg":
            remaining_stcg,

        "remaining_ltcg":
            remaining_ltcg,

        "unabsorbed_stcl":
            remaining_stcl,

        "unabsorbed_ltcl":
            remaining_ltcl,
    }


# ============================================================
# LOAD VERIFIED INCOME
# ============================================================

def load_income_transactions(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date,
):
    """
    Load only explicitly classified income,
    interest and dividend transactions.
    """

    result = db.execute(
        text(
            """
            SELECT
                id,
                transaction_date,
                transaction_type,
                amount
            FROM transactions
            WHERE user_id = :user_id
              AND transaction_date >= :start_date
              AND transaction_date <= :end_date
              AND transaction_type IN (
                  'income',
                  'interest',
                  'dividend'
              )
            ORDER BY
                transaction_date ASC,
                id ASC
            """
        ),
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    return [
        dict(row._mapping)
        for row in result
    ]


# ============================================================
# API ENDPOINT
# ============================================================

@router.get("/")
def income_tax_aggregation(
    user_id: int = Query(
        ...,
        ge=1,
    ),
    financial_year: str = Query(
        "2026-27"
    ),
    db: Session = Depends(get_db),
):
    """
    Aggregate verified income and current-year
    capital gains/losses.
    """

    # ========================================================
    # FINANCIAL YEAR
    # ========================================================

    start_date, end_date = (
        get_financial_year_dates(
            financial_year
        )
    )

    # ========================================================
    # VERIFIED INCOME
    # ========================================================

    income_transactions = (
        load_income_transactions(
            db,
            user_id,
            start_date,
            end_date,
        )
    )

    income_total = Decimal("0")
    interest_total = Decimal("0")
    dividend_total = Decimal("0")

    income_details = []

    for transaction in (
        income_transactions
    ):

        amount = decimal(
            transaction["amount"]
        )

        transaction_type = str(
            transaction[
                "transaction_type"
            ]
            or ""
        ).lower()

        if transaction_type == "income":

            income_total += amount

        elif transaction_type == "interest":

            interest_total += amount

        elif transaction_type == "dividend":

            dividend_total += amount

        income_details.append(
            {
                "transaction_id":
                    transaction["id"],

                "transaction_date":
                    (
                        transaction[
                            "transaction_date"
                        ].isoformat()
                        if transaction[
                            "transaction_date"
                        ]
                        else None
                    ),

                "transaction_type":
                    transaction_type,

                "amount":
                    money(amount),
            }
        )

    # ========================================================
    # CAPITAL GAINS
    # ========================================================

    investments = load_investments(
        db,
        user_id,
    )

    investment_transactions = (
        load_investment_transactions(
            db,
            user_id,
            end_date,
        )
    )

    capital_gains = (
        calculate_capital_gains(
            investments,
            investment_transactions,
            start_date,
            end_date,
        )
    )

    setoff = apply_loss_setoff(
        capital_gains["stcg"],
        capital_gains["ltcg"],
    )

    remaining_stcg = setoff[
        "remaining_stcg"
    ]

    remaining_ltcg = setoff[
        "remaining_ltcg"
    ]

    capital_gains_after_setoff = (
        remaining_stcg
        + remaining_ltcg
    )

    # ========================================================
    # VERIFIED NON-CAPITAL INCOME
    # ========================================================

    verified_non_capital_income = (
        income_total
        + interest_total
        + dividend_total
    )

    provisional_total = (
        verified_non_capital_income
        + capital_gains_after_setoff
    )

    # ========================================================
    # CURRENTLY UNAVAILABLE INCOME HEADS
    # ========================================================

    salary_available = False
    business_available = False
    house_property_available = False

    # ========================================================
    # AGGREGATION STATUS
    # ========================================================

    if (
        salary_available
        and business_available
        and house_property_available
    ):

        aggregation_status = "complete"

    elif (
        verified_non_capital_income != 0
        or capital_gains_after_setoff != 0
    ):

        aggregation_status = (
            "partial_income_data"
        )

    else:

        aggregation_status = (
            "income_data_unavailable"
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "success",

        "engine": (
            "Income Aggregation & "
            "Taxable Income Engine"
        ),

        "version": ENGINE_VERSION,

        "read_only": True,

        "financial_year": {
            "financial_year":
                financial_year,

            "start_date":
                start_date.isoformat(),

            "end_date":
                end_date.isoformat(),
        },

        "aggregation_status":
            aggregation_status,

        # ----------------------------------------------------
        # INCOME HEADS
        # ----------------------------------------------------

        "income_heads": {

            "salary": {
                "available":
                    salary_available,

                "amount":
                    None,

                "reason":
                    "No verified salary-income "
                    "source is currently available "
                    "in the Financial OS.",
            },

            "business_profession": {
                "available":
                    business_available,

                "amount":
                    None,

                "reason":
                    "No verified business/profession "
                    "income source is currently "
                    "available in the Financial OS.",
            },

            "house_property": {
                "available":
                    house_property_available,

                "amount":
                    None,

                "reason":
                    "No verified house-property "
                    "income source is currently "
                    "available in the Financial OS.",
            },

            "other_sources": {

                "available":
                    True,

                "income":
                    money(
                        income_total
                    ),

                "interest":
                    money(
                        interest_total
                    ),

                "dividend":
                    money(
                        dividend_total
                    ),

                "total":
                    money(
                        verified_non_capital_income
                    ),

                "source":
                    "Financial OS transactions",
            },
        },

        # ----------------------------------------------------
        # CAPITAL GAINS
        # ----------------------------------------------------

        "capital_gains": {

            "available":
                True,

            "stcg_before_setoff":
                money(
                    setoff[
                        "stcg_before_setoff"
                    ]
                ),

            "ltcg_before_setoff":
                money(
                    setoff[
                        "ltcg_before_setoff"
                    ]
                ),

            "stcl_before_setoff":
                money(
                    setoff[
                        "stcl_before_setoff"
                    ]
                ),

            "ltcl_before_setoff":
                money(
                    setoff[
                        "ltcl_before_setoff"
                    ]
                ),

            "stcl_setoff_against_stcg":
                money(
                    setoff[
                        "stcl_setoff_against_stcg"
                    ]
                ),

            "stcl_setoff_against_ltcg":
                money(
                    setoff[
                        "stcl_setoff_against_ltcg"
                    ]
                ),

            "ltcl_setoff_against_ltcg":
                money(
                    setoff[
                        "ltcl_setoff_against_ltcg"
                    ]
                ),

            "stcg_after_setoff":
                money(
                    remaining_stcg
                ),

            "ltcg_after_setoff":
                money(
                    remaining_ltcg
                ),

            "total_after_setoff":
                money(
                    capital_gains_after_setoff
                ),

            "unabsorbed_stcl":
                money(
                    setoff[
                        "unabsorbed_stcl"
                    ]
                ),

            "unabsorbed_ltcl":
                money(
                    setoff[
                        "unabsorbed_ltcl"
                    ]
                ),

            "sale_count":
                len(
                    capital_gains[
                        "sales"
                    ]
                ),

            "unmatched_quantity":
                money(
                    capital_gains[
                        "unmatched_quantity"
                    ]
                ),

            "source":
                "Current-year FIFO capital-gain "
                "calculation",
        },

        # ----------------------------------------------------
        # AGGREGATED VALUES
        # ----------------------------------------------------

        "aggregated_values": {

            "verified_non_capital_income":
                money(
                    verified_non_capital_income
                ),

            "capital_gains_after_setoff":
                money(
                    capital_gains_after_setoff
                ),

            "provisional_taxable_income":
                money(
                    provisional_total
                ),
        },

        # ----------------------------------------------------
        # TAXABLE INCOME STATUS
        # ----------------------------------------------------

        "taxable_income": {

            "status":
                "not_final",

            "amount":
                None,

            "provisional_amount":
                money(
                    provisional_total
                ),

            "reason":
                "Final taxable income requires "
                "all applicable income heads plus "
                "eligible deductions and exemptions.",
        },

        # ----------------------------------------------------
        # TRANSACTIONS
        # ----------------------------------------------------

        "transaction_summary": {

            "income_transaction_count":
                len(
                    income_transactions
                ),

            "income":
                money(
                    income_total
                ),

            "interest":
                money(
                    interest_total
                ),

            "dividend":
                money(
                    dividend_total
                ),

            "details":
                income_details,
        },

        # ----------------------------------------------------
        # CAPITAL-GAIN SALES
        # ----------------------------------------------------

        "capital_gain_sales":
            capital_gains[
                "sales"
            ],

        # ----------------------------------------------------
        # SCOPE
        # ----------------------------------------------------

        "scope": {

            "salary_income":
                salary_available,

            "business_profession_income":
                business_available,

            "house_property_income":
                house_property_available,

            "other_sources":
                True,

            "capital_gains":
                True,

            "deductions":
                False,

            "exempt_income":
                False,

            "final_taxable_income":
                False,

            "final_tax_liability":
                False,

            "database_write":
                False,
        },

        # ----------------------------------------------------
        # NEXT ENGINE
        # ----------------------------------------------------

        "next_engine":
            "Deductions & Exempt Income Engine",
    }
