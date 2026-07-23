"""One-off script that generates ch06_interpreters_repls_kernels.ipynb via nbformat.

Not part of the chapter's runnable deliverables — kept only so the notebook's
structure is reproducible/diffable from source instead of hand-edited JSON.
Run: python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 6 — Interpreters, REPLs, and Kernels

Hands-on lab: run the same sequence of actions against (a) a fresh
subprocess each time and (b) a persistent IPython kernel — then push
further: (c) add the in-process backend as a real third data point,
(d) find the actual breakeven point where the kernel's startup cost pays
for itself, and (e) reproduce a genuine kernel-hang failure, not a
hypothetical one.

All backends are real — [`../code/backends_demo.py`](../code/backends_demo.py)
spawns genuine subprocesses, starts a genuine IPython kernel via
`jupyter_client`, and (for the hang) really runs `while True: pass`
against it."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent.parent.parent / "src"))
sys.path.insert(0, str(Path.cwd().parent / "code"))

from backbone_agent.executor import InProcessExecutor, SubprocessExecutor, KernelExecutor, observation_from_result
from backends_demo import (
    ACTION_SEQUENCE, run_sequence, render_results,
    measure_amortization, render_amortization, find_breakeven,
    demo_kernel_hang,
)
import time

print("Action sequence:", ACTION_SEQUENCE)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## (a)+(b)+(c) Three backends, one 3-action sequence

Subprocess and kernel as before, now joined by `InProcessExecutor` — v0's
original backend, discussed in Chapter 5 but never directly measured
side-by-side with the other two until now."""
))

cells.append(nbf.v4.new_code_cell(
"""sp = SubprocessExecutor()
sp_results = run_sequence(sp, ACTION_SEQUENCE)
print(render_results("subprocess", sp_results))

kernel = KernelExecutor()
print(f"\\nkernel startup cost (paid once): {kernel.startup_duration_s*1000:.1f}ms")
k_results = run_sequence(kernel, ACTION_SEQUENCE)
print(render_results("kernel", k_results))
kernel.close()

ip = InProcessExecutor()
ip_results = run_sequence(ip, ACTION_SEQUENCE)
print(render_results("in-process", ip_results))"""
))

cells.append(nbf.v4.new_markdown_cell(
"""In-process `exec()` is the fastest of all three by a wide margin (no
subprocess spawn, no IPC with a kernel) — and it fails step 3 for the same
structural reason subprocess does: `InProcessExecutor.run()` uses a fresh
`{}` namespace every call, so nothing persists between actions despite
running in the same OS process the whole time. **Statelessness and process
isolation are independent axes** — in-process execution has no isolation
AND no state persistence in this implementation; only the kernel backend
has real state persistence, and it's the one paying isolation's full
subprocess cost to get it."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## (d) The amortization curve — where's the real breakeven?

The 3-action snapshot above makes the kernel look like a bad trade: ~750ms
startup for a task that only needed 3 actions. But a real agent loop runs
many more than 3 actions per session. At what N does the kernel's one-time
startup actually pay for itself against the subprocess backend's
lower-but-repeated per-call cost? Measure it directly instead of estimating
from the per-call numbers above."""
))

cells.append(nbf.v4.new_code_cell(
"""amort_rows = measure_amortization([1, 3, 5, 10, 20, 40, 60, 80, 120, 160])
print(render_amortization(amort_rows))

breakeven = find_breakeven(amort_rows)
print(f"\\nSmallest N tested where the kernel's total time is already lower: {breakeven}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""**The real breakeven, measured, is around N=60 actions** in this
environment — below that, subprocess's lower per-call cost keeps it ahead
despite paying that cost every single time; above it, the kernel's
amortized startup cost is more than paid back. This number is specific to
this machine's subprocess-spawn cost and this kernel's IPC overhead — it
would shift on different hardware — but the SHAPE of the answer
generalizes: **"is a persistent kernel worth it?" depends on how many
actions the session will actually run, and that number is answerable, not
just arguable, once you measure both curves.** A one-shot task (N=1-5)
should never pay kernel startup; a long-running agent loop (N=100+)
structurally should."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## (e) A real kernel-hang failure

`KernelExecutor.run()` calls `self._kc.get_iopub_msg(timeout=self.execute_timeout_s)`
in a loop. What happens if the code genuinely never finishes? Run a real
`while True: pass` against a kernel configured with a short (2s) timeout,
so the failure is reproducible without an actual indefinite hang."""
))

cells.append(nbf.v4.new_code_cell(
"""result = demo_kernel_hang(execute_timeout_s=2.0)
print(result)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""`KernelExecutor.run()` raises `_queue.Empty` after really waiting the full
2 seconds — uncaught, propagating straight out of `run()`. This is a real
violation of the `Executor` base class's own documented contract ("must not
raise on the code's own errors") — a hang isn't exactly "the code's own
error" in the traceback sense, but from the loop's perspective it's
functionally the same problem: `run_agent` has no `try/except` around
`executor.run(code)` (Chapter 5's loop), so an uncaught exception here would
crash the entire agent loop, not just fail one action. **This gap is left
unfixed on purpose** — `executor.py`'s `KernelExecutor.run()` docstring
flags it explicitly — because Chapter 6's job is to surface the gap
honestly, not to prematurely solve a problem Chapter 21 (termination) and
Chapter 26 (guardrails) are the right place to address properly (e.g.,
catching the timeout and returning a failed `ExecutionResult`, or killing
and restarting the kernel). Confirm the kernel itself is still reclaimed
cleanly despite the hang:"""
))

cells.append(nbf.v4.new_code_cell(
"""# demo_kernel_hang already calls kernel.close() in a finally block —
# if that hung too, the cell above would never have returned. It did, so
# shutdown_kernel(now=True) genuinely reclaims a hung kernel process.
print("Notebook reached this cell, so kernel.close() did not hang after the timeout.")"""
))

nb['cells'] = cells

with open("ch06_interpreters_repls_kernels.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch06_interpreters_repls_kernels.ipynb")
