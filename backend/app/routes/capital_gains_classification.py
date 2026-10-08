# ============================================================
# FINANCIAL OS
# CAPITAL GAINS CLASSIFICATION ENGINE v1.1
# ============================================================
#
# Purpose:
# - Classify realised capital gains as STCG / LTCG
# - Use verified FIFO results
# - Automatically resolve asset class from investments
# - Use actual FIFO holding period
#
# IMPORTANT:
# - READ-ONLY
# - Does NOT modify database data
# - Does NOT modify capital_gains.py
# - Does NOT calculate tax liability
# - Does NOT calculate tax rates
# - Does NOT guess unknown investment types
#
# FLOW:
#
# Investment
#     ↓
# Asset Classification Resolver
#     ↓
# FIFO Capital Gains Engine
#     ↓
# Holding Period
#     ↓
# STCG / LTCG
#
# ============================================================


from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.routes.capital_gains import (
    get_financial_year_dates,
    load_transactions,
    calculate_fifo_gains,
)

from app.routes.asset_classification import (
    resolve_asset_class,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/capital-gains-classification",
    tags=["Capital Gains Classification"],
)


# ============================================================
# HOLDING PERIOD RULES
# ============================================================

ASSET_CLASS_RULES = {

    "listed_equity": {
        "minimum_long_term_months": 12,
        "threshold_days": 365,
        "rule": (
            "Long-term when held for more than "
            "12 months."
        ),
    },

    "equity_oriented_mf": {
        "minimum_long_term_months": 12,
        "threshold_days": 365,
        "rule": (
            "Long-term when held for more than "
            "12 months."
        ),
    },

    "unlisted_equity": {
        "minimum_long_term_months": 24,
        "threshold_days": 730,
        "rule": (
            "Long-term when held for more than "
            "24 months."
        ),
    },

    "listed_other_security": {
        "minimum_long_term_months": 12,
        "threshold_days": 365,
        "rule": (
            "Long-term when held for more than "
            "12 months."
        ),
    },

    "unlisted_other_security": {
        "minimum_long_term_months": 24,
        "threshold_days": 730,
        "rule": (
            "Long-term when held for more than "
            "24 months."
        ),
    },
}


# ============================================================
# CLASSIFICATION HELPER
# ============================================================

def classify_gain(
    holding_days,
    asset_class,
):
    """
    Classify one realised gain.

    Conservative v1.1 rule:
    - Holding period must be available.
    - Asset class must be recognised.
    - Unknown asset classes remain UNCLASSIFIED.
    """

    if asset_class not in ASSET_CLASS_RULES:

        return {
            "classification": "UNCLASSIFIED",
            "classification_status": (
                "unknown_asset_class"
            ),
        }

    if holding_days is None:

        return {
            "classification": "UNCLASSIFIED",
            "classification_status": (
                "missing_holding_period"
            ),
        }

    rule = ASSET_CLASS_RULES[
        asset_class
    ]

    threshold_days = rule[
        "threshold_days"
    ]

    if holding_days > threshold_days:

        return {
            "classification": "LTCG",
            "classification_status": (
                "classified"
            ),
            "threshold_days": (
                threshold_days
            ),
            "threshold_months": (
                rule[
                    "minimum_long_term_months"
                ]
            ),
        }

    return {
        "classification": "STCG",
        "classification_status": (
            "classified"
        ),
        "threshold_days": (
            threshold_days
        ),
        "threshold_months": (
            rule[
                "minimum_long_term_months"
            ]
        ),
    }


# ============================================================
# LOAD INVESTMENT ASSET CLASSES
# ============================================================

