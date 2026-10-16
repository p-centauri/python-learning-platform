import asyncio
from collections.abc import Sequence
import math

from .models import MAX_SOURCES, BatchReport, ConfigError, FeedError, Opener, Source, validate_source


async def ingest(
    sources: Sequence[Source],
    *,
    opener: Opener,
    workers: int = 2,
    queue_size: int = 2,
    timeout: float = 1.0,
) -> BatchReport:
    if (
        not isinstance(sources, Sequence)
        or isinstance(sources, (str, bytes))
        or len(sources) > MAX_SOURCES
        or type(workers) is not int
        or not 1 <= workers <= 4
        or type(queue_size) is not int
        or not 1 <= queue_size <= 16
        or type(timeout) not in (int, float)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 30
    ):
        raise ConfigError("Invalid job configuration")
    snapshot: list[Source] = []
    for source in sources:
        if len(snapshot) >= MAX_SOURCES:
            raise ConfigError("Invalid job configuration")
        validate_source(source)
        snapshot.append(source)
    configured = tuple(snapshot)
    if len({source.label for source in configured}) != len(configured):
        raise ConfigError("Source labels must be unique")
    if not configured:
        return {"sources": 0, "count": 0, "total": 0}
    queue: asyncio.Queue[Source | None] = asyncio.Queue(maxsize=queue_size)
    results: dict[str, tuple[int, int]] = {}

    async def produce() -> None:
        for source in configured:
            await queue.put(source)
        for _ in range(workers):
            await queue.put(None)

    async def consume() -> None:
        while True:
            source = await queue.get()
            try:
                if source is None:
                    return
                count = total = 0
                async with opener(source) as records:
                    async for record in records:
                        count += 1
                        total += record.value
                # Publish this source's aggregate only after its owner closes.
                results[source.label] = (count, total)
            finally:
                queue.task_done()

    async with asyncio.timeout(float(timeout)):
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(consume()) for _ in range(workers)]
            group.create_task(produce())
    if any(task.cancelled() for task in tasks) or len(results) != len(configured):
        raise FeedError("Incomplete batch")
    return {
        "sources": len(configured),
        "count": sum(count for count, _ in results.values()),
        "total": sum(total for _, total in results.values()),
    }
