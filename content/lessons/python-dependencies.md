## Describe compatibility and reproduce an environment

A dependency declaration says what a package needs. A lock or complete pinned environment records what an application actually installs. This is lesson 3 of 8. A version range can allow several combinations; it is not a complete record of one working installation.

For a reusable library, supported ranges should follow tested compatibility. For this bounded lab, HTTPX is pinned to 0.28.1 so its examples and finite tests have a known target. This is a teaching choice, not a claim that this release is the newest or that pinning alone makes a program secure.

## Separate runtime and development work

Your users need HTTPX to import and run the HTTP adapter. They do not need mypy, Ruff or build just to run it. Optional development extras install these tools when requested. Build-system requirements are used while creating a distribution, not as its runtime dependency list.

```python
import tomllib

project = tomllib.loads('''
[project]
dependencies = ["httpx==0.28.1"]
[project.optional-dependencies]
dev = ["mypy==2.3.1", "build==1.2.2.post1"]
''')["project"]
assert "mypy==2.3.1" not in project["dependencies"]
assert "mypy==2.3.1" in project["optional-dependencies"]["dev"]
```

HTTPX also depends on other distributions. Pinning HTTPX alone does not pin those transitive dependencies. Record all resolved versions for a reproducible application environment; include hashes and the supported interpreter/platform when appropriate. `pip freeze` is an environment inventory, not proof that all listed packages are needed or all combinations are supported.

## Use the interpreter you intended

Prefer `.venv/bin/python -m pip` for this project. It binds pip to that interpreter. Activate an environment if useful, but verify it rather than assuming your terminal's python and pip names agree. Never solve a project dependency problem by installing everything into the system interpreter.

## Guided practice

Compare the starter's dependencies with its dev extra and build table. After installing, run `python -m pip check`. Inspect the installed HTTPX requirements and list its resolved dependencies. Keep this record with test evidence.

## Independent task

Create a second environment without the dev extra and install the wheel. Run the command and import the public API. Confirm runtime tools work without the development tools. Plan how you would retest before changing the HTTPX pin.

## Check your work

Explain why a green test in one old environment can miss an undeclared dependency. Do not claim complete dependency security from pip check; it checks declared version requirements, not vulnerabilities. Continue with [wheel tests and CI](/lessons/python-package-checks).
