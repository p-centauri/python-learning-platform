import hashlib
import hmac
import math
import secrets
import time
from collections import defaultdict, deque
from threading import BoundedSemaphore, Lock
from datetime import timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import LoginSession, User, utcnow

router = APIRouter(prefix="/auth", tags=["auth"])
DB = Annotated[Session, Depends(get_db, scope="function")]
COOKIE = "academy_session"
password_work = BoundedSemaphore(2)
# Failed sign-ins per account, so many addresses can't take turns guessing one password. The
# per-address limit (main.py) can't see that. Per process, like that limit; see SECURITY.md.
FAILURE_WINDOW_SECONDS = 15 * 60
MAX_FAILURES_PER_EMAIL = 5
login_failures = defaultdict(deque)
failure_lock = Lock()


def hash_password(password: str, salt: bytes | None = None):
    salt = salt or secrets.token_bytes(16)
    with password_work:
        digest = hashlib.scrypt(password.encode(), salt=salt, n=131072, r=8, p=1, maxmem=256 * 1024 * 1024)
    return f"scrypt$131072$8$1${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str):
    parts = stored.split("$")
    # Read the initial local-development hash format, then upgrade on login.
    if len(parts) == 3:
        _, salt, expected = parts
        n, r, p = 16384, 8, 1
    else:
        _, n, r, p, salt, expected = parts
        n, r, p = int(n), int(r), int(p)
    with password_work:
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt), n=n, r=r, p=p, maxmem=256 * 1024 * 1024
        )
    return hmac.compare_digest(actual.hex(), expected)


DUMMY_PASSWORD_HASH = hash_password("unavailable-account-placeholder")


def failure_retry_after(email):
    """Seconds until this account may try again, or None. Also drops expired entries."""
    now = time.monotonic()
    with failure_lock:
        for key in list(login_failures):
            window = login_failures[key]
            while window and window[0] <= now - FAILURE_WINDOW_SECONDS:
                window.popleft()
            if not window:
                del login_failures[key]
        window = login_failures.get(email)
        if window is None or len(window) < MAX_FAILURES_PER_EMAIL:
            return None
        return max(1, math.ceil(window[0] + FAILURE_WINDOW_SECONDS - now))


def record_failure(email):
    with failure_lock:
        login_failures[email].append(time.monotonic())


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def expired(session):
    value = session.expires_at
    value = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return value <= utcnow()


def current_user(request: Request, db: DB):
    token = request.cookies.get(COOKIE)
    session = db.get(LoginSession, token_digest(token)) if token else None
    if not session or expired(session):
        raise HTTPException(401, "Sign in to continue.")
    query = select(User).where(User.id == session.user_id)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        query = query.with_for_update()
    user = db.scalar(query)
    if not user:
        raise HTTPException(401, "Account not found.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        # A reset may revoke the session while this request waits for the user lock.
        session = db.scalar(
            select(LoginSession)
            .where(LoginSession.token_hash == token_digest(token))
            .execution_options(populate_existing=True)
        )
        if not session or expired(session):
            raise HTTPException(401, "Sign in to continue.")
    return user


Learner = Annotated[User, Depends(current_user)]


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class Registration(Credentials):
    name: str = Field(min_length=1, max_length=80)


def identity(user):
    return {"id": user.id, "name": user.name, "email": user.email}


def start_session(user, db, response):
    token = secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            token_hash=token_digest(token),
            user_id=user.id,
            expires_at=utcnow() + timedelta(days=settings.session_days),
        )
    )
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    return identity(user)


@router.post("/register", status_code=201)
def register(data: Registration, db: DB, response: Response):
    if not data.name.strip():
        raise HTTPException(422, "Name cannot be blank.")
    user = User(
        email=str(data.email).lower(), name=data.name.strip(), password_hash=hash_password(data.password)
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists.")
    return start_session(user, db, response)


@router.post("/login")
def login(data: Credentials, db: DB, response: Response):
    email = str(data.email).lower()
    # Checked before hashing, and the same for unknown emails, so it reveals nothing about accounts.
    retry_after = failure_retry_after(email)
    if retry_after is not None:
        raise HTTPException(
            429,
            "Too many failed sign-in attempts for this account. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    user = db.scalar(select(User).where(User.email == email))
    # Perform the same expensive hash when the account is absent.
    stored = user.password_hash if user else DUMMY_PASSWORD_HASH
    valid = verify_password(data.password, stored)
    if not user or not valid:
        record_failure(email)
        raise HTTPException(401, "Email or password is incorrect.")
    if len(user.password_hash.split("$")) == 3:
        user.password_hash = hash_password(data.password)
    return start_session(user, db, response)


@router.get("/me")
def me(user: Learner):
    return identity(user)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: DB):
    token = request.cookies.get(COOKIE)
    if token:
        db.execute(delete(LoginSession).where(LoginSession.token_hash == token_digest(token)))
    response.delete_cookie(COOKIE, path="/")
