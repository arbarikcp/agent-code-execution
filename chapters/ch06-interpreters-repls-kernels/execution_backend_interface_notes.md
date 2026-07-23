# Execution-Backend Interface — Notes

*Chapter 6 deliverable: an execution-backend interface with two implementations.*

The deliverable is the code: `src/backbone_agent/executor.py`. This document
records the interface, the two new implementations it adds (subprocess,
persistent kernel), and the measured trade-off between them.

## The interface

```python
@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    success: bool
    error: str | None = None
    duration_s: float = 0.0

class Executor(ABC):
    @abstractmethod
    def run(self, code: str) -> ExecutionResult: ...
    def close(self) -> None: ...   # no-op by default
```

Any backend that implements `run()` (and optionally `close()` for cleanup)
can be handed to `run_agent(..., executor=...)` in `loop.py` — the loop's own
control flow does not change based on which backend is running the code.
`observation_from_result()` turns any backend's `ExecutionResult` into the
same observation-string format the loop appends to context, so v0's exact
formatting is preserved regardless of backend.

## Implementation 1 — `SubprocessExecutor` (one-shot execution)

Spawns `python -c <code>` — a brand-new OS process — on every `run()` call.
Nothing persists between calls because there is no "between calls": each
process starts, executes, and exits.

## Implementation 2 — `KernelExecutor` (persistent kernel)

Starts one real IPython kernel via `jupyter_client.KernelManager` and reuses
it for every `run()` call, communicating over the actual Jupyter
`execute_request`/`execute_reply`/`iopub` protocol (not a custom shortcut).
State (variables, imports) persists naturally because it's the same live
interpreter process throughout.

(`InProcessExecutor`, wrapping Chapter 5's original `exec()`-based behavior,
is also present behind the same interface — see the chapter README for why
it's included alongside, rather than instead of, the two new ones.)

## Measured: same 3-action sequence, both backends, real numbers

Sequence: `x = 10`, `y = 20`, `print(x + y)`. Run via
`code/backends_demo.py` against a real subprocess-per-call and a real
persistent kernel:

```
=== (a) Fresh subprocess per action ===
  step 1: 'x = 10'             -> success=True  duration=  14.7ms
  step 2: 'y = 20'             -> success=True  duration=  16.6ms
  step 3: 'print(x + y)'       -> success=False duration=  20.2ms  observation="NameError: name 'x' is not defined"
  total wall time for 3 actions: 51.5ms

=== (b) Persistent IPython kernel ===
  kernel startup cost (paid once): 730.4ms
  step 1: 'x = 10'             -> success=True  duration=   7.9ms
  step 2: 'y = 20'             -> success=True  duration=   4.0ms
  step 3: 'print(x + y)'       -> success=True  duration=   4.1ms  observation='30'
  total wall time for 3 actions (excl. startup): 16.1ms
```

**Reading this:**

- **Correctness:** only the kernel backend can pass step 3 at all. The
  subprocess backend's `NameError` isn't a bug — it's the structurally
  correct outcome of running each action in a process that doesn't exist
  anymore by the next action.
- **Per-call cost:** the subprocess backend pays ~15-20ms of interpreter
  startup on *every* call; the kernel backend, once started, answers in a
  few milliseconds because there's no startup left to pay per call.
- **Startup cost:** the kernel backend pays ~730ms once, up front; the
  subprocess backend never pays that as a lump sum, but pays a smaller
  version of it, repeatedly, forever.

## When each backend wins

- **Subprocess (one-shot):** a single, short, stateless action where no
  later action needs anything this one produced in memory; also the simpler
  backend to reason about and to isolate (Chapter 9 revisits this for
  isolation, not just cost).
- **Persistent kernel:** any multi-step task — which is most of what this
  guide is about — where later actions build on earlier results (a loaded
  dataset, a defined function, an open connection) without needing to
  re-derive them from scratch every turn. The 730ms startup cost is paid
  back within a handful of actions and never paid again for the rest of the
  run.

Chapter 7 (Stateful vs. Stateless Execution) picks this exact distinction back
up as its own subject; Chapter 9 (Execution Backends) expands this same
`Executor` interface to a third backend (remote/sandboxed) and formalizes the
full trade-off table (speed, isolation, statefulness, cost).
