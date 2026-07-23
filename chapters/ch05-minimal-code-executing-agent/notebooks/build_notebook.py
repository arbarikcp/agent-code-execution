"""One-off script that generates ch05_minimal_agent.ipynb via nbformat.

Not part of the chapter's runnable deliverables — kept only so the notebook's
structure is reproducible/diffable from source instead of hand-edited JSON.
Run: python build_notebook.py   (requires GROQ_API_KEY in the environment —
this notebook makes real, live model calls, per CLAUDE.md's "run everything
you write.")
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 5 — A Minimal Code-Executing Agent

Hands-on lab: build the backbone agent and solve three small tasks (a math
problem, a file transform, an API-free data task), per
`agent_code_execution_study_guide.md` Chapter 5's hands-on direction.

This is the first chapter in the guide that makes a **live model call** —
every response below is real output from `groq/llama-3.3-70b-versatile` via
litellm, not scripted. Requires `GROQ_API_KEY` in the environment."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent.parent.parent / "src"))
sys.path.insert(0, str(Path.cwd().parent / "code"))

from backbone_agent import run_agent
from backbone_agent.loop import SYSTEM_PROMPT

print(SYSTEM_PROMPT)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. Smallest possible run

One trivial task, full trace shown, to see the loop's mechanics before the
three hands-on tasks: the model emits a code block, `run_agent` really
executes it, the real result is appended as the next message, and the model
is called again — this time producing plain text (no code block), which
`run_agent` recognizes as the final answer per the stop signal in
`SYSTEM_PROMPT`."""
))

cells.append(nbf.v4.new_code_cell(
"""answer, messages = run_agent("What is 17 * 23? Compute it, don't just guess.", return_trace=True)
for m in messages:
    if m["role"] == "system":
        continue
    print(f"--- {m['role']} ---")
    print(m["content"].strip())
    print()
print("FINAL ANSWER:", answer)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. Three hands-on tasks

`three_tasks_demo.py` defines a math problem, a file transform (real CSV in,
real file written out), and an API-free data task, and verifies each against
an independently computed ground truth — not by trusting the agent's own
claim."""
))

cells.append(nbf.v4.new_code_cell(
"""from three_tasks_demo import task_1_math, task_2_file_transform, task_3_data_stats, render_trace

results = []"""
))

cells.append(nbf.v4.new_markdown_cell("### Task 1 — math (sum of the first 20 primes)"))

cells.append(nbf.v4.new_code_cell(
"""r1 = task_1_math()
results.append(r1)
print(render_trace(r1["messages"]))
print(f"\\nExpected: {r1['expected']}  |  Success: {r1['success']}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""### Task 2 — file transform (average a CSV column, write a real file)

Watch this one closely: the model's first attempt commonly reaches for
`pandas`, which isn't installed in this minimal environment — a real
`ModuleNotFoundError`, not staged. Per the chapter's "first thing that will
go wrong" fill-in pointer, this *is* that first thing, caught live. The
traceback becomes the next Observation, and the model's second code action
switches to the stdlib `csv` + `statistics` modules and succeeds."""
))

cells.append(nbf.v4.new_code_cell(
"""r2 = task_2_file_transform()
results.append(r2)
print(render_trace(r2["messages"]))
print(f"\\nExpected: {r2['expected']}  |  Success: {r2['success']}")
print(f"File written: {r2['file_written']}  |  File contents: {r2['file_contents']!r}")"""
))

cells.append(nbf.v4.new_markdown_cell("### Task 3 — API-free data task (mean/median/stdev)"))

cells.append(nbf.v4.new_code_cell(
"""r3 = task_3_data_stats()
results.append(r3)
print(render_trace(r3["messages"]))
print(f"\\nExpected: {r3['expected']}  |  Success: {r3['success']}")"""
))

cells.append(nbf.v4.new_markdown_cell("## 3. Summary"))

cells.append(nbf.v4.new_code_cell(
"""n_success = sum(1 for r in results if r["success"])
print(f"{n_success}/{len(results)} tasks solved correctly")
for r in results:
    print(f"  - {r['name']}: {'OK' if r['success'] else 'FAILED'}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Whatever `ModuleNotFoundError` (or other failure) appears above is real,
live-model output from whichever run actually happened when this notebook
was last executed — not guaranteed to be identical every time it's re-run
(the model can choose a different first attempt), which is itself the
chapter's point about the first thing that goes wrong: it's *emergent* from
a real, imperfect environment, not something the harness pre-declared."""
))

nb['cells'] = cells

with open("ch05_minimal_agent.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch05_minimal_agent.ipynb")
