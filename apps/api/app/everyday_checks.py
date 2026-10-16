"""Trusted real PostgreSQL concurrency drill. No public endpoint or learner execution."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
import secrets
from threading import Barrier, Event
import time
from fastapi import HTTPException, Request, Response
from sqlalchemy import create_engine, delete, event, select, text
from sqlalchemy.orm import sessionmaker
from .accounts import RecoveryInput, recover
from .auth import current_user, hash_password, token_digest, COOKIE
from .config import settings
from .database import engine, SessionLocal
from .models import User, AccountRecoveryKey, LoginSession, utcnow


def main():
    assert engine.dialect.name == "postgresql"
    suffix = secrets.token_hex(5)
    key = "academy-recovery-" + secrets.token_urlsafe(32)
    with SessionLocal.begin() as db:
        user = User(
            name="Concurrency fixture",
            email=f"concurrency-{suffix}@example.com",
            password_hash=hash_password("a-long-fixture-passphrase"),
        )
        db.add(user)
        db.flush()
        uid = user.id
        db.add(AccountRecoveryKey(user_id=uid, token_hash=token_digest(key)))
        db.add(
            LoginSession(
                user_id=uid,
                token_hash=token_digest(secrets.token_urlsafe(32)),
                expires_at=utcnow() + timedelta(days=1),
            )
        )
        email = user.email
    barrier = Barrier(2)

    def reset():
        with SessionLocal() as db:
            barrier.wait(timeout=5)
            try:
                recover(
                    RecoveryInput(
                        email=email,
                        recovery_key=key,
                        new_password="a-new-fixture-passphrase",
                        confirm_password="a-new-fixture-passphrase",
                    ),
                    db,
                    Response(),
                )
                db.commit()
                return 200
            except HTTPException as error:
                db.rollback()
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(lambda _: reset(), range(2)))
    assert outcomes == [200, 401], outcomes
    with SessionLocal() as db:
        assert db.get(AccountRecoveryKey, uid).used_at is not None
        assert not list(db.scalars(select(LoginSession).where(LoginSession.user_id == uid)))
    token = secrets.token_urlsafe(32)
    with SessionLocal.begin() as db:
        db.add(
            LoginSession(user_id=uid, token_hash=token_digest(token), expires_at=utcnow() + timedelta(days=1))
        )
    tag = "academy_blocked_" + suffix
    owned_engine = create_engine(
        settings.database_url, connect_args={"application_name": tag}, hide_parameters=True
    )
    factory = sessionmaker(owned_engine)
    read_session = Event()

    @event.listens_for(owned_engine, "after_cursor_execute")
    def observe(conn, cursor, statement, params, context, many):
        if "FROM sessions" in statement:
            read_session.set()

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/fixture",
            "headers": [(b"cookie", f"{COOKIE}={token}".encode())],
        }
    )

    def queued_request():
        with factory() as db:
            try:
                current_user(request, db)
                db.commit()
                return 200
            except HTTPException as error:
                db.rollback()
                return error.status_code

    observed = False
    try:
        with ThreadPoolExecutor(max_workers=1) as pool, SessionLocal() as owner:
            owner.scalar(select(User).where(User.id == uid).with_for_update())
            future = pool.submit(queued_request)
            assert read_session.wait(5)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                owner.execute(text("SELECT pg_stat_clear_snapshot()"))
                observed = bool(
                    owner.scalar(
                        text(
                            "SELECT count(*) FROM pg_stat_activity WHERE application_name=:tag AND wait_event_type='Lock'"
                        ),
                        {"tag": tag},
                    )
                )
                if observed:
                    break
                time.sleep(0.02)
            assert observed, "The queued mutation must really wait for the locked user."
            owner.execute(delete(LoginSession).where(LoginSession.user_id == uid))
            owner.commit()
            queued_status = future.result(timeout=5)
            assert queued_status == 401, queued_status
    finally:
        owned_engine.dispose()
    print(
        json.dumps(
            {
                "concurrent_recovery_statuses": outcomes,
                "consumed_once": True,
                "all_sessions_revoked": True,
                "actual_user_lock_wait_observed": observed,
                "queued_revoked_session_status": queued_status,
                "scope": "Actual PostgreSQL competing recovery and post-lock authentication recheck; dedicated fixture account only.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
