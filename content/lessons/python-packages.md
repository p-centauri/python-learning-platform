## Turn a folder into an installable package

A package should work after installation, even when the user is outside your source folder. This is lesson 1 of 8 in the packaging and HTTP ingestion module. You have already separated parsing from resource ownership. Now make that code usable by another program and by a terminal command.

Python has two related names: a **distribution** is what pip installs; an **import package** is what Python imports. Our distribution is `academy-ingest-lab`, while its import is `academy_ingest`. They do not have to match character for character. Unlike a JavaScript package's package.json alone, Python's pyproject.toml also selects a build backend.

## Declare three different kinds of configuration

`[build-system]` declares tools needed to build the distribution. `[project]` declares its name, version, Python requirement and runtime dependencies. `[tool...]` configures development tools. Putting a runtime dependency only in a linter section will not install it for your users.

```python
import tomllib

metadata = tomllib.loads('''
[build-system]
requires = ["setuptools==83.0.0", "wheel==0.48.0"]
build-backend = "setuptools.build_meta"
[project]
name = "academy-ingest-lab"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["httpx==0.28.1"]
[project.scripts]
academy-ingest = "academy_ingest.cli:main"
''')
assert metadata["project"]["dependencies"] == ["httpx==0.28.1"]
assert metadata["project"]["scripts"]["academy-ingest"] == "academy_ingest.cli:main"
```

The script entry names an importable function, without parentheses. The installed wrapper calls it and uses its integer return as the exit status. Keep network calls and printing inside that function; importing the library should not start the command.

## Guided practice

Open the [ingestion package project](/projects#python-ingestion-package) and download its starter. Identify its runtime dependency, build dependencies and optional development tools. Trace the installed command to `main`. Read the contract before changing the two unfinished files.

## Independent task

Create the environment described in the README and install the starter in editable mode. Confirm importing it is quiet. The public tests intentionally fail until parsing and HTTP ownership are implemented. Do not hide these failures or treat a successful installation as a passing implementation.

## Check your work

Explain which tool reads each table. Move your terminal outside the package folder and locate the installed import. Record the interpreter used for installation so pip and Python cannot silently refer to different environments. Later lessons will verify the built wheel separately from editable development.

Continue with [imports and bundled resources](/lessons/python-imports-resources).
