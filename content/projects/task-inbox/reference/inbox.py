"""Maintainer reference; never included in the learner download."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str

    def __post_init__(self) -> None:
        for name, value in (("task_id", self.task_id), ("title", self.title)):
            if not isinstance(value, str) or not value or value != value.strip():
                raise ValueError(f"{name} must be nonblank, trimmed text")


class TaskStore(Protocol):
    def add(self, task: Task) -> None: ...
    def all(self) -> tuple[Task, ...]: ...


class MemoryTaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> None:
        if task.task_id in self._tasks:
            raise ValueError("duplicate task_id")
        self._tasks[task.task_id] = task

    def all(self) -> tuple[Task, ...]:
        return tuple(self._tasks.values())


def parse_task(payload: object) -> Task:
    if not isinstance(payload, dict) or set(payload) != {"task_id", "title"}:
        raise ValueError("expected exactly task_id and title")
    task_id = payload["task_id"]
    title = payload["title"]
    if not isinstance(task_id, str) or not isinstance(title, str):
        raise ValueError("task_id and title must be text")
    return Task(task_id.strip(), title.strip())


class TaskService:
    def __init__(self, store: TaskStore) -> None:
        self._store = store

    def create(self, payload: object) -> Task:
        task = parse_task(payload)
        self._store.add(task)
        return task

    def all(self) -> tuple[Task, ...]:
        return self._store.all()
