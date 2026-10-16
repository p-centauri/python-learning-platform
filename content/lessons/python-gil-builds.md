## The idea in plain language

The Global Interpreter Lock belongs to particular interpreter implementations and builds. In ordinary GIL-enabled CPython, one thread executes Python bytecode at a time per interpreter. Threads can still overlap waiting, and some native extensions release the GIL around work.

Python 3.13 introduced optional free-threaded CPython builds. They can run threads without the GIL, but the runtime GIL may be enabled, including by an extension that lacks support. A build configured for free threading and the current runtime GIL state are different facts. Other Python implementations may behave differently too.

The example reports implementation, free-threaded build configuration and an optional runtime probe. sys._is_gil_enabled is implementation-specific and may be unavailable; use a guarded probe and report unknown honestly. Do not label every Python 3.13 installation free-threaded or assume every extension supports it.

Built-in containers use internal synchronization in free-threaded CPython, but that does not make an arbitrary sequence of reads/writes atomic or protect your application invariant. Use explicit synchronization and avoid assuming undocumented internal locking guarantees. Small immutable returned messages reduce unnecessary shared state.

Native library thread pools can also create oversubscription when nested inside an outer pool. Choose worker counts from measurements and deployment constraints. This unit verifies behavior and ownership, not throughput, latency or expertise. Reproduce build details and measure in the next unit before choosing an optimization.

## Worked example

Save this trusted example as example.py and run it locally. Process startup requires a saved, guarded script.

```python
import platform
import sys
import sysconfig
print(platform.python_implementation())
print("free-threaded build:", bool(sysconfig.get_config_var("Py_GIL_DISABLED")))
probe = getattr(sys, "_is_gil_enabled", None)
state: object = probe() if callable(probe) else "unavailable"
print("runtime GIL enabled:", state)
```

## Guided practice

Record build configuration separately from current runtime state. Explain I/O/native GIL release and why multi-step invariants still need synchronization.

## Independent practice

Record the guarded probe from your installed interpreter and relevant native packages. Describe what it establishes, what is unknown and how you would measure the actual workload.

## Check your work

Do not assume version equals build or that a free-threaded build makes compound operations safe. No unmeasured speedup claim.

Continue to [Offload contracts & the bounded worker lab](/lessons/python-offload-contracts).
