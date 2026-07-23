# Chapter 6 — Interpreters, REPLs, and Kernels

## 1. Concept

Chapter 5's backbone agent ran code via `exec()`, in-process, with no choice
in the matter. This chapter opens up that choice: the "environment" box in
Chapter 1's loop diagram is actually a machine with real design options — a
fresh interpreter per action (one-shot execution) versus one persistent
interpreter reused across actions (a kernel) — and the difference is not
cosmetic. It determines whether state survives between actions and how much
of each action's latency is interpreter startup versus actual work.

## 2. Why This Matters for Code-Executing Agents

An agent loop is, almost by definition, multi-step. Whether the execution
backend remembers anything between those steps changes what the agent can do
in one action versus what it must redo, and changes the latency profile of
every single turn. This chapter makes both effects measurable before Part II
goes on to build out the rest of the execution substrate (state management
properly in Chapter 7, rich output capture in Chapter 8, a fully pluggable
three-backend interface in Chapter 9).

## 3. Mental Model

```
One-shot execution:        [fresh interpreter] -> run -> exit  (repeat, from scratch, every action)
Persistent kernel:         [interpreter started once] -> run -> run -> run -> ... (same process, whole session)
```

A REPL (read-eval-print loop) is the natural shape of an agent's execution
surface either way — read an action in, evaluate it, print/return the
result — but "loop" in REPL refers to reading successive inputs, not
necessarily to *state* surviving between them. One-shot execution restarts
the REPL's underlying interpreter every time; a persistent kernel keeps one
REPL's interpreter alive and just keeps feeding it new input.

## 4. Architecture (place in the loop / context)

This chapter replaces the single hardcoded execution step in Chapter 5's
loop diagram with a named, swappable component:

```
... model emits code ──► [Executor.run(code)] ──► ExecutionResult ──► Observation ──► ...
                                  ▲
                    now pluggable: InProcessExecutor (Ch5),
                    SubprocessExecutor (Ch6), KernelExecutor (Ch6)
```

`loop.py::run_agent` gained an `executor` parameter; nothing else about the
loop's control flow changed. This is the shape Chapter 9 will later expand to
three backends and a full trade-off table, and the shape Chapter 18 formalizes
as one of the harness's clean interfaces.

## 5. Detailed Explanation

**REPL versus script execution.** A script runs top to bottom once and exits;
a REPL evaluates one input at a time and can be fed more input later. Both of
this chapter's new backends are REPL-*shaped* from the agent's point of view
(one action in, one result out, repeatable) — but only `KernelExecutor` is a
REPL in the stateful sense, because only it keeps one interpreter alive to
be fed more input.

**Jupyter/IPython kernel model.** `KernelExecutor` (in
`src/backbone_agent/executor.py`) starts a real IPython kernel via
`jupyter_client.KernelManager`, exactly the mechanism a Jupyter notebook
itself uses to run cells. The kernel is a separate process; the executor
talks to it over ZeroMQ channels, not by importing IPython in-process.

