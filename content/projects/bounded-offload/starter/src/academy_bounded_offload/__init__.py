"""Local authored offload exercise. Import creates no pool or thread."""
from .contracts import Job, Outcome
from .offload import collect_ordered, read_job, run_batch

__all__ = ["Job", "Outcome", "collect_ordered", "read_job", "run_batch"]
