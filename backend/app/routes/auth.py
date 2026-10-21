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
import re
import secrets
import time
import threading
from collections import defaultdict, deque
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from datetime import datetime
from app.models import User, UserCredential, AuthSession, AdminAuditLog
from app.finance_diary import record_finance_event

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Adds the "Authorize" button to /docs (Swagger ignores plain "authorization" header boxes).
# auto_error=False keeps our own 401 message below.
bearer_scheme = HTTPBearer(auto_error=False, description="Paste only the token from /api/auth/login (no word Bearer).")

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
    # Kept as "email" for backwards compatibility with existing clients.
    # On login this field accepts either the registered email or phone number.
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class ContactUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    phone_number: str | None = Field(default=None, max_length=25)
    current_password: str = Field(min_length=1, max_length=128)


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


def _issue_token(user_id: int, db: Session) -> str:
    now = int(time.time())
    jti = secrets.token_urlsafe(24)
    expires = now + 60 * 60 * 12
    payload = {"sub": user_id, "iat": now, "exp": expires, "jti": jti}
    db.add(AuthSession(jti=jti, user_id=user_id, expires_at=datetime.utcfromtimestamp(expires)))
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
    authorization: str | None = Header(default=None, include_in_schema=False),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer access token required.")
    payload = _decode_token(authorization[7:].strip())
    jti = payload.get("jti")
    session = db.query(AuthSession).filter(
        AuthSession.jti == jti, AuthSession.user_id == int(payload["sub"]),
        AuthSession.revoked_at.is_(None), AuthSession.expires_at > datetime.utcnow(),
    ).first() if jti else None
    if not session:
        raise HTTPException(status_code=401, detail="Session is invalid or has been revoked.")
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
    record_finance_event(
        db, user_id=user.id, event_type="created", entity_type="user_account", entity_id=user.id,
        description="Financial OS user account registered",
        snapshot={"user_id": user.id, "currency": user.currency},
    )
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
    identifier = str(request.email).strip().lower()
    if "@" not in identifier:
        import re
        identifier = re.sub(r"[\\s().-]", "", identifier)
    rate_limit_key = _login_rate_limit_key(http_request, identifier)
    _check_login_rate_limit(rate_limit_key)
    user = db.query(User).filter(
        (User.email == identifier) | (User.phone_number == identifier),
        User.is_active.is_(True),
    ).first()
    credential = db.query(UserCredential).filter(UserCredential.user_id == user.id).first() if user else None
    if not user or not credential or not _verify_password(request.password, credential.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email/phone number or password.")
    _clear_login_rate_limit(rate_limit_key)
    record_finance_event(
        db, user_id=user.id, event_type="login", entity_type="authentication",
        description="Successful login", snapshot={"method": "email" if "@" in identifier else "phone"},
    )
    db.commit()
    return {
        "status": "success",
        "token_type": "Bearer",
        "access_token": _issue_token(user.id, db),
        "expires_in": 43200,
        "user": {"id": user.id, "name": user.name, "email": user.email, "phone_number": user.phone_number, "currency": user.currency},
        "subscription": {"status": "not_configured", "message": "Payment and plan activation are not implemented yet."},
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "phone_number": user.phone_number, "currency": user.currency}


@router.patch("/contact")
def update_contact(
    request: ContactUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update one login contact after password re-authentication and throttling."""
    limit_key = f"contact-change:{user.id}"
    _check_login_rate_limit(limit_key)
    credential = db.query(UserCredential).filter(UserCredential.user_id == user.id).first()
    if not credential or not _verify_password(request.current_password, credential.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    _clear_login_rate_limit(limit_key)
    if (request.email is None) == (request.phone_number is None):
        raise HTTPException(status_code=422, detail="Update either email or phone number in one request.")

    old_email = (user.email or "").strip().lower()
    if request.email is not None:
        email = request.email.strip().lower()
        if len(email) > 255 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise HTTPException(status_code=422, detail="Enter a valid email address.")
        if email != old_email:
            duplicate = db.query(User).filter(User.email == email, User.id != user.id).first()
            if duplicate:
                raise HTTPException(status_code=409, detail="That email address is already registered.")
        user.email = email

    if request.phone_number is not None:
        phone = re.sub(r"[\s().-]", "", request.phone_number.strip())
        if not re.fullmatch(r"\+?[0-9]{10,15}", phone):
            raise HTTPException(status_code=422, detail="Enter a valid phone number with 10 to 15 digits.")
        duplicate = db.query(User).filter(User.phone_number == phone, User.id != user.id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="That phone number is already registered.")
        user.phone_number = phone

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="The contact detail is already registered to another account.") from exc
    db.refresh(user)
    result = {
        "status": "success",
        "message": "Contact detail updated. You can use the new email or phone number to log in.",
        "user": {"id": user.id, "name": user.name, "email": user.email, "phone_number": user.phone_number, "currency": user.currency},
    }
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_user_id = os.getenv("ADMIN_USER_ID", "").strip()
    if not admin_user_id and request.email is not None and admin_email and admin_email == old_email and user.email != old_email:
        result["admin_notice"] = "Your email no longer matches ADMIN_EMAIL on the server. Update ADMIN_EMAIL to the new address and restart the backend, or configure ADMIN_USER_ID to this account's database user ID to keep admin access stable."
    return result


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None, include_in_schema=False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Revoke the current bearer-token session immediately."""
    token = authorization[7:].strip()  # get_current_user already validated this header
    payload = _decode_token(token)
    session = db.query(AuthSession).filter(
        AuthSession.jti == payload.get("jti"), AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    ).first()
    if session:
        session.revoked_at = datetime.utcnow()
    record_finance_event(
        db, user_id=user.id, event_type="logout", entity_type="authentication",
        entity_id=payload.get("jti"), description="User logged out",
        snapshot={"session_revoked": bool(session)},
    )
    db.commit()
    return {"status": "success", "message": "Session revoked."}





















# ============================================================
# ADMIN FOUNDATION
# Configure ADMIN_EMAIL to the email address of the administrator.
# Admin status is derived from server configuration, not client input.
# ============================================================

def get_current_admin(user: User = Depends(get_current_user)) -> User:
    # Prefer a stable database user ID when configured. Email-based admin
    # checks otherwise break as soon as the administrator changes their login email.
    admin_user_id = os.getenv("ADMIN_USER_ID", "").strip()
    if admin_user_id:
        try:
            configured_user_id = int(admin_user_id)
            if configured_user_id <= 0:
                raise ValueError("ADMIN_USER_ID must be positive")
        except ValueError as exc:
            raise HTTPException(
                status_code=503,
                detail="ADMIN_USER_ID must be a positive database user ID.",
            ) from exc
        if user.id != configured_user_id:
            raise HTTPException(status_code=403, detail="Administrator access required.")
        return user

    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    if not admin_email:
        raise HTTPException(
            status_code=503,
            detail="Admin access is not configured. Set ADMIN_USER_ID or ADMIN_EMAIL on the backend.",
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
    admin_user_id = os.getenv("ADMIN_USER_ID", "").strip()
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "email": item.email,
                "phone_number": item.phone_number,
                "currency": item.currency,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "is_admin": str(item.id) == admin_user_id if admin_user_id else (item.email or "").strip().lower() == admin_email,
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
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="user_activated" if request.is_active else "user_deactivated",
        target_user_id=target.id,
        details=f"Account status changed to {'active' if request.is_active else 'inactive'}.",
    ))
    db.commit()
    db.refresh(target)
    return {"status": "success", "user_id": target.id, "is_active": target.is_active}
    


@router.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Permanently delete a non-admin user when related records allow safe deletion."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="The administrator cannot delete their own account.")
    admin_user_id = os.getenv("ADMIN_USER_ID", "").strip()
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    target_is_admin = (
        str(target.id) == admin_user_id if admin_user_id
        else (target.email or "").strip().lower() == admin_email
    )
    if target_is_admin:
        raise HTTPException(status_code=400, detail="Administrator accounts cannot be deleted here.")
    try:
        # ORM relationships cascade owned accounts, transactions, and categories.
        # The transaction ensures no partial deletion is committed.
        db.delete(target)
        db.add(AdminAuditLog(
            admin_user_id=admin.id,
            action="user_deleted",
            target_user_id=target.id,
            details="User account permanently deleted by administrator.",
        ))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This user has related records that prevent safe deletion. No changes were committed.",
        ) from exc
    return {"status": "success", "user_id": user_id, "deleted": True}


@router.get("/admin/overview")
def admin_overview(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return operational counts derived from the live database."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    inactive_users = total_users - active_users
    active_sessions = db.query(AuthSession).filter(
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > datetime.utcnow(),
    ).count()
    return {
        "users_total": total_users,
        "users_active": active_users,
        "users_inactive": inactive_users,
        "active_sessions": active_sessions,
        "admin_configuration_present": bool(
            os.getenv("ADMIN_USER_ID", "").strip() or os.getenv("ADMIN_EMAIL", "").strip()
        ),
        "auth_secret_configured": len(os.getenv("AUTH_SECRET_KEY", "").strip()) >= 32,
        "cors_configured": bool(os.getenv("CORS_ALLOWED_ORIGINS", "").strip()),
    }


@router.get("/admin/audit-logs")
def admin_audit_logs(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Return recent administrator activity, newest first."""
    rows = db.query(AdminAuditLog).order_by(
        AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc()
    ).offset(offset).limit(limit).all()
    return {
        "items": [
            {
                "id": row.id,
                "admin_user_id": row.admin_user_id,
                "action": row.action,
                "target_user_id": row.target_user_id,
                "details": row.details,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
        "limit": limit,
        "offset": offset,
    }
