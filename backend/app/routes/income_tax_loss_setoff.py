# ============================================================
# FINANCIAL OS
# INCOME TAX & LOSS SET-OFF ENGINE
# ============================================================
#
# Version: 1.0
#
# Purpose:
#   - Read current-year realised capital gains/losses
#   - Separate STCG, LTCG, STCL and LTCL
#   - Apply current-year capital-loss set-off rules
#   - Show remaining taxable capital gains
#   - Show unavailable income/loss information
#
# IMPORTANT:
#   This engine is READ-ONLY.
#
#   It does NOT modify the database.
#
#   It does NOT calculate:
#   - Salary income
#   - Business/professional income
#   - House-property income
#   - Other-source income
#   - Brought-forward losses
#   - TDS/TCS
#   - Final income-tax liability
#   - Final ITR
#
# ============================================================


from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.ownership import require_matching_user_id

from app.routes.tax_liability import (
    get_financial_year_dates,
    load_investments,
    load_investment_transactions,
    calculate_fifo_sales,
    classify_sale,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/income-tax-loss-setoff",
    tags=["Income Tax & Loss Set-off Engine"],
)


# ============================================================
# HELPERS
# ============================================================

def to_decimal(value):
    """
    Safely convert values to Decimal.
    """

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


def money(value):
    """
    Round financial values to two decimal places.
    """

    return to_decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# CAPITAL GAIN CLASSIFICATION
# ============================================================

def build_capital_gain_buckets(sales):
    """
    Separate realised capital gains/losses into:

        STCG
        LTCG
        STCL
        LTCL
        UNCLASSIFIED

    Each sale remains separate so that the engine can show
    exactly how the current-year set-off was calculated.
    """

    buckets = {
        "stcg_gain": Decimal("0"),
        "ltcg_gain": Decimal("0"),
        "stcl_loss": Decimal("0"),
        "ltcl_loss": Decimal("0"),
        "unclassified_gain": Decimal("0"),
        "unclassified_loss": Decimal("0"),
    }

    sale_details = []

    for sale in sales:

        classification = classify_sale(
            sale
        )

        gain_loss = to_decimal(
            sale[
                "realised_gain_loss"
            ]
        )

        classification_name = (
            classification[
                "classification"
            ]
        )

        # ----------------------------------------------------
        # STCG / STCL
        # ----------------------------------------------------

        if classification_name == "STCG":

            if gain_loss >= 0:

                buckets[
                    "stcg_gain"
                ] += gain_loss

            else:

                buckets[
                    "stcl_loss"
                ] += abs(gain_loss)

        # ----------------------------------------------------
        # LTCG / LTCL
        # ----------------------------------------------------

        elif classification_name == "LTCG":

            if gain_loss >= 0:

                buckets[
                    "ltcg_gain"
                ] += gain_loss

            else:

                buckets[
                    "ltcl_loss"
                ] += abs(gain_loss)

        # ----------------------------------------------------
        # UNCLASSIFIED
        # ----------------------------------------------------

        else:

            if gain_loss >= 0:

                buckets[
                    "unclassified_gain"
                ] += gain_loss

            else:

                buckets[
                    "unclassified_loss"
                ] += abs(gain_loss)

        # ----------------------------------------------------
        # SALE DETAIL
        # ----------------------------------------------------

        sale_details.append(
            {
                "sell_transaction_id":
                    sale[
                        "sell_transaction_id"
                    ],

                "investment_id":
                    sale[
                        "investment_id"
                    ],

                "investment_name":
                    sale[
                        "investment_name"
                    ],

                "symbol":
                    sale[
                        "symbol"
                    ],

                "asset_class":
                    classification[
                        "asset_class"
                    ],

                "classification":
                    classification_name,

                "sale_date":
                    sale[
                        "sale_date"
                    ],

                "realised_gain_loss":
                    money(
                        gain_loss
                    ),

                "holding_days":
                    sale[
                        "holding_days"
                    ],
            }
        )

    return (
        buckets,
        sale_details,
    )


# ============================================================
# CURRENT-YEAR CAPITAL LOSS SET-OFF
# ============================================================