**Execute request/reply.** `KernelExecutor.run()` sends an `execute_request`
(`self._kc.execute(code)`) and reads back `iopub` messages until it sees an
`idle` status for that request's `msg_id` — the real Jupyter messaging
protocol, not a simplified stand-in. Along the way it handles three message
types that matter for an agent: `stream` (stdout/stderr), `execute_result`
(a cell's trailing expression value — a preview of Chapter 8), and `error`
(a real traceback, with ANSI color codes stripped for clean text).

**Process-per-call versus kernel-per-session.** `SubprocessExecutor.run()`
spawns `python -c <code>` fresh, every call — this is "process-per-call."
`KernelExecutor` starts its kernel once, in `__init__`, and every `run()`
call reuses it — "kernel-per-session." The measured 3-action sequence in
`execution_backend_interface_notes.md` shows the direct consequence:
subprocess's step 3 (`print(x + y)`) fails with a real `NameError`, because
`x` and `y` no longer exist once their processes exited; the kernel's step 3
succeeds, printing `30`, because it's still the same interpreter.

**Startup cost and warm kernels — and the real breakeven point.** Measured
directly: subprocess pays ~15-20ms of interpreter startup on every call; the
kernel pays ~750ms once, then answers each call in a few milliseconds. That
much was true in the original version of this chapter. What wasn't measured
before is the actual crossover: `measure_amortization()` sweeps N from 1 to
160 trivial actions and totals real wall time for both backends. The result
— **N≈60** — is the smallest tested session length where the kernel's total
time is already lower than the subprocess backend's. Below that, subprocess
wins on raw total time despite paying its smaller cost on every call; above
it, the kernel's amortized startup is worth it. This number replaced a
plainly wrong guess: an earlier draft of this chapter's deliverable asserted
the startup "is paid back within a handful of actions" without measuring it
— off by more than an order of magnitude from the real N≈60. That correction
is preserved in `execution_backend_interface_notes.md` as a concrete
reminder that a plausible-sounding unmeasured claim can be badly wrong even
when the DIRECTION of the claim (kernels amortize) is correct.

**A third backend, measured alongside the other two.** `InProcessExecutor`
(Chapter 5's original) was previously discussed but never run side-by-side
with the other two. Measured on the same 3-action sequence, it's dramatically
faster than both (no subprocess spawn, no kernel IPC — ~2ms total vs.
subprocess's ~47ms and the kernel's ~758ms startup) and shares subprocess's
statelessness (step 3 fails identically). This makes a point the two-backend
version of this chapter couldn't: **state persistence and process isolation
are independent axes**, not two ends of one dial. In-process has neither;
subprocess has isolation without persistence; the kernel has persistence
but pays isolation's full process cost for it. No backend among these three
offers persistence WITHOUT paying for a separate process.

**Language runtimes.** Not separately implemented this chapter (Chapter 10
covers polyglot execution), but the same one-shot-vs-persistent distinction
applies identically to a Node subprocess vs. a long-lived Node REPL, or a
bash subprocess vs. a persistent shell session — the mechanism (fresh
process vs. reused process) is language-agnostic; only the specific
protocol (Jupyter's `execute_request`, Node's REPL protocol, a shell's
stdin) differs.

## 6. Minimal Implementation

`src/backbone_agent/executor.py`:

- `ExecutionResult` — backend-agnostic result: stdout, stderr, success,
  error, duration.
- `Executor` (ABC) — `run(code) -> ExecutionResult`, optional `close()`.
- `InProcessExecutor` — Chapter 5's original behavior, now behind the
  interface (unchanged: fresh `{}` namespace per call).
- `SubprocessExecutor` — one-shot: `python -c <code>` per call.
- `KernelExecutor(startup_timeout_s, execute_timeout_s)` — persistent: one
  real IPython kernel, reused; `execute_timeout_s` is a Chapter 6 addition
  that makes the real hang failure (Section 8) reproducible in 2 seconds
  instead of the default 30.
- `observation_from_result()` — shared formatting so `loop.py` behaves
  identically no matter which backend produced the result.

`code/backends_demo.py` adds `measure_amortization()` /
`render_amortization()` / `find_breakeven()` (the real N≈60 crossover) and
`demo_kernel_hang()` (the real `queue.Empty` reproduction).

`loop.py::run_agent` gained `executor: Executor | None = None`, defaulting
to `InProcessExecutor()` — v0's exact prior behavior when no executor is
passed, confirmed via `tests/test_backbone_smoke.py` after the refactor.

Run the comparison directly:

```bash
source .venv/bin/activate
python chapters/ch06-interpreters-repls-kernels/code/backends_demo.py
```

(Full output in `execution_backend_interface_notes.md`.)

## 7. Hands-on Lab

`notebooks/ch06_interpreters_repls_kernels.ipynb` (executed, committed with
outputs) runs the chapter's required comparison and then three deeper
measurements: all three backends (not just two) on the same 3-action
sequence; the full amortization sweep (N=1 to 160) with the real N≈60
breakeven; and the real kernel-hang reproduction.

To extend it yourself: add a 4th and 5th action to `ACTION_SEQUENCE` that
each depend on the previous one (e.g. `z = x + y`, `print(z * 2)`) and rerun
— the subprocess and in-process backends should both fail starting at
whichever step first references prior state; only the kernel should keep
succeeding.

## 8. Failure Lab

Not hypothetical — run, with real output in `execution_backend_interface_notes.md`:
`demo_kernel_hang(execute_timeout_s=2.0)` runs a genuine `while True: pass`
against a real `KernelExecutor` and gets back
`{'raised': True, 'exception_type': '_queue.Empty', 'elapsed_s': 2.008...}`
— an uncaught exception propagating straight out of `run()`, violating the
`Executor` base class's own documented contract ("must not raise on the
code's own errors"). Since `run_agent` (Chapter 5) has no `try/except`
around `executor.run(code)`, this would crash the entire agent loop, not
fail one action gracefully. Separately confirmed: a hung kernel's
accumulated state (every variable from every prior `run()` call) is lost
along with the exception, because there's only one interpreter and its
current call never returned — but the OS process itself IS still cleanly
reclaimed by `kernel.close()`'s `shutdown_kernel(now=True)`, confirmed by
the notebook reaching its next cell. Contrast with `SubprocessExecutor`,
which already handles its own timeout gracefully (`subprocess.run(...,
timeout=...)` → a clean `ExecutionResult(success=False, ...)`, no
exception) — the kernel's ungraceful failure here isn't inherent to
persistent kernels in general, it's a genuine gap in this specific
`KernelExecutor.run()` implementation, left unfixed on purpose (flagged in
its own docstring) so this Failure Lab has something real to show rather
than a patched-over non-issue. (No restart/recovery logic exists —
intentionally left for Chapter 26's guardrail material.)

## 9. Instrumentation (what to log / trace / measure)

Per execution: which backend ran it, `duration_s`, and whether it was the
"first" call for a kernel backend (to separately attribute startup cost).
`ExecutionResult.duration_s` already carries this; a real system would tag
each result with a backend identifier before logging so per-backend latency
can be aggregated separately — exactly the kind of per-component
measurement Chapter 61 (Cost, Latency, and Performance) formalizes later.

## 10. Design Considerations

- **The interface must not leak backend-specific behavior into the loop.**
  `run_agent` never checks which `Executor` subtype it received — it only
  calls `.run()` and formats the result. This is what makes Chapter 9's later
  three-backend expansion a non-event for `loop.py`.
- **Startup cost is a real, payable-once investment, not free — and its
  payback point is a number you should measure, not guess.** The measured
  N≈60 breakeven in this environment is over an order of magnitude higher
  than an earlier unmeasured guess of "a handful of actions." Don't reach
  for `KernelExecutor` for a workload dominated by short, unrelated action
  counts without checking where your own breakeven actually falls.
- **A persistent kernel is a single point of failure for the whole run's
  state, AND its current failure handling is worse than the simpler
  backend's**, as Section 8 shows directly: `SubprocessExecutor` degrades
  gracefully on a timeout; `KernelExecutor` currently does not. Any
  production use of a kernel backend needs both a restart/recovery story
  and a fix to this specific gap — out of scope for this minimal v0,
  flagged for later (Chapters 21, 26).

## 11. Common Mistakes

- **Assuming "persistent" means "safer."** It means "stateful," which is a
  different axis from safety or isolation entirely — Chapter 9's trade-off
  table treats these as separate columns for exactly this reason.
- **Forgetting to pay (or amortize) kernel startup cost when benchmarking.**
  Comparing one subprocess call to one kernel call without accounting for
  the kernel's one-time startup misrepresents the trade-off; always compare
  over a realistic number of actions per session, as this chapter's demo
  does explicitly.
- **Treating `InProcessExecutor` as obsolete now that two more backends
  exist.** It isn't — no subprocess boundary, no kernel management, lowest
  overhead of all three; still the right default for tests and for chapters
  that don't need process isolation, which is why `run_agent` still defaults
  to it.

## 12. Comparisons / Alternatives

| | `InProcessExecutor` (Ch5) | `SubprocessExecutor` (Ch6) | `KernelExecutor` (Ch6) |
|---|---|---|---|
| State across calls | No (fresh namespace) | No (fresh process) | Yes (same interpreter) |
| 3-action total time (measured) | ~2ms | ~47ms | ~758ms startup + ~21ms |
| Per-call overhead beyond startup | Lowest | ~15-20ms (measured) | ~4-8ms after startup (measured) |
| One-time startup cost | None | None | ~750ms (measured) |
| Breakeven vs. subprocess (measured) | N/A | — | ≈N=60 actions |
| Process isolation from the harness | None | Full (separate OS process) | Full (separate OS process) |
| Unhandled hang failure? | N/A (no long-running risk beyond the harness itself) | No — clean timeout via `subprocess.run(timeout=...)` | **Yes — uncaught `queue.Empty`** (Section 8) |
| Protocol | Direct `exec()` call | stdin/stdout via `subprocess` | Real Jupyter `execute_request`/`iopub` |

## 13. Review Questions

1. Why does `SubprocessExecutor`'s step 3 fail with a *real* `NameError`
   rather than some kind of "no state available" error — what does that
   distinction tell you about what a subprocess actually is?
2. What three IPython message types does `KernelExecutor.run()` handle, and
   what would break if it ignored `execute_result` entirely?
3. The measured breakeven is N≈60 actions. Name two things about a real
   deployment (not this benchmark) that could shift that number substantially
   higher or lower — think about what makes a subprocess spawn expensive or
   cheap on different infrastructure.
4. What is the one thing `run_agent` is never allowed to do, per this
   chapter's design, regardless of which `Executor` it's given — and does
   `KernelExecutor.run()` actually honor that, per Section 8's finding?
5. `SubprocessExecutor` handles its own timeout gracefully;
   `KernelExecutor` doesn't. Is that difference inherent to "one-shot vs.
   persistent," or could a persistent-kernel executor be written to handle
   timeouts as gracefully as subprocess does? What would it need to do
   differently in its `run()` method?
6. Why did the original (pre-measurement) claim that kernel startup "pays
   back within a handful of actions" turn out to be wrong by more than an
   order of magnitude — what made it plausible-sounding despite being
   unmeasured?

## 14. Chapter Summary

The execution backend is a real design choice, not an implementation detail:
one-shot execution (a fresh interpreter per action) trades away state
persistence for isolation and simplicity; a persistent kernel trades a
one-time startup cost for real state continuity and lower per-call latency
afterward. Measured on an identical 3-action sequence across all THREE
backends: in-process took ~2ms but failed step 3; subprocess took ~47ms and
also failed step 3 with a genuine `NameError`; the kernel paid ~758ms once,
then answered each call in a few milliseconds, and passed step 3 correctly.
Pushed further than a single snapshot, a full amortization sweep (N=1 to
160) found the REAL breakeven point — N≈60 actions — correcting an earlier
unmeasured guess ("a handful of actions") that was wrong by more than an
order of magnitude. And a genuine failure case — a real `while True: pass`
against the kernel — surfaced an actual gap: `KernelExecutor.run()` raises
an uncaught `queue.Empty` on a hang, violating the `Executor` interface's
own contract, left unfixed on purpose so the gap is visible rather than
quietly patched. `src/backbone_agent/executor.py` now exposes all three
backends behind one `Executor` interface, and `loop.py::run_agent` accepts
any of them via the `executor` parameter without any change to its own
control flow — confirmed via the regression smoke test after every change
this chapter made.

## 15. Chapter Deliverable

**An execution-backend interface with two implementations** —
`SubprocessExecutor` and `KernelExecutor` in `src/backbone_agent/executor.py`
(behind the shared `Executor` interface, alongside Chapter 5's
`InProcessExecutor`) — documented with measured results, the real N≈60
amortization breakeven, and the real kernel-hang failure in
[`execution_backend_interface_notes.md`](execution_backend_interface_notes.md).

## 16. Further Reading

- Jupyter's messaging protocol specification
  (`https://jupyter-client.readthedocs.io/en/latest/messaging.html`) — the
  real `execute_request`/`execute_reply`/`iopub` protocol `KernelExecutor`
  implements a client for; worth reading directly to see the full message
  type catalog beyond the three handled here.
- `jupyter_client` documentation — the library used for `KernelManager` and
  the blocking kernel client; the same library real Jupyter frontends use to
  talk to kernels.
- IPython's own architecture overview — for how the kernel process itself
  (not just the client protocol) turns a REPL into something a network
  client can drive, useful background for why "kernel" and "REPL" are
  related but not identical concepts.
