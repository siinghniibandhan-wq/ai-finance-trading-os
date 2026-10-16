"""Owner confirmations that a tax-report section is complete for a year."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import TaxCreditEntry, TaxDeductionClaim, TaxReviewConfirmation, User
from app.routes.auth import get_current_user
from app.routes.ownership import require_matching_user_id
from app.tax_review_rules import REVIEW_SECTIONS, section_status

router = APIRouter(prefix="/api/tax-review", tags=["Tax Review"])


class ReviewConfirmInput(BaseModel):
    user_id: int = Field(ge=1)
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    section: str = Field(pattern=r"^(tds_advance_tax|deductions_exemptions)$")
    note: str | None = Field(default=None, max_length=1000)


def pending_counts(db, user_id, financial_year):
    credits = db.query(TaxCreditEntry).filter(
        TaxCreditEntry.user_id == user_id,
        TaxCreditEntry.financial_year == financial_year,
        TaxCreditEntry.status != "verified",
    ).count()
    claims = db.query(TaxDeductionClaim).filter(
        TaxDeductionClaim.user_id == user_id,
        TaxDeductionClaim.financial_year == financial_year,
        TaxDeductionClaim.status != "verified",
    ).count()
    return {"tds_advance_tax": credits, "deductions_exemptions": claims}


def review_state(db, user_id, financial_year):
    """Per-section completeness for one user and year."""
    confirmed = {
        row.section for row in db.query(TaxReviewConfirmation).filter(
            TaxReviewConfirmation.user_id == user_id,
            TaxReviewConfirmation.financial_year == financial_year,
        ).all()
    }
    pending = pending_counts(db, user_id, financial_year)
    state = {}
    for name in REVIEW_SECTIONS:
        done, reason = section_status(name in confirmed, pending[name])
        state[name] = {
            "complete": done,
            "confirmed_by_user": name in confirmed,
            "pending_review_count": pending[name],
            "reason": reason,
        }
    return state


@router.get("/", dependencies=[Depends(require_matching_user_id)])
def get_tax_review(
    user_id: int = Query(..., ge=1),
    financial_year: str = Query("2026-27", pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
):
    return {"user_id": user_id, "financial_year": financial_year,
            "sections": review_state(db, user_id, financial_year)}


@router.post("/confirm", status_code=201)
def confirm_section(
    payload: ReviewConfirmInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the owner's own confirmation. The app does not check documents."""
    row = db.query(TaxReviewConfirmation).filter(
        TaxReviewConfirmation.user_id == current_user.id,
        TaxReviewConfirmation.financial_year == payload.financial_year,
        TaxReviewConfirmation.section == payload.section,
    ).first()
    if row is None:
        row = TaxReviewConfirmation(
            user_id=current_user.id, financial_year=payload.financial_year,
            section=payload.section, note=payload.note,
        )
        db.add(row)
    else:
        row.note = payload.note
    db.commit()
    return {"sections": review_state(db, current_user.id, payload.financial_year)}


@router.delete("/confirm", dependencies=[Depends(require_matching_user_id)])
def remove_confirmation(
    user_id: int = Query(..., ge=1),
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    section: str = Query(..., pattern=r"^(tds_advance_tax|deductions_exemptions)$"),
    db: Session = Depends(get_db),
):
    db.query(TaxReviewConfirmation).filter(
        TaxReviewConfirmation.user_id == user_id,
        TaxReviewConfirmation.financial_year == financial_year,
        TaxReviewConfirmation.section == section,
    ).delete()
    db.commit()
    return {"sections": review_state(db, user_id, financial_year)}
