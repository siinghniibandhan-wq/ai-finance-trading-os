# ============================================================
# FINANCIAL OS
# CATEGORIES API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Category, User
from app.routes.auth import get_current_user
from app.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"],
)


# ============================================================
# CREATE CATEGORY
# ============================================================

@router.post("/", response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --------------------------------------------------------
    # Use authenticated identity; ignore any client-supplied user_id
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    # --------------------------------------------------------
    # Prevent duplicate category names for the same user
    # --------------------------------------------------------

    existing_category = (
        db.query(Category)
        .filter(
            Category.user_id == current_user.id,
            Category.name == category_data.name,
        )
        .first()
    )

    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category already exists.",
        )

    # --------------------------------------------------------
    # Create category
    # --------------------------------------------------------

    category = Category(
        user_id=current_user.id,
        name=category_data.name,
        category_type=category_data.category_type,
        description=category_data.description,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


# ============================================================
# LIST CATEGORIES
# ============================================================

@router.get("/", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Category)
        .filter(Category.user_id == current_user.id)
        .order_by(Category.id.asc())
        .all()
    )


# ============================================================
# GET CATEGORY
# ============================================================

@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == current_user.id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found.",
        )

    return category


# ============================================================
# UPDATE CATEGORY
# ============================================================

@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == current_user.id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found.",
        )

    update_data = category_data.model_dump(
        exclude_unset=True
    )

    # Ownership is fixed to the authenticated user; never permit reassignment.
    update_data.pop("user_id", None)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category


# ============================================================
# DELETE CATEGORY
# ============================================================

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == current_user.id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found.",
        )

    db.delete(category)
    db.commit()

    return {
        "status": "deleted",
        "category_id": category_id,
    }
