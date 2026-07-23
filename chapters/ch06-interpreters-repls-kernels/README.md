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

**Startup cost and warm kernels.** Measured directly: subprocess pays
~15-20ms of interpreter startup on every call; the kernel pays ~730ms once,
then answers each call in a few milliseconds. A "warm" kernel — already
started, sitting ready — is what makes that second number small; the whole
point of kernel-per-session is amortizing the startup cost across many calls
instead of paying a smaller version of it repeatedly forever.

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
- `KernelExecutor` — persistent: one real IPython kernel, reused.
- `observation_from_result()` — shared formatting so `loop.py` behaves
  identically no matter which backend produced the result.

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
outputs) runs the chapter's required comparison directly: the same 3-action
sequence (`x = 10`, `y = 20`, `print(x + y)`) against a real
`SubprocessExecutor` and a real `KernelExecutor`, with per-step
success/duration and a discussion of what the numbers mean.

To extend it yourself: add a 4th and 5th action to `ACTION_SEQUENCE` that
each depend on the previous one (e.g. `z = x + y`, `print(z * 2)`) and rerun
— the subprocess backend should fail starting at whichever step first
references prior state; the kernel backend should keep succeeding.

## 8. Failure Lab

Reproduce a kernel-specific failure that a subprocess backend structurally
cannot have: run `kernel.run("while True: pass")` against a fresh
`KernelExecutor` with a short `get_iopub_msg` timeout, or more safely,
observe that a kernel that crashes or hangs mid-execution leaves the
*entire session's* accumulated state unrecoverable — every variable set in
every prior `run()` call is gone, because there's only one interpreter and it
just died. Contrast with `SubprocessExecutor`: a hung or crashed call there
only ever loses that one action's result; every other call was already a
fresh process anyway. This is the honest cost of kernel-per-session
persistence: it concentrates risk into one long-lived process instead of
spreading it across many short-lived ones. (`KernelExecutor` has no restart
logic — that's a gap intentionally left for Chapter 26's guardrail material.)

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
- **Startup cost is a real, payable-once investment, not free.** Don't reach
  for `KernelExecutor` for a workload that's dominated by single, unrelated
  actions — the 730ms is wasted if nothing after it needs the kernel's state.
- **A persistent kernel is a single point of failure for the whole run's
  state**, as the Failure Lab shows. Any production use of a kernel backend
  needs a restart/recovery story — out of scope for this minimal v0, flagged
  for later.

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
| Per-call overhead | Lowest | ~15-20ms (measured) | ~4-8ms after startup (measured) |
| One-time startup cost | None | None | ~730ms (measured) |
| Process isolation from the harness | None | Full (separate OS process) | Full (separate OS process) |
| Protocol | Direct `exec()` call | stdin/stdout via `subprocess` | Real Jupyter `execute_request`/`iopub` |

## 13. Review Questions

1. Why does `SubprocessExecutor`'s step 3 fail with a *real* `NameError`
   rather than some kind of "no state available" error — what does that
   distinction tell you about what a subprocess actually is?
2. What three IPython message types does `KernelExecutor.run()` handle, and
   what would break if it ignored `execute_result` entirely?
3. If a task needed exactly one code action and nothing else, which backend
   would you choose, and why would `KernelExecutor`'s startup cost be pure
   waste in that case?
4. What is the one thing `run_agent` is never allowed to do, per this
   chapter's design, regardless of which `Executor` it's given?
5. Why is losing all session state after one crashed call a *structural*
   property of kernel-per-session, not a bug that better error handling
   could fully eliminate?

## 14. Chapter Summary

The execution backend is a real design choice, not an implementation detail:
one-shot execution (a fresh interpreter per action) trades away state
persistence for isolation and simplicity; a persistent kernel trades a
one-time startup cost for real state continuity and lower per-call latency
afterward. Measured directly on an identical 3-action sequence: subprocess
paid ~15-20ms per call but failed the state-dependent step 3 with a genuine
`NameError`; the kernel paid ~730ms once, then answered each call in a few
milliseconds, and passed step 3 correctly. `src/backbone_agent/executor.py`
now exposes both behind one `Executor` interface (alongside Chapter 5's
`InProcessExecutor`), and `loop.py::run_agent` accepts any of them via a new
`executor` parameter without any change to its own control flow — confirmed
via the regression smoke test after the refactor.

## 15. Chapter Deliverable

**An execution-backend interface with two implementations** —
`SubprocessExecutor` and `KernelExecutor` in `src/backbone_agent/executor.py`
(behind the shared `Executor` interface, alongside Chapter 5's
`InProcessExecutor`) — documented with measured results in
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
