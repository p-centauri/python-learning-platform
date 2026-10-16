## A test checks a promise

This is lesson 9 of 9. A test provides an input, runs real code and checks the expected behavior. The goal is to catch mistakes. A test that replaces the function itself with a fake answer does not show that the function works.

```python
import unittest

def category_name(text):
    cleaned = text.strip().lower()
    if not cleaned:
        raise ValueError("category cannot be empty")
    return cleaned

class CategoryTests(unittest.TestCase):
    def test_clean_name(self):
        self.assertEqual(category_name(" Food "), "food")

    def test_empty_name(self):
        with self.assertRaises(ValueError):
            category_name("   ")
```

Save this in a test file and run `python -m unittest discover -v`. `unittest` ships with Python. A test method starts with `test_`. `assertEqual` compares values; `assertRaises` checks the failure contract. A failing assertion is useful information, not a reason to delete the test.

## Guided practice

Change category_name so it forgets to strip whitespace. The clean-name test should fail. Restore the implementation, then add a test for `café`. This small deliberate mistake proves that a test can detect a particular bug; a green suite alone cannot prove that every important behavior is covered.

## Independent project: expense tracker

[Download the starter and acceptance tests](/api/projects/python-expenses/starter). The ZIP includes a complete command wrapper, sample CSV/JSON, an exact contract, public tests and three intentionally unfinished learner functions. Work in your own folder. The app does not execute your code or collect a coding grade.

Implement `parse_amount(text)`, `summarize_rows(rows)`, and `summarize_csv(path)` in `expenses.py`. Start with amounts, then category totals, then file handling. Use the examples from earlier lessons, but write and explain the integration yourself. The CLI reads one CSV path and prints one report with `row_count`, `total_cents` and `by_category`.

```sh
python -m unittest discover -s tests -v
python cli.py sample.csv
```

The supplied tests fail initially because the functions are unfinished. As you implement each promise, more tests should pass. Do not change expected results just to make a wrong implementation pass. Add your own regression tests for bugs you discover. Sample output is in `expected.json`; compare parsed JSON values rather than whitespace or key order.

## Explained approach, without the finished implementation

Convert amount text to integer cents using the exact format rule. Start each summary with a fresh count, total and category dictionary. For each valid record, normalize the category, parse the amount, and add its contribution once. Add record context to validation errors. Open and validate CSV in a with block, then feed its rows into the summary. Only the CLI prints the final JSON.

A reviewer should ask you to explain one invalid input, one quoted comma, one zero amount and two consecutive summary calls. Correctly handled empty input and fresh state matter as much as the happy path. The reference implementation used to verify the starter is not included in the learner download.

## Module finish check

Run the supplied tests, add at least three tests of your own, and demonstrate the command from a different folder. Review the checklist in [Projects](/projects#python-expenses). Its checkboxes record your own evidence; they are not an automatic pass or certification. Then take the [beginner Python assessment](/exams), which uses separate questions. If a topic is weak, return to its lesson before retaking the same bank.

Next learning work includes deeper object design, typing and intermediate Python. This foundation is complete for the expense-tracker contract, not proof that you know all of Python.

[Continue: text, time and debugging](/lessons/python-text-bytes)
