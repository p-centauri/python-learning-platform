"""Implement the TODOs using the contract in README.md."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str

    def __post_init__(self) -> None:
        # Validate already-normalized values, including direct constructor calls.
        raise NotImplementedError("Validate task fields")


class TaskStore(Protocol):
    def add(self, task: Task) -> None: ...
    def all(self) -> tuple[Task, ...]: ...


class MemoryTaskStore:
    def __init__(self) -> None:
        # Allocate per-instance state here.
        pass

    def add(self, task: Task) -> None:
        raise NotImplementedError("Reject duplicate IDs and store tasks")

    def all(self) -> tuple[Task, ...]:
        raise NotImplementedError("Return an ordered snapshot")


def parse_task(payload: object) -> Task:
    raise NotImplementedError("Validate and normalize outside input")


class TaskService:
    def __init__(self, store: TaskStore) -> None:
        self._store = store

    def create(self, payload: object) -> Task:
        raise NotImplementedError("Parse before writing; propagate failures")

    def all(self) -> tuple[Task, ...]:
        raise NotImplementedError("Read through the injected store")
