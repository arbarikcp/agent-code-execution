"""Generate the Chapter 4 notebook from readable source.

Run from this directory:
    python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 4 — Why Code Execution?

This lab examines four mechanisms behind code actions:

1. composition under a step budget;
2. reuse of an available runtime library;
3. interpreter errors as revision feedback;
4. dependence on changing environment state.

The first experiment is a deterministic protocol simulation, not a live-model
success benchmark. The remaining examples execute real Python but use
prewritten actions."""
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
"""## 1. Step-budget feasibility

For a `k`-file task, this simulation assumes a one-call-per-turn structured
protocol needs `k + 2` steps, while one compound code action plus a final
response needs 2. The table asks which sampled traces fit an eight-step limit."""
))

cells.append(nbf.v4.new_code_cell(
"""ks = [1, 3, 5, 6, 7, 10, 20]
results = run_benchmark(ks, max_steps=8)
print(render_benchmark_table(results))

summary = summarize_benchmark(results)
for approach, stats in summary.items():
    print(
        f"{approach}: {stats['n_fit']}/{stats['n_tasks']} traces fit "
        f"({stats['fit_rate']:.0%}); average steps needed = "
        f"{stats['avg_steps_needed']:.1f}"
    )"""
))

cells.append(nbf.v4.new_markdown_cell(
"""The fractions describe these selected task sizes under the stated formulas.
No model chose actions, so they must not be reported as empirical task-success
rates. Parallel calls or a batch-read tool would change the structured
protocol."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. Sweep the budget

Changing the budget exposes the boundary implied by the same formulas."""
))

cells.append(nbf.v4.new_code_cell(
"""budget_sweep = sweep_budgets([3, 4, 6, 8, 10, 12, 16, 24], ks)
print(render_budget_sweep(budget_sweep))"""
))

cells.append(nbf.v4.new_markdown_cell(
"""A structured trace fits when `k + 2 <= budget`; the code trace fits whenever
`budget >= 2`. The curve is therefore algebraic, not probabilistic. As an
extension, add a `read_many_files(paths)` tool and derive a new formula."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Runtime library reuse

The code action imports `statistics.mean`, which is already present in the
Python runtime. No dedicated `compute_mean` tool is registered, although the
runtime and import policy are still dependencies."""
))

cells.append(nbf.v4.new_code_cell(
"""mean_result = demo_tool_reuse()
print(f"code action result: {mean_result}")
print(f"Example dedicated tool schema:\\n{HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""A general calculator, batch-processing tool, or harness function could
provide the same capability without arbitrary code. Code becomes more valuable
when useful operations are numerous or difficult to enumerate in advance."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 4. Runtime feedback

The first prewritten action divides by zero. The demo captures the real
traceback, then runs a second prewritten action that handles zero safely."""
))

cells.append(nbf.v4.new_code_cell(
"""traceback_text, fixed_avg = demo_dynamic_revision()
print(f"Error observation: {traceback_text.strip().splitlines()[-1]}")
print(f"Result from corrected action: {fixed_avg}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""This proves that an interpreter can supply actionable feedback. It does not
prove that a live model will diagnose or repair the error correctly."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 5. Changing environment state

The same source reads the clock twice. Different results show that preserving
source code alone is insufficient for reproducibility."""
))

cells.append(nbf.v4.new_code_cell(
"""first, second = demo_nondeterminism()
print(f"run 1: {first}")
print(f"run 2: {second}")
print(f"different observed values: {first != second}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""This behavior is not unique to code: a structured time or network tool can
also observe changing state. A narrow tool registry makes those capabilities
explicit; a broad runtime may expose them through imports or system APIs."""
))

nb["cells"] = cells

with open("ch04_why_code_execution.ipynb", "w") as notebook_file:
    nbf.write(nb, notebook_file)

print("wrote ch04_why_code_execution.ipynb")
