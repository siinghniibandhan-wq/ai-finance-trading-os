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
import threading
from collections import defaultdict, deque
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User, UserCredential

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Basic process-local login throttling. For multi-instance production deployments,
# replace this store with a shared Redis/database limiter so limits apply globally.
_LOGIN_WINDOW_SECONDS = 15 * 60
_LOGIN_MAX_ATTEMPTS = 5
_login_attempts: dict[str, deque[float]] = defaultdict(deque)
_login_attempts_lock = threading.Lock()

def _login_rate_limit_key(request: Request, email: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{email.strip().lower()}"

def _check_login_rate_limit(key: str) -> None:
    now = time.monotonic()
    with _login_attempts_lock:
        attempts = _login_attempts[key]
        while attempts and now - attempts[0] >= _LOGIN_WINDOW_SECONDS:
            attempts.popleft()
        if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 15 minutes.")
        attempts.append(now)

def _clear_login_rate_limit(key: str) -> None:
    with _login_attempts_lock:
        _login_attempts.pop(key, None)


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
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    rate_limit_key = _login_rate_limit_key(http_request, email)
    _check_login_rate_limit(rate_limit_key)
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    credential = db.query(UserCredential).filter(UserCredential.user_id == user.id).first() if user else None
    if not user or not credential or not _verify_password(request.password, credential.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    _clear_login_rate_limit(rate_limit_key)
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
# ADMIN FOUNDATION
# Configure ADMIN_EMAIL to the email address of the administrator.
# Admin status is derived from server configuration, not client input.
# ============================================================

def get_current_admin(user: User = Depends(get_current_user)) -> User:
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    if not admin_email:
        raise HTTPException(
            status_code=503,
            detail="Admin access is not configured. Set ADMIN_EMAIL on the backend.",
        )
    if (user.email or "").strip().lower() != admin_email:
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return user


class UserStatusRequest(BaseModel):
    is_active: bool


@router.get("/admin/users")
def admin_list_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List customer accounts for the configured administrator."""
    users = db.query(User).order_by(User.id.asc()).offset(offset).limit(limit).all()
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "email": item.email,
                "currency": item.currency,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "is_admin": (item.email or "").strip().lower() == (os.getenv("ADMIN_EMAIL", "").strip().lower()),
            }
            for item in users
        ],
        "limit": limit,
        "offset": offset,
    }


@router.patch("/admin/users/{user_id}/status")
def admin_update_user_status(
    user_id: int,
    request: UserStatusRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Activate/deactivate a customer; prevent admin self-lockout."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target.id == admin.id and not request.is_active:
        raise HTTPException(status_code=400, detail="The administrator cannot deactivate their own account.")
    target.is_active = request.is_active
    db.commit()
    db.refresh(target)
    return {"status": "success", "user_id": target.id, "is_active": target.is_active}