def calculate_capital_loss_setoff(
    stcg_gain,
    ltcg_gain,
    stcl_loss,
    ltcl_loss,
):
    """
    Apply current-year capital-loss set-off rules.

    Rules used:

    1. STCL can be set off against:
       - STCG
       - LTCG

    2. LTCL can be set off only against:
       - LTCG

    The engine uses STCL against STCG first.
    Remaining STCL can then reduce LTCG.

    LTCL is then applied against remaining LTCG.
    """

    # --------------------------------------------------------
    # STARTING VALUES
    # --------------------------------------------------------

    remaining_stcg = max(
        stcg_gain,
        Decimal("0"),
    )

    remaining_ltcg = max(
        ltcg_gain,
        Decimal("0"),
    )

    remaining_stcl = max(
        stcl_loss,
        Decimal("0"),
    )

    remaining_ltcl = max(
        ltcl_loss,
        Decimal("0"),
    )

    # --------------------------------------------------------
    # STCL -> STCG
    # --------------------------------------------------------

    stcl_against_stcg = min(
        remaining_stcl,
        remaining_stcg,
    )

    remaining_stcl -= (
        stcl_against_stcg
    )

    remaining_stcg -= (
        stcl_against_stcg
    )

    # --------------------------------------------------------
    # STCL -> LTCG
    # --------------------------------------------------------

    stcl_against_ltcg = min(
        remaining_stcl,
        remaining_ltcg,
    )

    remaining_stcl -= (
        stcl_against_ltcg
    )

    remaining_ltcg -= (
        stcl_against_ltcg
    )

    # --------------------------------------------------------
    # LTCL -> LTCG
    # --------------------------------------------------------

    ltcl_against_ltcg = min(
        remaining_ltcl,
        remaining_ltcg,
    )

    remaining_ltcl -= (
        ltcl_against_ltcg
    )

    remaining_ltcg -= (
        ltcl_against_ltcg
    )

    # --------------------------------------------------------
    # TOTAL SET-OFF
    # --------------------------------------------------------

    total_stcl_setoff = (
        stcl_against_stcg
        + stcl_against_ltcg
    )

    total_ltcl_setoff = (
        ltcl_against_ltcg
    )

    total_setoff = (
        total_stcl_setoff
        + total_ltcl_setoff
    )

    # --------------------------------------------------------
    # UNABSORBED CURRENT-YEAR LOSSES
    # --------------------------------------------------------

    unabsorbed_stcl = (
        remaining_stcl
    )

    unabsorbed_ltcl = (
        remaining_ltcl
    )

    return {
        "stcl_against_stcg":
            stcl_against_stcg,

        "stcl_against_ltcg":
            stcl_against_ltcg,

        "ltcl_against_ltcg":
            ltcl_against_ltcg,

        "total_stcl_setoff":
            total_stcl_setoff,

        "total_ltcl_setoff":
            total_ltcl_setoff,

        "total_setoff":
            total_setoff,

        "remaining_stcg":
            remaining_stcg,

        "remaining_ltcg":
            remaining_ltcg,

        "unabsorbed_stcl":
            unabsorbed_stcl,

        "unabsorbed_ltcl":
            unabsorbed_ltcl,
    }


# ============================================================
# ENDPOINT
# ============================================================

