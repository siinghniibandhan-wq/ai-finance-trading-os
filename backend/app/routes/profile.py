"""Authenticated, user-scoped Account Completion profile API."""
import json
import os
import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User, UserProfile, UserCredential
from app.routes.auth import get_current_user, _verify_password, _check_login_rate_limit, _clear_login_rate_limit

router = APIRouter(prefix="/api/profile", tags=["Account Profile"])


class EmailChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_email: str = Field(min_length=5, max_length=255)
    current_password: str = Field(min_length=1, max_length=128)


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?\d{10,15}$")


def _normalize_phone(value: Any) -> str:
    cleaned = re.sub(r"[\s\-()]", "", str(value or ""))
    if not cleaned:
        return ""
    if not _PHONE_RE.fullmatch(cleaned):
        raise HTTPException(status_code=422, detail="Enter a valid phone number (10-15 digits, optional + country code).")
    return cleaned


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: dict[str, Any] = Field(default_factory=dict)


@router.get("/me")
def get_my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    profile = {}
    if row and row.profile_json:
        try:
            profile = json.loads(row.profile_json)
        except (TypeError, json.JSONDecodeError):
            raise HTTPException(status_code=500, detail="Saved profile data could not be read safely.")
    return {"user": {"id": user.id, "name": user.name, "email": user.email, "phone_number": user.phone_number, "currency": user.currency}, "profile": profile, "updated_at": row.updated_at.isoformat() if row and row.updated_at else None}


@router.put("/me")
def save_my_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Bound payload size and reject arbitrary nested/oversized content.
    serialized = json.dumps(payload.profile, ensure_ascii=False, separators=(",", ":"))
    if len(serialized) > 100_000:
        raise HTTPException(status_code=413, detail="Profile payload is too large.")
    if "phone" in payload.profile:
        payload.profile["phone"] = _normalize_phone(payload.profile["phone"])
        serialized = json.dumps(payload.profile, ensure_ascii=False, separators=(",", ":"))
    row = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if row is None:
        row = UserProfile(user_id=user.id, profile_json=serialized)
        db.add(row)
    else:
        row.profile_json = serialized
        row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return {"status": "saved", "profile": payload.profile, "updated_at": row.updated_at.isoformat() if row.updated_at else None}



@router.put("/email")
def change_my_email(payload: EmailChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change the login email after current-password verification."""
    new_email = payload.new_email.strip().lower()
    if not _EMAIL_RE.fullmatch(new_email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    old_email = (user.email or "").strip().lower()
    if new_email == old_email:
        raise HTTPException(status_code=400, detail="That is already your email address.")
    limit_key = f"email-change:{user.id}"
    _check_login_rate_limit(limit_key)
    credential = db.query(UserCredential).filter(UserCredential.user_id == user.id).first()
    if not credential or not _verify_password(payload.current_password, credential.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    _clear_login_rate_limit(limit_key)
    if db.query(User).filter(User.email == new_email, User.id != user.id).first():
        raise HTTPException(status_code=409, detail="That email is already used by another account.")
    user.email = new_email
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That email is already used by another account.") from exc
    db.refresh(user)
    result = {"status": "saved", "user": {"id": user.id, "name": user.name, "email": user.email, "currency": user.currency}}
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    if admin_email and admin_email == old_email:
        result["admin_notice"] = "Your email no longer matches ADMIN_EMAIL on the server. Update ADMIN_EMAIL to the new address and restart the backend, or admin-only features including live trading will be blocked."
    return result
