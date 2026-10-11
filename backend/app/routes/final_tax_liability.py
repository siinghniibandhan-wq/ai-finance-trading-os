# ============================================================
# FINANCIAL OS
# FINAL TAX LIABILITY ENGINE
# ============================================================
#
# Version: 1.0
#
# Purpose:
#   Calculate the final tax-liability framework from the
#   Final Taxable Income Engine.
#
# IMPORTANT:
#   READ-ONLY.
#
#   This engine does NOT:
#   - modify financial data
#   - modify investments
#   - modify transactions
#   - modify tax records
#   - create tax records
#
# Current scope:
#   1. Final taxable-income input
#   2. Normal slab-rate tax
#   3. Special-rate capital-gain tax
#   4. Section 87A rebate context
#   5. Surcharge
#   6. Health & Education Cess
#   7. Final tax payable
#
# Important:
#   If required income heads are unavailable in Module 11,
#   final liability remains INCOMPLETE rather than guessing.
#
# Next engine:
#   ITR-Ready Tax Report Engine
#
# ============================================================

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User, TaxCreditEntry
from app.routes.final_taxable_income import get_final_taxable_income


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/final-tax-liability",
    tags=["Final Tax Liability"],
)


# ============================================================
# ENGINE VERSION
# ============================================================

ENGINE_VERSION = "1.0"


# ============================================================
# TAX CONSTANTS
# ============================================================

CESS_RATE = Decimal("0.04")

STCG_111A_RATE = Decimal("0.20")
LTCG_112A_RATE = Decimal("0.125")

LTCG_112A_EXEMPTION = Decimal("125000")


# ============================================================
# 87A CONSTANTS
# ============================================================

NEW_REGIME_87A_INCOME_LIMIT = Decimal("1200000")
NEW_REGIME_87A_MAX_REBATE = Decimal("60000")

OLD_REGIME_87A_INCOME_LIMIT = Decimal("500000")
OLD_REGIME_87A_MAX_REBATE = Decimal("12500")


# ============================================================
# MONEY HELPER
# ============================================================

def money(value):
    if value is None:
        value = Decimal("0")

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# DECIMAL HELPER
# ============================================================

def decimal(value):
    if value is None:
        return Decimal("0")

    return Decimal(str(value))


# ============================================================
# FINANCIAL YEAR
# ============================================================

def get_financial_year_dates(financial_year):
    try:
        start_year = int(
            financial_year.split("-")[0]
        )
    except Exception:
        raise ValueError(
            "financial_year must use format YYYY-YY, "
            "for example 2026-27."
        )

    return (
        date(start_year, 4, 1),
        date(start_year + 1, 3, 31),
    )


# ============================================================
# NORMAL TAX — NEW REGIME
# ============================================================

def calculate_new_regime_slab_tax(
    taxable_income,
):
    """
    AY 2026-27 new-regime slabs:

    Up to 4L          0%
    4L - 8L           5%
    8L - 12L          10%
    12L - 16L         15%
    16L - 20L         20%
    20L - 24L         25%
    Above 24L         30%
    """

    income = max(
        decimal(taxable_income),
        Decimal("0"),
    )

    tax = Decimal("0")

    slabs = [
        (
            Decimal("400000"),
            Decimal("0.00"),
        ),
        (
            Decimal("800000"),
            Decimal("0.05"),
        ),
        (
            Decimal("1200000"),
            Decimal("0.10"),
        ),
        (
            Decimal("1600000"),
            Decimal("0.15"),
        ),
        (
            Decimal("2000000"),
            Decimal("0.20"),
        ),
        (
            Decimal("2400000"),
            Decimal("0.25"),
        ),
        (
            None,
            Decimal("0.30"),
        ),
    ]

    previous_limit = Decimal("0")

    for upper_limit, rate in slabs:

        if upper_limit is None:

            taxable_slice = (
                income - previous_limit
            )

            if taxable_slice > 0:
                tax += (
                    taxable_slice * rate
                )

            break

        taxable_slice = min(
            max(
                income - previous_limit,
                Decimal("0"),
            ),
            upper_limit - previous_limit,
        )

        if taxable_slice > 0:
            tax += (
                taxable_slice * rate
            )

        if income <= upper_limit:
            break

        previous_limit = upper_limit

    return money(tax)


