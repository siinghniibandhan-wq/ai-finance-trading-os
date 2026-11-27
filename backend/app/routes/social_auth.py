# ============================================================
# FINANCIAL OS - SOCIAL SIGN-IN (GOOGLE, GITHUB)
# Additive module. The existing email/password login in auth.py is unchanged.
#
# Flow (authorization-code flow, handled on the server):
#   1. Browser opens  /api/auth/social/<provider>/start
#   2. We send the browser to the provider with a signed "state" value
#      (and a matching one-time cookie, so a forged link cannot sign anyone in).
#   3. Provider sends the browser back to /api/auth/social/<provider>/callback
#   4. We swap the code for the person's profile, find or create the user,
#      create a normal Financial OS session, and send the browser to the website.
#
# Secrets are read from the server environment only:
#   GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
#   GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET
# A provider's button is shown only when both of its values are set.
# ============================================================

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.finance_diary import record_finance_event
from app.models import SocialIdentity, User
from app.routes.auth import _b64, _check_login_rate_limit, _client_ip, _issue_token, _secret

router = APIRouter(prefix="/api/auth/social", tags=["Social login"])
logger = logging.getLogger(__name__)

_STATE_LIFETIME_SECONDS = 10 * 60
_NONCE_COOKIE = "fos_oauth_nonce"
_HTTP_TIMEOUT_SECONDS = 10

# To add another provider later (for example Microsoft), add an entry here and
# one profile-reading function below. Nothing else needs to change.
PROVIDERS = {
    "google": {
        "label": "Google",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scope": "openid email profile",
        "client_id_env": "GOOGLE_CLIENT_ID",
        "client_secret_env": "GOOGLE_CLIENT_SECRET",
        "extra_auth_params": {"prompt": "select_account"},
    },
    "github": {
        "label": "GitHub",
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "scope": "read:user user:email",
        "client_id_env": "GITHUB_CLIENT_ID",
        "client_secret_env": "GITHUB_CLIENT_SECRET",
        "extra_auth_params": {},
    },
}


# ------------------------------------------------------------
# Settings helpers
# ------------------------------------------------------------

def _api_public_url() -> str:
    return (os.getenv("API_PUBLIC_URL", "").strip() or "https://wealthmanager.duckdns.org").rstrip("/")


def _frontend_url() -> str:
    return (os.getenv("FRONTEND_URL", "").strip() or "https://main.d1qcu4l3dz9f9e.amplifyapp.com").rstrip("/")


def _callback_url(provider: str) -> str:
    return f"{_api_public_url()}/api/auth/social/{provider}/callback"


def _credentials(provider: str) -> tuple[str, str] | None:
    config = PROVIDERS.get(provider)
    if not config:
        return None
    client_id = os.getenv(config["client_id_env"], "").strip()
    client_secret = os.getenv(config["client_secret_env"], "").strip()
    if not client_id or not client_secret:
        return None
    return client_id, client_secret


# ------------------------------------------------------------
# Signed "state" (stops forged sign-in links)
# ------------------------------------------------------------

def _sign(value: str) -> str:
    return _b64(hmac.new(_secret(), f"social-state:{value}".encode(), hashlib.sha256).digest())


def _make_state(provider: str, nonce: str) -> str:
    payload = {"p": provider, "n": nonce, "e": int(time.time()) + _STATE_LIFETIME_SECONDS}
    encoded = _b64(json.dumps(payload, separators=(",", ":")).encode())
    return f"{encoded}.{_sign(encoded)}"


def _read_state(state: str) -> dict | None:
    """Return the state payload when the signature is valid and not expired, else None."""
    try:
        encoded, supplied = state.split(".", 1)
        if not hmac.compare_digest(supplied, _sign(encoded)):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if int(payload["e"]) <= int(time.time()):
            return None
        if payload.get("p") not in PROVIDERS or not isinstance(payload.get("n"), str):
            return None
        return payload
    except Exception:
        return None


# ------------------------------------------------------------
# Small HTTP helpers (standard library only, no new packages)
# ------------------------------------------------------------

def _http_json(url: str, *, data: dict | None = None, headers: dict | None = None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=body, headers=headers or {})
    with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310 (fixed https URLs)
        return json.loads(response.read().decode("utf-8"))


def _exchange_code(provider: str, code: str) -> str:
    config = PROVIDERS[provider]
    client_id, client_secret = _credentials(provider)  # type: ignore[misc]
    result = _http_json(
        config["token_url"],
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": _callback_url(provider),
            "grant_type": "authorization_code",
        },
        headers={"Accept": "application/json", "User-Agent": "FinancialOS-Login"},
    )
    token = result.get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("Provider did not return an access token.")
    return token


def _profile_google(access_token: str) -> dict:
    info = _http_json(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )
    return {
        "id": str(info.get("sub") or ""),
        "email": str(info.get("email") or "").strip().lower(),
        "email_verified": info.get("email_verified") is True,
        "name": str(info.get("name") or "").strip(),
    }


def _profile_github(access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FinancialOS-Login",
    }
    user = _http_json("https://api.github.com/user", headers=headers)
    emails = _http_json("https://api.github.com/user/emails", headers=headers)
    verified = [item for item in emails if isinstance(item, dict) and item.get("verified") is True and item.get("email")]
    primary = next((item for item in verified if item.get("primary") is True), None) or (verified[0] if verified else None)
    return {
        "id": str(user.get("id") or ""),
        "email": str(primary["email"]).strip().lower() if primary else "",
        "email_verified": primary is not None,
        "name": str(user.get("name") or user.get("login") or "").strip(),
    }


