import cProfile
from dataclasses import asdict
from io import StringIO
import json
from pathlib import Path
import platform
import pstats
from time import process_time_ns
import tracemalloc
from academy_measured_cache import sample
from academy_ingestion_service import Datum
from .contracts import Analysis, Item
from .operations import analyse, prepare
from .support import unique


def compare(items: tuple[Item, ...], requests: tuple[int, ...]) -> dict[str, object]:
    """Owned standalone profiling of frozen values; never stop a borrowed allocation tracer."""
    if tracemalloc.is_tracing():
        raise RuntimeError("profiling requires an unowned tracer")

    def baseline() -> Analysis:
        return analyse(items, requests, cached=False)

    def candidate() -> Analysis:
        return analyse(items, requests, cached=True)

    samples = {
        "baseline_wall": sample(baseline),
        "cached_wall": sample(candidate),
        "baseline_cpu": sample(baseline, clock=process_time_ns),
        "cached_cpu": sample(candidate, clock=process_time_ns),
    }
    before = samples["baseline_wall"].last
    for measured in samples.values():
        if measured.last.snapshot != before.snapshot or measured.last.fingerprints != before.fingerprints:
            raise ValueError("report outputs changed")
    profiles: dict[str, object] = {}
    memory: dict[str, object] = {}
    for name, work in (("baseline", baseline), ("cached", candidate)):
        profiler = cProfile.Profile()
        profiler.runcall(work)
        stream = StringIO()
        pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("cumulative").print_stats(12)
        calls = sum(
            entry.callcount
            for entry in profiler.getstats()
            if not isinstance(entry.code, str) and entry.code.co_name == "fingerprint"
        )
        profiles[name] = dict(
            fingerprint_calls=calls, functions=len(profiler.getstats()), text=stream.getvalue()
        )
        tracemalloc.start(1)
        try:
            result = work()
            retained, peak = tracemalloc.get_traced_memory()
            del result
            after = tracemalloc.get_traced_memory()[0]
            memory[name] = dict(retained=retained, peak=peak, after_release=after)
        finally:
            tracemalloc.stop()
    cached = samples["cached_wall"].last
    return dict(
        python=platform.python_version(),
        implementation=platform.python_implementation(),
        platform=platform.platform(),
        scope="frozen service values; synthetic 128-round fingerprint CPU component",
        repeats=3,
        cache_capacity=8,
        cache_state="fresh per invocation",
        variant_order=list(samples),
        equivalent=True,
        items=len(items),
        requests=len(requests),
        baseline_computations=before.computations,
        cached_computations=cached.computations,
        cached_hits=cached.hits,
        cache_size=cached.cache_size,
        timings_ns={name: measured.elapsed_ns for name, measured in samples.items()},
        profiles=profiles,
        traced_python_bytes=memory,
        limits="No speed threshold, RSS, production workload, concurrent cache, freshness or end-to-end throughput claim.",
    )


def review_case(path: Path) -> dict[str, object]:
    """Read only bounded JSON data, never Python/importable submissions. Originality needs a reviewer."""
    with path.open("rb") as stream:
        raw = stream.read(8193)
    if len(raw) > 8192:
        raise ValueError("review case exceeds bound")
    payload = json.loads(raw, object_pairs_hook=unique)
    if type(payload) is not dict or set(payload) != {
        "case_id",
        "namespace",
        "purpose",
        "rows",
        "requests",
        "expected_latest",
        "expected_computations",
    }:
        raise ValueError("invalid review case")
    if type(payload["purpose"]) is not str or not 1 <= len(payload["purpose"].strip()) <= 1000:
        raise ValueError("explain the independent case")
    if type(payload["case_id"]) is not str or not 1 <= len(payload["case_id"]) <= 32:
        raise ValueError("invalid case id")
    rows = payload["rows"]
    if type(rows) is not list or len(rows) > 256:
        raise ValueError("invalid case rows")
    saved: list[Datum] = []
    for row in rows:
        if type(row) is not dict or set(row) != {"id", "revision", "value"}:
            raise ValueError("invalid case row")
        saved.append(Datum(row["id"], row["revision"], row["value"]))
    if type(payload["requests"]) is not list:
        raise ValueError("invalid case requests")
    items = prepare(payload["namespace"], saved)
    before = analyse(items, tuple(payload["requests"]))
    after = analyse(items, tuple(payload["requests"]), cached=True)
    expected = payload["expected_latest"]
    if type(expected) is not list or len(expected) > 64:
        raise ValueError("invalid expected latest rows")
    for row in expected:
        if type(row) is not dict or set(row) != {"id", "revision", "value"}:
            raise ValueError("invalid expected row")
        Datum(row["id"], row["revision"], row["value"])
    counts = payload["expected_computations"]
    if (
        type(counts) is not dict
        or set(counts) != {"baseline", "cached"}
        or any(type(v) is not int or not 0 <= v <= 256 for v in counts.values())
    ):
        raise ValueError("invalid expected computations")
    latest = [asdict(item.datum) for item in items]
    if (
        latest != expected
        or counts != dict(baseline=before.computations, cached=after.computations)
        or before.fingerprints != after.fingerprints
        or before.snapshot != after.snapshot
    ):
        raise ValueError("case expectation mismatch")
    return dict(
        case_id=payload["case_id"],
        purpose=payload["purpose"],
        latest=latest,
        computations=counts,
        equivalent=True,
        originality="requires manual review",
    )
