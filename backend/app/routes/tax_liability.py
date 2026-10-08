# ============================================================
# FINANCIAL OS
# TAX LIABILITY ENGINE v1.0
# ============================================================
#
# Purpose:
#   Combine Financial OS tax data into an estimated
#   capital-gain tax liability.
#
# IMPORTANT:
#   - READ-ONLY
#   - Does NOT modify database
#   - Does NOT modify investments
#   - Does NOT modify transactions
#   - Does NOT modify capital-gain calculations
#
# v1.0 scope:
#   - STCG Section 111A
#   - LTCG Section 112A
#   - Aggregate LTCG threshold
#   - STT confirmation
#   - Basic tax
#   - Surcharge context
#   - Health & Education Cess
#   - Taxpayer context
#
# NOT YET INCLUDED:
#   - Complete salary/business tax computation
#   - Capital-loss set-off
#   - Capital-loss carry-forward
#   - Complete 87A computation
#   - Complete old-regime deductions
#   - Complete surcharge/marginal-relief calculation
#   - TDS/TCS
#   - Advance tax
#   - Complete ITR computation
#
# ============================================================


from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy import (
    func,
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Transaction

from app.routes.capital_gains import (
    get_financial_year_dates,
    load_transactions,
    calculate_fifo_gains,
)

from app.routes.asset_classification import (
    resolve_asset_class,
)

from app.routes.capital_gains_classification import (
    classify_gain,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/tax-liability",
    tags=["Tax Liability"],
)


# ============================================================
# TAX CONSTANTS
# ============================================================

STCG_RATE_111A = Decimal("0.20")

LTCG_RATE_112A = Decimal("0.125")

LTCG_112A_THRESHOLD = Decimal(
    "125000"
)

CESS_RATE = Decimal("0.04")

MAX_SPECIAL_GAIN_SURCHARGE_RATE = Decimal(
    "0.15"
)


# ============================================================
# DECIMAL HELPER
# ============================================================

def to_decimal(value):
    """
    Safely convert a value to Decimal.
    """

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


# ============================================================
# MONEY HELPER
# ============================================================

def money(value):
    """
    Round monetary values to two decimal places.
    """

    return to_decimal(
        value
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# ASSET CLASS LOADER
# ============================================================

def load_asset_classes(
    db: Session,
    user_id: int,
):
    """
    Load investment asset classifications.

    Uses the existing Asset Classification Resolver.
    """

    rows = (
        db.execute(
            """
            SELECT
                id,
                name,
                investment_type,
                symbol
            FROM investments
            WHERE user_id = :user_id
            ORDER BY id ASC
            """,
            {
                "user_id": user_id,
            },
        )
    )

    asset_classes = {}

    for row in rows:

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
        }

    return asset_classes


# ============================================================
# CAPITAL GAIN SUMMARY
# ============================================================

def build_capital_gain_summary(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date,
):
    """
    Build STCG/LTCG totals from the existing
    FIFO + classification engines.
    """

    asset_classes = load_asset_classes(
        db=db,
        user_id=user_id,
    )

    transactions = load_transactions(
        db=db,
        user_id=user_id,
        end_date=end_date,
    )

    gains = calculate_fifo_gains(
        transactions=transactions,
        start_date=start_date,
        end_date=end_date,
    )

    stcg = Decimal("0")
    ltcg = Decimal("0")
    unclassified = Decimal("0")

    realised_transactions = []

    for transaction in gains[
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

        else:

            asset_class = (
                investment_info[
                    "asset_class"
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

        gain_loss = to_decimal(
            transaction[
                "realised_gain_loss"
            ]
        )

        if classification_name == "STCG":

            stcg += gain_loss

        elif classification_name == "LTCG":

            ltcg += gain_loss

        else:

            unclassified += gain_loss

        realised_transactions.append(
            {
                **transaction,
                "asset_class": (
                    asset_class
                ),
                "classification": (
                    classification_name
                ),
            }
        )

    return {
        "stcg": stcg,
        "ltcg": ltcg,
        "unclassified": unclassified,
        "transactions": (
            realised_transactions
        ),
    }


# ============================================================
# CAPITAL GAIN TAX
# ============================================================

def calculate_capital_gain_tax(
    stcg,
    ltcg,
    stt_confirmed,
):
    """
    Calculate special-rate capital-gain tax.

    STCG:
        Section 111A at 20% only when
        STT condition is confirmed.

    LTCG:
        Section 112A at 12.5% after the
        aggregate ₹1.25 lakh threshold.
    """

    stcg = money(stcg)
    ltcg = money(ltcg)

    # --------------------------------------------------------
    # STCG
    # --------------------------------------------------------

    if stt_confirmed:

        stcg_taxable = stcg

        stcg_tax = money(
            stcg_taxable
            * STCG_RATE_111A
        )

        stcg_status = (
            "calculated"
        )

    else:

        stcg_taxable = Decimal("0")
        stcg_tax = Decimal("0")

        stcg_status = (
            "requires_stt_confirmation"
        )

    # --------------------------------------------------------
    # LTCG
    # --------------------------------------------------------

    if ltcg > LTCG_112A_THRESHOLD:

        ltcg_taxable = (
            ltcg
            - LTCG_112A_THRESHOLD
        )

    else:

        ltcg_taxable = Decimal("0")

    ltcg_tax = money(
        ltcg_taxable
        * LTCG_RATE_112A
    )

    # --------------------------------------------------------
    # BASE TAX
    # --------------------------------------------------------

    base_tax = money(
        stcg_tax
        + ltcg_tax
    )

    return {
        "stcg": {
            "gross_gain": stcg,
            "taxable_gain": (
                stcg_taxable
            ),
            "rate": (
                STCG_RATE_111A
            ),
            "tax": stcg_tax,
            "status": stcg_status,
            "section": "111A",
        },

        "ltcg": {
            "gross_gain": ltcg,
            "threshold": (
                LTCG_112A_THRESHOLD
            ),
            "taxable_gain": (
                ltcg_taxable
            ),
            "rate": (
                LTCG_RATE_112A
            ),
            "tax": ltcg_tax,
            "section": "112A",
        },

        "base_tax": base_tax,
    }


# ============================================================
# TAX LIABILITY ENDPOINT
# ============================================================

@router.get("/")
def get_tax_liability(
    user_id: int,
    financial_year: str = "2026-27",
    taxpayer_type: str = "individual",
    residential_status: str = "resident",
    tax_regime: str = "new",
    stt_confirmed: bool = False,
    db: Session = Depends(get_db),
):
    """
    Return an estimated tax liability snapshot.

    Example:

    /api/tax-liability/
    ?user_id=1

    Optional context:

    taxpayer_type=individual
    residential_status=resident
    tax_regime=new
    stt_confirmed=true
    """

    # ========================================================
    # NORMALIZE TAX CONTEXT
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
    # VALIDATE TAXPAYER
    # ========================================================

    valid_taxpayer_types = {
        "individual",
        "huf",
    }

    if taxpayer_type not in (
        valid_taxpayer_types
    ):

        return {
            "status": "error",
            "message": (
                "taxpayer_type must be "
                "individual or huf."
            ),
        }

    # ========================================================
    # VALIDATE RESIDENTIAL STATUS
    # ========================================================

    valid_residential_status = {
        "resident",
        "non_resident",
    }

    if residential_status not in (
        valid_residential_status
    ):

        return {
            "status": "error",
            "message": (
                "residential_status must be "
                "resident or non_resident."
            ),
        }

    # ========================================================
    # VALIDATE TAX REGIME
    # ========================================================

    valid_tax_regimes = {
        "new",
        "old",
    }

    if tax_regime not in (
        valid_tax_regimes
    ):

        return {
            "status": "error",
            "message": (
                "tax_regime must be "
                "new or old."
            ),
        }

    # ========================================================
    # FINANCIAL YEAR
    # ========================================================

    (
        resolved_financial_year,
        start_date,
        end_date,
    ) = get_financial_year_dates(
        financial_year
    )

    # ========================================================
    # CAPITAL GAINS
    # ========================================================

    capital_gains = (
        build_capital_gain_summary(
            db=db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
    )

    # ========================================================
    # TAX CALCULATION
    # ========================================================

    tax = calculate_capital_gain_tax(
        stcg=capital_gains[
            "stcg"
        ],
        ltcg=capital_gains[
            "ltcg"
        ],
        stt_confirmed=stt_confirmed,
    )

    base_tax = money(
        tax["base_tax"]
    )

    # ========================================================
    # SURCHARGE
    # ========================================================
    #
    # We do NOT guess surcharge because complete total
    # income is not yet available to this engine.
    #
    # Special-rate capital-gain income is subject to
    # specific surcharge limitations.
    #
    # Therefore v1.0 exposes the applicable maximum
    # special-rate surcharge context but does not apply it.
    #
    # ========================================================

    surcharge = Decimal("0")

    surcharge_status = (
        "not_calculated_total_income_required"
    )

    # ========================================================
    # CESS
    # ========================================================
    #
    # Cess is calculated only on tax + surcharge.
    #
    # Since surcharge is currently zero in v1.0,
    # this is 4% of base tax.
    #
    # ========================================================

    cess = money(
        (
            base_tax
            + surcharge
        )
        * CESS_RATE
    )

    total_capital_gain_tax = money(
        base_tax
        + surcharge
        + cess
    )

    # ========================================================
    # 87A CONTEXT
    # ========================================================

    rebate_possible = (
        taxpayer_type == "individual"
        and residential_status == "resident"
    )

    if tax_regime == "new":

        rebate_limit = Decimal(
            "60000"
        )

        rebate_income_limit = Decimal(
            "1200000"
        )

    else:

        rebate_limit = Decimal(
            "12500"
        )

        rebate_income_limit = Decimal(
            "500000"
        )

    # ========================================================
    # ENGINE STATUS
    # ========================================================

    if (
        capital_gains[
            "unclassified"
        ] != 0
    ):

        engine_status = (
            "requires_review"
        )

    elif (
        capital_gains[
            "stcg"
        ] != 0
        and not stt_confirmed
    ):

        engine_status = (
            "requires_stt_confirmation"
        )

    else:

        engine_status = (
            "capital_gain_liability_calculated"
        )

    # ========================================================
    # FINAL SCOPE STATUS
    # ========================================================

    final_liability_status = (
        "incomplete_total_income_required"
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "success",

        "user_id": user_id,

        "tax_liability_engine": {
            "name": (
                "Tax Liability Engine"
            ),
            "version": "1.0",
            "read_only": True,
            "status": engine_status,
            "final_liability_status": (
                final_liability_status
            ),
        },

        "financial_year": (
            resolved_financial_year
        ),

        "taxpayer_context": {
            "type": taxpayer_type,
            "residential_status": (
                residential_status
            ),
            "tax_regime": tax_regime,
        },

        "capital_gains": {
            "stcg": money(
                capital_gains[
                    "stcg"
                ]
            ),
            "ltcg": money(
                capital_gains[
                    "ltcg"
                ]
            ),
            "unclassified": money(
                capital_gains[
                    "unclassified"
                ]
            ),
        },

        "tax_rates": {
            "section_111a_stcg": (
                STCG_RATE_111A
            ),
            "section_112a_ltcg": (
                LTCG_RATE_112A
            ),
            "section_112a_threshold": (
                LTCG_112A_THRESHOLD
            ),
        },

        "tax_calculation": {
            "stcg": tax["stcg"],
            "ltcg": tax["ltcg"],
            "base_tax": base_tax,
        },

        "surcharge": {
            "calculated": False,
            "amount": surcharge,
            "maximum_special_gain_rate": (
                MAX_SPECIAL_GAIN_SURCHARGE_RATE
            ),
            "status": surcharge_status,
        },

        "cess": {
            "rate": CESS_RATE,
            "amount": cess,
        },

        "estimated_capital_gain_tax": {
            "tax": base_tax,
            "surcharge": surcharge,
            "cess": cess,
            "total": (
                total_capital_gain_tax
            ),
        },

        "rebate_context": {
            "section": "87A",
            "possible": rebate_possible,
            "maximum_rebate": (
                rebate_limit
            ),
            "income_limit": (
                rebate_income_limit
            ),
            "calculated": False,
        },

        "scope": {
            "capital_gains": True,
            "salary_tax": False,
            "business_tax": False,
            "other_income_tax": False,
            "loss_setoff": False,
            "loss_carry_forward": False,
            "tds": False,
            "tcs": False,
            "advance_tax": False,
            "complete_itr": False,
        },

        "next_engine": (
            "Income Tax & Loss Set-off Engine"
        ),

        "limitations": [
            (
                "This v1.0 calculates capital-gain "
                "tax liability only."
            ),
            (
                "It is not a complete final income-tax "
                "liability calculation."
            ),
            (
                "Complete surcharge requires total "
                "income and applicable tax details."
            ),
            (
                "87A rebate is exposed as context but "
                "is not automatically applied."
            ),
            (
                "Capital-loss set-off and carry-forward "
                "are not yet implemented."
            ),
            (
                "TDS/TCS and advance-tax credits are "
                "not yet implemented."
            ),
        ],

        "read_only": True,
    }
