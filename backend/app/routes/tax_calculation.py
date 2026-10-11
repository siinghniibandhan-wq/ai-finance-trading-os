# ============================================================
# FINANCIAL OS
# TAX CALCULATION ENGINE v1.0
# ============================================================
#
# Purpose:
# - Calculate indicative tax on realised capital gains
# - Use Capital Gains Classification Engine
# - Apply current special capital-gain rates
# - Apply Section 112A LTCG threshold
# - Calculate 4% Health & Education Cess
#
# IMPORTANT:
# - READ-ONLY
# - Does NOT modify database
# - Does NOT modify capital gains
# - Does NOT modify investments
# - Does NOT calculate complete ITR liability
# - Does NOT calculate surcharge
# - Does NOT calculate slab-rate income tax
# - STT condition must be explicitly confirmed
#
# CURRENT RULES USED:
#
# Listed equity / qualifying Section 111A STCG:
#     20%
#
# Section 112A LTCG:
#     12.5%
#
# Section 112A threshold:
#     First ₹1,25,000 of eligible LTCG
#     is excluded from the 12.5% calculation.
#
# Cess:
#     4% on calculated income tax + surcharge, where applicable.
#
# ============================================================


from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
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

from app.routes.capital_gains_classification import (
    classify_gain_by_dates,
)
from app.routes.final_tax_liability import get_tax_rule_set


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/tax-calculation",
    tags=["Tax Calculation"],
)


# ============================================================
# TAX CONSTANTS
# ============================================================

STCG_RATE_111A = Decimal("0.20")

LTCG_RATE_112A = Decimal("0.125")

LTCG_112A_EXEMPTION_LIMIT = Decimal(
    "125000"
)

CESS_RATE = Decimal("0.04")


# ============================================================
# MONEY ROUNDING
# ============================================================

def money(value):
    """
    Round monetary values to two decimal places.
    """

    return Decimal(
        str(value)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# INVESTMENT ASSET CLASSES
# ============================================================

def load_asset_classes(
    db: Session,
    user_id: int,
):
    """
    Load investment asset classifications.

    Uses the existing Asset Classification Resolver.
    """

    from sqlalchemy import text

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
        }

    return asset_classes


# ============================================================
# TAX CALCULATION
# ============================================================

