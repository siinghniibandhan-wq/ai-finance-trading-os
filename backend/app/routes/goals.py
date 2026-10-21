# ============================================================
# FINANCIAL OS - FINANCIAL GOALS API
# Persistent CRUD for goals; does not modify account balances.
# ============================================================
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import FinancialGoal, User
from app.routes.auth import get_current_user
from app.finance_diary import record_finance_event

router = APIRouter(prefix="/api/goals", tags=["Financial Goals"])

class GoalPayload(BaseModel):
    user_id: int = 1
    name: str = Field(min_length=1, max_length=150)
    category: str = Field(default="Other", max_length=60)
    target_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    target_date: Optional[date] = None
    monthly_contribution: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    notes: Optional[str] = None
    status: str = "active"

def serialize(goal: FinancialGoal):
    target = float(goal.target_amount or 0)
    current = float(goal.current_amount or 0)
    return {
        "id": goal.id, "user_id": goal.user_id, "name": goal.name,
        "category": goal.category, "target_amount": target,
        "current_amount": current, "remaining_amount": max(0, target-current),
        "progress_percent": min(100, (current / target * 100) if target else 0),
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "monthly_contribution": float(goal.monthly_contribution or 0),
        "notes": goal.notes, "status": goal.status,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
        "updated_at": goal.updated_at.isoformat() if goal.updated_at else None,
    }

@router.get("/")
def list_goals(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == current_user.id).order_by(FinancialGoal.created_at.desc()).all()
    return {"status": "success", "goals": [serialize(g) for g in goals]}

@router.post("/")
def create_goal(payload: GoalPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Bind the goal to the authenticated user, not payload.user_id.
    if payload.current_amount > payload.target_amount:
        # Valid use case (goal already exceeded) is allowed; progress caps at 100%.
        pass
    values = payload.model_dump(exclude={"user_id"})
    goal = FinancialGoal(user_id=current_user.id, **values)
    db.add(goal); db.flush()
    record_finance_event(db, user_id=current_user.id, event_type="created", entity_type="financial_goal", entity_id=goal.id, description=f"Financial goal created: {goal.name}", snapshot={"id": goal.id, "target_amount": goal.target_amount, "current_amount": goal.current_amount, "target_date": goal.target_date, "status": goal.status})
    record_finance_event(db, user_id=current_user.id, event_type="updated", entity_type="financial_goal", entity_id=goal.id, description=f"Financial goal updated: {goal.name}", snapshot={"target_amount": goal.target_amount, "current_amount": goal.current_amount, "target_date": goal.target_date, "status": goal.status})
    db.commit(); db.refresh(goal)
    return {"status": "success", "goal": serialize(goal)}

@router.put("/{goal_id}")
def update_goal(goal_id: int, payload: GoalPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    goal = db.query(FinancialGoal).filter(FinancialGoal.id == goal_id, FinancialGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    for key, value in payload.model_dump(exclude={"user_id"}).items():
        if key != "user_id": setattr(goal, key, value)
    db.commit(); db.refresh(goal)
    return {"status": "success", "goal": serialize(goal)}

@router.delete("/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    goal = db.query(FinancialGoal).filter(FinancialGoal.id == goal_id, FinancialGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    record_finance_event(db, user_id=current_user.id, event_type="deleted", entity_type="financial_goal", entity_id=goal.id, description=f"Financial goal deleted: {goal.name}", snapshot={"target_amount": goal.target_amount, "current_amount": goal.current_amount, "status": goal.status})
    db.delete(goal); db.commit()
    return {"status": "success", "deleted_id": goal_id}
