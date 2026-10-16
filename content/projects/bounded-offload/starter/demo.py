"""Run as a saved script; the startup guard is required for spawned processes."""
import json
import os
from pathlib import Path
import sys
import sysconfig
from tempfile import TemporaryDirectory

from academy_bounded_offload import Job, run_batch

def main() -> None:
    with TemporaryDirectory() as directory:
        jobs: list[Job] = []
        for name, value in [("api", 5), ("worker", 10)]:
            path = Path(directory) / (name + ".txt")
            path.write_bytes(str(value).encode("ascii") + b"\n")
            jobs.append(Job(name, str(path)))
        thread_results = run_batch(jobs, mode="thread")
        process_results = run_batch(jobs, mode="process")
        assert all(r.file_closed for r in thread_results + process_results)
        assert all(r.worker_pid == os.getpid() for r in thread_results)
        assert all(r.worker_pid != os.getpid() for r in process_results)
        assert [r.id for r in process_results] == ["api", "worker"]
        probe = getattr(sys, "_is_gil_enabled", None)
        print(json.dumps({
            "thread_total": sum(r.value for r in thread_results),
            "process_total": sum(r.value for r in process_results),
            "worker_files_closed": True, "process_boundary": True,
            "free_threaded_build": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
            "gil_enabled": probe() if callable(probe) else "unavailable",
        }))

if __name__ == "__main__":
    main()