def calculate_tax(
    stcg,
    ltcg,
    stt_confirmed,
    stcg_rate=STCG_RATE_111A,
    ltcg_rate=LTCG_RATE_112A,
    ltcg_exemption_limit=LTCG_112A_EXEMPTION_LIMIT,
    cess_rate=CESS_RATE,
):
    """
    Calculate indicative special-rate capital-gain tax.

    STCG:
        Calculated at 20% only when STT condition is confirmed.

    LTCG:
        Section 112A treatment is calculated at 12.5%
        after the ₹1.25 lakh aggregate threshold.

    This function does NOT calculate:
    - slab income tax
    - basic exemption adjustment
    - rebate
    - surcharge
    - deductions
    - losses from other heads
    - MAT/AMT
    - complete ITR liability
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
            * stcg_rate
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
    # LTCG SECTION 112A
    # --------------------------------------------------------

    if ltcg > ltcg_exemption_limit:

        ltcg_taxable = (
            ltcg
            - ltcg_exemption_limit
        )

    else:

        ltcg_taxable = Decimal("0")

    ltcg_tax = money(
        ltcg_taxable
        * ltcg_rate
    )

    # --------------------------------------------------------
    # TOTAL SPECIAL-RATE TAX
    # --------------------------------------------------------

    base_tax = money(
        stcg_tax
        + ltcg_tax
    )

    # --------------------------------------------------------
    # HEALTH & EDUCATION CESS
    # --------------------------------------------------------

    cess = money(
        base_tax
        * cess_rate
    )

    total_tax_with_cess = money(
        base_tax
        + cess
    )

    return {
        "stcg": {
            "gross_gain": stcg,
            "stt_confirmed": (
                stt_confirmed
            ),
            "taxable_gain": (
                stcg_taxable
            ),
            "rate": (
                stcg_rate
            ),
            "tax": stcg_tax,
            "status": stcg_status,
        },

        "ltcg": {
            "gross_gain": ltcg,
            "section": "112A",
            "threshold": (
                ltcg_exemption_limit
            ),
            "taxable_gain": (
                ltcg_taxable
            ),
            "rate": (
                ltcg_rate
            ),
            "tax": ltcg_tax,
        },

        "summary": {
            "base_tax": base_tax,
            "cess_rate": cess_rate,
            "health_education_cess": cess,
            "tax_plus_cess": (
                total_tax_with_cess
            ),
        },
    }


# ============================================================
# API
# ============================================================

@router.get("/")
def tax_calculation(
    user_id: int,
    financial_year: str = "2026-27",
    stt_confirmed: bool = False,
    db: Session = Depends(get_db),
):
    """
    Return indicative capital-gain tax calculation.

    stt_confirmed:
        false = do not assume STT eligibility
        true  = user confirms applicable STT condition
    """

    # --------------------------------------------------------
    # FINANCIAL YEAR RULES — fail closed for unsupported years
    # --------------------------------------------------------
    try:
        rule_set = get_tax_rule_set(financial_year)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    capital_gains_rules = rule_set["capital_gains"]
    stcg_rate = Decimal(str(capital_gains_rules["section_111a_rate"]))
    ltcg_rate = Decimal(str(capital_gains_rules["section_112a_rate"]))
    ltcg_exemption_limit = Decimal(str(capital_gains_rules["section_112a_annual_exemption"]))
    cess_rate = Decimal(str(rule_set["cess_rate"]))

    (
        resolved_financial_year,
        start_date,
        end_date,
    ) = get_financial_year_dates(
        financial_year
    )

    # --------------------------------------------------------
    # ASSET CLASSES
    # --------------------------------------------------------

    asset_classes = load_asset_classes(
        db=db,
        user_id=user_id,
    )

    # --------------------------------------------------------
    # LOAD LEDGER
    # --------------------------------------------------------

    transactions = load_transactions(
        db=db,
        user_id=user_id,
        end_date=end_date,
    )

    # --------------------------------------------------------
    # FIFO GAINS
    # --------------------------------------------------------

    gains = calculate_fifo_gains(
        transactions=transactions,
        start_date=start_date,
        end_date=end_date,
    )

    stcg = Decimal("0")
    ltcg = Decimal("0")
    unclassified = Decimal("0")

    classified_transactions = []

    # --------------------------------------------------------
    # CLASSIFY REALISED GAINS
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # CLASSIFY AND ALLOCATE GAIN AT FIFO-LOT LEVEL
        # ----------------------------------------------------
        # A sale may consume several acquisition lots. Allocate net proceeds
        # proportionally by matched quantity and compare each allocation with
        # that lot's own FIFO cost basis. Never classify a mixed sale by its
        # weighted-average holding period.
        sale_date = transaction.get("sale_date")
        if isinstance(sale_date, datetime):
            sale_date = sale_date.date()
        elif isinstance(sale_date, str):
            try:
                sale_date = date.fromisoformat(sale_date[:10])
            except ValueError:
                sale_date = None

        lot_results = []
        matched_lots = transaction.get("matched_lots") or []
        matched_quantity = Decimal("0")
        for lot in matched_lots:
            matched_quantity += Decimal(str(lot.get("quantity", 0)))

        for lot in matched_lots:
            buy_date = lot.get("buy_date")
            if isinstance(buy_date, datetime):
                buy_date = buy_date.date()
            elif isinstance(buy_date, str):
                try:
                    buy_date = date.fromisoformat(buy_date[:10])
                except ValueError:
                    buy_date = None

            classification = classify_gain_by_dates(
                acquisition_date=buy_date,
                sale_date=sale_date,
                asset_class=asset_class,
            )
            lot_quantity = Decimal(str(lot.get("quantity", 0)))
            cost_basis = Decimal(str(lot.get("cost_basis", 0)))
            if matched_quantity > 0:
                allocated_net_proceeds = (
                    Decimal(str(transaction.get("net_sale_proceeds", 0)))
                    * lot_quantity / matched_quantity
                )
            else:
                allocated_net_proceeds = Decimal("0")
            lot_gain = allocated_net_proceeds - cost_basis
            classification_name = classification["classification"]
            if classification_name == "STCG":
                stcg += lot_gain
            elif classification_name == "LTCG":
                ltcg += lot_gain
            else:
                unclassified += lot_gain
            lot_results.append({
                **lot,
                "allocated_net_sale_proceeds": allocated_net_proceeds,
                "realised_gain_loss": lot_gain,
                "capital_gain_classification": classification,
            })

        if not matched_lots:
            gain_loss = Decimal(str(transaction.get("realised_gain_loss", 0)))
            unclassified += gain_loss

        # Sale-level status is MIXED when FIFO lots span STCG/LTCG, and
        # UNCLASSIFIED if any lot cannot safely be classified.
        lot_types = {x["capital_gain_classification"]["classification"] for x in lot_results}
        if not lot_results or "UNCLASSIFIED" in lot_types:
            sale_classification = {"classification": "UNCLASSIFIED", "classification_status": "one_or_more_lots_unclassified"}
        elif len(lot_types) > 1:
            sale_classification = {"classification": "MIXED", "classification_status": "sale_contains_multiple_holding_period_classes"}
        else:
            sale_classification = {"classification": next(iter(lot_types)), "classification_status": "classified_by_fifo_lot_dates"}

        classified_transactions.append({
            **transaction,
            "asset_class": asset_class,
            "capital_gain_classification": sale_classification,
            "lot_level_results": lot_results,
        })

    # --------------------------------------------------------
    # TAX CALCULATION
    # --------------------------------------------------------

    tax = calculate_tax(
        stcg=stcg,
        ltcg=ltcg,
        stt_confirmed=(
            stt_confirmed
        ),
        stcg_rate=stcg_rate,
        ltcg_rate=ltcg_rate,
        ltcg_exemption_limit=ltcg_exemption_limit,
        cess_rate=cess_rate,
    )

    # --------------------------------------------------------
    # ENGINE STATUS
    # --------------------------------------------------------

    unmatched_quantity = Decimal(str(gains.get("summary", {}).get("unmatched_quantity", 0)))

    if unclassified != 0 or unmatched_quantity != 0:
        engine_status = "requires_review"

    elif (
        stcg != 0
        and not stt_confirmed
    ):

        engine_status = (
            "requires_stt_confirmation"
        )

    else:

        engine_status = (
            "calculated_special_rate_tax"
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "status": "success",

        "user_id": user_id,

        "tax_calculation_engine": {
            "name": (
                "Tax Calculation Engine"
            ),
            "version": "1.0",
            "read_only": True,
            "status": engine_status,
        },

        "financial_year": (
            resolved_financial_year
        ),

        "start_date": start_date,

        "end_date": end_date,

        "data_source": {
            "capital_gains": (
                "Capital Gains Data Engine"
            ),
            "classification": (
                "Capital Gains Classification Engine"
            ),
            "asset_class": (
                "Asset Classification Resolver"
            ),
        },

        "tax_rules": {
            "stcg_111a_rate": (
                stcg_rate
            ),
            "ltcg_112a_rate": (
                ltcg_rate
            ),
            "ltcg_112a_threshold": (
                ltcg_exemption_limit
            ),
            "cess_rate": cess_rate,
            "stt_confirmed": (
                stt_confirmed
            ),
        },

        "capital_gains": {
            "stcg": money(stcg),
            "ltcg": money(ltcg),
            "unclassified": money(unclassified),
            "unmatched_quantity": unmatched_quantity,
        },

        "tax": tax,

        "realised_transactions": (
            classified_transactions
        ),

        "limitations": [
            (
                "This is not a complete ITR "
                "tax-liability calculation."
            ),
            (
                "Surcharge is not calculated."
            ),
            (
                "Other income and slab-rate "
                "tax are not included."
            ),
            (
                "Rebate and basic-exemption "
                "adjustments are not included."
            ),
            (
                "STT eligibility must be "
                "confirmed before Section "
                "111A STCG tax is calculated."
            ),
            (
                "This endpoint currently supports only financial years "
                "registered in the Final Tax Liability rule registry."
            ),
            (
                "Any unmatched FIFO sale quantity requires review and is "
                "not silently treated as a fully reconciled gain."
            ),
        ],
    }
