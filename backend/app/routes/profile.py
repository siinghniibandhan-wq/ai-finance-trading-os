"""Authenticated, user-scoped Account Completion profile API."""
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User, UserProfile
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Account Profile"])


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
