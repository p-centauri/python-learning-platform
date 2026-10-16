"""Positive protocol example. Checked statically; no top-level side effects."""

from inbox import Task, TaskService, TaskStore


class RecordingStore:
    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def add(self, task: Task) -> None:
        self.tasks.append(task)

    def all(self) -> tuple[Task, ...]:
        return tuple(self.tasks)


def example() -> tuple[Task, ...]:
    # No inheritance: compatible operations are sufficient.
    store: TaskStore = RecordingStore()
    service = TaskService(store)
    service.create({"task_id": "t1", "title": "Read docs"})
    return service.all()
