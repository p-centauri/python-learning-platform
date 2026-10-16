## Separate the reusable work from the command

This is lesson 8 of 9. A module is a Python file you can import. Put reusable functions in `expenses.py` and a thin command wrapper in `cli.py`. The wrapper reads arguments, calls your functions, then chooses what to print and which exit status to return.

```python
import argparse

def read_args(argv):
    parser = argparse.ArgumentParser(description="Summarize expense records")
    parser.add_argument("csv_path", help="UTF-8 CSV with category,amount header")
    return parser.parse_args(argv)

assert read_args(["sample.csv"]).csv_path == "sample.csv"
```

`argparse` provides a help page and rejects missing required arguments. The `argv` parameter lets tests pass a list directly. Real command-line code usually calls `parse_args()` without a list so it reads the process's arguments.

## Use the main guard

Put execution under `if __name__ == "__main__":`. The guarded code runs when you execute `python cli.py sample.csv`, but not when a test imports the module. Otherwise, importing your functions could unexpectedly read files or print a report.

The starter project's wrapper already handles command arguments and expected errors. You implement its calculation and CSV functions. Run `python cli.py --help` first; help should work even before your functions are implemented. Keep the working directory and the path to your CSV separate: a caller may run the script from a different folder using absolute paths.

## stdout, stderr and exit status

stdout carries the successful JSON report. stderr carries a short error message. Exit status 0 means success; the starter uses 2 for expected invalid input or file errors. Other nonzero statuses may indicate a programming bug. A message printed to stdout is not an error contract by itself: scripts often check the exit status and parse stdout automatically.

Wait until the complete input is validated before printing JSON. The wrapper should print exactly one JSON document on success, with no debugging lines before or after it. On failure, stdout stays empty. If you see NotImplementedError from the starter, that is an intentional reminder that the learner functions still need to be written, not an accepted handling of a bad CSV.

## Guided practice

Download the starter from the project link below. Run the help command and compare it with running the CLI without its required path. The first should succeed, while the second should explain the missing argument and exit nonzero. Read the wrapper and find its main guard.

## Independent task

Write a tiny separate CLI that accepts a name and prints one greeting. Put argument parsing in a function and guard program execution. Import that file from another script and verify that importing it does not print the greeting. Then return to the provided expense CLI instead of writing another incompatible interface.

## Check your work

You can run the expense command from another directory when given the script and CSV paths. Help is available, and imports do not start work. You understand why tests should call calculation functions directly while also testing the real command as a separate process.

[Download expense-tracker starter](/api/projects/python-expenses/starter)

[Next: tests and your expense-tracker project](/lessons/python-tests)
