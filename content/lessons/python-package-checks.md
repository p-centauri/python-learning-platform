## Test the artifact that another person installs

Test behavior and packaging separately. This is lesson 4 of 8. Editable tests can pass while your wheel omits a module or resource. A production artifact should be built once and tested in a clean environment outside the source tree.

Run lint to find selected code problems, a type checker to check declared relationships, and runtime tests to observe behavior. None replaces the others. A package can type-check while returning the wrong number, or pass sample inputs while leaking a response on failure.

## Make the checks observable

```python
from pathlib import PurePosixPath

wheel_members = {
    "academy_ingest/__init__.py",
    "academy_ingest/cli.py",
    "academy_ingest/defaults.json",
    "academy_ingest/py.typed",
}
required = {"academy_ingest/defaults.json", "academy_ingest/py.typed"}
assert required <= wheel_members
assert all(PurePosixPath(name).parts[0] == "academy_ingest" for name in wheel_members)
```

This toy assertion explains the inspection, but it does not build anything. For the project, inspect the real wheel, install it, check the real import path, and run the public suite against that installation. A source distribution is a source archive; a wheel is the installable artifact. Build both and test a wheel built from the extracted source archive too, so missing source files are detected.

## A useful CI order

Install the declared tools in a controlled environment. Run lint, types and behavior tests. Build distributions. Install the wheel into a fresh environment, change away from the checkout, and repeat the relevant runtime and command checks. Preserve failure output so someone else can reproduce it. Later production work adds platform/version matrices and release integrity; this lab's one environment is limited evidence.

## Guided practice

Use the starter README's commands and inspect each output. Distinguish an installation error from the expected NotImplementedError in unfinished learner functions. Do not replace the implementation with a mock just to make tests pass.

## Independent task

Finish the parser before HTTP work, with tests for split records and late failures. After the whole module, build and test the final wheel from an unrelated folder. Add a regression that would catch an accidentally omitted defaults.json.

## Check your work

Record actual commands, versions and exit codes. Explain what still needs human review, especially memory use and ownership. Continue with [managed HTTP clients](/lessons/python-http-clients).
