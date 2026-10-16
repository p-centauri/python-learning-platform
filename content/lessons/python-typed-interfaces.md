## The idea in plain language

A useful typed interface tells callers what they can rely on while letting implementations vary. A read-only value protocol can accept a frozen record without requiring that record to inherit the protocol. Compatibility includes types and calling rules, not just matching method names. Keep the smallest interface your operation needs.

The example totals values through a read-only protocol. Its compatible Metric dataclass stays an ordinary value object. A static protocol check does not prove that an implementation has the right validation, side effects, error behavior or resource ownership. Even runtime-checkable protocols mainly inspect attribute presence, rather than validating full signatures or generic values. Keep explicit runtime boundary checks where they belong.

Finish the lab's four functions without widening public results to Any, adding unjustified casts or using type-ignore comments. Its positive fixtures assert concrete results, covariance/contravariance directions, call shapes and narrowing branches. Ten isolated negative fixtures must fail for the documented diagnostics, rather than a missing import or syntax error. A checker that accepts everything would fail this evidence design. Conversely, the unfinished starter may pass static checks while every runtime function still raises NotImplementedError.

Build a source archive and wheel, install the wheel with pinned checker/test tools in a fresh environment, and run outside source without PYTHONPATH or MYPYPATH. Adapt prior ingestion records into typed transformations and prior object snapshots through a small offline adapter. Preserve the original package contracts. Submit actual commands/output, two new regressions and a corrected rejected call for four manual criteria. This finishes a bounded typing unit; context/resource lifetime is published next, while threads/processes, measured performance and the full backend/applied AI path remain open. Finite local checks and a manual review do not certify expert knowledge.

## Worked example

Run this trusted example locally and compare actual behavior with its static contract.

```python
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

class HasValue(Protocol):
    @property
    def value(self) -> int: ...

@dataclass(frozen=True)
class Metric:
    value: int

def total(rows: Iterable[HasValue]) -> int:
    return sum(row.value for row in rows)

print(total([Metric(5), Metric(10)]))  # 15
```

## Guided practice

Identify the single operation total requires. Explain why Metric can satisfy it without inheritance and why a different value property returning str would not be a compatible interface. Separate that checker rejection from runtime business validation.

## Independent practice

Finish the typed transformation lab and run runtime cases, positive/negative checker fixtures, strict types/lint, builds and clean installed checks. Add two regressions, compose prior records/snapshots offline, and submit evidence with a rejected call and its correction.

## Check your work

You can show both useful accepted callers and deliberately rejected misuse, then demonstrate the installed package actually behaves. Report the finite scope of checks and manual judgment instead of treating annotations as expertise.

Open the [Typed transformation lab](/projects#python-typed-transforms) to download and submit evidence. The context/resource unit is published next; concurrency and measurement remain planned.

Continue to [ExitStack & partial resource acquisition](/lessons/python-exit-stack).
