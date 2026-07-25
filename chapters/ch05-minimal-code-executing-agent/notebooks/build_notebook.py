"""Generate the Chapter 5 notebook from readable source.

Run from this directory:
    python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 5 — A Minimal Code-Executing Agent

This lab isolates the five mechanics of the first agent:

```text
generate → extract → execute → observe → repeat or finish
```

A scripted model keeps the lab deterministic and offline. Only the model call
is replaced; code extraction, execution, observation formatting, loop control,
and termination use the real backbone implementation."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from reliability_and_ablation import (
    ScriptedModel,
    check_code_extraction,
    check_error_recovery_path,
    check_observation_feedback,
    check_step_budget,
    check_termination_signal,
    run_with_script,
)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. Generate and extract

The v0 protocol recognizes one fenced Python block as an action. Plain text
without a recognized block is treated as the final answer."""
))

cells.append(nbf.v4.new_code_cell(
"""check_code_extraction()
print("PASS: fenced action and plain-text finish are distinguished")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. Execute and observe

The first scripted reply prints `42`. Before returning the second reply, the
script asserts that the real stdout was appended to model context as an
observation."""
))

cells.append(nbf.v4.new_code_cell(
"""model = ScriptedModel(
    "```python\\nprint(6 * 7)\\n```",
    lambda messages: (
        "The final answer is 42."
        if messages[-1]["content"] == "Observation:\\n42\\n"
        else (_ for _ in ()).throw(AssertionError("observation missing"))
    ),
)

answer, trace = run_with_script(
    "Compute 6 * 7 with code.",
    model,
    return_trace=True,
)

for message in trace:
    print(f"{message['role'].upper()}: {message['content']}")
print(f"\\nFinal answer: {answer}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""The second model call is what makes this a feedback loop rather than
generate-and-execute once."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Return errors as observations

The next check executes `10 / 0`, confirms that the real traceback enters
context, executes corrected code, and then finishes."""
))

cells.append(nbf.v4.new_code_cell(
"""check_error_recovery_path()
print("PASS: traceback → corrected action → successful observation → finish")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""The correction is scripted. This verifies the feedback path, not a live
model's ability to diagnose arbitrary failures."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 4. Terminate or exhaust the budget

Plain text is v0's success signal. A model that keeps emitting code is stopped
by `max_steps`."""
))

cells.append(nbf.v4.new_code_cell(
"""check_termination_signal()
check_step_budget()
print("PASS: final-text termination and step-budget failure")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 5. Optional live evaluation

Run the three curriculum tasks from the repository root after configuring
`BACKBONE_MODEL` and its provider credentials:

```bash
python chapters/ch05-minimal-code-executing-agent/code/three_tasks_demo.py
```

That script verifies a computation, a file transformation, and an API-free
data-analysis answer against independently calculated expectations. Live-model
results are evaluations of that configured model and environment; they are not
required to understand or test the loop mechanics above."""
))

nb["cells"] = cells

with open("ch05_minimal_agent.ipynb", "w") as notebook_file:
    nbf.write(nb, notebook_file)

print("wrote ch05_minimal_agent.ipynb")
