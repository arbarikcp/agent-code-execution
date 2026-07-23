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

Hands-on lab: run the same sequence of actions against (a) a fresh subprocess
each time and (b) a persistent IPython kernel, and observe the difference,
per `agent_code_execution_study_guide.md` Chapter 6's hands-on direction.

Both backends are real — [`../code/backends_demo.py`](../code/backends_demo.py)
spawns a genuine subprocess per call for (a), and starts one genuine IPython
kernel (via `jupyter_client`) for (b), reused across calls. Nothing here is
simulated."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent.parent.parent / "src"))
sys.path.insert(0, str(Path.cwd().parent / "code"))

from backbone_agent.executor import SubprocessExecutor, KernelExecutor, observation_from_result
from backends_demo import ACTION_SEQUENCE, run_sequence, render_results
import time

print("Action sequence:", ACTION_SEQUENCE)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## (a) Fresh subprocess per action

`SubprocessExecutor.run()` spawns `python -c <code>` — a brand-new OS
process — every single call. There is no "between calls" for a subprocess
backend: each process starts, runs, and exits."""
))

cells.append(nbf.v4.new_code_cell(
"""sp = SubprocessExecutor()
sp_start = time.monotonic()
sp_results = run_sequence(sp, ACTION_SEQUENCE)
sp_wall = time.monotonic() - sp_start
print(render_results("subprocess", sp_results))
print(f"\\ntotal wall time: {sp_wall*1000:.1f}ms")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Step 3 (`print(x + y)`) really fails with a real `NameError` — `x` and `y`
were set in *previous processes* that no longer exist by the time step 3's
process starts. This isn't a limitation we're choosing to demonstrate; it's
what a one-shot backend structurally cannot do."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## (b) Persistent IPython kernel

`KernelExecutor` starts one real IPython kernel via `jupyter_client`'s
`KernelManager`, and every `run()` call sends an `execute_request` to that
*same* kernel over its `execute_reply`/`iopub` channels — the real Jupyter
execution protocol, not a custom shortcut."""
))

cells.append(nbf.v4.new_code_cell(
"""kernel = KernelExecutor()
print(f"kernel startup cost (paid once): {kernel.startup_duration_s*1000:.1f}ms")

k_start = time.monotonic()
k_results = run_sequence(kernel, ACTION_SEQUENCE)
k_wall = time.monotonic() - k_start
print(render_results("kernel", k_results))
print(f"\\ntotal wall time (excl. startup): {k_wall*1000:.1f}ms")
kernel.close()"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Step 3 really succeeds — `x + y` prints `30` — because `x` and `y` still
exist in the *same* live interpreter's namespace. This is genuine
persistence, not an `Executor`-level trick: the kernel process itself never
restarted between calls."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## Reading the trade-off

Two numbers from the run above matter more than the raw milliseconds (which
will vary run to run):

1. **Per-call cost, ignoring startup:** the subprocess backend pays full
   Python interpreter startup on *every* call (observed here: ~15-20ms each);
   the kernel backend, once started, answers each call in a few milliseconds
   because there's no interpreter startup left to pay.
2. **Startup cost, paid once vs. never:** the kernel backend pays a real,
   one-time startup cost (observed here: several hundred milliseconds) that
   the subprocess backend never pays as a lump sum — but pays a smaller
   version of, repeatedly, on every single call instead.

For a short-lived, single-action task, a subprocess can be cheaper overall
(no startup investment to amortize). For a multi-step agent loop — the shape
this entire guide is about — a kernel's one-time startup is paid back
quickly once there are more than a handful of actions, *and* it's the only
one of the two that can pass step 3 at all. This is "startup cost and warm
kernels," measured rather than asserted."""
))

nb['cells'] = cells

with open("ch06_interpreters_repls_kernels.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch06_interpreters_repls_kernels.ipynb")
