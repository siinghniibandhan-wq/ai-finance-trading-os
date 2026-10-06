# ============================================================
# FINANCIAL OS
# USERS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


# ============================================================
# CREATE USER
# ============================================================

@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    # Prevent duplicate email addresses.
    if user_data.email:
        existing_user = (
            db.query(User)
            .filter(User.email == user_data.email)
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already exists.",
            )

    user = User(
        name=user_data.name,
        email=user_data.email,
        currency=user_data.currency,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# LIST USERS
# ============================================================

@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id.desc()).all()


# ============================================================
# GET USER
# ============================================================

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return user
