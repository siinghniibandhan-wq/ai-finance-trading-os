# =====================================================
# AI FINANCE TRADING OS
# BUDGET API
# =====================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.database import get_db
from database.models import Category


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/api/budgets",
    tags=["Budgets"],
)


# =====================================================
# DATABASE TABLE
#
# This table is created automatically if it does not
# already exist.
# =====================================================

CREATE_BUDGETS_TABLE = """
CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    month VARCHAR(7) NOT NULL,
    category_id INTEGER NULL,
    amount NUMERIC(14, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


# =====================================================
# PYDANTIC SCHEMAS
# =====================================================

class BudgetCreate(BaseModel):
    month: str = Field(..., min_length=7, max_length=7)
    category_id: int
    amount: float = Field(..., gt=0)


class BudgetUpdate(BaseModel):
    month: str = Field(..., min_length=7, max_length=7)
    category_id: int
    amount: float = Field(..., gt=0)


# =====================================================
# ENSURE TABLE EXISTS
# =====================================================

def ensure_budget_table(db: Session):
    db.execute(text(CREATE_BUDGETS_TABLE))
    db.commit()


# =====================================================
# VALIDATE MONTH
#
# Expected format:
# YYYY-MM
# =====================================================

def validate_month(month: str):

    if len(month) != 7:
        raise HTTPException(
            status_code=400,
            detail="Month must use YYYY-MM format.",
        )

    if month[4] != "-":
        raise HTTPException(
            status_code=400,
            detail="Month must use YYYY-MM format.",
        )

    try:
        year = int(month[:4])
        month_number = int(month[5:])

        if year < 1900 or month_number < 1 or month_number > 12:
            raise ValueError

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid month. Use YYYY-MM format.",
        )


# =====================================================
# VALIDATE CATEGORY
# =====================================================

def validate_category(category_id: int, db: Session):

    category = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            Category.is_active.is_(True),
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found.",
        )

    return category


# =====================================================
# GET ALL BUDGETS
# =====================================================

@router.get("/")
def get_budgets(
    month: str | None = None,
    db: Session = Depends(get_db),
):

    ensure_budget_table(db)

    if month:
        validate_month(month)

        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    month,
                    category_id,
                    amount,
                    created_at,
                    updated_at
                FROM budgets
                WHERE month = :month
                ORDER BY id DESC
                """
            ),
            {"month": month},
        ).mappings().all()

    else:

        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    month,
                    category_id,
                    amount,
                    created_at,
                    updated_at
                FROM budgets
                ORDER BY month DESC, id DESC
                """
            )
        ).mappings().all()

    return [dict(row) for row in rows]


# =====================================================
# GET SINGLE BUDGET
# =====================================================

@router.get("/{budget_id}")
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
):

    ensure_budget_table(db)

    row = db.execute(
        text(
            """
            SELECT
                id,
                month,
                category_id,
                amount,
                created_at,
                updated_at
            FROM budgets
            WHERE id = :budget_id
            """
        ),
        {"budget_id": budget_id},
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Budget not found.",
        )

    return dict(row)


# =====================================================
# CREATE BUDGET
# =====================================================

@router.post("/", status_code=201)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
):

    ensure_budget_table(db)

    validate_month(data.month)

    validate_category(data.category_id, db)

    # -------------------------------------------------
    # Prevent duplicate category budget for same month
    # -------------------------------------------------

    existing = db.execute(
        text(
            """
            SELECT id
            FROM budgets
            WHERE month = :month
              AND category_id = :category_id
            LIMIT 1
            """
        ),
        {
            "month": data.month,
            "category_id": data.category_id,
        },
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A budget already exists for this category and month.",
        )

    result = db.execute(
        text(
            """
            INSERT INTO budgets
                (month, category_id, amount)
            VALUES
                (:month, :category_id, :amount)
            RETURNING
                id,
                month,
                category_id,
                amount,
                created_at,
                updated_at
            """
        ),
        {
            "month": data.month,
            "category_id": data.category_id,
            "amount": data.amount,
        },
    )

    db.commit()

    row = result.mappings().first()

    return dict(row)


# =====================================================
# UPDATE BUDGET
# =====================================================

@router.put("/{budget_id}")
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
):

    ensure_budget_table(db)

    validate_month(data.month)

    validate_category(data.category_id, db)

    existing = db.execute(
        text(
            """
            SELECT id
            FROM budgets
            WHERE id = :budget_id
            """
        ),
        {"budget_id": budget_id},
    ).first()

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Budget not found.",
        )

    duplicate = db.execute(
        text(
            """
            SELECT id
            FROM budgets
            WHERE month = :month
              AND category_id = :category_id
              AND id != :budget_id
            LIMIT 1
            """
        ),
        {
            "month": data.month,
            "category_id": data.category_id,
            "budget_id": budget_id,
        },
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="A budget already exists for this category and month.",
        )

    result = db.execute(
        text(
            """
            UPDATE budgets
            SET
                month = :month,
                category_id = :category_id,
                amount = :amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :budget_id
            RETURNING
                id,
                month,
                category_id,
                amount,
                created_at,
                updated_at
            """
        ),
        {
            "month": data.month,
            "category_id": data.category_id,
            "amount": data.amount,
            "budget_id": budget_id,
        },
    )

    db.commit()

    row = result.mappings().first()

    return dict(row)


# =====================================================
# DELETE BUDGET
# =====================================================

@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
):

    ensure_budget_table(db)

    result = db.execute(
        text(
            """
            DELETE FROM budgets
            WHERE id = :budget_id
            RETURNING id
            """
        ),
        {"budget_id": budget_id},
    )

    db.commit()

    row = result.first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Budget not found.",
        )

    return {
        "message": "Budget deleted successfully.",
        "budget_id": budget_id,
    }
