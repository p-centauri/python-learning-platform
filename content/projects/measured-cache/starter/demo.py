"""Trusted toy workload; raw observations are evidence, never timing pass/fail gates."""

import argparse
import cProfile
from io import StringIO
import json
from pathlib import Path
import platform
import pstats
from time import process_time_ns
import tracemalloc

from academy_measured_cache import CacheKey, LruCache, sample

KEYS = tuple(CacheKey("demo", "item-" + str(n % 4)) for n in range(32))


def compute(key: CacheKey) -> int:
    return sum((ord(letter) + offset) ** 2 for offset in range(128) for letter in key.id)


def baseline() -> tuple[int, int]:
    return sum(compute(key) for key in KEYS), len(KEYS)


def cached() -> tuple[int, int, int]:
    cache = LruCache[int](capacity=4)
    total = 0
    for key in KEYS:
        total += cache.get_or_compute(key, lambda: compute(key))
    info = cache.info()
    return total, info.misses, info.hits


def memory_observation() -> dict[str, int]:
    # This standalone script owns a fresh tracer. Do not stop an application's borrowed tracer.
    tracemalloc.start(1)
    try:
        before = tracemalloc.get_traced_memory()[0]
        cache = LruCache[bytes](capacity=4)
        for key in KEYS[:4]:
            cache.get_or_compute(key, lambda: bytes(4096))
        filled, peak = tracemalloc.get_traced_memory()
        cache.clear()
        after = tracemalloc.get_traced_memory()[0]
        return {"before": before, "filled": filled, "after_clear": after, "peak": peak}
    finally:
        tracemalloc.stop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    wall_base = sample(baseline)
    wall_cache = sample(cached)
    cpu_base = sample(baseline, clock=process_time_ns)
    cpu_cache = sample(cached, clock=process_time_ns)
    assert wall_base.last[0] == wall_cache.last[0] == cpu_base.last[0] == cpu_cache.last[0]
    profiler = cProfile.Profile()
    profiler.runcall(baseline)
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("cumulative")
    stats.print_stats(8)
    report = {
        "schema": "2026.10-measurement-v1",
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "workload_items": len(KEYS),
        "distinct_keys": 4,
        "repeats": 3,
        "cache_capacity": 4,
        "cache_state": "fresh per repetition",
        "variant_order": ["baseline-wall", "cached-wall", "baseline-cpu", "cached-cpu"],
        "timings_ns": {
            "baseline_wall": wall_base.elapsed_ns,
            "cached_wall": wall_cache.elapsed_ns,
            "baseline_cpu": cpu_base.elapsed_ns,
            "cached_cpu": cpu_cache.elapsed_ns,
        },
        "equivalent_total": wall_base.last[0],
        "baseline_computations": wall_base.last[1],
        "cached_computations": wall_cache.last[1],
        "cached_hits": wall_cache.last[2],
        "memory_traced_bytes": memory_observation(),
        "profile_functions": len(profiler.getstats()),
        "profile_text": stream.getvalue(),
        "limits": "Sequential toy samples; instrumentation is separate; no speedup, RSS, freshness or thread-safety claim.",
    }
    output = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(output + "\n")
    print(output)


if __name__ == "__main__":
    main()
