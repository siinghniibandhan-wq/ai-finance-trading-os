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

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
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
                not salary_income_available,

            "house_property":
                not house_property_available,

            "business_or_profession":
                not business_income_available,
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
