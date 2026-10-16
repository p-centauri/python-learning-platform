from pathlib import Path
from tempfile import TemporaryDirectory
from academy_bounded_offload import Job, run_batch
from academy_resource_scopes import Resource, current_request, owned_resources, request_scope
from .contracts import Item


def observe_jobs(items: tuple[Item, ...]) -> dict[str, object]:
    """Actual earlier thread/spawn worker APIs on owned files; no shared Engine in workers."""
    events: list[str | None] = []
    closed: list[bool] = []

    def factory() -> Resource[tuple[Job, ...]]:
        directory = TemporaryDirectory(prefix="academy-review-jobs-")
        try:
            jobs: list[Job] = []
            for item in items[:8]:
                path = Path(directory.name) / item.datum.id
                path.write_bytes(str(item.datum.value).encode("ascii") + b"\n")
                jobs.append(Job(item.datum.id, str(path)))

            def close() -> None:
                events.append(current_request())
                directory.cleanup()
                closed.append(not Path(directory.name).exists())

            return Resource(tuple(jobs), close)
        except BaseException:
            directory.cleanup()
            raise

    with request_scope("review-jobs"), owned_resources([factory]) as batches:
        threaded = run_batch(batches[0], mode="thread", workers=2, pending=2, limit=8)
        spawned = run_batch(batches[0], mode="process", workers=2, pending=2, limit=8)
        same = tuple((r.id, r.value) for r in threaded) == tuple((r.id, r.value) for r in spawned)
        files_closed = all(r.file_closed for r in (*threaded, *spawned))
    return dict(
        jobs=len(threaded),
        equivalent=same,
        files_closed=files_closed,
        context_restored=current_request() is None,
        cleanup_labels=events,
        directories_removed=closed,
        thread_pids=sorted({r.worker_pid for r in threaded}),
        spawn_pids=sorted({r.worker_pid for r in spawned}),
    )