def load_asset_classes(
    db: Session,
    user_id: int,
):
    """
    Load investments and automatically resolve their
    asset classes using the Asset Classification Resolver.
    """

    result = db.execute(
        text(
            """
            SELECT
                id,
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

    asset_classes = {}

    for row in result:

        investment = dict(
            row._mapping
        )

        resolution = (
            resolve_asset_class(
                investment[
                    "investment_type"
                ]
            )
        )

        asset_classes[
            investment["id"]
        ] = {
            "investment_id": (
                investment["id"]
            ),
            "name": (
                investment["name"]
            ),
            "investment_type": (
                investment[
                    "investment_type"
                ]
            ),
            "symbol": (
                investment["symbol"]
            ),
            "asset_class": (
                resolution[
                    "asset_class"
                ]
            ),
            "classification_status": (
                resolution[
                    "status"
                ]
            ),
            "classification_reason": (
                resolution[
                    "reason"
                ]
            ),
        }

    return asset_classes


# ============================================================
# API
# ============================================================

@router.get("/")
def capital_gains_classification(
    user_id: int,
    financial_year: str = "2026-27",
    db: Session = Depends(get_db),
):
    """
    Automatically classify realised capital gains.

    Asset class is resolved from the existing investments
    table through the Asset Classification Resolver.
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
    # LOAD INVESTMENT ASSET CLASSES
    # --------------------------------------------------------

    asset_classes = load_asset_classes(
        db=db,
        user_id=user_id,
    )

    # --------------------------------------------------------
    # LOAD INVESTMENT TRANSACTIONS
    # --------------------------------------------------------

    transactions = load_transactions(
        db=db,
        user_id=user_id,
        end_date=end_date,
    )

    # --------------------------------------------------------
    # FIFO CAPITAL GAINS
    # --------------------------------------------------------

    result = calculate_fifo_gains(
        transactions=transactions,
        start_date=start_date,
        end_date=end_date,
    )

    classified_transactions = []

    total_stcg = Decimal("0")
    total_ltcg = Decimal("0")
    total_unclassified = Decimal("0")

    classified_count = 0
    unclassified_count = 0

    # --------------------------------------------------------
    # CLASSIFY EACH REALISED TRANSACTION
    # --------------------------------------------------------

    for transaction in result[
        "transactions"
    ]:

        investment_id = (
            transaction[
                "investment_id"
            ]
        )

        investment_info = (
            asset_classes.get(
                investment_id
            )
        )

        if investment_info is None:

            asset_class = (
                "UNCLASSIFIED"
            )

            asset_status = (
                "investment_not_found"
            )

            asset_reason = (
                "Investment record was not "
                "found for this transaction."
            )

        else:

            asset_class = (
                investment_info[
                    "asset_class"
                ]
            )

            asset_status = (
                investment_info[
                    "classification_status"
                ]
            )

            asset_reason = (
                investment_info[
                    "classification_reason"
                ]
            )

        classification = classify_gain(
            holding_days=(
                transaction[
                    "holding_days"
                ]
            ),
            asset_class=asset_class,
        )

        classification_name = (
            classification[
                "classification"
            ]
        )

        gain_loss = Decimal(
            str(
                transaction[
                    "realised_gain_loss"
                ]
            )
        )

        if classification_name == "STCG":

            total_stcg += gain_loss
            classified_count += 1

        elif classification_name == "LTCG":

            total_ltcg += gain_loss
            classified_count += 1

        else:

            total_unclassified += gain_loss
            unclassified_count += 1

        classified_transactions.append(
            {
                **transaction,

                "investment": {
                    "investment_id": (
                        investment_id
                    ),
                    "name": (
                        investment_info[
                            "name"
                        ]
                        if investment_info
                        else None
                    ),
                    "investment_type": (
                        investment_info[
                            "investment_type"
                        ]
                        if investment_info
                        else None
                    ),
                    "symbol": (
                        investment_info[
                            "symbol"
                        ]
                        if investment_info
                        else None
                    ),
                },

                "asset_class": (
                    asset_class
                ),

                "asset_classification": {
                    "status": (
                        asset_status
                    ),
                    "reason": (
                        asset_reason
                    ),
                },

                "capital_gain_classification": (
                    classification
                ),
            }
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "status": "success",

        "user_id": user_id,

        "classification_engine": {
            "name": (
                "Capital Gains Classification Engine"
            ),
            "version": "1.1",
            "read_only": True,
        },

        "financial_year": (
            resolved_financial_year
        ),

        "start_date": start_date,

        "end_date": end_date,

        "method": "FIFO",

        "asset_class_source": (
            "Asset Classification Resolver"
        ),

        "summary": {
            "sale_count": len(
                classified_transactions
            ),
            "classified_count": (
                classified_count
            ),
            "unclassified_count": (
                unclassified_count
            ),
            "stcg_realised_gain_loss": (
                total_stcg
            ),
            "ltcg_realised_gain_loss": (
                total_ltcg
            ),
            "unclassified_realised_gain_loss": (
                total_unclassified
            ),
        },

        "realised_transactions": (
            classified_transactions
        ),

        "tax_calculation": {
            "status": "not_calculated",
            "message": (
                "Tax rates, exemptions, "
                "deductions, surcharge, cess "
                "and final tax liability are "
                "not calculated by this engine."
            ),
        },
    }
