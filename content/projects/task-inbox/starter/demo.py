"""Run from any directory: python /path/to/task-inbox/demo.py."""

import json
from dataclasses import asdict
from inbox import MemoryTaskStore, TaskService


def main() -> None:
    service = TaskService(MemoryTaskStore())
    service.create({"task_id": " t1 ", "title": " Read traceback "})
    service.create({"task_id": "t2", "title": "Write regression test"})
    print(json.dumps([asdict(task) for task in service.all()], ensure_ascii=False))


if __name__ == "__main__":
    main()
