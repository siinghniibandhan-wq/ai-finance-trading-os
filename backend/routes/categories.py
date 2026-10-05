from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Category
from database.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)


router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"],
)


@router.get("/", response_model=list[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
):
    return (
        db.query(Category)
        .filter(Category.is_active.is_(True))
        .order_by(Category.id.asc())
        .all()
    )


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
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
            detail="Category not found",
        )

    return category


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=201,
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
):
    if data.parent_id is not None:
        parent = (
            db.query(Category)
            .filter(
                Category.id == data.parent_id,
                Category.is_active.is_(True),
            )
            .first()
        )

        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Parent category not found",
            )

    category = Category(
        name=data.name,
        category_type=data.category_type,
        parent_id=data.parent_id,
        description=data.description,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
):
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
            detail="Category not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "parent_id" in update_data:
        parent_id = update_data["parent_id"]

        if parent_id == category_id:
            raise HTTPException(
                status_code=400,
                detail="A category cannot be its own parent",
            )

        if parent_id is not None:
            parent = (
                db.query(Category)
                .filter(
                    Category.id == parent_id,
                    Category.is_active.is_(True),
                )
                .first()
            )

            if not parent:
                raise HTTPException(
                    status_code=404,
                    detail="Parent category not found",
                )

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}")
def archive_category(
    category_id: int,
    db: Session = Depends(get_db),
):
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
            detail="Category not found",
        )

    child_exists = (
        db.query(Category)
        .filter(
            Category.parent_id == category_id,
            Category.is_active.is_(True),
        )
        .first()
    )

    if child_exists:
        raise HTTPException(
            status_code=400,
            detail="Cannot archive category with active subcategories",
        )

    category.is_active = False

    db.commit()

    return {
        "message": "Category archived successfully",
        "category_id": category_id,
          }
