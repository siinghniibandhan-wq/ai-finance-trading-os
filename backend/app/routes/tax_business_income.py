"""User-scoped business and professional tax records.

Money transactions are exposed as review candidates, never silently converted
into business income. A candidate becomes a tax record only after an explicit
user action, and remains excluded from taxable income until verified.
"""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import TaxBusinessIncomeRecord, Transaction, Category, User
from app.routes.auth import get_current_user
from app.tax_income_safety import non_income_reason, find_duplicates

router = APIRouter(prefix="/api/tax-business-income", tags=["Tax Business Income"])

EXCLUDED_RECEIPT_CATEGORIES = {
    "salary", "salary & wages", "salaries", "loan disbursement",
    "interest", "dividend",
}


def _financial_year_dates(financial_year: str) -> tuple[date, date]:
    """Validate an Indian financial-year string and return inclusive dates."""
    if not isinstance(financial_year, str) or len(financial_year) != 7 or financial_year[4] != "-":
        raise HTTPException(status_code=400, detail="Invalid Indian financial year.")
    try:
        start_year = int(financial_year[:4])
        end_short = int(financial_year[5:])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Indian financial year.")
    if end_short != (start_year + 1) % 100 or not 2000 <= start_year <= 2100:
        raise HTTPException(status_code=400, detail="Invalid Indian financial year.")
    return date(start_year, 4, 1), date(start_year + 1, 3, 31)


class BusinessRecordIn(BaseModel):
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    record_type: str = Field(pattern=r"^(receipt|expense)$")
    income_type: str = Field(pattern=r"^(business|profession|freelance)$")
    category: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    transaction_date: date
    description: str | None = Field(default=None, max_length=2000)
    evidence_reference: str | None = Field(default=None, max_length=1000)
    source_transaction_id: int | None = Field(default=None, ge=1)


def _normalized_category(db: Session, transaction: Transaction) -> str:
    if not transaction.category_id:
        return ""
    category = db.query(Category).filter_by(id=transaction.category_id).first()
    return str(category.name if category else "").strip().lower()


def _is_business_receipt_candidate(db: Session, transaction: Transaction) -> bool:
    if str(transaction.transaction_type or "").strip().lower() != "income":
        return False
    category_path = _normalized_category(db, transaction)
    # The app stores hierarchical categories such as
    # "Other Sources > Savings Interest"; inspect the final segment as well
    # as the full path so tax-source categories are not offered as business.
    leaf_category = category_path.replace("/", ">").split(">")[-1].strip()
    if leaf_category in EXCLUDED_RECEIPT_CATEGORIES:
        return False
    if any(term in category_path for term in ("loan disbursement", "salary", "interest", "dividend", "house property")):
        return False
    if "gross salary:" in str(transaction.description or "").lower():
        return False
    if non_income_reason(category_path, transaction.description):
        return False
    return True


