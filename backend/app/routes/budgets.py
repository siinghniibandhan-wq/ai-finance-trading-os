# ============================================================
# FINANCIAL OS
# BUDGET API ROUTES
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Budget, Category, User
from app.finance_diary import record_finance_event
from app.routes.auth import get_current_user
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
    current_user: User = Depends(get_current_user),
):
    # Never trust a user_id supplied by the client or attach another user's category.
    category = (
        db.query(Category)
        .filter(Category.id == budget_data.category_id, Category.user_id == current_user.id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")

    budget = Budget(
        user_id=current_user.id,
        month=budget_data.month,
        category_id=category.id,
        amount=budget_data.amount,
    )

    db.add(budget)
    db.flush()
    record_finance_event(db, user_id=current_user.id, event_type="created", entity_type="budget", entity_id=budget.id, description=f"Budget created for category {category.name}", snapshot={"id": budget.id, "month": budget.month, "category_id": budget.category_id, "amount": budget.amount})
    record_finance_event(db, user_id=current_user.id, event_type="updated", entity_type="budget", entity_id=budget.id, description=f"Budget updated: {budget.id}", snapshot={"month": budget.month, "category_id": budget.category_id, "amount": budget.amount})
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id)
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
    current_user: User = Depends(get_current_user),
):
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == current_user.id)
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
    current_user: User = Depends(get_current_user),
):
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == current_user.id)
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
        category = (
            db.query(Category)
            .filter(Category.id == budget_data.category_id, Category.user_id == current_user.id)
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        budget.category_id = category.id

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
    current_user: User = Depends(get_current_user),
):
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == current_user.id)
        .first()
    )

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Budget not found.",
        )

    record_finance_event(db, user_id=current_user.id, event_type="deleted", entity_type="budget", entity_id=budget.id, description=f"Budget deleted: {budget.id}", snapshot={"month": budget.month, "category_id": budget.category_id, "amount": budget.amount})
    db.delete(budget)
    db.commit()

    return {
        "message": "Budget deleted successfully.",
        "id": budget_id,
    }
