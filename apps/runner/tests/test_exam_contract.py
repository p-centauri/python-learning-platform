"""A frozen exam cannot silently use changed private execution cases."""

from copy import deepcopy
from hashlib import sha256
import json
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from pydantic import ValidationError
from runner.main import ExamRunInput, exam_run, repair_definition


class ExamContractTests(unittest.TestCase):
    def payload(self, **changes):
        exam = repair_definition()
        digest = sha256(
            json.dumps(exam["execution"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return ExamRunInput(
            **{
                "exam_id": exam["id"],
                "version": exam["version"],
                "execution_digest": digest,
                "code": "def repair(case): return {}",
                **changes,
            }
        )

    def test_fixed_contract_is_selected_and_changes_fail_before_execution(self):
        exam = repair_definition()
        with patch("runner.main.run_definition", return_value={"status": "fixture"}) as execute:
            self.assertEqual(exam_run(self.payload()), {"status": "fixture"})
            execute.assert_called_once_with("def repair(case): return {}", exam["execution"])
        for changes in [{"exam_id": "missing"}, {"version": "changed"}, {"execution_digest": "0" * 64}]:
            with patch("runner.main.run_definition") as execute:
                with self.assertRaises(HTTPException) as error:
                    exam_run(self.payload(**changes))
                self.assertEqual(error.exception.status_code, 409)
                execute.assert_not_called()
        changed = deepcopy(exam)
        changed["execution"]["tests"][0]["expected"] = {"changed": True}
        payload = self.payload()
        with (
            patch("runner.main.repair_definition", return_value=changed),
            patch("runner.main.run_definition") as execute,
        ):
            with self.assertRaises(HTTPException) as error:
                exam_run(payload)
            self.assertEqual(error.exception.status_code, 409)
            execute.assert_not_called()

    def test_code_limits_and_caller_supplied_contracts_are_rejected(self):
        for changes in [{"code": " "}, {"code": "é" * 9000}, {"tests": []}, {"execution_digest": "short"}]:
            with self.assertRaises(ValidationError):
                self.payload(**changes)
