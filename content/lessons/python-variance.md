## The idea in plain language

Variance describes whether a generic interface can safely substitute related element types. Think about the operations callers are allowed to perform. A producer of Dog values can serve a caller that only asks for Animal values: every Dog is an Animal. That direction is covariance.

A consumer able to accept any Animal can serve a caller that only sends Dogs. It already knows how to handle those inputs. That reversed direction is contravariance. It would be unsafe to send arbitrary Animals to a consumer that only handles Dogs. Function parameter types follow this consumer reasoning; return types follow producer reasoning.

A writable list of Dogs cannot be handed out as a writable list of Animals. That caller could append an Animal that is not a Dog and break the original promise. list is invariant. A read-only Sequence[Animal] interface can accept the dog list because it offers reading rather than arbitrary replacement. A property in a protocol likewise describes read-only access, while a publicly writable field can require invariance.

The example declares the producer parameter covariant explicitly so the allowed direction is visible. Modern generic class syntax can let a checker infer variance from the class interface; the lab uses explicit traditional declarations for its read-only Valued and consuming Consumer protocols. Do not choose covariance by intuition while adding a setter that consumes that same parameter. A read-only interface limits what that caller can request; it does not freeze the original list, its elements, or aliases held by other code. Static substitution rules and runtime ownership are related design questions with separate evidence.

## Worked example

Run this trusted example locally and compare actual behavior with its static contract.

```python
from collections.abc import Sequence
from typing import Protocol, TypeVar

class Animal:
    pass
class Dog(Animal):
    pass

T_co = TypeVar("T_co", covariant=True)
class Producer(Protocol[T_co]):
    @property
    def value(self) -> T_co: ...

class DogProducer:
    @property
    def value(self) -> Dog:
        return Dog()

dogs: list[Dog] = [Dog()]
view: Sequence[Animal] = dogs
dog_source: Producer[Dog] = DogProducer()
animal_source: Producer[Animal] = dog_source
print(type(animal_source.value).__name__, len(view))  # Dog 1
```

## Guided practice

Draw the allowed Dog-producer to Animal-producer arrow. Then explain why the writable list arrow would allow a bad append. For a consumer, reverse the arrow and use one accepted input to justify the change.

## Independent practice

Run the lab’s positive producer/consumer fixtures and its rejected substitutions. Write a small animal consumer that can stand in for a dog consumer. Keep a read-only interface for earlier records and show that it does not claim their owner can never change a mutable source.

## Check your work

You can justify each direction using an actual read or write operation. A property or Sequence limits the caller’s operations; it does not establish deep immutability or thread safety.

Continue to [ParamSpec & signature-preserving decorators](/lessons/python-paramspec).
