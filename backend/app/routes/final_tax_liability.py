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
    age_category="under_60",
    residential_status="resident",
):
    """
    Calculate old-regime slab tax for an individual.

    age_category values:
      - under_60
      - 60_to_79
      - 80_plus

    Senior-citizen basic exemption thresholds apply only to residents.
    If age is unknown, callers may calculate a provisional under-60
    estimate, but must mark the assessment incomplete.
    """
    income = max(decimal(taxable_income), Decimal("0"))

    # Non-residents do not receive the higher age-based basic exemption.
    effective_age = (
        age_category
        if residential_status == "resident"
        else "under_60"
    )

    if effective_age == "80_plus":
        slabs = [
            (Decimal("500000"), Decimal("0.00")),
            (Decimal("1000000"), Decimal("0.20")),
            (None, Decimal("0.30")),
        ]
    elif effective_age == "60_to_79":
        slabs = [
            (Decimal("300000"), Decimal("0.00")),
            (Decimal("500000"), Decimal("0.05")),
            (Decimal("1000000"), Decimal("0.20")),
            (None, Decimal("0.30")),
        ]
    else:
        slabs = [
            (Decimal("250000"), Decimal("0.00")),
            (Decimal("500000"), Decimal("0.05")),
            (Decimal("1000000"), Decimal("0.20")),
            (None, Decimal("0.30")),
        ]

    tax = Decimal("0")
    previous_limit = Decimal("0")

    for upper_limit, rate in slabs:
        if upper_limit is None:
            taxable_slice = income - previous_limit
            if taxable_slice > 0:
                tax += taxable_slice * rate
            break

        taxable_slice = min(
            max(income - previous_limit, Decimal("0")),
            upper_limit - previous_limit,
        )
        if taxable_slice > 0:
            tax += taxable_slice * rate
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
    age_category="under_60",
    residential_status="resident",
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

    normal_surcharge = money(normal_tax * rate)

    # Special-rate income has a maximum surcharge rate of 15% under
    # the configured rules. Keep it separate from ordinary slab tax.
    special_surcharge_rate = min(rate, Decimal("0.15"))
    special_surcharge = money(special_rate_tax * special_surcharge_rate)

    surcharge_marginal_relief = Decimal("0.00")
    relief_threshold = None
    relief_review_required = False

    # Marginal relief at surcharge thresholds is safely calculated here
    # only when no special-rate tax is present. With special-rate gains,
    # the income composition at the threshold is needed for an exact
    # comparison; do not guess or silently apply an approximate relief.
    thresholds = [Decimal("5000000"), Decimal("10000000"), Decimal("20000000"), Decimal("50000000")]
    crossed = next((t for t in thresholds if income > t), None)
    if crossed is not None and (normal_surcharge + special_surcharge) > 0:
        if decimal(special_rate_tax) > 0:
            relief_review_required = True
        else:
            threshold_tax = (
                calculate_new_regime_slab_tax(crossed)
                if tax_regime == "new"
                else calculate_old_regime_slab_tax(
                    crossed, age_category=age_category,
                    residential_status=residential_status
                )
            )
            tax_plus_surcharge = decimal(normal_tax) + normal_surcharge
            permitted_tax = threshold_tax + (income - crossed)
            surcharge_marginal_relief = min(
                normal_surcharge,
                max(tax_plus_surcharge - permitted_tax, Decimal("0")),
            )
            normal_surcharge = money(normal_surcharge - surcharge_marginal_relief)
            relief_threshold = int(crossed)

    return {
        "rate": rate,
        "normal_income_surcharge": normal_surcharge,
        "special_rate_surcharge": special_surcharge,
        "marginal_relief": money(surcharge_marginal_relief),
        "marginal_relief_threshold": relief_threshold,
        "marginal_relief_review_required": relief_review_required,
        "total": money(normal_surcharge + special_surcharge),
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
    """Calculate Section 87A rebate and New Regime marginal relief.

    This helper handles ordinary slab tax only. Special-rate capital-gains
    tax remains separate in the caller. Rules here reflect the configured
    ₹12 lakh / ₹60,000 New Regime threshold and ₹5 lakh / ₹12,500 Old Regime
    threshold; callers must use the matching financial-year rule set.
    """
    income = max(decimal(taxable_income), Decimal("0"))
    slab_tax = max(decimal(normal_tax), Decimal("0"))

    is_new = tax_regime == "new"
    income_limit = (
        NEW_REGIME_87A_INCOME_LIMIT
        if is_new else OLD_REGIME_87A_INCOME_LIMIT
    )
    maximum_rebate = (
        NEW_REGIME_87A_MAX_REBATE
        if is_new else OLD_REGIME_87A_MAX_REBATE
    )

    if residential_status != "resident":
        return {
            "eligible": False,
            "reason": "Section 87A is available only to eligible resident individuals.",
            "income_limit": money(income_limit),
            "maximum_rebate": money(maximum_rebate),
            "rebate": money(0),
            "marginal_relief": money(0),
        }

    if income <= income_limit:
        # The statutory rebate applies only while income is within the limit.
        rebate = min(slab_tax, maximum_rebate)
        return {
            "eligible": True,
            "reason": "Taxable income is within the configured Section 87A limit.",
            "income_limit": money(income_limit),
            "maximum_rebate": money(maximum_rebate),
            "rebate": money(rebate),
            "marginal_relief": money(0),
        }

    # New-regime marginal relief is NOT itself a Section 87A rebate.
    # Keep it separately reported so downstream calculations do not label
    # relief as a rebate or accidentally apply the two twice. This calculation
    # applies to ordinary slab tax only; special-rate tax remains separate.
    if is_new:
        excess_income = income - income_limit
        marginal_relief = max(slab_tax - excess_income, Decimal("0"))
        if marginal_relief > 0:
            return {
                "eligible": True,
                "reason": "New-regime marginal relief limits ordinary slab tax to the income exceeding the configured threshold.",
                "income_limit": money(income_limit),
                "maximum_rebate": money(maximum_rebate),
                "rebate": money(0),
                "marginal_relief": money(marginal_relief),
            }

    return {
        "eligible": False,
        "reason": "Taxable income exceeds the applicable Section 87A threshold and no marginal relief applies to ordinary slab tax.",
        "income_limit": money(income_limit),
        "maximum_rebate": money(maximum_rebate),
        "rebate": money(0),
        "marginal_relief": money(0),
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
# OFFICIAL STATEMENT RECONCILIATION PREVIEW (AIS / FORM 26AS)
# ============================================================

class OfficialTaxCreditRecord(BaseModel):
    """A normalized credit row manually extracted from an official statement."""
    credit_type: str = Field(pattern=r"^(tds|advance_tax|self_assessment_tax)$")
    amount: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    source_reference: str = Field(min_length=1, max_length=200)


class TaxCreditReconciliationPreviewInput(BaseModel):
    # Preview only: no entry is automatically verified or changed.
    user_id: int = Field(ge=1)
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    official_records: list[OfficialTaxCreditRecord] = Field(min_length=1, max_length=2000)


def normalize_credit_reference(value):
    """Normalize source references for robust matching without changing stored values."""
    return " ".join(str(value or "").strip().casefold().split())


@router.post("/credits/reconcile-preview")
def preview_official_tax_credit_reconciliation(
    payload: TaxCreditReconciliationPreviewInput,
    db: Session = Depends(get_db),
):
    """
    Compare user-provided rows transcribed from AIS / Form 26AS with saved credits.

    This is a reconciliation preview only. It does not fetch official records,
    verify their authenticity, update entry statuses, or change tax liability.
    """
    if not db.query(User).filter(User.id == payload.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

    saved_entries = db.query(TaxCreditEntry).filter(
        TaxCreditEntry.user_id == payload.user_id,
        TaxCreditEntry.financial_year == payload.financial_year,
    ).order_by(TaxCreditEntry.id.asc()).all()

    official_by_ref = {}
    for record in payload.official_records:
        ref = normalize_credit_reference(record.source_reference)
        official_by_ref.setdefault(ref, []).append(record)

    saved_by_ref = {}
    for entry in saved_entries:
        ref = normalize_credit_reference(entry.source_reference)
        if ref:
            saved_by_ref.setdefault(ref, []).append(entry)

    duplicate_official_refs = sorted(
        ref for ref, rows in official_by_ref.items() if len(rows) > 1
    )
    duplicate_saved_refs = sorted(
        ref for ref, rows in saved_by_ref.items() if len(rows) > 1
    )

    matched = []
    mismatches = []
    official_unmatched = []
    saved_unmatched = []
    reviewed_official_refs = set()
    reviewed_saved_ids = set()

    # Only one-to-one reference matches can be considered for comparison.
    for ref, official_rows in official_by_ref.items():
        if ref in duplicate_official_refs:
            mismatches.append({
                "source_reference": ref,
                "reason": "duplicate_reference_in_official_records",
                "official_record_count": len(official_rows),
            })
            continue

        saved_rows = saved_by_ref.get(ref, [])
        if len(saved_rows) > 1:
            mismatches.append({
                "source_reference": ref,
                "reason": "duplicate_reference_in_saved_records",
                "saved_entry_ids": [row.id for row in saved_rows],
            })
            continue

        if not saved_rows:
            official_unmatched.append({
                "source_reference": official_rows[0].source_reference,
                "credit_type": official_rows[0].credit_type,
                "amount": str(official_rows[0].amount),
            })
            continue

        official = official_rows[0]
        saved = saved_rows[0]
        reviewed_official_refs.add(ref)
        reviewed_saved_ids.add(saved.id)

        if saved.credit_type != official.credit_type or decimal(saved.amount) != decimal(official.amount):
            mismatches.append({
                "source_reference": official.source_reference,
                "saved_entry_id": saved.id,
                "saved_credit_type": saved.credit_type,
                "official_credit_type": official.credit_type,
                "saved_amount": str(saved.amount),
                "official_amount": str(official.amount),
                "reason": "credit_type_or_amount_mismatch",
            })
        else:
            matched.append({
                "source_reference": official.source_reference,
                "saved_entry_id": saved.id,
                "credit_type": official.credit_type,
                "amount": str(official.amount),
                "saved_status": saved.status,
                "verification_status": (
                    "already_verified" if saved.status == "verified"
                    else "still_requires_verification"
                ),
            })

    for entry in saved_entries:
        ref = normalize_credit_reference(entry.source_reference)
        if not ref:
            saved_unmatched.append({
                "saved_entry_id": entry.id,
                "source_reference": None,
                "credit_type": entry.credit_type,
                "amount": str(entry.amount),
                "reason": "missing_source_reference",
            })
        elif ref not in official_by_ref and entry.id not in reviewed_saved_ids:
            saved_unmatched.append({
                "saved_entry_id": entry.id,
                "source_reference": entry.source_reference,
                "credit_type": entry.credit_type,
                "amount": str(entry.amount),
                "status": entry.status,
                "reason": "not_found_in_official_records",
            })

    has_issues = bool(
        mismatches or official_unmatched or saved_unmatched
        or duplicate_official_refs or duplicate_saved_refs
    )
    return {
        "status": "review_required" if has_issues else "matched_pending_verification",
        "user_id": payload.user_id,
        "financial_year": payload.financial_year,
        "source": "user_supplied_official_statement_rows",
        "official_source_authenticity_verified": False,
        "records_persisted_or_modified": False,
        "entries_marked_verified": False,
        "tax_liability_changed": False,
        "summary": {
            "matched_count": len(matched),
            "mismatch_count": len(mismatches),
            "official_unmatched_count": len(official_unmatched),
            "saved_unmatched_count": len(saved_unmatched),
            "duplicate_official_references": duplicate_official_refs,
            "duplicate_saved_references": duplicate_saved_refs,
        },
        "matched": matched,
        "mismatches": mismatches,
        "official_records_not_saved": official_unmatched,
        "saved_entries_not_in_official_records": saved_unmatched,
        "next_step": (
            "Resolve mismatches and independently verify statement authenticity before marking any credit verified."
        ),
    }


# ============================================================
# VERIFIED CREDIT RECONCILIATION
# ============================================================

def summarize_verified_tax_credits(entries):
    """
    Count only verified entries with a source reference that is unique
    within this user's financial-year credit set.

    If the same reference appears more than once (even under different
    credit types), exclude every matching row pending reconciliation.
    Verified rows without a reference are also excluded from the payable
    calculation because they cannot be matched to a source record.
    """
    verified = [entry for entry in entries if entry.status == "verified"]

    reference_rows = {}
    for entry in verified:
        reference = (entry.source_reference or "").strip().casefold()
        if reference:
            reference_rows.setdefault(reference, []).append(entry)

    duplicate_references = sorted(
        reference for reference, rows in reference_rows.items()
        if len(rows) > 1
    )

    totals = {
        credit_type: {
            "verified_amount": Decimal("0.00"),
            "eligible_entry_count": 0,
            "excluded_duplicate_count": 0,
            "excluded_missing_reference_count": 0,
        }
        for credit_type in ("tds", "advance_tax", "self_assessment_tax")
    }

    included_entry_ids = []
    excluded_entry_ids = []

    for entry in verified:
        summary = totals.get(entry.credit_type)
        if summary is None:
            excluded_entry_ids.append(entry.id)
            continue

        reference = (entry.source_reference or "").strip().casefold()
        if not reference:
            summary["excluded_missing_reference_count"] += 1
            excluded_entry_ids.append(entry.id)
            continue

        if reference in duplicate_references:
            summary["excluded_duplicate_count"] += 1
            excluded_entry_ids.append(entry.id)
            continue

        summary["verified_amount"] += decimal(entry.amount)
        summary["eligible_entry_count"] += 1
        included_entry_ids.append(entry.id)

    for summary in totals.values():
        summary["verified_amount"] = money(summary["verified_amount"])

    return {
        "by_type": totals,
        "duplicate_source_references": duplicate_references,
        "included_entry_ids": included_entry_ids,
        "excluded_entry_ids": excluded_entry_ids,
        "excluded_entries_require_review": bool(excluded_entry_ids),
    }


# ============================================================
# OLD VS NEW REGIME COMPARISON
# ============================================================

def build_regime_comparison(old_result, new_result):
    """Compare two liability results without pretending incomplete
    assessments are final. Tax-credit balances are deliberately excluded
    from this comparison because the comparison is based on tax before
    TDS/advance-tax credits.
    """
    results = {"old": old_result, "new": new_result}
    summaries = {}
    incomplete_reasons = {}

    for regime, result in results.items():
        if result.get("status") != "success":
            incomplete_reasons[regime] = [
                result.get("message", "Tax engine did not return a successful result.")
            ]
            summaries[regime] = {"status": "unavailable", "tax_before_credits": None}
            continue

        reasons = []
        if result.get("liability_status") != "calculated":
            reasons.append(result.get("engine_status", "liability_not_final"))
        taxable = result.get("taxable_income", {})
        if taxable.get("final_taxable_income") is None:
            reasons.append("final_taxable_income_unavailable")

        tax_value = result.get("final_tax", {}).get("total_tax_payable")
        if tax_value is None:
            reasons.append("tax_amount_unavailable")

        summaries[regime] = {
            "status": "incomplete" if reasons else "calculated",
            "tax_before_credits": tax_value,
            "taxable_income": taxable.get("final_taxable_income"),
            "tax_credits_applied": False,
        }
        if reasons:
            incomplete_reasons[regime] = sorted(set(reasons))

    if incomplete_reasons:
        return {
            "status": "incomplete",
            "message": "Both regimes must have complete, calculated assessments before a lower-tax comparison is shown.",
            "regimes": summaries,
            "missing_or_conditional_items": incomplete_reasons,
            "comparison": None,
        }

    old_tax = decimal(summaries["old"]["tax_before_credits"])
    new_tax = decimal(summaries["new"]["tax_before_credits"])
    difference = money(abs(old_tax - new_tax))
    if old_tax == new_tax:
        lower_regime = "tie"
    else:
        lower_regime = "old" if old_tax < new_tax else "new"

    return {
        "status": "calculated",
        "message": "Indicative comparison of calculated tax before TDS, advance-tax, and self-assessment-tax credits.",
        "regimes": summaries,
        "missing_or_conditional_items": {},
        "comparison": {
            "lower_tax_regime": lower_regime,
            "estimated_difference": difference,
            "is_final_regime_recommendation": False,
            "note": "Confirm eligibility, all income heads, special-rate rules, and applicable financial-year law before choosing a regime.",
        },
    }


@router.get("/compare-regimes")
def compare_tax_regimes(
    user_id: int = Query(..., ge=1),
    financial_year: str = Query("2026-27"),
    residential_status: str = Query("resident"),
    age_category: str | None = Query(None, pattern=r"^(under_60|60_to_79|80_plus)$"),
    stt_confirmed: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Run the existing income/liability engines for old and new regimes.

    This endpoint is read-only. It intentionally does not copy income data,
    create records, or apply user-entered provisional credit overrides.
    """
    old_result = get_final_tax_liability(
        user_id=user_id,
        financial_year=financial_year,
        tax_regime="old",
        residential_status=residential_status,
        age_category=age_category,
        stt_confirmed=stt_confirmed,
        tds_credit=None,
        advance_tax_credit=None,
        self_assessment_tax_credit=None,
        db=db,
    )
    new_result = get_final_tax_liability(
        user_id=user_id,
        financial_year=financial_year,
        tax_regime="new",
        residential_status=residential_status,
        age_category=age_category,
        stt_confirmed=stt_confirmed,
        tds_credit=None,
        advance_tax_credit=None,
        self_assessment_tax_credit=None,
        db=db,
    )
    comparison = build_regime_comparison(old_result, new_result)
    return {
        "status": comparison["status"],
        "user_id": user_id,
        "financial_year": financial_year,
        "residential_status": residential_status,
        "engine": "Old vs New Regime Comparison",
        "read_only": True,
        **{key: value for key, value in comparison.items() if key != "status"},
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
    age_category: str | None = Query(
        None,
        pattern=r"^(under_60|60_to_79|80_plus)$",
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
                normal_taxable_income,
                age_category=age_category or "under_60",
                residential_status=residential_status,
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

    rebate_amount = decimal(rebate["rebate"])
    marginal_relief_amount = decimal(rebate.get("marginal_relief"))

    # ========================================================
    # TAX AFTER REBATE
    # ========================================================

    tax_after_rebate = max(
        normal_tax - rebate_amount - marginal_relief_amount,
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
        age_category=age_category or "under_60",
        residential_status=residential_status,
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
        reconciliation = summarize_verified_tax_credits(entries)
        required_types = ("tds", "advance_tax", "self_assessment_tax")
        for credit_type in required_types:
            summary = reconciliation["by_type"][credit_type]
            persisted_credit_summary[credit_type] = {
                "verified_amount": summary["verified_amount"],
                "verified_entry_count": summary["eligible_entry_count"],
                "excluded_duplicate_count": summary["excluded_duplicate_count"],
                "excluded_missing_reference_count": summary["excluded_missing_reference_count"],
            }
        credits_complete = all(
            persisted_credit_summary[key]["verified_entry_count"] > 0
            for key in required_types
        ) and not reconciliation["excluded_entries_require_review"]
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

        engine_status = "incomplete_missing_income_heads"
        liability_status = "not_final"

    elif tax_regime == "old" and age_category is None and residential_status == "resident":

        engine_status = "requires_age_confirmation"
        liability_status = "conditional"

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

            "age_category":
                age_category,

            "old_regime_age_assumption":
                ("under_60_provisional" if tax_regime == "old" and age_category is None
                 else None),
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
        "tax_rule_notes": {
            "old_regime_age_based_basic_exemption": True,
            "old_regime_age_confirmation_required_for_resident": True,
            "age_category_options": ["under_60", "60_to_79", "80_plus"],
            "rules_scope": "individual slab-rate calculation; special cases still require separate review",
        },

        # Persisted records count only after a separate verification step.
        "tax_credits": {
            **credit_breakdown,
            "total": total_credits,
            "data_status": balance_status,
            "verified": credits_verified,
            "source": "query_parameters_self_reported" if manual_credit_mode else "persisted_verified_entries",
            "persisted_verified_summary": persisted_credit_summary if not manual_credit_mode else None,
            "reconciliation": (
                {
                    "duplicate_source_references": reconciliation["duplicate_source_references"],
                    "included_entry_ids": reconciliation["included_entry_ids"],
                    "excluded_entry_ids": reconciliation["excluded_entry_ids"],
                    "excluded_entries_require_review": reconciliation["excluded_entries_require_review"],
                }
                if not manual_credit_mode else None
            ),
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

            "marginal_relief":
                money(
                    rebate.get("marginal_relief", 0)
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

            "marginal_relief":
                money(surcharge.get("marginal_relief", 0)),

            "marginal_relief_threshold":
                surcharge.get("marginal_relief_threshold"),

            "marginal_relief_review_required":
                surcharge.get("marginal_relief_review_required", False),

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
