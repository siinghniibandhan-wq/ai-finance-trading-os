"""
============================================================
FINANCIAL OS
DEDUCTIONS & EXEMPT INCOME ENGINE
============================================================

Version: 1.0

Purpose:
- Provide a structured deduction framework.
- Respect old/new tax-regime differences.
- Track verified deduction data when available.
- Track exempt-income categories when available.
- Do NOT invent deduction amounts.
- Do NOT treat ordinary expenses as tax deductions.
- Do NOT calculate final tax liability.

Important:
- Read-only.
- No database writes.
- Current Financial OS does not yet contain a dedicated
  verified deduction/exemption ledger.
============================================================
"""

from fastapi import (
    APIRouter,
    Query,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/deductions-exempt-income",
    tags=["Deductions & Exempt Income"],
)


ENGINE_VERSION = "1.0"


# ============================================================
# DEDUCTION CATALOG
# ============================================================

DEDUCTION_CATALOG = {

    # --------------------------------------------------------
    # COMMON / REGIME-SPECIFIC
    # --------------------------------------------------------

    "STANDARD_DEDUCTION_SALARY": {
        "section": "Section 16(ia)",
        "name": "Standard deduction from eligible salary/pension",
        "old_regime_available": True,
        "new_regime_available": True,
        "maximum_amount": None,
        "maximum_amount_by_regime": {"old": 50000, "new": 75000},
        "basis": "salary_income_and_financial_year_rules",
    },

    "80C": {
        "section": "80C",
        "name": "Specified investments and payments",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": 150000,
        "basis": "combined_limit",
    },

    "80CCC": {
        "section": "80CCC",
        "name": "Annuity / pension contribution",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_rules",
    },

    "80CCD_1": {
        "section": "80CCD(1)",
        "name": "Employee contribution to NPS",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_rules",
    },

    "80CCD_1B": {
        "section": "80CCD(1B)",
        "name": "Additional NPS contribution",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": 50000,
        "basis": "maximum_limit",
    },

    "80CCD_2": {
        "section": "80CCD(2)",
        "name": "Employer contribution to NPS",
        "old_regime_available": True,
        "new_regime_available": True,
        "maximum_amount": None,
        "basis": "percentage_of_salary_subject_to_rules",
    },

    "80CCH": {
        "section": "80CCH",
        "name": "Agnipath / Agniveer Corpus contribution",
        "old_regime_available": True,
        "new_regime_available": True,
        "maximum_amount": None,
        "basis": "eligible_contribution",
    },

    "80D": {
        "section": "80D",
        "name": "Health insurance / preventive health check-up",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "age_and_relationship_dependent",
    },

    "80DD": {
        "section": "80DD",
        "name": "Dependent with disability",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    "80DDB": {
        "section": "80DDB",
        "name": "Specified medical treatment",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    "80E": {
        "section": "80E",
        "name": "Interest on education loan",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "eligible_interest_subject_to_rules",
    },

    "80EE": {
        "section": "80EE",
        "name": "Interest on qualifying housing loan",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    "80EEA": {
        "section": "80EEA",
        "name": "Interest on qualifying affordable housing loan",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    "80EEB": {
        "section": "80EEB",
        "name": "Interest on electric vehicle loan",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    "80G": {
        "section": "80G",
        "name": "Eligible donations",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "eligible_donation_rules",
    },

    "80GG": {
        "section": "80GG",
        "name": "Rent paid by eligible taxpayer",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    "80GGA": {
        "section": "80GGA",
        "name": "Eligible scientific research / rural development donation",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    "80GGC": {
        "section": "80GGC",
        "name": "Contribution to political parties / electoral trusts",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    "80TTA": {
        "section": "80TTA",
        "name": "Savings account interest",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": 10000,
        "basis": "maximum_limit",
    },

    "80TTB": {
        "section": "80TTB",
        "name": "Interest income for eligible senior citizens",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": 50000,
        "basis": "maximum_limit",
    },

    "80U": {
        "section": "80U",
        "name": "Person with disability",
        "old_regime_available": True,
        "new_regime_available": False,
        "maximum_amount": None,
        "basis": "subject_to_conditions",
    },

    # --------------------------------------------------------
    # HOUSE PROPERTY
    # --------------------------------------------------------

    "24B": {
        "section": "24(b)",
        "name": "Interest on housing / house-property loan",
        "old_regime_available": True,
        "new_regime_available": True,
        "maximum_amount": None,
        "basis": "self_occupied_old_regime_limit_or_let_out_property_rules; eligibility depends on property use and regime",
    },
}


# ============================================================
# EXEMPT INCOME CATALOG
# ============================================================

EXEMPT_INCOME_CATALOG = {

    "agricultural_income": {
        "category": "Agricultural income",
        "section": "10(1)",
    },

    "share_of_huf_income": {
        "category": "Share of income received by member of HUF",
        "section": "10(2)",
    },

    "certain_partner_share": {
        "category": "Certain share of profit from partnership firm",
        "section": "10(2A)",
    },

    "life_insurance_receipts": {
        "category": "Eligible life insurance receipts",
        "section": "10(10D)",
    },

    "specified_allowances": {
        "category": "Specified exempt allowances",
        "section": "10",
    },

    "hra_exemption": {
        "category": "House Rent Allowance exemption (where eligible)",
        "section": "10(13A)",
    },

    "lta_exemption": {
        "category": "Leave Travel Allowance exemption (where eligible)",
        "section": "10(5)",
    },

    "other_exempt_income": {
        "category": "Other legally exempt income",
        "section": "10 / applicable provision",
    },
}


# ============================================================
# REGIME FILTER
# ============================================================

def regime_available(
    item,
    tax_regime,
):
    """
    Determine whether a deduction is available
    under the selected regime.
    """

    if tax_regime == "old":
        return item[
            "old_regime_available"
        ]

    return item[
        "new_regime_available"
    ]


# ============================================================
# API
# ============================================================

@router.get("/")
def deductions_exempt_income(
    user_id: int = Query(
        ...,
        ge=1,
    ),
    financial_year: str = Query(
        "2026-27",
    ),
    tax_regime: str = Query(
        "new",
    ),
):
    """
    Deductions & Exempt Income Engine.

    This version is a read-only framework.

    No deduction amount is inferred from ordinary
    Financial OS transactions.
    """

    # ========================================================
    # VALIDATE TAX REGIME
    # ========================================================

    tax_regime = (
        str(tax_regime)
        .strip()
        .lower()
    )

    if tax_regime not in (
        "old",
        "new",
    ):
        return {
            "status": "error",
            "message": (
                "tax_regime must be "
                "'old' or 'new'."
            ),
        }

    # ========================================================
    # FILTER DEDUCTIONS FOR REGIME
    # ========================================================

    applicable_deductions = []

    unavailable_deductions = []

    for key, item in (
        DEDUCTION_CATALOG.items()
    ):

        available = regime_available(
            item,
            tax_regime,
        )

        regime_amounts = item.get("maximum_amount_by_regime", {})
        output_item = {
            "section":
                item["section"],

            "name":
                item["name"],

            "available_under_selected_regime":
                available,

            "maximum_amount":
                regime_amounts.get(tax_regime, item["maximum_amount"]),

            "maximum_amount_by_regime": regime_amounts or None,

            "basis":
                item["basis"],

            "verified_claimed_amount":
                0,

            "data_source":
                "No dedicated verified deduction ledger",
        }

        if available:

            applicable_deductions.append(
                output_item
            )

        else:

            unavailable_deductions.append(
                output_item
            )

    # ========================================================
    # EXEMPT INCOME
    # ========================================================

    exempt_income_categories = []

    for key, item in (
        EXEMPT_INCOME_CATALOG.items()
    ):

        exempt_income_categories.append(
            {
                "category":
                    item["category"],

                "section":
                    item["section"],

                "verified_amount":
                    0,

                "available":
                    False,

                "reason":
                    (
                        "No dedicated verified "
                        "exempt-income source is "
                        "currently available."
                    ),
            }
        )

    # ========================================================
    # TOTALS
    # ========================================================

    total_verified_deductions = 0
    total_verified_exempt_income = 0

    # ========================================================
    # STATUS
    # ========================================================

    status = (
        "framework_ready_no_verified_claims"
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "success",

        "engine": (
            "Deductions & Exempt Income Engine"
        ),

        "version":
            ENGINE_VERSION,

        "read_only":
            True,

        "user_id":
            user_id,

        "financial_year": {
            "financial_year":
                financial_year,
        },

        "tax_regime":
            tax_regime,

        "rule_year_status": (
            "catalogue_framework_for_selected_year; verify current Finance Act and eligibility before filing"
            if financial_year in {"2025-26", "2026-27"}
            else "financial_year_not_in_catalogue_validation_window; verify all limits against the applicable Finance Act"
        ),

        "automatic_claim_adjustment": False,
        "automatic_claim_adjustment_reason": "The repository has no verified deduction/evidence ledger; catalog entries are eligibility guidance and are not deducted from taxable income automatically.",

        "engine_status":
            status,

        # ----------------------------------------------------
        # VERIFIED TOTALS
        # ----------------------------------------------------

        "verified_totals": {

            "deductions":
                total_verified_deductions,

            "exempt_income":
                total_verified_exempt_income,

            "data_available":
                False,
        },

        # ----------------------------------------------------
        # APPLICABLE DEDUCTIONS
        # ----------------------------------------------------

        "applicable_deductions":
            applicable_deductions,

        # ----------------------------------------------------
        # NOT AVAILABLE UNDER REGIME
        # ----------------------------------------------------

        "regime_restricted_deductions":
            unavailable_deductions,

        # ----------------------------------------------------
        # EXEMPT INCOME
        # ----------------------------------------------------

        "exempt_income":
            exempt_income_categories,

        # ----------------------------------------------------
        # IMPORTANT DATA RULE
        # ----------------------------------------------------

        "data_policy": {
            "ordinary_expenses_are_deductions":
                False,

            "deductions_inferred_from_transactions":
                False,

            "exempt_income_inferred":
                False,

            "database_write":
                False,
        },

        # ----------------------------------------------------
        # COMPLETENESS
        # ----------------------------------------------------

        "completeness": {

            "deduction_ledger":
                False,

            "exempt_income_ledger":
                False,

            "verified_claims":
                False,

            "final_deduction_amount":
                False,
        },

        # ----------------------------------------------------
        # NEXT ENGINE
        # ----------------------------------------------------

        "next_engine":
            "Final Taxable Income Engine",
    }
