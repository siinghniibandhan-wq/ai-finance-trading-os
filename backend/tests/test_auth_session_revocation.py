"""Integration test for Financial OS bearer-session revocation.

Run from backend/ with:
  AUTH_SECRET_KEY='local-test-secret-change-me-1234567890' pytest -q tests/test_auth_session_revocation.py

This test uses a temporary SQLite database and a minimal FastAPI app containing
only the production authentication router. It does not connect to production DB.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Set these before importing app.database.database / app.routes.auth.
_tmp_dir = tempfile.TemporaryDirectory(prefix="financial-os-auth-test-")
_db_path = Path(_tmp_dir.name) / "auth-test.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path.as_posix()}"
os.environ.setdefault("AUTH_SECRET_KEY", "local-test-secret-change-me-1234567890")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base, get_db
from app.models import AuthSession, FinanceDiaryEntry, User, UserCredential
from app.routes.auth import router as auth_router

TEST_ENGINE = create_engine(
    f"sqlite:///{_db_path.as_posix()}",
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False)

# Create only the tables needed by the authentication router.
Base.metadata.create_all(
    bind=TEST_ENGINE,
    tables=[User.__table__, UserCredential.__table__, AuthSession.__table__, FinanceDiaryEntry.__table__],
)

app = FastAPI()
app.include_router(auth_router)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_login_logout_revokes_old_bearer_token():
    # Use a unique test email so repeated local runs do not collide.
    email = "session-revocation-test@example.test"
    password = "Test-Password-Only-123!"

    # Clean up a prior run if the test process/database is reused.
    db = TestSessionLocal()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    register = client.post(
        "/api/auth/register",
        json={"name": "Session Revocation Test", "email": email, "password": password},
    )
    assert register.status_code == 201, register.text

    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json().get("access_token")
    assert token, "Login did not return an access token"
    auth = {"Authorization": f"Bearer {token}"}

    # Token must work before logout.
    before_logout = client.get("/api/auth/me", headers=auth)
    assert before_logout.status_code == 200, before_logout.text

    # Logout must succeed for the active token.
    logout = client.post("/api/auth/logout", headers=auth)
    assert logout.status_code == 200, logout.text

    # The exact same token must no longer authenticate.
    after_logout = client.get("/api/auth/me", headers=auth)
    assert after_logout.status_code == 401, (
        "SECURITY FAILURE: old bearer token still works after logout; "
        f"received HTTP {after_logout.status_code}: {after_logout.text}"
    )

    # Also ensure a protected endpoint rejects the revoked token.
    # /api/auth/me is the minimal protected endpoint and is the canonical check.
    assert "revoked" in after_logout.text.lower() or "invalid" in after_logout.text.lower()



def test_account_contact_updates_email_and_phone_login(monkeypatch):
    original_email = "contact-update-test@example.test"
    new_email = "contact-update-new@example.test"
    phone = "+919876543210"
    password = "Test-Password-Only-456!"

    register = client.post(
        "/api/auth/register",
        json={"name": "Contact Update Test", "email": original_email, "password": password},
    )
    assert register.status_code == 201, register.text
    token = client.post("/api/auth/login", json={"email": original_email, "password": password}).json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    update_email = client.patch(
        "/api/auth/contact",
        headers=auth,
        json={"email": new_email, "current_password": password},
    )
    assert update_email.status_code == 200, update_email.text
    assert update_email.json()["user"]["email"] == new_email

    login_new_email = client.post("/api/auth/login", json={"email": new_email, "password": password})
    assert login_new_email.status_code == 200, login_new_email.text

    # Admin status is configured by email, so the UI must warn if this address changes.
    monkeypatch.setenv("ADMIN_EMAIL", new_email)
    final_email = "contact-update-final@example.test"
    update_admin_email = client.patch(
        "/api/auth/contact",
        headers=auth,
        json={"email": final_email, "current_password": password},
    )
    assert update_admin_email.status_code == 200, update_admin_email.text
    assert "ADMIN_EMAIL" in update_admin_email.json()["admin_notice"]

    update_phone = client.patch(
        "/api/auth/contact",
        headers=auth,
        json={"phone_number": "+91 98765-43210", "current_password": password},
    )
    assert update_phone.status_code == 200, update_phone.text
    assert update_phone.json()["user"]["phone_number"] == phone

    login_phone = client.post("/api/auth/login", json={"email": phone, "password": password})
    assert login_phone.status_code == 200, login_phone.text

    wrong_password = client.patch(
        "/api/auth/contact",
        headers=auth,
        json={"phone_number": "+919876543211", "current_password": "wrong-password"},
    )
    assert wrong_password.status_code == 401, wrong_password.text

    for _ in range(4):
        repeated_wrong_password = client.patch(
            "/api/auth/contact",
            headers=auth,
            json={"phone_number": "+919876543212", "current_password": "wrong-password"},
        )
        assert repeated_wrong_password.status_code == 401, repeated_wrong_password.text
    throttled = client.patch(
        "/api/auth/contact",
        headers=auth,
        json={"phone_number": "+919876543212", "current_password": "wrong-password"},
    )
    assert throttled.status_code == 429, throttled.text
