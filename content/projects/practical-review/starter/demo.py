"""Installed loopback service + frozen reporting/profile/process evidence; guarded main only."""

import argparse
import asyncio
from dataclasses import asdict
from importlib.metadata import version
import json
import os
from pathlib import Path
import httpx
from sqlalchemy import text
from sqlalchemy.pool import QueuePool
from academy_ingestion_service import Datum, create_app, check_migrations
from academy_measured_cache import CacheKey, LruCache, legacy_get
from academy_practical_review import prepare, read_all
from academy_practical_review.evidence import compare, review_case
from academy_practical_review.jobs import observe_jobs
from academy_practical_review.rehearsal import store
from academy_practical_review.server import serving
import warnings


def observe(case_path: Path) -> dict[str, object]:
    namespace = "review"
    token = "local_demo_token_12345"
    rows = tuple(
        Datum("item-" + str(i).zfill(2), revision, 0 if i == 0 and revision == 4 else i * 10 + revision)
        for i in range(32)
        for revision in range(1, 5)
    )
    with store(os.environ["ACADEMY_PRACTICAL_DSN"]) as engine:
        with (
            serving(create_app(engine, {token: namespace})) as url,
            httpx.Client(base_url=url, timeout=5) as caller,
        ):
            auth = {"Authorization": "Bearer " + token}
            path = f"/namespaces/{namespace}/readings"
            inserted = []
            for offset in (0, 64):
                reply = caller.post(
                    path, headers=auth, json={"items": [asdict(row) for row in rows[offset : offset + 64]]}
                )
                assert reply.status_code == 200
                inserted.append(reply.json())
            duplicate = caller.post(path, headers=auth, json={"items": [asdict(rows[0])]})
            conflict = caller.post(
                path,
                headers=auth,
                json={
                    "items": [dict(id="new", revision=1, value=5), dict(id=rows[0].id, revision=1, value=999)]
                },
            )
            denied = caller.get(path).status_code
            forbidden = caller.get("/namespaces/other/readings", headers=auth).status_code
            ready = caller.get("/ready").status_code
            with engine.connect() as connection:
                before = tuple(
                    connection.execute(text("SELECT * FROM feed_record ORDER BY id,revision")).all()
                )
            responses: list[httpx.Response] = []

            async def collect() -> tuple[Datum, ...]:
                async def observe_response(response: httpx.Response) -> None:
                    responses.append(response)

                async with httpx.AsyncClient(
                    base_url=url, timeout=5, event_hooks={"response": [observe_response]}
                ) as client:
                    return await read_all(client, namespace, token)

            observed = asyncio.run(collect())
            assert observed == rows and all(response.is_closed for response in responses)
        items = prepare(namespace, observed)
        requests = tuple(range(8)) * 16 + tuple(range(8, 32))
        measurements = compare(items, requests)
        cyclic = compare(items, tuple(range(32)) * 2)
        workers = observe_jobs(items)
        # Preserve an existing deprecated caller; do not erase its warning/identity behavior.
        cache = LruCache[Datum](1)
        key = CacheKey(namespace, rows[0].id, rows[0].revision)
        first = cache.get_or_compute(key, lambda: rows[0])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            old = legacy_get(cache, key, lambda: rows[1])
        assert old is first and len(caught) == 1
        cache.clear()
        case = review_case(case_path)
        check_migrations(engine)
        with engine.connect() as connection:
            unchanged = (
                tuple(connection.execute(text("SELECT * FROM feed_record ORDER BY id,revision")).all())
                == before
            )
            head = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            server = int(connection.execute(text("SHOW server_version_num")).scalar_one())
        assert isinstance(engine.pool, QueuePool)
        return dict(
            schema="2026.10-practical-review-v1",
            transport="actual loopback TCP",
            head=head,
            server_version=server,
            workload=dict(
                source_rows=128,
                ids=32,
                revisions=4,
                selected_latest=32,
                requests=152,
                hot_ids=8,
                hot_repeats=16,
                cold_requests=24,
            ),
            service=dict(
                inserted=inserted,
                duplicate=duplicate.json(),
                conflict=conflict.status_code,
                missing=denied,
                forbidden=forbidden,
                ready=ready,
                read_pages=len(responses),
                responses_closed=all(r.is_closed for r in responses),
                facts_unchanged=unchanged,
            ),
            measured=measurements,
            cyclic=cyclic,
            workers=workers,
            compatibility=dict(
                legacy_same_object=old is first,
                legacy_warnings=len(caught),
                cache_cleared=cache.info().size == 0,
            ),
            reviewer_case=case,
            checked_out=engine.pool.checkedout(),
            versions={
                name: version(name)
                for name in (
                    "academy-practical-review-lab",
                    "academy-ingest-lab",
                    "academy-feed-objects-lab",
                    "academy-typed-transforms-lab",
                    "academy-resource-scopes-lab",
                    "academy-bounded-offload-lab",
                    "academy-measured-cache-lab",
                    "academy-ingestion-service-lab",
                )
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--case", required=True, type=Path)
    args = parser.parse_args()
    report = observe(args.case)
    output = json.dumps(report, indent=2) + "\n"
    args.output.write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
