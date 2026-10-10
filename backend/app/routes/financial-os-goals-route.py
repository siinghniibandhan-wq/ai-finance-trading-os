# ============================================================
# FINANCIAL OS - PERSISTENT FINANCIAL GOALS API
# ============================================================

from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import FinancialGoal, User

router = APIRouter(prefix="/api/goals", tags=["Financial Goals"])

ALLOWED_CATEGORIES = {
    "Savings", "Emergency Fund", "Major Purchase", "Education",
    "Financial Independence", "Retirement", "Other",
}
ALLOWED_STATUSES = {"active", "paused", "completed"}


def serialize_goal(goal: FinancialGoal):
    target = Decimal(str(goal.target_amount or 0))
    current = Decimal(str(goal.current_amount or 0))
    remaining = max(Decimal("0"), target - current)
    progress = (current / target * 100) if target > 0 else Decimal("0")
    return {
        "id": goal.id,
        "user_id": goal.user_id,
        "name": goal.name,
        "category": goal.category,
        "target_amount": float(target),
        "current_amount": float(current),
        "remaining_amount": float(remaining),
        "progress_percent": float(min(Decimal("100"), progress)),
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "monthly_contribution": float(goal.monthly_contribution or 0),
        "notes": goal.notes,
        "status": goal.status,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
        "updated_at": goal.updated_at.isoformat() if goal.updated_at else None,
    }


def parse_amount(value, field_name):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"{field_name} must be a valid amount.")
    if not amount.is_finite() or amount < 0:
        raise HTTPException(status_code=422, detail=f"{field_name} must be zero or greater.")
    return amount.quantize(Decimal("0.01"))


def validate_payload(payload, partial=False):
    data = {}
    if not partial or "name" in payload:
        name = str(payload.get("name", "")).strip()
        if not name:
            raise HTTPException(status_code=422, detail="Goal name is required.")
        if len(name) > 150:
            raise HTTPException(status_code=422, detail="Goal name must be 150 characters or fewer.")
        data["name"] = name

    if not partial or "category" in payload:
        category = str(payload.get("category", "Other")).strip()
        if category not in ALLOWED_CATEGORIES:
            raise HTTPException(status_code=422, detail="Select a valid goal category.")
        data["category"] = category

    for field in ("target_amount", "current_amount", "monthly_contribution"):
        if not partial or field in payload:
            default = 0 if field != "target_amount" else None
            value = payload.get(field, default)
            if value is None and field == "target_amount":
                raise HTTPException(status_code=422, detail="Target amount is required.")
            data[field] = parse_amount(value, field.replace("_", " ").title())

    if not partial or "target_date" in payload:
        raw_date = payload.get("target_date")
        if raw_date in (None, ""):
            data["target_date"] = None
        else:
            try:
                data["target_date"] = date.fromisoformat(str(raw_date))
            except ValueError:
                raise HTTPException(status_code=422, detail="Target date must use YYYY-MM-DD.")

    if not partial or "notes" in payload:
        notes = payload.get("notes")
        data["notes"] = str(notes).strip()[:2000] if notes else None

    if not partial or "status" in payload:
        status = str(payload.get("status", "active")).lower()
        if status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=422, detail="Invalid goal status.")
        data["status"] = status
    return data


@router.get("/")
def list_goals(user_id: int, db: Session = Depends(get_db)):
    if not db.query(User.id).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found.")
    goals = (
        db.query(FinancialGoal)
        .filter(FinancialGoal.user_id == user_id)
        .order_by(FinancialGoal.created_at.desc(), FinancialGoal.id.desc())
        .all()
    )
    return {"status": "success", "goals": [serialize_goal(goal) for goal in goals]}


@router.post("/", status_code=201)
def create_goal(payload: dict, user_id: int, db: Session = Depends(get_db)):
    if not db.query(User.id).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found.")
    data = validate_payload(payload)
    goal = FinancialGoal(user_id=user_id, **data)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return {"status": "success", "goal": serialize_goal(goal)}


@router.put("/{goal_id}")
def update_goal(goal_id: int, payload: dict, user_id: int, db: Session = Depends(get_db)):
    goal = db.query(FinancialGoal).filter(
        FinancialGoal.id == goal_id,
        FinancialGoal.user_id == user_id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")
    data = validate_payload(payload, partial=True)
    for key, value in data.items():
        setattr(goal, key, value)
    db.commit()
    db.refresh(goal)
    return {"status": "success", "goal": serialize_goal(goal)}


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, user_id: int, db: Session = Depends(get_db)):
    goal = db.query(FinancialGoal).filter(
        FinancialGoal.id == goal_id,
        FinancialGoal.user_id == user_id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")
    db.delete(goal)
    db.commit()
    return {"status": "success", "deleted_id": goal_id}
