## Imports should not depend on your current folder

Use the installed package and explicit resource APIs rather than guessing a file's location. This is lesson 2 of 8. A program that works only from its repository root has an accidental dependency on the caller's current directory.

The starter uses `src/academy_ingest/`. A src layout keeps importable code below a separate directory, making accidental imports from the checkout less likely. Install it before testing. Do not patch sys.path in each test to conceal a broken package configuration. An editable install connects your environment to source for development; a wheel install uses the built artifact.

## Load data through the package

Use `importlib.resources` for data shipped inside an import package. Configure your build backend to include the file as well. The API cannot rescue a resource that was omitted from the wheel.

```python
from importlib.resources import files
import json

# A standard-library example that runs without this lab installed.
readme = files("email").joinpath("__init__.py")
assert readme.is_file()

example_defaults = '{"demo_url":"https://feed.example.test/events"}'
defaults = json.loads(example_defaults)
assert defaults["demo_url"].startswith("https://")
```

In the installed lab, use `files("academy_ingest").joinpath("defaults.json").read_text(encoding="utf-8")`. This describes the package resource, not the working directory. Resources may be provided through different loaders; do not assume every resource is a permanent filesystem path. Use `as_file` with a visible context if a library requires a real path.

## Keep imports quiet

`__init__.py` exposes a small public API. `__main__.py` starts the command for `python -m academy_ingest`. Importing `academy_ingest.cli` defines functions but does not call main. Avoid naming your own files json.py or httpx.py: they can shadow the libraries you meant to import.

## Guided practice

Inspect the package-data configuration and find `defaults.json` and `py.typed`. The latter tells type checkers that the installed package supplies typing information; it does not validate runtime inputs. Trace relative imports inside the package.

## Independent task

Build a wheel and inspect its archive. Check that both data files and the CLI module are inside it. Run the installed demo from an unrelated temporary folder. Record the actual imported module path.

## Check your work

Delete neither source files nor environments to prove independence. Use a separate environment and directory instead. If imports fail only after installation, inspect wheel contents and package discovery before adding path hacks. Continue with [dependencies and repeatable environments](/lessons/python-dependencies).
