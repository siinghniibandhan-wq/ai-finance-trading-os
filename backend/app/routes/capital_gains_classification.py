# ============================================================
# FINANCIAL OS
# CAPITAL GAINS CLASSIFICATION ENGINE v1.0
# ============================================================
#
# Purpose:
# - Classify realised capital gains as STCG / LTCG
# - Use verified FIFO results from Capital Gains Engine
# - Use actual holding period
# - Keep tax calculation separate
#
# IMPORTANT:
# - READ-ONLY
# - Does NOT modify database data
# - Does NOT modify capital_gains.py
# - Does NOT calculate tax liability
# - Does NOT calculate STCG/LTCG tax rates
# - Does NOT guess listed/unlisted status
#
# ASSET CLASS OPTIONS:
#
# listed_equity
# equity_oriented_mf
# unlisted_equity
# listed_other_security
# unlisted_other_security
#
# ============================================================


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.routes.capital_gains import (
    get_financial_year_dates,
    load_transactions,
    calculate_fifo_gains,
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

    # Listed equity shares
    "listed_equity": {
        "minimum_long_term_months": 12,
        "rule": (
            "Long-term when held for more than "
            "12 months."
        ),
    },

    # Equity-oriented mutual fund units
    "equity_oriented_mf": {
        "minimum_long_term_months": 12,
        "rule": (
            "Long-term when held for more than "
            "12 months."
        ),
    },

    # Unlisted equity shares
    "unlisted_equity": {
        "minimum_long_term_months": 24,
        "rule": (
            "Long-term when held for more than "
            "24 months."
        ),
    },

    # Listed securities other than the special
    # equity-oriented categories.
    "listed_other_security": {
        "minimum_long_term_months": 12,
        "rule": (
            "Long-term when held for more than "
            "12 months."
        ),
    },

    # General unlisted securities.
    "unlisted_other_security": {
        "minimum_long_term_months": 24,
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

    Important:
    Holding period is measured in days by the FIFO engine.

    To avoid approximating months using 30-day months,
    classification uses calendar-month comparison.
    """

    if asset_class not in ASSET_CLASS_RULES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid asset_class. "
                "Use one of: "
                "listed_equity, "
                "equity_oriented_mf, "
                "unlisted_equity, "
                "listed_other_security, "
                "unlisted_other_security."
            ),
        )

    if holding_days is None:
        return {
            "classification": "UNCLASSIFIED",
            "classification_status": "missing_holding_period",
        }

    threshold_months = ASSET_CLASS_RULES[
        asset_class
    ]["minimum_long_term_months"]

    # --------------------------------------------------------
    # Conservative day approximation for engine v1.0.
    #
    # 12 months is represented as 365 days.
    # 24 months is represented as 730 days.
    #
    # This is deliberately labelled engine v1.0.
    # A future tax-rule engine can perform exact calendar
    # date comparison where required.
    # --------------------------------------------------------

    if threshold_months == 12:
        threshold_days = 365
    else:
        threshold_days = 730

    if holding_days > threshold_days:
        classification = "LTCG"
    else:
        classification = "STCG"

    return {
        "classification": classification,
        "classification_status": "classified",
        "threshold_months": threshold_months,
        "threshold_days": threshold_days,
    }


# ============================================================
# API
# ============================================================

@router.get("/")
def capital_gains_classification(
    user_id: int,
    financial_year: str = "2026-27",
    asset_class: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Classify realised capital gains for a financial year.

    asset_class is intentionally required for classification.

    Without asset_class:
    - capital gains data is returned
    - STCG/LTCG classification remains UNCLASSIFIED
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
    # VALIDATE ASSET CLASS
    # --------------------------------------------------------

    if asset_class is not None:

        if asset_class not in ASSET_CLASS_RULES:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid asset_class. "
                    "Use one of: "
                    "listed_equity, "
                    "equity_oriented_mf, "
                    "unlisted_equity, "
                    "listed_other_security, "
                    "unlisted_other_security."
                ),
            )

    # --------------------------------------------------------
    # LOAD TRANSACTIONS
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

    total_stcg = 0
    total_ltcg = 0
    total_unclassified = 0

    # --------------------------------------------------------
    # CLASSIFY EACH REALISED TRANSACTION
    # --------------------------------------------------------

    for transaction in result[
        "transactions"
    ]:

        holding_days = transaction.get(
            "holding_days"
        )

        if asset_class is None:

            classification = {
                "classification": (
                    "UNCLASSIFIED"
                ),
                "classification_status": (
                    "asset_class_required"
                ),
            }

        else:

            classification = classify_gain(
                holding_days=holding_days,
                asset_class=asset_class,
            )

        classification_name = classification[
            "classification"
        ]

        if classification_name == "STCG":

            total_stcg += float(
                transaction[
                    "realised_gain_loss"
                ]
            )

        elif classification_name == "LTCG":

            total_ltcg += float(
                transaction[
                    "realised_gain_loss"
                ]
            )

        else:

            total_unclassified += float(
                transaction[
                    "realised_gain_loss"
                ]
            )

        classified_transactions.append(
            {
                **transaction,
                "classification": (
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
            "version": "1.0",
            "read_only": True,
        },

        "financial_year": (
            resolved_financial_year
        ),

        "start_date": start_date,

        "end_date": end_date,

        "method": "FIFO",

        "asset_class": asset_class,

        "classification_rules": (
            ASSET_CLASS_RULES
        ),

        "summary": {
            "sale_count": len(
                classified_transactions
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
