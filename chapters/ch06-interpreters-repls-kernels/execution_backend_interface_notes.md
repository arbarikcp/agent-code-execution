# Execution-Backend Interface — Notes

*Chapter 6 deliverable: an execution-backend interface with two implementations.*

The deliverable is the code: `src/backbone_agent/executor.py`. This document
records the interface, the three implementations now measured behind it, the
real amortization breakeven point, and a genuine unhandled failure mode.

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

## Three implementations, all measured together

- **`InProcessExecutor`** — Chapter 5's original backend: `exec()` in this
  process, fresh `{}` namespace every call.
- **`SubprocessExecutor`** — one-shot: `python -c <code>`, a brand-new OS
  process on every call. Nothing persists between calls because there is no
  "between calls" — each process starts, executes, and exits.
- **`KernelExecutor`** — persistent: one real IPython kernel
  (`jupyter_client.KernelManager`), reused across calls over the actual
  Jupyter `execute_request`/`execute_reply`/`iopub` protocol. State
  persists naturally because it's the same live interpreter throughout.

## Measured: same 3-action sequence, all three backends, real numbers

Sequence: `x = 10`, `y = 20`, `print(x + y)` — via `code/backends_demo.py`:

```
subprocess:    46.9ms total, step 3 FAILED (as expected)
kernel:       757.6ms startup + 20.8ms, step 3 passed
in-process:     2.0ms total, step 3 FAILED (as expected)
```

**Reading this:** only the kernel backend passes step 3 — `x` and `y` no
longer exist by the time a fresh subprocess or a fresh in-process namespace
handles step 3. In-process is dramatically faster than either
process-based backend (no subprocess spawn, no kernel IPC) but shares
subprocess's statelessness — **statelessness and process isolation are
independent axes**: in-process execution has neither isolation nor state
persistence; subprocess has isolation but no persistence; the kernel has
persistence but pays isolation's full process cost to get it.

## The real amortization breakeven — measured, not asserted

The 3-action snapshot makes the kernel look like a poor trade (750ms startup
for 3 actions). But a real agent session runs many more than 3 actions. At
what N does the kernel's one-time startup actually pay for itself?
`measure_amortization()` sweeps N from 1 to 160 and measures TOTAL wall time
for both backends directly:

```
 N actions |  subprocess total |  kernel total | kernel wins?
-------------------------------------------------------------
         1 |             29ms |        537ms |           no
         3 |             72ms |        547ms |           no
         5 |             96ms |        570ms |           no
        10 |            153ms |        496ms |           no
        20 |            267ms |        582ms |           no
        40 |            510ms |        644ms |           no
        60 |            744ms |        668ms |          yes
        80 |            993ms |        720ms |          yes
       120 |          1452ms |        839ms |          yes
       160 |          1993ms |        930ms |          yes

Smallest N tested where kernel's total time is already lower: 60
```

**This corrects an earlier, unverified claim in this exact document.** The
first draft of these notes asserted the startup cost "is paid back within a
handful of actions" — a plausible-sounding guess, never actually measured.
The real breakeven, measured directly, is around **N=60 actions** in this
environment — not a handful. Below N=60, subprocess's lower-but-repeated
per-call cost keeps it cheaper overall despite paying it every time; above
N=60, the kernel's amortized startup is worth it. This specific number is
tied to this machine's subprocess-spawn cost and kernel IPC overhead and
would shift elsewhere — the reusable lesson is that "is a persistent kernel
worth it?" is a question with a measurable answer, not just an argument, and
guessing at the crossover point (as the original version of this document
did) can be wrong by more than an order of magnitude.

## A real, unhandled failure: the kernel can hang

`KernelExecutor.run()` calls `self._kc.get_iopub_msg(timeout=execute_timeout_s)`
in a loop. Run a genuine `while True: pass` against a kernel configured with
a 2-second timeout:

```python
result = demo_kernel_hang(execute_timeout_s=2.0)
# {'raised': True, 'exception_type': '_queue.Empty', 'elapsed_s': 2.008...}
```

`run()` raises `_queue.Empty`, uncaught, after really waiting the full
timeout — a genuine violation of the `Executor` base class's own documented
contract ("must not raise on the code's own errors"). Since
`run_agent` (Chapter 5) has no `try/except` around `executor.run(code)`, an
uncaught exception here would crash the entire agent loop, not just fail one
action. This is left unfixed on purpose (flagged directly in
`KernelExecutor.run()`'s docstring) — surfacing the gap honestly is this
chapter's job; fixing it belongs to Chapter 21 (termination) or Chapter 26
(guardrails). Separately confirmed: `kernel.close()` (`shutdown_kernel(now=True)`)
successfully reclaims the hung kernel process afterward — the hang doesn't
leak a zombie process, even though it does propagate an unhandled exception.

## When each backend wins

- **In-process:** lowest overhead of all three, no isolation, no
  persistence — the right default when isolation doesn't matter (tests,
  trusted code) and state doesn't need to survive across calls.
- **Subprocess (one-shot):** isolated, no persistence, cheapest of the two
  process-based backends per call, and simplest to reason about — the right
  choice below the measured ~60-action breakeven, or whenever no later
  action needs anything from an earlier one.
- **Persistent kernel:** the only backend with real state continuity, worth
  its startup cost once a session's action count clears the measured
  breakeven — but the one genuine unhandled failure mode (a hang) means it
  also needs a recovery story a one-shot backend never has to have.

Chapter 7 (Stateful vs. Stateless Execution) picks the state-continuity
distinction back up as its own subject; Chapter 9 (Execution Backends)
expands this same `Executor` interface to a third backend (remote/sandboxed)
and formalizes the full trade-off table (speed, isolation, statefulness,
cost) — starting from the measured numbers here, not from scratch.
