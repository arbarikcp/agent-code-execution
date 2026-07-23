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

Hands-on lab: reproduce a small CodeAct-style example and measure success and
step count against a JSON-tool baseline, per
`agent_code_execution_study_guide.md` Chapter 4's hands-on direction.

This notebook runs three separate, real demonstrations — one per empirical
claim in the chapter's Detailed Explanation — from
[`../code/why_code.py`](../code/why_code.py). None of the numbers below are
asserted; they're computed by actually executing the code each time this
notebook runs."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from why_code import (
    run_benchmark,
    summarize_benchmark,
    render_benchmark_table,
    demo_tool_reuse,
    HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN,
    demo_dynamic_revision,
)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. Composability under a shared step budget

Same task family as Chapters 2–3 (sum k files), now run across a *range* of
k, under a shared 8-step budget — a stand-in for the kind of per-task step
ceiling Chapter 27 formalizes later. JSON tool calling needs `k + 2` steps
(k reads + 1 write + 1 final answer); a code action needs a constant 2 steps
(1 code action + 1 final answer) no matter how large k gets. Both solvers
really execute against a real (in-memory) workspace, and every success is
checked against the real expected sum via an `assert` in
`run_benchmark` — nothing here is a canned pass/fail."""
))

cells.append(nbf.v4.new_code_cell(
"""ks = [1, 3, 5, 6, 7, 10, 20]
results = run_benchmark(ks, max_steps=8)
print(render_benchmark_table(results))"""
))

cells.append(nbf.v4.new_code_cell(
"""summary = summarize_benchmark(results)
for approach, stats in summary.items():
    print(f"{approach}: {stats['n_success']}/{stats['n_tasks']} succeeded "
          f"({stats['success_rate']:.0%}), avg steps needed = {stats['avg_steps_needed']:.1f}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""**Reading this table:** at k=6, JSON tool calling exactly fits the 8-step
budget (8 steps: 6 reads + write + final). At k=7 it needs 9 steps and fails
outright — not a degraded answer, a hard miss, because the harness would cut
it off mid-task. The code action never comes close to the budget at any k
tested, because its step count doesn't scale with k at all.

This is our own toy benchmark, sized to make the effect visible in under 10
tasks — it is not a reproduction of the CodeAct paper's own benchmark numbers
(see the chapter README for the paper's verified claim: "up to 20% higher
success rate" on API-Bank, across 17 LLMs). The mechanism is the same one the
paper's real benchmark exercises at much larger scale: a fixed step/turn
budget increasingly favors an action space whose step count doesn't grow with
task size."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. Tool reuse — zero registration for existing library code

A code action can call `statistics.mean` — an ordinary stdlib function nobody
registered as an agent tool — the moment `import statistics` runs. JSON tool
calling has no equivalent: every new *kind* of operation needs a schema
defined and exposed in advance, like the one shown below for the same
"compute a mean" operation."""
))

cells.append(nbf.v4.new_code_cell(
"""mean_result = demo_tool_reuse()
print(f"code action result: {mean_result}")
print()
print("JSON mode would first need a schema like:")
print(HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Dynamic revision — a real traceback drives a real fix

The first code action really divides by zero (`count.txt` holds `"0"`); its
real traceback is captured, not hand-written. The second code action is
written *as if* informed by that traceback — it guards the zero-count case —
and really succeeds on the same (real) execution."""
))

cells.append(nbf.v4.new_code_cell(
"""traceback_text, fixed_avg = demo_dynamic_revision()
print("First action's real traceback:")
print(traceback_text)
print(f"Second action's result after the fix: {fixed_avg}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## Chapter deliverable input

The numbers computed in this notebook — the 8-step-budget success rates
(100% code vs. 57% JSON tool calls here), the tool-reuse demonstration, and
the traceback-driven fix — are the "benchmark notes" the chapter's written
rationale (`code_as_action_rationale.md`) cites directly, alongside the
CodeAct paper's own verified claim."""
))

nb['cells'] = cells

with open("ch04_why_code_execution.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch04_why_code_execution.ipynb")
