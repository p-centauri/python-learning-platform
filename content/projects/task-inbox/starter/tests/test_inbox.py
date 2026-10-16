"""Public behavioral tests. Add your own edge cases too."""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from inbox import MemoryTaskStore, Task, TaskService, parse_task


class RecordingStore:
    def __init__(self):
        self.writes = []

    def add(self, task):
        self.writes.append(task)

    def all(self):
        return tuple(self.writes)


class InboxTests(unittest.TestCase):
    def test_task_value_and_frozen_fields(self):
        task = Task("t1", "Read")
        self.assertEqual(task, Task("t1", "Read"))
        self.assertNotEqual(task, Task("t2", "Read"))
        with self.assertRaises(FrozenInstanceError):
            task.title = "Changed"

    def test_direct_construction_rejects_invalid_fields(self):
        for value in [None, 3, True, "", " ", " x", "x "]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Task(value, "Read")
                with self.assertRaises(ValueError):
                    Task("t1", value)

    def test_parse_normalizes_without_mutating_input(self):
        raw = {"task_id": " T1 ", "title": " Read  Café \n"}
        self.assertEqual(parse_task(raw), Task("T1", "Read  Café"))
        self.assertEqual(raw, {"task_id": " T1 ", "title": " Read  Café \n"})

    def test_parse_rejects_shapes_and_keys(self):
        for value in [
            None,
            [],
            "{}",
            7,
            {},
            {"task_id": "t1"},
            {"task_id": "t1", "title": "Read", "extra": 1},
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_task(value)

    def test_parse_rejects_bad_field_values(self):
        for key in ["task_id", "title"]:
            for value in [True, 1, 2.5, None, [], "", " \t"]:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    parse_task({"task_id": "t1", "title": "Read", key: value})

    def test_stores_own_separate_state(self):
        one, two = MemoryTaskStore(), MemoryTaskStore()
        self.assertEqual(one.all(), ())
        one.add(Task("t1", "Read"))
        self.assertEqual(two.all(), ())
        self.assertEqual(one.all(), (Task("t1", "Read"),))

    def test_snapshots_order_and_duplicate_titles(self):
        store = MemoryTaskStore()
        first, second = Task("z", "Read"), Task("a", "Read")
        store.add(first)
        before = store.all()
        store.add(second)
        self.assertIsInstance(before, tuple)
        self.assertEqual(before, (first,))
        self.assertEqual(store.all(), (first, second))

    def test_duplicate_id_preserves_old_value(self):
        store = MemoryTaskStore()
        store.add(Task("t1", "Original"))
        with self.assertRaises(ValueError):
            store.add(Task("t1", "Replacement"))
        self.assertEqual(store.all(), (Task("t1", "Original"),))
        store.add(Task("T1", "Case matters"))
        self.assertEqual(len(store.all()), 2)

    def test_service_uses_injected_store_once(self):
        store = RecordingStore()
        service = TaskService(store)
        accepted = service.create({"task_id": " t1 ", "title": " Read "})
        self.assertEqual(accepted, Task("t1", "Read"))
        self.assertEqual(store.writes, [accepted])
        self.assertEqual(service.all(), (accepted,))
        store.add(Task("t2", "Added outside service"))
        self.assertEqual(len(service.all()), 2)

    def test_invalid_input_never_writes(self):
        store = RecordingStore()
        service = TaskService(store)
        for payload in [None, {"task_id": "t1", "title": " "}]:
            with self.assertRaises(ValueError):
                service.create(payload)
        self.assertEqual(store.writes, [])

    def test_storage_failure_propagates_without_retry(self):
        error = RuntimeError("storage unavailable")

        class FailingStore(RecordingStore):
            def add(self, task):
                self.writes.append(task)
                raise error

        store = FailingStore()
        with self.assertRaises(RuntimeError) as caught:
            TaskService(store).create({"task_id": "t1", "title": "Read"})
        self.assertIs(caught.exception, error)
        self.assertEqual(len(store.writes), 1)

    def test_two_services_can_deliberately_share(self):
        store = MemoryTaskStore()
        first, second = TaskService(store), TaskService(store)
        first.create({"task_id": "t1", "title": "Read"})
        self.assertEqual(second.all(), (Task("t1", "Read"),))
        with self.assertRaises(ValueError):
            second.create({"task_id": " t1 ", "title": "Duplicate"})
        self.assertEqual(first.all(), (Task("t1", "Read"),))

    def test_demo_from_another_directory(self):
        script = Path(__file__).resolve().parents[1] / "demo.py"
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run(
                [sys.executable, str(script)], cwd=directory, capture_output=True, text=True, timeout=5
            )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, "")
        self.assertEqual(
            json.loads(run.stdout),
            [
                {"task_id": "t1", "title": "Read traceback"},
                {"task_id": "t2", "title": "Write regression test"},
            ],
        )

    def test_imports_are_quiet(self):
        run = subprocess.run(
            [sys.executable, "-c", "import inbox; import demo"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertEqual(run.stderr, "")


if __name__ == "__main__":
    unittest.main()
