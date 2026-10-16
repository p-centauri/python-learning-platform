# Typed task inbox

Build a small service with clear ownership and replaceable storage. This is an in-memory learning project, not a database service. Use Python 3.13+ and its standard library at runtime. The only extra development tool is mypy 2.3.1. There are intentional `NotImplementedError` placeholders in `inbox.py`; implement them without weakening the public interfaces or tests.

## Setup and commands

Extract the ZIP, enter `task-inbox`, create/activate your own virtual environment, then run:

```sh
python -m pip install mypy==2.3.1
python -m unittest discover -s tests -v
python -m mypy
python demo.py
```

On macOS/Linux, create it with `python3 -m venv .venv` and activate with `source .venv/bin/activate`. On Windows use `py -3 -m venv .venv` and `.venv\Scripts\Activate.ps1` in PowerShell. Runtime tests need no third-party libraries; mypy needs installation separately. The supplied configuration checks the implementation, demo and typed usage fixture. A clean type check on the unfinished starter is possible and does not mean the project works.

## Exact contract

- `Task(task_id: str, title: str)` is a frozen dataclass. Both fields must be nonempty strings already equal to their `strip()` result. Direct construction rejects blank, untrimmed or non-string fields with `ValueError`; it does not silently normalize. Equal fields give equal task values. Normal field reassignment is blocked. Fields contain strings, not mutable nested values.
- `parse_task(payload: object) -> Task` accepts a dictionary with exactly `task_id` and `title`. Both values must be strings. Strip leading/trailing whitespace, reject resulting empty strings with `ValueError`, then construct a Task. Reject missing/extra keys and all other input shapes, including JSON text that has not been parsed. Do not coerce numbers/bools or mutate the dictionary. Preserve case, internal whitespace and Unicode spelling. IDs are case-sensitive.
- `TaskStore` is a protocol with `add(task: Task) -> None` and `all() -> tuple[Task, ...]`. It accepts validated Task objects; it does not validate raw input. It promises insertion order, rejection of duplicate IDs with `ValueError` before mutation, and snapshots that do not change when future items are added.
- `MemoryTaskStore` implements those operations without needing to inherit the protocol. Each instance owns separate state. Duplicate titles with different IDs are allowed. A rejected duplicate ID must leave the old task and order intact. Empty `all()` returns `()`.
- `TaskService(store: TaskStore)` keeps the caller-supplied store. `create(payload: object) -> Task` parses first, writes exactly once only after validation, and returns the accepted Task. Invalid input performs no write. Propagate storage exceptions unchanged; do not return success or retry automatically. `all()` reads through the same injected store.
- `demo.py` prints one JSON array and a newline on stdout after successful completion: `[{"task_id": "t1", "title": "Read traceback"}, {"task_id": "t2", "title": "Write regression test"}]`. Importing inbox or demo does not print or run the demo. The command works when invoked by absolute path from another directory.

No disk/network persistence, concurrency guarantee, batch transaction or retries are promised. Two services given the same store deliberately share its state. A separate store means separate state. Python underscore conventions and frozen dataclasses are design aids, not security boundaries.

## Work in stages

1. Validate the Task value and implement parsing. Test direct construction as well as raw dictionaries.
2. Implement the memory store. Prove separate state, stable order, duplicates and old snapshots.
3. Wire the service to the injected protocol. Use a recording fake and a failing fake to exercise the real service. Do not mock the method under test.
4. Run the runtime tests and mypy independently. Temporarily change `RecordingStore.all` in `typecheck_examples.py` to return `tuple[str, ...]` and return a string tuple. Run mypy, record the incompatible-interface diagnostic, then restore the fixture and run it again.

Add at least two regression tests of your own. Submit a short design note to a human reviewer: responsibility of each class, validation boundary, who owns state, how the protocol helps, and why types do not prove persistence or input validity. Record commands and results, including the intentional type failure. The academy's checkboxes are self-report; the app does not collect or execute your code, ingest results or award practical mastery.
