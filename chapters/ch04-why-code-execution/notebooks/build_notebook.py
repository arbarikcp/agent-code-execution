"""One-off script that generates ch04_why_code_execution.ipynb via nbformat.

Not part of the chapter's runnable deliverables — kept only so the notebook's
structure is reproducible/diffable from source instead of hand-edited JSON.
Run: python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 4 — Why Code Execution

Hands-on lab, pushed past a single 8-step-budget snapshot into four real
measurements from [`../code/why_code.py`](../code/why_code.py):

1. The original step-budget benchmark (one budget, one snapshot).
2. Does it generalize? A full SWEEP across budgets 3-24.
3. Tool reuse and dynamic revision (unchanged from the original chapter).
4. A real, measured non-determinism demonstration — not just asserted."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from why_code import (
    run_benchmark, summarize_benchmark, render_benchmark_table,
    sweep_budgets, render_budget_sweep,
    demo_tool_reuse, HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN,
    demo_dynamic_revision, demo_nondeterminism,
)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. The original snapshot: one budget (8), one set of task sizes"""
))

cells.append(nbf.v4.new_code_cell(
"""ks = [1, 3, 5, 6, 7, 10, 20]
results = run_benchmark(ks, max_steps=8)
print(render_benchmark_table(results))
summary = summarize_benchmark(results)
for approach, stats in summary.items():
    print(f"{approach}: {stats['n_success']}/{stats['n_tasks']} succeeded "
          f"({stats['success_rate']:.0%}), avg steps needed = {stats['avg_steps_needed']:.1f}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. Does the 57%-vs-100% gap generalize, or was budget=8 special?

One snapshot (57% vs. 100%) invites an obvious question: is that ratio
specific to `max_steps=8`, or does the pattern hold generally? Sweep the
budget itself, from a tight 3 steps up to a generous 24, holding the same
task sizes fixed."""
))

cells.append(nbf.v4.new_code_cell(
"""budget_sweep = sweep_budgets([3, 4, 6, 8, 10, 12, 16, 24], ks)
print(render_budget_sweep(budget_sweep))"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Code's success rate is **100% at every single budget tested**, including
the tightest one (3 steps) — because a code action never needs more than 2
steps regardless of task size, so any budget that could run an agent at all
is already enough. JSON tool calling's success rate climbs monotonically
with the budget — 14% -> 29% -> 57% -> 71% -> 86% -> 100% — only reaching
parity with code once the budget (24) is generous enough to fit every task
size in this particular test set. **The "max k JSON can fit" column makes
the mechanism explicit: it's always exactly `budget - 2`**, because JSON
needs `k+2` steps per task; there's nothing probabilistic or emergent about
the curve — it's a direct, exact consequence of the two step-cost formulas
(`k+2` vs. constant `2`). The 8-step snapshot from §1 is one point on this
line, not a cherry-picked special case."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Tool reuse and dynamic revision (unchanged mechanics)"""
))

cells.append(nbf.v4.new_code_cell(
"""mean_result = demo_tool_reuse()
print(f"code action result: {mean_result}")
print(f"JSON mode would first need a schema like:\\n  {HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN}")

traceback_text, fixed_avg = demo_dynamic_revision()
print(f"\\nFirst action's real traceback (tail): {traceback_text.strip().splitlines()[-1]}")
print(f"Second action's result after the fix: {fixed_avg}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 4. Non-determinism — measured, not just claimed

The original chapter asserted "non-determinism" as a cost of code actions
without demonstrating it. Here's a direct demonstration: run the exact same
source text twice and check whether the output differs."""
))

cells.append(nbf.v4.new_code_cell(
"""r1, r2 = demo_nondeterminism()
print(f"run 1: {r1}")
print(f"run 2: {r2}")
print(f"identical source code, different output: {r1 != r2}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Same source text (`import time; result = time.time()`), executed twice,
genuinely different results — not because anything went wrong, but because
`exec()` places no constraint at all on what a code action is allowed to
call. A JSON tool-calling system's non-determinism, by contrast, is bounded
by whatever tools were actually registered — if nobody registered a
`get_current_time` tool, the agent has no way to introduce this specific
non-determinism at all. This is the real, demonstrated shape of the
"wider failure surface" cost side of Chapter 4's argument: not a
hypothetical risk, a one-line reproduction."""
))

nb['cells'] = cells

with open("ch04_why_code_execution.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch04_why_code_execution.ipynb")
