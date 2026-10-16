## The idea in plain language

super() delegates to the next applicable implementation in the current object's method resolution order, or MRO. It does not mean "call my named parent". Python's C3 ordering respects local base order and consistent inheritance relationships. Inspect __mro__ for the actual class instead of guessing a diamond's route.

In the example, Combined searches Left, then Right, then Root. Inside Left.labels, super() continues after Left in Combined's order and reaches Right. If Left were used alone, that same source would reach Root instead. This is why calling Root.labels(self) directly inside a reusable mixin can skip behavior that another class expected to join the chain.

Cooperation is a contract. Every participant needs a compatible signature, a deliberate termination point, and exactly one delegation when its job requires the rest of the chain. A method that never delegates can stop the chain; two delegations can duplicate side effects. Constructors need the same care with arguments and initialization. Multiple inheritance itself does not guarantee that an existing base class was written to cooperate.

A mixin supplies a small behavior intended to combine with others. Keep its expectations explicit. Composition is often easier: give an object another object that performs a job, instead of making initialization and method order depend on a complex hierarchy. Here we use a pure trace to observe ordering without adding a framework or performing external side effects. The project's reviewer asks for this reproduction and a reasoned choice between inheritance and composition. A successful trace proves its own order, not the safety of every library hierarchy.

## Worked example

Run this trusted example locally and predict the output before execution.

```python
class Root:
    def labels(self) -> tuple[str, ...]:
        return ("root",)

class Left(Root):
    def labels(self) -> tuple[str, ...]:
        return ("left",) + super().labels()

class Right(Root):
    def labels(self) -> tuple[str, ...]:
        return ("right",) + super().labels()

class Combined(Left, Right):
    pass

print(Combined().labels())  # ('left', 'right', 'root')
print([base.__name__ for base in Combined.__mro__])
```

## Guided practice

Draw the MRO and put a marker just after Left when its super call runs. Swap Combined base order and predict the resulting trace before execution. Observe that Root occurs once in each cooperative trace.

## Independent practice

Add a small Trace mixin with the same labels signature and one super delegation. Record the resulting diamond order. Then replace one delegation with a direct Root call and explain the missing behavior. Submit the comparison with the lab; choose composition for a separate configurable policy and explain why.

## Check your work

You can explain the next implementation using the actual receiver class. You can identify a stopped or duplicated chain without assuming all bases cooperate. Keep the pure trace separate from real external effects.

Continue to [Special methods & honest containers](/lessons/python-special-methods).