# ============================================================
# NORMAL TAX — OLD REGIME
# ============================================================

def calculate_old_regime_slab_tax(
    taxable_income,
):
    """
    Old-regime slabs for an individual below 60.

    Up to 2.5L       0%
    2.5L - 5L        5%
    5L - 10L         20%
    Above 10L        30%
    """

    income = max(
        decimal(taxable_income),
        Decimal("0"),
    )

    tax = Decimal("0")

    slabs = [
        (
            Decimal("250000"),
            Decimal("0.00"),
        ),
        (
            Decimal("500000"),
            Decimal("0.05"),
        ),
        (
            Decimal("1000000"),
            Decimal("0.20"),
        ),
        (
            None,
            Decimal("0.30"),
        ),
    ]

    previous_limit = Decimal("0")

    for upper_limit, rate in slabs:

        if upper_limit is None:

            taxable_slice = (
                income - previous_limit
            )

            if taxable_slice > 0:
                tax += (
                    taxable_slice * rate
                )

            break

        taxable_slice = min(
            max(
                income - previous_limit,
                Decimal("0"),
            ),
            upper_limit - previous_limit,
        )

        if taxable_slice > 0:
            tax += (
                taxable_slice * rate
            )

        if income <= upper_limit:
            break

        previous_limit = upper_limit

    return money(tax)


# ============================================================
# SURCHARGE
# ============================================================

def calculate_surcharge(
    total_income,
    normal_tax,
    special_rate_tax,
    tax_regime,
):
    """
    Calculate surcharge using the applicable income thresholds.

    For AY 2026-27:

    Up to 50L       0%
    50L - 1Cr       10%
    1Cr - 2Cr       15%
    2Cr - 5Cr       25%
    Above 5Cr       25% new regime / 37% old regime

    Special-rate income is subject to the applicable surcharge
    limitations. This engine keeps the special-rate surcharge
    separately visible.
    """

    income = decimal(total_income)

    if income <= Decimal("5000000"):
        rate = Decimal("0")

    elif income <= Decimal("10000000"):
        rate = Decimal("0.10")

    elif income <= Decimal("20000000"):
        rate = Decimal("0.15")

    elif income <= Decimal("50000000"):
        rate = Decimal("0.25")

    else:

        if tax_regime == "new":
            rate = Decimal("0.25")
        else:
            rate = Decimal("0.37")

    normal_surcharge = money(
        normal_tax * rate
    )

    # Special-rate income has a maximum surcharge rate
    # of 15% under the applicable rules.
    special_surcharge_rate = min(
        rate,
        Decimal("0.15"),
    )

    special_surcharge = money(
        special_rate_tax
        * special_surcharge_rate
    )

    return {
        "rate": rate,
        "normal_income_surcharge":
            normal_surcharge,
        "special_rate_surcharge":
            special_surcharge,
        "total":
            money(
                normal_surcharge
                + special_surcharge
            ),
    }


# ============================================================
# 87A REBATE
# ============================================================

def calculate_87a_rebate(
    taxable_income,
    normal_tax,
    tax_regime,
    residential_status,
):
    """
    Calculate the 87A rebate context.

    New regime:
        taxable income <= 12L
        maximum rebate = 60,000

    Old regime:
        taxable income <= 5L
        maximum rebate = 12,500

    The rebate is applied only against eligible normal
    income tax. Special-rate capital-gain tax is not treated
    as ordinary slab tax here.
    """

    income = decimal(taxable_income)

    if residential_status != "resident":

        return {
            "eligible": False,
            "reason":
                "Section 87A rebate is available "
                "to resident individuals.",
            "income_limit": (
                NEW_REGIME_87A_INCOME_LIMIT
                if tax_regime == "new"
                else OLD_REGIME_87A_INCOME_LIMIT
            ),
            "maximum_rebate": (
                NEW_REGIME_87A_MAX_REBATE
                if tax_regime == "new"
                else OLD_REGIME_87A_MAX_REBATE
            ),
            "rebate": Decimal("0"),
        }

    if tax_regime == "new":

        income_limit = (
            NEW_REGIME_87A_INCOME_LIMIT
        )

        maximum_rebate = (
            NEW_REGIME_87A_MAX_REBATE
        )

    else:

        income_limit = (
            OLD_REGIME_87A_INCOME_LIMIT
        )

        maximum_rebate = (
            OLD_REGIME_87A_MAX_REBATE
        )

    if income <= income_limit:

        rebate = min(
            decimal(normal_tax),
            maximum_rebate,
        )

        return {
            "eligible": True,
            "reason":
                "Taxable income is within the "
                "applicable Section 87A limit.",
            "income_limit":
                money(income_limit),
            "maximum_rebate":
                money(maximum_rebate),
            "rebate":
                money(rebate),
        }

    return {
        "eligible": False,
        "reason":
            "Taxable income exceeds the applicable "
            "Section 87A income limit.",
        "income_limit":
            money(income_limit),
        "maximum_rebate":
            money(maximum_rebate),
        "rebate":
            Decimal("0"),
    }


