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
- Claim endpoints write user-entered claims to the existing claim table.
- Claims start pending and do not affect taxable income until user-confirmed
  with an evidence reference.
- The app does not independently inspect evidence or determine legal eligibility.
============================================================
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.auth import get_current_user
from app.routes.ownership import require_matching_user_id
from app.models import TaxDeductionClaim, User


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
        "old_regime_available": True,
        "new_regime_available": True,
    },

    "share_of_huf_income": {
        "category": "Share of income received by member of HUF",
        "section": "10(2)",
        "old_regime_available": True,
        "new_regime_available": True,
    },

    "certain_partner_share": {
        "category": "Certain share of profit from partnership firm",
        "section": "10(2A)",
        "old_regime_available": True,
        "new_regime_available": True,
    },

    "life_insurance_receipts": {
        "category": "Eligible life insurance receipts",
        "section": "10(10D)",
        "old_regime_available": True,
        "new_regime_available": True,
    },

    "specified_allowances": {
        "category": "Specified exempt allowances",
        "section": "10",
        "old_regime_available": True,
        "new_regime_available": False,
    },

    "hra_exemption": {
        "category": "House Rent Allowance exemption (where eligible)",
        "section": "10(13A)",
        "old_regime_available": True,
        "new_regime_available": False,
    },

    "lta_exemption": {
        "category": "Leave Travel Allowance exemption (where eligible)",
        "section": "10(5)",
        "old_regime_available": True,
        "new_regime_available": False,
    },

    "other_exempt_income": {
        "category": "Other legally exempt income",
        "section": "10 / applicable provision",
        "old_regime_available": True,
        "new_regime_available": True,
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
# HRA EXEMPTION CALCULATOR (SECTION 10(13A))
# ============================================================

# One authoritative, financial-year-aware HRA city rule map. Rule 279 of the
# Income-tax Rules, 2026 expands the 50% salary limit to eight cities from
# FY 2026-27. Earlier years retain the four-city list. Verify future amendments
# before extending this effective-date rule.
HRA_METRO_CITIES_THROUGH_FY_2025_26 = {"delhi", "mumbai", "kolkata", "chennai"}
HRA_METRO_CITIES_FROM_FY_2026_27 = HRA_METRO_CITIES_THROUGH_FY_2025_26 | {
    "hyderabad", "pune", "ahmedabad", "bengaluru"
}
HRA_CITY_ALIASES = {
    "new delhi": "delhi",
    "nct of delhi": "delhi",
    "bombay": "mumbai",
    "calcutta": "kolkata",
    "madras": "chennai",
    "bangalore": "bengaluru",
}
HRA_NON_METRO_CITY_SUGGESTIONS = [
    "Bhopal", "Bhubaneswar", "Chandigarh", "Coimbatore", "Dehradun",
    "Dhanbad", "Faridabad", "Ghaziabad", "Guwahati", "Gurugram", "Gurgaon", "Indore",
    "Jaipur", "Jabalpur", "Jamshedpur", "Kanpur", "Kochi", "Kota",
    "Lucknow", "Ludhiana", "Madurai", "Mangaluru", "Mysuru", "Nagpur",
    "Nashik", "Noida", "Patna", "Raipur", "Rajkot", "Ranchi",
    "Surat", "Thiruvananthapuram", "Udaipur", "Vadodara", "Varanasi",
    "Visakhapatnam",
]


def _financial_year_start(financial_year: str | None) -> int | None:
    """Parse FY labels such as 2026-27 without guessing malformed values."""
    try:
        start, end = (financial_year or "").split("-", 1)
        start_year, end_year = int(start), int(end)
        if end_year != (start_year + 1) % 100:
            return None
        return start_year
    except (ValueError, TypeError):
        return None


def classify_hra_city(city: str, financial_year: str = "2026-27") -> str:
    """Classify a city under the HRA rule effective for the selected FY.

    Unknown cities default to non-metro. Invalid/unknown FY labels conservatively
    use the legacy four-city list rather than granting the expanded limit.
    """
    key = " ".join((city or "").strip().casefold().split())
    key = HRA_CITY_ALIASES.get(key, key)
    start_year = _financial_year_start(financial_year)
    metro_cities = (
        HRA_METRO_CITIES_FROM_FY_2026_27
        if start_year is not None and start_year >= 2026
        else HRA_METRO_CITIES_THROUGH_FY_2025_26
    )
    return "metro" if key in metro_cities else "non_metro"


class HRAInputs(BaseModel):
    """Annual inputs for the statutory least-of-three HRA calculation.

    annual_basic_salary and annual_da_forming_retirement_benefits must cover
    the same period as rent/HRA and should only include eligible salary.
    """
    annual_basic_salary: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    annual_da_forming_retirement_benefits: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    annual_commission_on_turnover_at_fixed_percentage: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    annual_hra_received: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    annual_rent_paid: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    city: str = Field(min_length=2, max_length=100)
    # Optional for backward compatibility with older clients that send city only.
    city_classification: str | None = Field(default=None, pattern=r"^(metro|non_metro)$")


def calculate_hra_exemption(inputs: HRAInputs, tax_regime: str, financial_year: str = "2026-27"):
    """Calculate HRA exemption as the least of the three statutory limits.

    This is a calculation based on user-supplied annual figures. The app does
    not independently verify salary slips, rent receipts, landlord details,
    or legal eligibility. HRA exemption is not available under the new regime.
    """
    regime = (tax_regime or "").strip().lower()
    if regime not in {"old", "new"}:
        raise ValueError("tax_regime must be 'old' or 'new'.")
    if regime == "new":
        raise ValueError("HRA exemption under section 10(13A) is not available under the selected new tax regime.")

    salary = (
        inputs.annual_basic_salary
        + inputs.annual_da_forming_retirement_benefits
        + inputs.annual_commission_on_turnover_at_fixed_percentage
    ).quantize(Decimal("0.01"))
    if salary <= 0:
        raise ValueError("Enter a positive annual basic salary and eligible DA for HRA calculation.")

    # The backend is authoritative: never trust a client-supplied classification.
    # City name determines the class; unlisted cities default to non-metro.
    city_classification = classify_hra_city(inputs.city, financial_year)
    is_metro = city_classification == "metro"
    rent_less_ten_percent = max(inputs.annual_rent_paid - (salary * Decimal("0.10")), Decimal("0"))
    salary_percentage_limit = salary * (Decimal("0.50") if is_metro else Decimal("0.40"))
    candidates = {
        "hra_received": inputs.annual_hra_received,
        "rent_paid_minus_10_percent_salary": rent_less_ten_percent,
        "salary_percentage_limit": salary_percentage_limit,
    }
    exemption = min(candidates.values()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "status": "calculated",
        "section": "10(13A)",
        "tax_regime": "old",
        "city": inputs.city.strip(),
        "city_classification": city_classification,
        "city_classification_source": "server_tax_rules",
        "financial_year": financial_year,
        "metro_city_for_hra": is_metro,
        "annual_salary_for_hra": str(salary),
        "limits": {key: str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) for key, value in candidates.items()},
        "calculated_exemption": str(exemption),
        "formula": "Least of HRA received, rent paid minus 10% of eligible salary, and the salary percentage limit applicable to the selected financial year and city.",
        "verification_notice": "Estimate from user-entered figures only. Verify eligibility and supporting documents before filing. Eligible salary here includes basic salary and DA forming part of retirement benefits; commission is included only if it meets the statutory fixed-percentage-of-turnover condition.",
    }


