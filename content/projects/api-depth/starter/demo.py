"""Actual installed loopback HTTP observations on an explicitly disposable PostgreSQL store."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from collections.abc import Iterator
import json
import os
from pathlib import Path
import socket
from threading import Thread
import time
import httpx
import uvicorn
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.pool import QueuePool
from academy_api_depth import create_app
from academy_api_depth.rehearsal import store
from academy_api_depth.support import sign
from academy_delivery_schema import inspect_state


@contextmanager
def serving(app: FastAPI) -> Iterator[str]:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(64)
    server = uvicorn.Server(
        uvicorn.Config(
            app, log_level="critical", access_log=False, lifespan="off", timeout_graceful_shutdown=2
        )
    )
    worker = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    worker.start()
    try:
        end = time.monotonic() + 5
        while not server.started:
            if not worker.is_alive() or time.monotonic() >= end:
                raise RuntimeError("local server startup failed")
            time.sleep(0.01)
        yield "http://127.0.0.1:" + str(listener.getsockname()[1])
    finally:
        server.should_exit = True
        worker.join(5)
        listener.close()
        if worker.is_alive():
            raise RuntimeError("local server did not finish")


def observe() -> dict[str, object]:
    token = "local_demo_token_12345"
    secret = b"d" * 32
    now = 1700000000
    body = b'{"version":1,"id":"a","revision":1,"value":0}'
    with store(os.environ["ACADEMY_API_TEST_DSN"]) as (_, engine, namespace):
        app = create_app(engine, {token: namespace}, {namespace: secret}, clock=lambda: now)
        with serving(app) as url, httpx.Client(base_url=url, timeout=5) as api:
            path = f"/v1/namespaces/{namespace}"
            auth = {"Authorization": "Bearer " + token}
            first = api.get(path + "/snapshot", headers=auth)
            tag = first.headers["etag"]
            cached = api.get(path + "/snapshot", headers={**auth, "If-None-Match": "W/" + tag})
            denied = api.get(path + "/snapshot", headers={"If-None-Match": "*"})
            forbidden = api.get("/v1/namespaces/other/snapshot", headers={**auth, "If-None-Match": "*"})

            def headers(delivery: str, payload: bytes, timestamp: int = now) -> dict[str, str]:
                return {
                    "Content-Type": "application/json",
                    "X-Delivery-ID": delivery,
                    "X-Signed-At": str(timestamp),
                    "X-Signature": sign(secret, namespace, delivery, str(timestamp), payload),
                }

            def send() -> tuple[int, bool]:
                with httpx.Client(base_url=url, timeout=5) as caller:
                    reply = caller.post(path + "/webhooks", headers=headers("d", body), content=body)
                    return reply.status_code, bool(reply.json()["duplicate"])

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(send) for _ in range(2)]
                duplicates = sorted(f.result(timeout=6) for f in futures)
            tamper = api.post(path + "/webhooks", headers=headers("bad", body), content=body + b" ")
            conflict = api.post(path + "/webhooks", headers=headers("d", body + b" "), content=body + b" ")
            stale = api.post(path + "/webhooks", headers=headers("old", body, now - 301), content=body)
            malformed = api.post(path + "/webhooks", headers=headers("invalid", b"{"), content=b"{")
            changed = api.get(path + "/snapshot", headers={**auth, "If-None-Match": tag})
            with engine.connect() as blocker, blocker.begin():
                blocker.execute(text("LOCK TABLE api_webhook_receipt IN ACCESS EXCLUSIVE MODE"))
                blocked = api.post(path + "/webhooks", headers=headers("retry", body), content=body)
            recovered = api.post(path + "/webhooks", headers=headers("retry", body), content=body)
            readiness = api.get("/ready").status_code
            old = api.get(f"/namespaces/{namespace}/readings", headers=auth)
        with engine.connect() as connection:
            receipts = connection.execute(text("SELECT count(*) FROM api_webhook_receipt")).scalar_one()
            facts = connection.execute(text("SELECT count(*) FROM feed_record")).scalar_one()
            outbox = connection.execute(text("SELECT count(*) FROM delivery_outbox")).scalar_one()
            server_version = int(connection.execute(text("SHOW server_version_num")).scalar_one())
        assert isinstance(engine.pool, QueuePool)
        return dict(
            schema="2026.10-api-depth-v1",
            transport="actual loopback TCP",
            head=list(inspect_state(engine).revisions),
            server_version=server_version,
            cache=dict(
                first=first.status_code,
                conditional=cached.status_code,
                empty_304=cached.content == b"",
                changed=changed.status_code,
                changed_tag=changed.headers["etag"] != tag,
                policy=first.headers["cache-control"],
                vary=first.headers["vary"],
            ),
            permission=dict(
                unauthenticated=denied.status_code,
                forbidden=forbidden.status_code,
                no_error_tag="etag" not in denied.headers and "etag" not in forbidden.headers,
            ),
            webhooks=dict(
                competing=duplicates,
                tamper=tamper.status_code,
                conflict=conflict.status_code,
                stale=stale.status_code,
                invalid=malformed.status_code,
                blocked=blocked.status_code,
                recovered=recovered.status_code,
                receipts=receipts,
                facts=facts,
                outbox=outbox,
            ),
            compatibility=dict(
                ready=readiness, old_read=old.status_code, old_policy=old.headers["cache-control"]
            ),
            checked_out=engine.pool.checkedout(),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = observe()
    output = json.dumps(report, indent=2) + "\n"
    args.output.write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
