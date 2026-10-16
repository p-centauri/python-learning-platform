"""Offline recovery and owned sessions; no email delivery or security questions."""

import hmac
import secrets
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictStr
from sqlalchemy import delete, select
from .auth import DB, Learner, COOKIE, hash_password, token_digest, verify_password
from .models import AccountRecoveryKey, LoginSession, User, utcnow
from .projects import utc_timestamp

router = APIRouter(prefix="/account", tags=["account security"])


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PasswordProof(StrictInput):
    current_password: StrictStr = Field(min_length=12, max_length=256)


def verify_current(user, password):
    if not verify_password(password, user.password_hash):
        raise HTTPException(401, "Current password is incorrect.")


@router.get("")
def overview(user: Learner, db: DB):
    key = db.get(AccountRecoveryKey, user.id)
    return {
        "recovery_enabled": bool(key and key.used_at is None),
        "recovery_created_at": utc_timestamp(key.created_at) if key else None,
        "recovery_used_at": utc_timestamp(key.used_at) if key else None,
        "note": "Recovery uses a previously saved offline key. No recovery email is sent. A reset consumes the key and signs out every session.",
    }


@router.post("/recovery-key", status_code=201)
def generate(data: PasswordProof, user: Learner, db: DB):
    verify_current(user, data.current_password)
    token = "academy-recovery-" + secrets.token_urlsafe(32)
    row = db.get(AccountRecoveryKey, user.id)
    if row is None:
        row = AccountRecoveryKey(user_id=user.id, token_hash=token_digest(token))
        db.add(row)
    else:
        row.token_hash = token_digest(token)
        row.created_at = utcnow()
        row.used_at = None
    db.flush()
    return {
        "recovery_key": token,
        "created_at": utc_timestamp(row.created_at),
        "note": "Shown once. Save offline; generating another key invalidates this one. It is valid until used, revoked or your password changes.",
    }


@router.delete("/recovery-key", status_code=204)
def revoke(data: PasswordProof, user: Learner, db: DB):
    verify_current(user, data.current_password)
    db.execute(delete(AccountRecoveryKey).where(AccountRecoveryKey.user_id == user.id))


class RecoveryInput(StrictInput):
    email: EmailStr
    recovery_key: StrictStr = Field(pattern=r"^academy-recovery-[A-Za-z0-9_-]{43}$")
    new_password: StrictStr = Field(min_length=12, max_length=256)
    confirm_password: StrictStr = Field(min_length=12, max_length=256)


def same_passwords(data):
    if data.new_password != data.confirm_password:
        raise HTTPException(422, "The new passwords must match.")


@router.post("/recover")
def recover(data: RecoveryInput, db: DB, response: Response):
    same_passwords(data)
    # Do the same expensive work for every well-formed request, including unknown accounts.
    new_hash = hash_password(data.new_password)
    user = db.scalar(select(User).where(User.email == str(data.email).lower()).with_for_update())
    key = db.get(AccountRecoveryKey, user.id) if user else None
    expected = key.token_hash if key else "0" * 64
    valid = hmac.compare_digest(token_digest(data.recovery_key), expected)
    if not user or not key or key.used_at is not None or not valid:
        raise HTTPException(401, "Email or recovery key is incorrect, revoked or already used.")
    user.password_hash = new_hash
    key.used_at = utcnow()
    db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    response.delete_cookie(COOKIE, path="/")
    return {
        "reset": True,
        "note": "Password changed. All sessions are signed out and the recovery key is consumed. Sign in with your new password, then save a new recovery key.",
    }


class PasswordChange(PasswordProof):
    new_password: StrictStr = Field(min_length=12, max_length=256)
    confirm_password: StrictStr = Field(min_length=12, max_length=256)


@router.post("/password")
def change_password(data: PasswordChange, user: Learner, db: DB, response: Response):
    same_passwords(data)
    verify_current(user, data.current_password)
    user.password_hash = hash_password(data.new_password)
    db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    db.execute(delete(AccountRecoveryKey).where(AccountRecoveryKey.user_id == user.id))
    response.delete_cookie(COOKIE, path="/")
    return {
        "changed": True,
        "note": "Sign in with your new password. All sessions and the previous recovery key were revoked.",
    }


def session_id(row):
    return token_digest(row.token_hash)[:24]


@router.get("/sessions")
def sessions(user: Learner, db: DB, request: Request):
    current = token_digest(request.cookies[COOKIE])
    return [
        {
            "id": session_id(row),
            "current": row.token_hash == current,
            "expires_at": utc_timestamp(row.expires_at),
        }
        for row in db.scalars(
            select(LoginSession)
            .where(LoginSession.user_id == user.id, LoginSession.expires_at > utcnow())
            .order_by(LoginSession.expires_at.desc())
        )
    ]


@router.delete("/sessions/{id}", status_code=204)
def remove_session(id: str, user: Learner, db: DB, request: Request, response: Response):
    row = next(
        (
            r
            for r in db.scalars(select(LoginSession).where(LoginSession.user_id == user.id))
            if session_id(r) == id
        ),
        None,
    )
    if row is None:
        raise HTTPException(404, "Session not found.")
    if row.token_hash == token_digest(request.cookies[COOKIE]):
        response.delete_cookie(COOKIE, path="/")
    db.delete(row)
