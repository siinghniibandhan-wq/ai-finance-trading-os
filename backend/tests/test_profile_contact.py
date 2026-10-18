import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.database.database import Base
from app.routes import auth, profile


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'profile-contact.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    for uid, email in ((1, "me@example.com"), (2, "other@example.com")):
        session.add(models.User(id=uid, name=f"U{uid}", email=email))
        session.add(models.UserCredential(user_id=uid, password_hash=auth._hash_password("correct-horse-battery")))
    session.commit()
    auth._login_attempts.clear()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        auth._login_attempts.clear()


def _change(db, email, password="correct-horse-battery"):
    user = db.get(models.User, 1)
    return profile.change_my_email(profile.EmailChange(new_email=email, current_password=password), user, db)


def test_email_change_success_lowercases(db):
    result = _change(db, "New.Me@Example.com")
    assert result["user"]["email"] == "new.me@example.com"
    assert db.get(models.User, 1).email == "new.me@example.com"


def test_email_change_wrong_password_rejected(db):
    with pytest.raises(HTTPException) as exc:
        _change(db, "new@example.com", "wrong-password")
    assert exc.value.status_code == 401
    assert db.get(models.User, 1).email == "me@example.com"


def test_email_change_duplicate_rejected(db):
    with pytest.raises(HTTPException) as exc:
        _change(db, "other@example.com")
    assert exc.value.status_code == 409


def test_email_change_admin_notice(db, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "me@example.com")
    assert "ADMIN_EMAIL" in _change(db, "new@example.com")["admin_notice"]


def test_phone_normalized_and_validated(db):
    user = db.get(models.User, 1)
    saved = profile.save_my_profile(profile.ProfileUpdate(profile={"phone": "+91 98765-43210"}), user, db)
    assert saved["profile"]["phone"] == "+919876543210"
    with pytest.raises(HTTPException) as exc:
        profile.save_my_profile(profile.ProfileUpdate(profile={"phone": "12ab"}), user, db)
    assert exc.value.status_code == 422
