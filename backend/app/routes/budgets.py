# ============================================================
# FINANCIAL OS
# BUDGET API ROUTES
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Budget
from app.schemas import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/budgets",
    tags=["Budgets"],
)


# ============================================================
# CREATE BUDGET
# ============================================================

@router.post(
    "/",
    response_model=BudgetResponse,
)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
):
    budget = Budget(
        user_id=budget_data.user_id,
        month=budget_data.month,
        category_id=budget_data.category_id,
        amount=budget_data.amount,
    )

    db.add(budget)
    db.commit()
    db.refresh(budget)

    return budget


# ============================================================
# LIST BUDGETS
# ============================================================

@router.get(
    "/",
    response_model=list[BudgetResponse],
)
def list_budgets(
    user_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(Budget)
        .filter(Budget.user_id == user_id)
        .order_by(Budget.month.desc(), Budget.id.desc())
        .all()
    )


# ============================================================
# GET SINGLE BUDGET
# ============================================================

@router.get(
    "/{budget_id}",
    response_model=BudgetResponse,
)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
):
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id)
        .first()
    )

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Budget not found.",
        )

    return budget


# ============================================================
# UPDATE BUDGET
# ============================================================

@router.put(
    "/{budget_id}",
    response_model=BudgetResponse,
)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db),
):
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id)
        .first()
    )

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Budget not found.",
        )

    if budget_data.month is not None:
        budget.month = budget_data.month

    if budget_data.category_id is not None:
        budget.category_id = budget_data.category_id

    if budget_data.amount is not None:
        budget.amount = budget_data.amount

    db.commit()
    db.refresh(budget)

    return budget


# ============================================================
# DELETE BUDGET
# ============================================================

@router.delete(
    "/{budget_id}",
)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
):
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id)
        .first()
    )

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Budget not found.",
        )

    db.delete(budget)
    db.commit()

    return {
        "message": "Budget deleted successfully.",
        "id": budget_id,
    }