_PROFILE_READERS = {"google": _profile_google, "github": _profile_github}


# ------------------------------------------------------------
# Redirect helpers
# ------------------------------------------------------------

def _redirect(url: str) -> RedirectResponse:
    response = RedirectResponse(url, status_code=302)
    response.headers["Cache-Control"] = "no-store"
    response.delete_cookie(_NONCE_COOKIE, path="/api/auth/social")
    return response


def _fail(code: str) -> RedirectResponse:
    """Send the person back to the login page with a short, safe reason code."""
    return _redirect(f"{_frontend_url()}/login?social_error={urllib.parse.quote(code)}")


# ------------------------------------------------------------
# Find or create the Financial OS user
# ------------------------------------------------------------

_EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _resolve_user(db: Session, provider: str, profile: dict) -> User | str:
    """Return the user to sign in, or a short error code string."""
    provider_user_id = profile["id"][:128]
    email = profile["email"]

    identity = db.query(SocialIdentity).filter(
        SocialIdentity.provider == provider, SocialIdentity.provider_user_id == provider_user_id
    ).first()
    if identity:
        user = db.query(User).filter(User.id == identity.user_id).first()
    else:
        # Only a provider-VERIFIED email may be matched to an existing account.
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.add(SocialIdentity(user_id=user.id, provider=provider, provider_user_id=provider_user_id, email=email))
        else:
            name = (profile["name"] or email.split("@")[0])[:150]
            user = User(name=name, email=email, currency="INR")
            db.add(user)
            db.flush()
            db.add(SocialIdentity(user_id=user.id, provider=provider, provider_user_id=provider_user_id, email=email))
            record_finance_event(
                db, user_id=user.id, event_type="created", entity_type="user_account", entity_id=user.id,
                description="Financial OS user account created with social sign-in",
                snapshot={"user_id": user.id, "currency": user.currency, "provider": provider},
            )

    if not user:
        return "account_unavailable"
    if not user.is_active or getattr(user, "is_deleted", False):
        return "account_disabled"
    return user


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------

@router.get("/providers")
def social_providers():
    """Which sign-in buttons the login page should show (never returns secrets)."""
    return {
        "providers": [
            {"id": provider_id, "label": config["label"]}
            for provider_id, config in PROVIDERS.items()
            if _credentials(provider_id)
        ]
    }


@router.get("/{provider}/start")
def social_start(provider: str, request: Request):
    _check_login_rate_limit(f"social-start:{_client_ip(request)}", max_attempts=30, window=600)
    credentials = _credentials(provider)
    if not credentials:
        return _fail("not_configured")
    config = PROVIDERS[provider]
    nonce = secrets.token_urlsafe(24)
    params = {
        "client_id": credentials[0],
        "redirect_uri": _callback_url(provider),
        "response_type": "code",
        "scope": config["scope"],
        "state": _make_state(provider, nonce),
        **config["extra_auth_params"],
    }
    response = RedirectResponse(f"{config['auth_url']}?{urllib.parse.urlencode(params)}", status_code=302)
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        _NONCE_COOKIE, nonce, max_age=_STATE_LIFETIME_SECONDS, httponly=True,
        secure=_api_public_url().startswith("https://"), samesite="lax", path="/api/auth/social",
    )
    return response


@router.get("/{provider}/callback")
def social_callback(
    provider: str,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    _check_login_rate_limit(f"social-callback:{_client_ip(request)}", max_attempts=30, window=600)
    if provider not in PROVIDERS or not _credentials(provider):
        return _fail("not_configured")
    if error:
        return _fail("cancelled")

    payload = _read_state(state or "")
    cookie_nonce = request.cookies.get(_NONCE_COOKIE, "")
    if (
        not payload
        or payload["p"] != provider
        or not cookie_nonce
        or not hmac.compare_digest(str(payload["n"]), cookie_nonce)
        or not code
    ):
        return _fail("invalid_state")

    try:
        access_token = _exchange_code(provider, code)
        profile = _PROFILE_READERS[provider](access_token)
    except (urllib.error.URLError, ValueError, KeyError, TypeError, json.JSONDecodeError, OSError) as exc:
        # Log the kind of problem only. Never log codes, tokens or secrets.
        logger.warning("Social sign-in with %s failed (%s)", provider, type(exc).__name__)
        return _fail("provider_error")

    if not profile["id"] or not profile["email"] or not profile["email_verified"] or not _EMAIL_PATTERN.fullmatch(profile["email"]) or len(profile["email"]) > 255:
        return _fail("email_unverified")

    try:
        user = _resolve_user(db, provider, profile)
        if isinstance(user, str):
            db.rollback()
            return _fail(user)
        access = _issue_token(user.id, db)
        record_finance_event(
            db, user_id=user.id, event_type="login", entity_type="authentication",
            description="Successful login", snapshot={"method": provider},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        return _fail("try_again")

    # The token goes in the URL fragment (#...), which browsers never send to servers
    # or put in logs. The website reads it once and immediately removes it.
    return _redirect(f"{_frontend_url()}/auth/callback#access_token={urllib.parse.quote(access)}")