@router.get("/", dependencies=[Depends(require_matching_user_id)])
def get_income_tax_loss_setoff(
    user_id: int,
    financial_year: str = "2026-27",
    db: Session = Depends(get_db),
):
    """
    Return current-year capital-gains loss set-off analysis.
    """

    # ========================================================
    # FINANCIAL YEAR
    # ========================================================

    try:

        start_date, end_date = (
            get_financial_year_dates(
                financial_year
            )
        )

    except ValueError as error:

        return {
            "status": "error",
            "message": str(error),
        }

    # ========================================================
    # LOAD EXISTING INVESTMENT DATA
    # ========================================================

    investments = load_investments(
        db,
        user_id,
    )

    transactions = (
        load_investment_transactions(
            db,
            user_id,
            end_date,
        )
    )

    # ========================================================
    # FIFO REALISED SALES
    # ========================================================

    sales = calculate_fifo_sales(
        investments,
        transactions,
        start_date,
        end_date,
    )

    # ========================================================
    # BUILD GAIN/LOSS BUCKETS
    # ========================================================

    buckets, sale_details = (
        build_capital_gain_buckets(
            sales
        )
    )

    # ========================================================
    # CURRENT-YEAR SET-OFF
    # ========================================================

    setoff = calculate_capital_loss_setoff(
        stcg_gain=buckets[
            "stcg_gain"
        ],

        ltcg_gain=buckets[
            "ltcg_gain"
        ],

        stcl_loss=buckets[
            "stcl_loss"
        ],

        ltcl_loss=buckets[
            "ltcl_loss"
        ],
    )

    # ========================================================
    # UNCLASSIFIED AMOUNTS
    # ========================================================

    unclassified_total = (
        buckets[
            "unclassified_gain"
        ]
        + buckets[
            "unclassified_loss"
        ]
    )

    # ========================================================
    # STATUS
    # ========================================================

    if (
        buckets[
            "unclassified_gain"
        ] > 0
        or buckets[
            "unclassified_loss"
        ] > 0
    ):

        engine_status = (
            "requires_asset_classification"
        )

    else:

        engine_status = (
            "capital_loss_setoff_calculated"
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "status": "success",

        "user_id": user_id,

        "engine": {

            "name":
                "Income Tax & Loss Set-off Engine",

            "version":
                "1.0",

            "read_only":
                True,

            "status":
                engine_status,
        },

        "financial_year": {

            "financial_year":
                financial_year,

            "start_date":
                start_date,

            "end_date":
                end_date,
        },

        # ====================================================
        # CURRENT-YEAR CAPITAL GAINS / LOSSES
        # ====================================================

        "current_year_capital_gains": {

            "stcg_gain":
                money(
                    buckets[
                        "stcg_gain"
                    ]
                ),

            "ltcg_gain":
                money(
                    buckets[
                        "ltcg_gain"
                    ]
                ),

            "stcl_loss":
                money(
                    buckets[
                        "stcl_loss"
                    ]
                ),

            "ltcl_loss":
                money(
                    buckets[
                        "ltcl_loss"
                    ]
                ),

            "unclassified_gain":
                money(
                    buckets[
                        "unclassified_gain"
                    ]
                ),

            "unclassified_loss":
                money(
                    buckets[
                        "unclassified_loss"
                    ]
                ),
        },

        # ====================================================
        # SET-OFF RULES
        # ====================================================

        "setoff_rules": {

            "short_term_capital_loss":

                "Can be set off against STCG and LTCG.",

            "long_term_capital_loss":

                "Can be set off only against LTCG.",

            "capital_loss_carry_forward":

                "Unabsorbed capital losses may be carried forward subject to applicable return-filing and statutory conditions.",

            "maximum_carry_forward_years":
                8,
        },

        # ====================================================
        # CURRENT-YEAR SET-OFF
        # ====================================================

        "current_year_setoff": {

            "stcl_against_stcg":
                money(
                    setoff[
                        "stcl_against_stcg"
                    ]
                ),

            "stcl_against_ltcg":
                money(
                    setoff[
                        "stcl_against_ltcg"
                    ]
                ),

            "ltcl_against_ltcg":
                money(
                    setoff[
                        "ltcl_against_ltcg"
                    ]
                ),

            "total_stcl_setoff":
                money(
                    setoff[
                        "total_stcl_setoff"
                    ]
                ),

            "total_ltcl_setoff":
                money(
                    setoff[
                        "total_ltcl_setoff"
                    ]
                ),

            "total_setoff":
                money(
                    setoff[
                        "total_setoff"
                    ]
                ),
        },

        # ====================================================
        # REMAINING CAPITAL GAINS
        # ====================================================

        "remaining_capital_gains": {

            "remaining_stcg":
                money(
                    setoff[
                        "remaining_stcg"
                    ]
                ),

            "remaining_ltcg":
                money(
                    setoff[
                        "remaining_ltcg"
                    ]
                ),

            "total_remaining_capital_gains":
                money(
                    setoff[
                        "remaining_stcg"
                    ]
                    + setoff[
                        "remaining_ltcg"
                    ]
                ),
        },

        # ====================================================
        # UNABSORBED CURRENT-YEAR LOSSES
        # ====================================================

        "unabsorbed_current_year_losses": {

            "stcl":
                money(
                    setoff[
                        "unabsorbed_stcl"
                    ]
                ),

            "ltcl":
                money(
                    setoff[
                        "unabsorbed_ltcl"
                    ]
                ),

            "total":
                money(
                    setoff[
                        "unabsorbed_stcl"
                    ]
                    + setoff[
                        "unabsorbed_ltcl"
                    ]
                ),
        },

        # ====================================================
        # BROUGHT-FORWARD LOSSES
        # ====================================================

        "brought_forward_losses": {

            "available":
                False,

            "stcl":
                None,

            "ltcl":
                None,

            "reason":
                "Financial OS does not yet contain verified brought-forward capital-loss records.",
        },

        # ====================================================
        # OTHER INCOME HEADS
        # ====================================================

        "other_income_heads": {

            "salary":
                {
                    "available": False,
                },

            "business_profession":
                {
                    "available": False,
                },

            "house_property":
                {
                    "available": False,
                },

            "other_sources":
                {
                    "available": False,
                },
        },

        # ====================================================
        # FINAL TAXABLE INCOME
        # ====================================================

        "taxable_income_context": {

            "status":
                "incomplete",

            "reason":
                "Complete income under all applicable heads, deductions and brought-forward losses are required before final taxable income can be calculated.",

            "capital_gains_after_current_year_setoff":
                money(
                    setoff[
                        "remaining_stcg"
                    ]
                    + setoff[
                        "remaining_ltcg"
                    ]
                ),
        },

        # ====================================================
        # SALE DETAILS
        # ====================================================

        "sale_count":
            len(sale_details),

        "sales":
            sale_details,

        # ====================================================
        # SCOPE
        # ====================================================

        "scope": {

            "current_year_capital_gains":
                True,

            "current_year_capital_loss_setoff":
                True,

            "brought_forward_capital_losses":
                False,

            "salary_income":
                False,

            "business_income":
                False,

            "house_property_income":
                False,

            "other_source_income":
                False,

            "deductions":
                False,

            "final_taxable_income":
                False,

            "final_tax_liability":
                False,

            "itr_calculation":
                False,
        },

        # ====================================================
        # NEXT ENGINE
        # ====================================================

        "next_engine":
            "Income Aggregation & Taxable Income Engine",
    }