class HRACalculatorRequest(HRAInputs):
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    tax_regime: str = Field(pattern=r"^(old|new)$")


@router.get("/hra-cities")
def hra_city_catalog(financial_year: str = "2026-27"):
    """Return unique searchable city suggestions for the requested financial year."""
    candidates = [
        "Delhi", "New Delhi", "Mumbai", "Bombay", "Kolkata", "Calcutta", "Chennai", "Madras",
        "Ahmedabad", "Bengaluru", "Hyderabad", "Pune", *HRA_NON_METRO_CITY_SUGGESTIONS,
    ]
    metro, non_metro, seen = [], [], set()
    for name in candidates:
        key = " ".join(name.casefold().split())
        if key in seen:
            continue
        seen.add(key)
        item = {"name": name, "classification": classify_hra_city(name, financial_year)}
        (metro if item["classification"] == "metro" else non_metro).append(item)
    return {
        "financial_year": financial_year,
        "metro": metro,
        "non_metro": non_metro,
        "unknown_city_default": "non_metro",
    }


@router.post("/hra-calculator")
def hra_calculator(payload: HRACalculatorRequest):
    """Calculate an indicative HRA exemption without writing to the database."""
    try:
        result = calculate_hra_exemption(payload, payload.tax_regime, payload.financial_year)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["financial_year"] = payload.financial_year
    result["database_write"] = False
    return result