# ============================================================
# TAX CREDIT INPUT SCHEMAS AND PERSISTENCE API
# ============================================================

CREDIT_TYPES = {"tds", "advance_tax", "self_assessment_tax"}


class TaxCreditEntryInput(BaseModel):
    # User-entered credits remain pending until reviewed externally.
    user_id: int = Field(ge=1)
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    credit_type: str = Field(pattern=r"^(tds|advance_tax|self_assessment_tax)$")
    amount: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    source_reference: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)


@router.post("/credits", status_code=201)
def create_tax_credit_entry(payload: TaxCreditEntryInput, db: Session = Depends(get_db)):
    """Save a self-reported credit; it does not become verified automatically."""
    if not db.query(User).filter(User.id == payload.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    reference = payload.source_reference.strip() if payload.source_reference else None
    if reference and db.query(TaxCreditEntry).filter(
        TaxCreditEntry.user_id == payload.user_id,
        TaxCreditEntry.financial_year == payload.financial_year,
        TaxCreditEntry.credit_type == payload.credit_type,
        TaxCreditEntry.source_reference == reference,
    ).first():
        raise HTTPException(status_code=409, detail="Duplicate tax credit source reference")
    entry = TaxCreditEntry(
        user_id=payload.user_id, financial_year=payload.financial_year,
        credit_type=payload.credit_type, amount=payload.amount,
        source_reference=reference, notes=payload.notes, status="pending_review",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {
        "id": entry.id, "user_id": entry.user_id, "financial_year": entry.financial_year,
        "credit_type": entry.credit_type, "amount": str(entry.amount),
        "source_reference": entry.source_reference, "status": entry.status,
        "counted_as_verified_credit": False,
    }


@router.get("/credits")
def list_tax_credit_entries(
    user_id: int = Query(..., ge=1),
    financial_year: str = Query("2026-27", pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
):
    """List tax-credit entries for one user and financial year."""
    entries = db.query(TaxCreditEntry).filter(
        TaxCreditEntry.user_id == user_id,
        TaxCreditEntry.financial_year == financial_year,
    ).order_by(TaxCreditEntry.created_at.desc(), TaxCreditEntry.id.desc()).all()
    return {
        "user_id": user_id, "financial_year": financial_year,
        "entries": [{
            "id": item.id, "credit_type": item.credit_type, "amount": str(item.amount),
            "source_reference": item.source_reference, "notes": item.notes,
            "status": item.status, "counted_as_verified_credit": item.status == "verified",
        } for item in entries],
    }


# ============================================================
# ENDPOINT
# ============================================================

@router.get("/")
def get_final_tax_liability(
    user_id: int = Query(
        ...,
        ge=1,
    ),
    financial_year: str = Query(
        "2026-27"
    ),
    tax_regime: str = Query(
        "new"
    ),
    residential_status: str = Query(
        "resident"
    ),
    stt_confirmed: bool = Query(
        False
    ),
    # Optional self-reported credits. None means unknown, not zero.
    tds_credit: float | None = Query(None, ge=0),
    advance_tax_credit: float | None = Query(None, ge=0),
    self_assessment_tax_credit: float | None = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """
    Calculate final tax liability framework.

    Example:

    /api/final-tax-liability/
    ?user_id=1
    &financial_year=2026-27
    &tax_regime=new
    &residential_status=resident
    &stt_confirmed=false
    """

    # ========================================================
    # VALIDATE REGIME
    # ========================================================

    tax_regime = str(
        tax_regime
    ).lower()

    if tax_regime not in {
        "new",
        "old",
    }:

        return {
            "status": "error",
            "message":
                "tax_regime must be 'new' or 'old'.",
        }

    # ========================================================
    # VALIDATE RESIDENTIAL STATUS
    # ========================================================

    residential_status = str(
        residential_status
    ).lower()

    if residential_status not in {
        "resident",
        "non_resident",
    }:

        return {
            "status": "error",
            "message":
                "residential_status must be "
                "'resident' or 'non_resident'.",
        }

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
    # AUTHORITATIVE TAXABLE-INCOME ENGINE
    # ========================================================
    # Reuse the existing engine instead of maintaining a second,
    # divergent copy of income, capital-gain, and deduction logic.
    # This is a direct in-process call; it does not make an HTTP request
    # and does not write to the database.

    income_result = get_final_taxable_income(
        user_id=user_id,
        financial_year=financial_year,
        tax_regime=tax_regime,
        db=db,
    )

    if income_result.get("status") != "success":
        return {
            "status": "error",
            "message": "The taxable-income engine could not produce a result.",
            "taxable_income_engine": income_result,
        }

    income_heads = income_result.get("income_heads", {})
    other_head = income_heads.get("other_sources", {})
    capital_head = income_heads.get("capital_gains", {})
    deductions_head = income_result.get("deductions", {})
    taxable_head = income_result.get("taxable_income", {})

    other_source_income = decimal(other_head.get("total"))
    stcg = decimal(capital_head.get("stcg_after_setoff"))
    ltcg = decimal(capital_head.get("ltcg_after_setoff"))
    verified_deductions = decimal(deductions_head.get("verified_amount"))
    verified_exempt_income = decimal(
        income_result.get("exempt_income", {}).get("verified_amount")
    )

    available_taxable_income = decimal(
        taxable_head.get("provisional_taxable_income")
    )

    missing_income_heads = [
        head for head in ("salary", "house_property", "business_or_profession")
        if not income_heads.get(head, {}).get("available", False)
    ]

    # ========================================================
    # SPECIAL-RATE TAX
    # ========================================================

    if stt_confirmed:

        stcg_tax = money(
            stcg * STCG_111A_RATE
        )

    else:

        stcg_tax = Decimal("0")

    # --------------------------------------------------------
    # LTCG 112A
    # --------------------------------------------------------

    ltcg_excess = max(
        ltcg - LTCG_112A_EXEMPTION,
        Decimal("0"),
    )

    ltcg_tax = money(
        ltcg_excess
        * LTCG_112A_RATE
    )

    special_rate_tax = money(
        stcg_tax
        + ltcg_tax
    )

    # ========================================================
    # NORMAL TAX
    # ========================================================
    #
    # Capital gains subject to special rates are excluded
    # from ordinary slab-tax calculation here.
    #
    # ========================================================

    normal_taxable_income = max(
        available_taxable_income - stcg - ltcg,
        Decimal("0"),
    )

    if tax_regime == "new":

        normal_tax = (
            calculate_new_regime_slab_tax(
                normal_taxable_income
            )
        )

    else:

        normal_tax = (
            calculate_old_regime_slab_tax(
                normal_taxable_income
            )
        )

    # ========================================================
    # 87A
    # ========================================================

    rebate = calculate_87a_rebate(
        available_taxable_income,
        normal_tax,
        tax_regime,
        residential_status,
    )

    rebate_amount = decimal(
        rebate["rebate"]
    )

    # ========================================================
    # TAX AFTER REBATE
    # ========================================================

    tax_after_rebate = max(
        normal_tax
        - rebate_amount,
        Decimal("0"),
    )

    # ========================================================
    # SURCHARGE
    # ========================================================

    surcharge = calculate_surcharge(
        available_taxable_income,
        tax_after_rebate,
        special_rate_tax,
        tax_regime,
    )

    # ========================================================
    # CESS
    # ========================================================

    tax_before_cess = money(
        tax_after_rebate
        + special_rate_tax
        + surcharge["total"]
    )

    cess = money(
        tax_before_cess
        * CESS_RATE
    )

    # ========================================================
    # TOTAL
    # ========================================================

    total_tax_payable = money(
        tax_before_cess
        + cess
    )

    # ========================================================
    # TAX CREDITS AND BALANCE
    # ========================================================
    # Explicit query parameters are provisional overrides. If absent,
    # persisted credits count only after a separate verification step.
    credit_values = {
        "tds": tds_credit,
        "advance_tax": advance_tax_credit,
        "self_assessment_tax": self_assessment_tax_credit,
    }
    manual_credit_mode = any(value is not None for value in credit_values.values())
    persisted_credit_summary = {}

    if manual_credit_mode:
        credits_complete = all(value is not None for value in credit_values.values())
        total_credits = (
            money(sum((decimal(value) for value in credit_values.values()), Decimal("0")))
            if credits_complete else None
        )
        credit_status = "self_reported_provisional" if credits_complete else "tax_credit_data_incomplete"
        credit_breakdown = {key: money(value) if value is not None else None
                            for key, value in credit_values.items()}
        credits_verified = False
    else:
        entries = db.query(TaxCreditEntry).filter(
            TaxCreditEntry.user_id == user_id,
            TaxCreditEntry.financial_year == financial_year,
        ).all()
        verified_entries = [entry for entry in entries if entry.status == "verified"]
        required_types = ("tds", "advance_tax", "self_assessment_tax")
        for credit_type in required_types:
            typed_entries = [e for e in verified_entries if e.credit_type == credit_type]
            persisted_credit_summary[credit_type] = {
                "verified_amount": money(sum((decimal(e.amount) for e in typed_entries), Decimal("0"))),
                "verified_entry_count": len(typed_entries),
            }
        credits_complete = all(
            persisted_credit_summary[key]["verified_entry_count"] > 0
            for key in required_types
        )
        credit_breakdown = {
            key: persisted_credit_summary[key]["verified_amount"]
            if persisted_credit_summary[key]["verified_entry_count"] > 0 else None
            for key in required_types
        }
        total_credits = (
            money(sum((decimal(value) for value in credit_breakdown.values()), Decimal("0")))
            if credits_complete else None
        )
        credit_status = "verified_persisted_credits" if credits_complete else "tax_credit_data_incomplete"
        credits_verified = credits_complete

    balance_after_credits = money(total_tax_payable - total_credits) if credits_complete else None
    balance_status = credit_status

    # ========================================================
    # FINAL STATUS
    # ========================================================

    if missing_income_heads:

        engine_status = (
            "incomplete_missing_income_heads"
        )

        liability_status = (
            "not_final"
        )

    elif not stt_confirmed and stcg > 0:

        engine_status = (
            "requires_stt_confirmation"
        )

        liability_status = (
            "conditional"
        )

    else:

        engine_status = (
            "calculated"
        )

        liability_status = (
            "calculated"
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "status": "success",

        "user_id": user_id,

        "engine": {
            "name":
                "Final Tax Liability Engine",
            "version":
                ENGINE_VERSION,
            "read_only":
                True,
        },

        # ----------------------------------------------------
        # TAX YEAR
        # ----------------------------------------------------

        "tax_year": {

            "financial_year":
                financial_year,

            "start_date":
                start_date,

            "end_date":
                end_date,

            "tax_regime":
                tax_regime,

            "residential_status":
                residential_status,
        },

        # ----------------------------------------------------
        # ENGINE STATUS
        # ----------------------------------------------------

        "engine_status":
            engine_status,

        "liability_status":
            liability_status,

        "taxable_income_engine_status": income_result.get("engine_status"),
        "taxable_income_source": "final-taxable-income engine",

        # Persisted records count only after a separate verification step.
        "tax_credits": {
            **credit_breakdown,
            "total": total_credits,
            "data_status": balance_status,
            "verified": credits_verified,
            "source": "query_parameters_self_reported" if manual_credit_mode else "persisted_verified_entries",
            "persisted_verified_summary": persisted_credit_summary if not manual_credit_mode else None,
        },
        "balance_after_credits": {
            "amount": balance_after_credits,
            "interpretation": (
                "positive=payable; negative=potential refund; zero=balanced"
                if credits_complete else None
            ),
            "status": balance_status,
        },

        # ----------------------------------------------------
        # TAXABLE INCOME
        # ----------------------------------------------------

        "taxable_income": {

            "available_taxable_income":
                money(
                    available_taxable_income
                ),

            "normal_taxable_income":
                money(
                    normal_taxable_income
                ),

            "stcg":
                money(stcg),

            "ltcg":
                money(ltcg),

            "verified_deductions":
                money(
                    verified_deductions
                ),

            "final_taxable_income":
                None
                if missing_income_heads
                else money(
                    available_taxable_income
                ),

            "status":
                "not_final"
                if missing_income_heads
                else "final",
        },

        # ----------------------------------------------------
        # NORMAL SLAB TAX
        # ----------------------------------------------------

        "normal_income_tax": {

            "taxable_income":
                money(
                    normal_taxable_income
                ),

            "tax_before_rebate":
                money(normal_tax),

            "rebate_87a":
                money(rebate_amount),

            "tax_after_rebate":
                money(
                    tax_after_rebate
                ),
        },

        # ----------------------------------------------------
        # SPECIAL RATE TAX
        # ----------------------------------------------------

        "special_rate_tax": {

            "stcg_111a": {

                "gain":
                    money(stcg),

                "section":
                    "111A",

                "rate":
                    money(
                        STCG_111A_RATE
                        * 100
                    ),

                "stt_confirmed":
                    stt_confirmed,

                "tax":
                    money(stcg_tax),
            },

            "ltcg_112a": {

                "gain":
                    money(ltcg),

                "section":
                    "112A",

                "rate":
                    money(
                        LTCG_112A_RATE
                        * 100
                    ),

                "threshold":
                    money(
                        LTCG_112A_EXEMPTION
                    ),

                "taxable_gain":
                    money(
                        ltcg_excess
                    ),

                "tax":
                    money(ltcg_tax),
            },

            "total":
                money(
                    special_rate_tax
                ),
        },

        # ----------------------------------------------------
        # REBATE
        # ----------------------------------------------------

        "rebate_87a": {

            "eligible":
                rebate["eligible"],

            "income_limit":
                money(
                    rebate["income_limit"]
                ),

            "maximum_rebate":
                money(
                    rebate["maximum_rebate"]
                ),

            "rebate":
                money(
                    rebate["rebate"]
                ),

            "reason":
                rebate["reason"],
        },

        # ----------------------------------------------------
        # SURCHARGE
        # ----------------------------------------------------

        "surcharge": {

            "rate":
                money(
                    surcharge["rate"]
                    * 100
                ),

            "normal_income_surcharge":
                money(
                    surcharge[
                        "normal_income_surcharge"
                    ]
                ),

            "special_rate_surcharge":
                money(
                    surcharge[
                        "special_rate_surcharge"
                    ]
                ),

            "total":
                money(
                    surcharge["total"]
                ),
        },

        # ----------------------------------------------------
        # CESS
        # ----------------------------------------------------

        "cess": {

            "rate":
                money(
                    CESS_RATE
                    * 100
                ),

            "amount":
                money(cess),
        },

        # ----------------------------------------------------
        # FINAL TAX
        # ----------------------------------------------------

        "final_tax": {

            "tax_before_cess":
                money(
                    tax_before_cess
                ),

            "cess":
                money(cess),

            "total_tax_payable":
                money(
                    total_tax_payable
                ),

            "status":
                liability_status,
        },

        # ----------------------------------------------------
        # MISSING DATA
        # ----------------------------------------------------

        "missing_data": {

            "income_heads":
                missing_income_heads,

            "salary":
                "salary" in missing_income_heads,

            "house_property":
                "house_property" in missing_income_heads,

            "business_or_profession":
                "business_or_profession" in missing_income_heads,
            "tax_credits": not credits_complete,
        },

        # ----------------------------------------------------
        # SCOPE
        # ----------------------------------------------------

        "scope": {

            "read_only":
                True,

            "database_write":
                False,

            "slab_tax_calculated":
                True,

            "capital_gains_tax_calculated":
                True,

            "rebate_calculated":
                True,

            "surcharge_calculated":
                True,

            "cess_calculated":
                True,

            "final_liability_complete":
                not bool(
                    missing_income_heads
                ),

            "itr_filed":
                False,
        },

        # ----------------------------------------------------
        # NEXT ENGINE
        # ----------------------------------------------------

        "next_engine":
            "ITR-Ready Tax Report Engine",
    }
