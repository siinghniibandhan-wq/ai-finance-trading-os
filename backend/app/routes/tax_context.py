# ============================================================
# FINANCIAL OS
# TAX CONTEXT ENGINE v1.0
# ============================================================
#
# Purpose:
#   Provide the taxpayer context required by the Tax Engine.
#
# IMPORTANT:
#   - READ-ONLY
#   - Does NOT modify database
#   - Does NOT calculate final tax liability
#   - Does NOT calculate ITR
#   - Does NOT change capital gains
#
# Context currently supported:
#   - taxpayer type
#   - residential status
#   - tax regime
#   - STT confirmation
#   - financial year
#
# ============================================================

from fastapi import APIRouter, HTTPException


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/tax-context",
    tags=["Tax Context"],
)


# ============================================================
# SUPPORTED VALUES
# ============================================================

SUPPORTED_TAXPAYER_TYPES = {
    "individual",
    "huf",
}

SUPPORTED_RESIDENTIAL_STATUS = {
    "resident",
    "non_resident",
}

SUPPORTED_TAX_REGIMES = {
    "new",
    "old",
}


# ============================================================
# TAX CONTEXT
# ============================================================

@router.get("/")
def get_tax_context(
    user_id: int,
    financial_year: str = "2026-27",
    taxpayer_type: str = "individual",
    residential_status: str = "resident",
    tax_regime: str = "new",
    stt_confirmed: bool = False,
):
    """
    Return read-only taxpayer context.

    Example:

    /api/tax-context/
    ?user_id=1
    &financial_year=2026-27
    &taxpayer_type=individual
    &residential_status=resident
    &tax_regime=new
    &stt_confirmed=true
    """

    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    taxpayer_type = (
        taxpayer_type.strip().lower()
    )

    residential_status = (
        residential_status.strip().lower()
    )

    tax_regime = (
        tax_regime.strip().lower()
    )

    # ========================================================
    # VALIDATE TAXPAYER TYPE
    # ========================================================

    if taxpayer_type not in SUPPORTED_TAXPAYER_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported taxpayer_type. "
                "Use individual or huf."
            ),
        )

    # ========================================================
    # VALIDATE RESIDENTIAL STATUS
    # ========================================================

    if (
        residential_status
        not in SUPPORTED_RESIDENTIAL_STATUS
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported residential_status. "
                "Use resident or non_resident."
            ),
        )

    # ========================================================
    # VALIDATE TAX REGIME
    # ========================================================

    if tax_regime not in SUPPORTED_TAX_REGIMES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported tax_regime. "
                "Use new or old."
            ),
        )

    # ========================================================
    # RESIDENT-ONLY REBATE ELIGIBILITY FLAG
    # ========================================================

    rebate_87a_possible = (
        taxpayer_type == "individual"
        and residential_status == "resident"
    )

    # ========================================================
    # REBATE LIMITS
    # ========================================================
    #
    # These are context values only.
    #
    # Final rebate calculation will be handled by
    # the Tax Liability Engine.
    #
    # ========================================================

    if tax_regime == "new":

        rebate_limit = 60000
        rebate_income_limit = 1200000

    else:

        rebate_limit = 12500
        rebate_income_limit = 500000

    # ========================================================
    # CAPITAL GAINS CONTEXT
    # ========================================================

    capital_gain_context = {
        "section_111a_stcg_rate": 0.20,
        "section_112a_ltcg_rate": 0.125,
        "section_112a_ltcg_threshold": 125000,
        "stt_confirmed": stt_confirmed,
    }

    # ========================================================
    # ENGINE STATUS
    # ========================================================

    status = "ready"

    if (
        residential_status == "non_resident"
        and rebate_87a_possible is False
    ):
        status = "ready_with_rebate_restriction"

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "success",

        "user_id": user_id,

        "tax_context_engine": {
            "name": "Tax Context Engine",
            "version": "1.0",
            "read_only": True,
            "status": status,
        },

        "financial_year": financial_year,

        "taxpayer": {
            "type": taxpayer_type,
            "residential_status": (
                residential_status
            ),
            "tax_regime": tax_regime,
        },

        "rebate_context": {
            "section": "87A",
            "possible": (
                rebate_87a_possible
            ),
            "maximum_rebate": rebate_limit,
            "income_limit": (
                rebate_income_limit
            ),
        },

        "capital_gain_context": (
            capital_gain_context
        ),

        "calculation_scope": {
            "final_tax_liability": False,
            "slab_tax": False,
            "surcharge": False,
            "marginal_relief": False,
            "rebate_calculation": False,
            "cess_calculation": False,
            "itr_calculation": False,
        },

        "next_engine": (
            "Tax Liability Engine"
        ),

        "limitations": [
            (
                "This endpoint provides taxpayer "
                "context only."
            ),
            (
                "It does not calculate final tax "
                "liability."
            ),
            (
                "Rebate eligibility is only exposed "
                "as context; final rebate calculation "
                "will be handled separately."
            ),
            (
                "Taxpayer information is not persisted "
                "to the database in v1.0."
            ),
        ],
    }
