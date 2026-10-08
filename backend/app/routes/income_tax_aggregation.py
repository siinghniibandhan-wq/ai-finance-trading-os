"""
Income Aggregation & Taxable Income Engine v1.0

Purpose:
- Read-only aggregation of verified income data.
- Uses existing Transaction records.
- Combines current-year capital-gains results.
- Does NOT invent missing income sources.
- Does NOT calculate final tax liability.
- Does NOT write to the database.

Endpoint:
GET /api/income-tax-aggregation/
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction

from app.routes.income_tax_loss_setoff import (
    get_financial_year_dates,
    calculate_current_year_setoff,
)


router = APIRouter(
    prefix="/api/income-tax-aggregation",
    tags=["Income Tax Aggregation"],
)


ENGINE_VERSION = "1.0"


def money(value):
    """Round monetary values to two decimal places."""
    return float(
        Decimal(str(value or 0)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    )


def load_income_transactions(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date,
):
    """
    Load transactions that are explicitly recorded as income,
    interest, or dividend.

    We intentionally do not treat:
    - refunds
    - transfers
    - withdrawals
    - tax payments
    - loan repayments
    - expenses

    as taxable income.
    """

    return (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.transaction_type.in_(
                [
                    "income",
                    "interest",
                    "dividend",
                ]
            ),
        )
        .order_by(Transaction.transaction_date.asc())
        .all()
    )


@router.get("/")
def income_tax_aggregation(
    user_id: int = Query(..., ge=1),
    financial_year: str = Query("2026-27"),
    db: Session = Depends(get_db),
):
    """
    Income Aggregation & Taxable Income Engine.

    Current scope:
    - Aggregates verified income transactions.
    - Separates interest and dividend receipts.
    - Adds capital gains after current-year loss set-off.
    - Reports unavailable income heads explicitly.
    - Does not calculate final tax liability.
    """

    # ---------------------------------------------------------
    # 1. FINANCIAL YEAR
    # ---------------------------------------------------------
    start_date, end_date = get_financial_year_dates(financial_year)

    # ---------------------------------------------------------
    # 2. VERIFIED INCOME TRANSACTIONS
    # ---------------------------------------------------------
    transactions = load_income_transactions(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    income_total = Decimal("0")
    interest_total = Decimal("0")
    dividend_total = Decimal("0")

    transaction_details = []

    for tx in transactions:
        amount = Decimal(str(tx.amount or 0))
        tx_type = str(tx.transaction_type or "").lower()

        if tx_type == "income":
            income_total += amount

        elif tx_type == "interest":
            interest_total += amount

        elif tx_type == "dividend":
            dividend_total += amount

        transaction_details.append(
            {
                "transaction_id": tx.id,
                "transaction_date": (
                    tx.transaction_date.isoformat()
                    if tx.transaction_date
                    else None
                ),
                "transaction_type": tx_type,
                "amount": money(amount),
            }
        )

    # ---------------------------------------------------------
    # 3. CAPITAL GAINS AFTER CURRENT-YEAR LOSS SET-OFF
    # ---------------------------------------------------------
    capital_gains = calculate_current_year_setoff(
        db=db,
        user_id=user_id,
        financial_year=financial_year,
    )

    remaining_stcg = Decimal(
        str(capital_gains.get("remaining_stcg", 0) or 0)
    )

    remaining_ltcg = Decimal(
        str(capital_gains.get("remaining_ltcg", 0) or 0)
    )

    current_year_capital_gains = (
        remaining_stcg + remaining_ltcg
    )

    # ---------------------------------------------------------
    # 4. OTHER INCOME HEADS
    # ---------------------------------------------------------
    #
    # The current Financial OS does not contain verified,
    # source-specific records for:
    #
    # - Salary
    # - Business / Profession
    # - House Property
    #
    # Therefore these are explicitly marked unavailable.
    #
    salary_available = False
    business_available = False
    house_property_available = False

    # ---------------------------------------------------------
    # 5. AGGREGATED VERIFIED RECEIPTS
    # ---------------------------------------------------------
    verified_non_capital_income = (
        income_total
        + interest_total
        + dividend_total
    )

    # This is NOT yet "final taxable income".
    # It is only the amount supported by current records
    # plus capital gains remaining after current-year set-off.
    provisional_taxable_income = (
        verified_non_capital_income
        + current_year_capital_gains
    )

    # ---------------------------------------------------------
    # 6. COMPLETENESS STATUS
    # ---------------------------------------------------------
    complete_income_heads = (
        salary_available
        and business_available
        and house_property_available
    )

    if complete_income_heads:
        aggregation_status = "complete"

    elif (
        verified_non_capital_income > 0
        or current_year_capital_gains > 0
    ):
        aggregation_status = "partial_income_data"

    else:
        aggregation_status = "income_data_unavailable"

    # ---------------------------------------------------------
    # 7. RESPONSE
    # ---------------------------------------------------------
    return {
        "status": "success",
        "engine": "Income Aggregation & Taxable Income Engine",
        "version": ENGINE_VERSION,
        "read_only": True,

        "financial_year": {
            "financial_year": financial_year,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },

        "aggregation_status": aggregation_status,

        "income_heads": {
            "salary": {
                "available": salary_available,
                "amount": None,
                "reason": (
                    "No verified salary-income source is currently "
                    "available in the Financial OS."
                ),
            },
            "business_profession": {
                "available": business_available,
                "amount": None,
                "reason": (
                    "No verified business/profession income source "
                    "is currently available in the Financial OS."
                ),
            },
            "house_property": {
                "available": house_property_available,
                "amount": None,
                "reason": (
                    "No verified house-property income source "
                    "is currently available in the Financial OS."
                ),
            },
            "other_sources": {
                "available": True,
                "income": money(income_total),
                "interest": money(interest_total),
                "dividend": money(dividend_total),
                "total": money(verified_non_capital_income),
                "source": "Financial OS transactions",
            },
        },

        "capital_gains": {
            "available": True,
            "stcg_after_setoff": money(remaining_stcg),
            "ltcg_after_setoff": money(remaining_ltcg),
            "total_after_setoff": money(current_year_capital_gains),
            "source": "Income Tax & Loss Set-off Engine",
        },

        "aggregated_values": {
            "verified_non_capital_income": money(
                verified_non_capital_income
            ),
            "capital_gains_after_setoff": money(
                current_year_capital_gains
            ),
            "provisional_taxable_income": money(
                provisional_taxable_income
            ),
        },

        "taxable_income": {
            "status": (
                "not_final"
                if not complete_income_heads
                else "ready_for_tax_calculation"
            ),
            "amount": (
                money(provisional_taxable_income)
                if complete_income_heads
                else None
            ),
            "reason": (
                "Final taxable income requires all applicable "
                "income heads and eligible deductions/exemptions."
                if not complete_income_heads
                else "All supported income heads are available."
            ),
        },

        "transaction_summary": {
            "income_transaction_count": len(transactions),
            "income": money(income_total),
            "interest": money(interest_total),
            "dividend": money(dividend_total),
            "details": transaction_details,
        },

        "scope": {
            "salary_income": salary_available,
            "business_profession_income": business_available,
            "house_property_income": house_property_available,
            "other_sources": True,
            "capital_gains": True,
            "deductions": False,
            "exempt_income": False,
            "final_taxable_income": False,
            "final_tax_liability": False,
            "database_write": False,
        },

        "next_engine": "Deductions & Exempt Income Engine",
    }
