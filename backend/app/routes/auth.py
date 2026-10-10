# ============================================================
# FINANCIAL OS - REGISTRATION AND LOGIN FOUNDATION
# Uses a separate credentials table so the existing users table
# and financial records are not destructively migrated.
# ============================================================

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User, UserCredential

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    currency: str = Field(default="INR", min_length=3, max_length=10)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


def _secret() -> bytes:
    value = os.getenv("AUTH_SECRET_KEY", "").strip()
    if len(value) < 32:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured. Set AUTH_SECRET_KEY to a random secret of at least 32 characters.",
        )
    return value.encode("utf-8")


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return f"pbkdf2_sha256$310000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(derived).decode()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt_text, digest_text = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _issue_token(user_id: int) -> str:
    now = int(time.time())
    payload = {"sub": user_id, "iat": now, "exp": now + 60 * 60 * 12}
    encoded = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def _decode_token(token: str) -> dict[str, Any]:
    try:
        encoded, supplied_signature = token.split(".", 1)
        expected_signature = _b64(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("Invalid signature")
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if int(payload["exp"]) <= int(time.time()):
            raise ValueError("Expired token")
        int(payload["sub"])
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.") from exc


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer access token required.")
    payload = _decode_token(authorization[7:].strip())
    user = db.query(User).filter(User.id == int(payload["sub"]), User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User account is unavailable.")
    return user


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(name=request.name.strip(), email=email, currency=request.currency.upper())
    db.add(user)
    db.flush()
    credential = UserCredential(user_id=user.id, password_hash=_hash_password(request.password))
    db.add(credential)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to create this account. The email may already be registered.") from exc
    db.refresh(user)
    return {
        "status": "success",
        "message": "Account created. Login is available; subscription and payment activation are not yet connected.",
        "user": {"id": user.id, "name": user.name, "email": user.email, "currency": user.currency},
    }


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    credential = db.query(UserCredential).filter(UserCredential.user_id == user.id).first() if user else None
    if not user or not credential or not _verify_password(request.password, credential.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "status": "success",
        "token_type": "Bearer",
        "access_token": _issue_token(user.id),
        "expires_in": 43200,
        "user": {"id": user.id, "name": user.name, "email": user.email, "currency": user.currency},
        "subscription": {"status": "not_configured", "message": "Payment and plan activation are not implemented yet."},
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "currency": user.currency}


# ============================================================
# ONE-TIME PASSWORD SETUP FOR AN EXISTING USER
# Uses AUTH_SETUP_SECRET stored in Render environment variables.
# ============================================================

from os import getenv
from hmac import compare_digest


class InitialPasswordSetupRequest(BaseModel):
    user_id: int
    setup_secret: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=12, max_length=128)


@router.post("/setup-password")
def setup_existing_user_password(
    request: InitialPasswordSetupRequest,
    db: Session = Depends(get_db),
):
    # 1. Verify the private setup secret.
    expected_secret = getenv("AUTH_SETUP_SECRET", "")

    if (
        len(expected_secret) < 32
        or not compare_digest(request.setup_secret, expected_secret)
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid setup authorization.",
        )

    # 2. Find the existing active account.
    user = (
        db.query(User)
        .filter(
            User.id == request.user_id,
            User.is_active.is_(True),
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Active user not found.",
        )

    # 3. Refuse to overwrite existing credentials.
    credential = (
        db.query(UserCredential)
        .filter(UserCredential.user_id == user.id)
        .first()
    )

    if credential:
        raise HTTPException(
            status_code=409,
            detail="Credentials already exist. Use the normal password-reset process.",
        )

    # 4. Create credentials for the existing user.
    credential = UserCredential(
        user_id=user.id,
        password_hash=_hash_password(request.new_password),
    )

    db.add(credential)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Password setup failed.",
        )

    return {
        "status": "success",
        "message": "Password configured for the existing account.",
        "user_id": user.id,
    }
