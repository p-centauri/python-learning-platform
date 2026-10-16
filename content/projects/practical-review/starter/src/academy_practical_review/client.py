import json
import re
import httpx
from academy_ingestion_service import Cursor, Datum
from academy_ingestion_service.contracts import field
from .operations import decode_page
from .support import unique


async def read_all(client: httpx.AsyncClient, namespace: str, token: str) -> tuple[Datum, ...]:
    """Borrow trusted configured client. At most eight scoped pages; close streams on cancellation."""
    field(namespace)
    if type(token) is not str or re.fullmatch(r"[A-Za-z0-9_-]{16,64}", token) is None:
        raise ValueError("invalid configured credential")
    saved: list[Datum] = []
    after: Cursor | None = None
    for _ in range(8):
        params = {"limit": "32"}
        if after is not None:
            params.update(after_id=after.id, after_revision=str(after.revision))
        async with client.stream(
            "GET",
            f"/namespaces/{namespace}/readings",
            params=params,
            headers={"Authorization": "Bearer " + token},
            follow_redirects=False,
        ) as response:
            if (
                response.status_code != 200
                or response.headers.get("content-type", "").split(";")[0].strip().lower()
                != "application/json"
            ):
                raise ValueError("service response refused")
            chunks = bytearray()
            async for chunk in response.aiter_bytes():
                if len(chunks) + len(chunk) > 8192:
                    raise ValueError("page body exceeds bound")
                chunks.extend(chunk)
            payload: object = json.loads(bytes(chunks), object_pairs_hook=unique)
            page = decode_page(payload)
        if (
            after is not None
            and page.items
            and (page.items[0].id, page.items[0].revision) <= (after.id, after.revision)
        ):
            raise ValueError("page did not advance")
        saved.extend(page.items)
        if page.next_cursor is None:
            return tuple(saved)
        after = page.next_cursor
    raise ValueError("page count exceeds bound")