@router.post("/")
def create_record(
    payload: BusinessRecordIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_date, end_date = _financial_year_dates(payload.financial_year)
    if not start_date <= payload.transaction_date <= end_date:
        raise HTTPException(status_code=400, detail="Transaction date is outside the selected financial year.")

    source_transaction_id = payload.source_transaction_id
    if source_transaction_id is not None:
        source = db.query(Transaction).filter_by(
            id=source_transaction_id, user_id=current_user.id
        ).first()
        if source is None:
            raise HTTPException(status_code=404, detail="Linked Money transaction was not found for this user.")
        if source.transaction_date != payload.transaction_date or Decimal(str(source.amount)) != payload.amount:
            raise HTTPException(status_code=400, detail="Linked transaction date and amount must match the tax record.")

        transaction_type = str(source.transaction_type or "").strip().lower()
        if payload.record_type == "receipt" and not _is_business_receipt_candidate(db, source):
            raise HTTPException(
                status_code=400,
                detail="This Money transaction is not eligible as a business receipt; salary, loans, interest, and dividends are excluded.",
            )
        if payload.record_type == "expense" and transaction_type != "expense":
            raise HTTPException(status_code=400, detail="An expense must link to an expense transaction.")

        existing_link = db.query(TaxBusinessIncomeRecord).filter_by(
            user_id=current_user.id, source_transaction_id=source_transaction_id
        ).first()
        if existing_link:
            raise HTTPException(status_code=409, detail="This Money transaction is already linked to a tax business record.")

    record = TaxBusinessIncomeRecord(
        user_id=current_user.id,
        financial_year=payload.financial_year,
        record_type=payload.record_type,
        income_type=payload.income_type,
        category=payload.category.strip(),
        amount=payload.amount,
        transaction_date=payload.transaction_date,
        description=payload.description,
        evidence_reference=payload.evidence_reference,
        source_transaction_id=source_transaction_id,
        status="pending_review",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.get("/")
def list_records(
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_date, end_date = _financial_year_dates(financial_year)
    records = (
        db.query(TaxBusinessIncomeRecord)
        .filter_by(user_id=current_user.id, financial_year=financial_year)
        .order_by(TaxBusinessIncomeRecord.transaction_date.desc(), TaxBusinessIncomeRecord.id.desc())
        .all()
    )
    receipts = sum(
        (r.amount for r in records if r.record_type == "receipt" and r.status == "verified"),
        Decimal("0"),
    )
    expenses = sum(
        (r.amount for r in records if r.record_type == "expense" and r.status == "verified"),
        Decimal("0"),
    )

    # Discover unlinked Money transactions for review. This is read-only and
    # deliberately does not infer that every generic income is business income.
    # A user must explicitly create a tax record and a reviewer must verify it.
    linked_ids = {
        row[0]
        for row in db.query(TaxBusinessIncomeRecord.source_transaction_id).filter(
            TaxBusinessIncomeRecord.user_id == current_user.id,
            TaxBusinessIncomeRecord.source_transaction_id.is_not(None),
        ).all()
    }
    money_rows = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.transaction_type.in_(("income", "expense")),
        )
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .all()
    )
    candidates = []
    exact_duplicate_ids, possible_duplicate_ids = find_duplicates(money_rows)
    for transaction in money_rows:
        if transaction.id in linked_ids or transaction.id in exact_duplicate_ids:
            continue
        tx_type = str(transaction.transaction_type or "").strip().lower()
        if tx_type == "income" and not _is_business_receipt_candidate(db, transaction):
            continue
        if tx_type == "expense" and _normalized_category(db, transaction) in {"loan repayment", "credit card payment", "transfer"}:
            continue
        candidates.append({
            "source_transaction_id": transaction.id,
            "record_type": "receipt" if tx_type == "income" else "expense",
            "transaction_date": transaction.transaction_date.isoformat(),
            "amount": str(transaction.amount),
            "category": _normalized_category(db, transaction) or None,
            "description": transaction.description,
            "review_required": True,
            "possible_duplicate": transaction.id in possible_duplicate_ids,
            "taxable_until_verified": False,
        })

    return {
        "financial_year": financial_year,
        "records": [_serialize(r) for r in records],
        "unlinked_money_transactions": candidates,
        "unlinked_candidate_count": len(candidates),
        "verified_gross_receipts": str(receipts),
        "verified_expenses": str(expenses),
        "provisional_verified_profit": str(receipts - expenses),
        "note": (
            "Unlinked Money transactions are review candidates only; they are not business income "
            "until explicitly recorded and verified. Self-reported records remain pending review by default. "
            "This summary is not a final tax computation."
        ),
    }


def _serialize(r):
    return {
        "id": r.id,
        "financial_year": r.financial_year,
        "record_type": r.record_type,
        "income_type": r.income_type,
        "category": r.category,
        "description": r.description,
        "amount": str(r.amount),
        "transaction_date": r.transaction_date.isoformat(),
        "evidence_reference": r.evidence_reference,
        "source_transaction_id": r.source_transaction_id,
        "status": r.status,
    }
