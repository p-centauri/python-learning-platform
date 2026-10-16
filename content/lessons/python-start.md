## What you are building

This is lesson 1 of 9 in **Python foundations: build an expense tracker**. By the end, you will read expenses from CSV, calculate category totals and print a JSON report from a command-line program. No web framework or paid service is needed. The module teaches the Python needed for this small project; it is not the entire beginner-to-expert curriculum.

A terminal runs commands. The Python interpreter runs Python instructions. A `.py` file keeps those instructions so you can run them again. If you know JavaScript, the interpreter plays a similar role to Node.js, but Python has its own syntax and package tools.

## Small example

Create an empty project folder and put this in `hello.py`:

```python
name = "Ali"
expenses = 3
print(f"Hello {name}: {expenses} expenses to review")
```

The `f` before the string lets braces insert values. Save the file, open a terminal in its folder and run `python3 hello.py` on macOS/Linux. On Windows, use `py hello.py`. You should see `Hello Ali: 3 expenses to review`. If the interpreter command is missing, install Python 3.13 or newer using the official Python downloads and setup instructions linked below.

## Keep one environment per project

Create a virtual environment using the Python version you intend to use. On macOS/Linux:

```sh
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python hello.py
python -m pip --version
```

On Windows PowerShell, use `py -3 -m venv .venv` and then `.\.venv\Scripts\python.exe hello.py`. You can use this explicit interpreter path without changing PowerShell's activation policy. The project only uses the standard library, so there are no packages to install yet.

An environment keeps project packages separate. It does not make unsafe code safe. `python -m pip` runs pip using that specific Python, helping avoid installing packages into the wrong environment. Keep your own source files outside `.venv`; the environment can be recreated, while your code should be saved in version control.

## Guided practice

Change the name and expense count. Run the saved file again. If the old message appears, check that you saved the file and that your terminal points to the correct folder. Use `python -c "import sys; print(sys.executable)"` to see which interpreter is running. On Windows, replace `python` with your environment's explicit path if needed.

## Independent task

Create `welcome.py` that prints the project name and a short list of its intended features. Run it from the terminal, then explain the difference between the source file, the interpreter and the environment. Do not install a package just to print text.

## Check your work

The program should produce the same message twice without errors. You should be able to show its exact command and interpreter path. A useful explanation is: “The file stores instructions; Python runs them; the environment holds this project's packages.” Use the two practice exercises below to check that distinction.

[Next: values and amounts](/lessons/python-values)