# ============================================================
# API
# ============================================================

def claim_is_regime_eligible(claim):
    """Safely check persisted claims, including unknown legacy keys."""
    item = DEDUCTION_CATALOG.get(claim.deduction_key) or EXEMPT_INCOME_CATALOG.get(claim.deduction_key)
    return bool(item and regime_available(item, claim.tax_regime))


class TaxDeductionClaimInput(BaseModel):
    user_id: int = Field(ge=1)
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    tax_regime: str = Field(pattern=r"^(old|new)$")
    deduction_key: str = Field(min_length=1, max_length=60)
    claimed_amount: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=2)
    hra_inputs: HRAInputs | None = None
    evidence_reference: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)


@router.post("/claims", status_code=201)
def create_deduction_claim(payload: TaxDeductionClaimInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save a user claim for review; never marks a claim verified automatically."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    item = DEDUCTION_CATALOG.get(payload.deduction_key)
    claim_type = "deduction"
    if not item:
        item = EXEMPT_INCOME_CATALOG.get(payload.deduction_key)
        claim_type = "exempt_income"
    if not item:
        raise HTTPException(status_code=400, detail="Unknown deduction_key or exempt-income key")
    if not regime_available(item, payload.tax_regime):
        raise HTTPException(status_code=400, detail=f"This {claim_type.replace('_', '-')} claim is not available under the selected regime")

    claimed_amount = payload.claimed_amount
    notes = payload.notes
    if payload.deduction_key == "hra_exemption":
        if payload.hra_inputs is None:
            raise HTTPException(status_code=400, detail="HRA claims require hra_inputs so the statutory exemption limit can be calculated.")
        try:
            hra_result = calculate_hra_exemption(payload.hra_inputs, payload.tax_regime, payload.financial_year)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        claimed_amount = Decimal(hra_result["calculated_exemption"])
        if claimed_amount <= 0:
            raise HTTPException(status_code=400, detail="The calculated HRA exemption is zero; no positive HRA claim can be created.")
        notes = json.dumps({
            "user_notes": payload.notes,
            "hra_calculation": hra_result,
            "hra_inputs": payload.hra_inputs.model_dump(mode="json"),
        }, default=str)
    elif claimed_amount is None:
        raise HTTPException(status_code=400, detail="claimed_amount is required for this claim type.")

    claim = TaxDeductionClaim(
        user_id=current_user.id, financial_year=payload.financial_year,
        tax_regime=payload.tax_regime, deduction_key=payload.deduction_key,
        claimed_amount=claimed_amount, evidence_reference=payload.evidence_reference,
        notes=notes, status="pending_review",
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return {"id": claim.id, "user_id": claim.user_id, "financial_year": claim.financial_year,
            "tax_regime": claim.tax_regime, "deduction_key": claim.deduction_key,
            "claimed_amount": str(claim.claimed_amount), "status": claim.status,
            "affects_taxable_income": False,
            "claim_type": claim_type,
            "message": "Claim saved for review. It does not affect taxable income until you verify it with an evidence reference. Exempt amounts are user-claimed and are not independently checked by this app."}


@router.get("/claims", dependencies=[Depends(require_matching_user_id)])
def list_deduction_claims(user_id: int = Query(..., ge=1),
                          financial_year: str = Query("2026-27"),
                          db: Session = Depends(get_db)):
    """List claims for one user and financial year; only the owner's records are queried."""
    claims = (db.query(TaxDeductionClaim)
              .filter(TaxDeductionClaim.user_id == user_id,
                      TaxDeductionClaim.financial_year == financial_year)
              .order_by(TaxDeductionClaim.created_at.desc()).all())
    return {"user_id": user_id, "financial_year": financial_year, "claims": [
        {"id": c.id, "tax_regime": c.tax_regime, "deduction_key": c.deduction_key,
         "claim_type": "deduction" if c.deduction_key in DEDUCTION_CATALOG else "exempt_income",
         "section": (DEDUCTION_CATALOG.get(c.deduction_key) or EXEMPT_INCOME_CATALOG.get(c.deduction_key) or {}).get("section"),
         "claimed_amount": str(c.claimed_amount), "status": c.status,
         "evidence_reference": c.evidence_reference, "notes": c.notes,
         "affects_taxable_income": (
             c.status == "verified"
             and claim_is_regime_eligible(c)
             and c.deduction_key in DEDUCTION_CATALOG
         ),
         "application_note": (
             "Deduction may be applied by the taxable-income engine when regime eligible."
             if c.deduction_key in DEDUCTION_CATALOG
             else "Verified exemption claim is recorded, but it is not currently deducted because the corresponding income head is not yet integrated."
         )
         } for c in claims]}


# ============================================================
# CLAIM REVIEW STEP (VERIFY / UN-VERIFY / DELETE)
# ============================================================
# A saved claim starts as "pending_review" and does not change taxable
# income. The owner can explicitly mark it "verified" once an evidence
# reference is recorded. The app does not read or check the documents:
# marking a claim verified is the owner's own confirmation.

class TaxClaimActionInput(BaseModel):
    user_id: int = Field(ge=1)
    evidence_reference: str | None = Field(default=None, max_length=2000)


def claim_verification_problem(evidence_reference):
    """Return a plain-language reason a claim cannot be verified, or None."""
    if not (evidence_reference or "").strip():
        return (
            "Add an evidence reference (receipt, policy, certificate or "
            "statement number) before marking a claim verified."
        )
    return None


def _get_owned_claim(db, claim_id, user_id):
    claim = (
        db.query(TaxDeductionClaim)
        .filter(
            TaxDeductionClaim.id == claim_id,
            TaxDeductionClaim.user_id == user_id,
        )
        .first()
    )
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


def _claim_summary(claim):
    is_exempt_income = claim.deduction_key in EXEMPT_INCOME_CATALOG
    return {
        "id": claim.id,
        "tax_regime": claim.tax_regime,
        "deduction_key": claim.deduction_key,
        "claim_type": "exempt_income" if is_exempt_income else "deduction",
        "claimed_amount": str(claim.claimed_amount),
        "status": claim.status,
        "evidence_reference": claim.evidence_reference,
        "affects_taxable_income": claim.status == "verified",
        "calculation_note": "User-confirmed amount; the app does not independently validate supporting documents or calculate HRA eligibility." if claim.deduction_key == "hra_exemption" else None,
    }


@router.post("/claims/{claim_id}/verify")
def verify_deduction_claim(
    claim_id: int,
    payload: TaxClaimActionInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark the owner's claim verified. Requires an evidence reference."""
    claim = _get_owned_claim(db, claim_id, current_user.id)
    evidence = (payload.evidence_reference or claim.evidence_reference or "").strip()
    problem = claim_verification_problem(evidence)
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    claim.evidence_reference = evidence
    claim.status = "verified"
    db.commit()
    db.refresh(claim)
    result = _claim_summary(claim)
    result["message"] = (
        "Marked verified on your confirmation. Keep the supporting "
        "document; this app does not check it."
    )
    return result


@router.post("/claims/{claim_id}/unverify")
def unverify_deduction_claim(
    claim_id: int,
    payload: TaxClaimActionInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a claim to pending review so it stops reducing taxable income."""
    claim = _get_owned_claim(db, claim_id, current_user.id)
    claim.status = "pending_review"
    db.commit()
    db.refresh(claim)
    result = _claim_summary(claim)
    result["message"] = "Claim returned to pending review."
    return result


@router.delete("/claims/{claim_id}", dependencies=[Depends(require_matching_user_id)])
def delete_deduction_claim(
    claim_id: int,
    user_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    """Delete one of the owner's claims."""
    claim = _get_owned_claim(db, claim_id, user_id)
    db.delete(claim)
    db.commit()
    return {"id": claim_id, "deleted": True}


@router.get("/", dependencies=[Depends(require_matching_user_id)])
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
            "deduction_key": key,
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
