"""Generate the Chapter 3 notebook from readable source.

Run from this directory:
    python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 3 — The Reason–Act–Observe Loop

This lab runs one task through ReAct-shaped and CodeAct-shaped loops, then
demonstrates why correct observations do not guarantee a correct answer.

The model output is scripted for determinism. Tool calls and code execution are
real within the in-memory teaching environment in
[`../code/react_vs_codeact.py`](../code/react_vs_codeact.py)."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from react_vs_codeact import (
    TASK_PROMPT, REACT_SCRIPT, ScriptedReActModel, run_react_loop,
    CODEACT_THOUGHT, CODEACT_CODE, run_codeact_loop, read_file,
    render_timeline, LONG_WORKSPACE, CORRECT_LONG_REACT_SCRIPT,
    FLAWED_LONG_REACT_SCRIPT, run_long_react_loop, run_long_codeact_loop,
)

print(TASK_PROMPT)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. Same loop, different action shape

`run_react_loop` calls `read_file` once per action. `run_codeact_loop`
executes one fixed code block. Both produce the same answer, but composition
lives in different parts of the system."""
))

cells.append(nbf.v4.new_code_cell(
"""react_transcript = run_react_loop(ScriptedReActModel(REACT_SCRIPT))
for kind, text in react_transcript:
    print(f"{kind}: {text}")

n_actions = sum(1 for kind, _ in react_transcript if kind == "Action")
print(f"\\nReAct-shaped trace: {n_actions} actions, {len(react_transcript)} entries")"""
))

cells.append(nbf.v4.new_code_cell(
"""codeact_transcript = run_codeact_loop(
    CODEACT_THOUGHT, CODEACT_CODE, {"read_file": read_file}
)
for kind, text in codeact_transcript:
    print(f"{kind}: {text}")

n_actions = sum(1 for kind, _ in codeact_transcript if kind.startswith("Action"))
print(f"\\nCodeAct-shaped trace: {n_actions} action, {len(codeact_transcript)} entries")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. Correct observations can still lead to a wrong answer

The next two six-file scripts receive identical, correct observations. They
differ at one reasoning step, where the flawed script treats `55 > 42` as
false. This isolates the difference between correct environment feedback and
correct interpretation of that feedback."""
))

cells.append(nbf.v4.new_code_cell(
"""expected_file = max(LONG_WORKSPACE, key=lambda path: int(LONG_WORKSPACE[path]))
expected_value = int(LONG_WORKSPACE[expected_file])

print(f"Ground truth: {expected_file} = {expected_value}; result = {expected_value + 10}")
print("\\nCorrect decision:")
print(CORRECT_LONG_REACT_SCRIPT[4].thought)
print("\\nFlawed decision:")
print(FLAWED_LONG_REACT_SCRIPT[4].thought)"""
))

cells.append(nbf.v4.new_code_cell(
"""correct_trace = run_long_react_loop(CORRECT_LONG_REACT_SCRIPT)
flawed_trace = run_long_react_loop(FLAWED_LONG_REACT_SCRIPT)

print(f"Correct trace: {correct_trace[-1][1]}")
print(f"Flawed trace:  {flawed_trace[-1][1]}")
print("\\nBoth traces received correct values from every read_file action.")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""The environment is correct, but the flawed script's state is not. The loop
checks that each action executes; it has no postcondition that validates the
selected maximum. Successful actions therefore do not prove task success."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Delegate deterministic computation

The CodeAct-shaped version delegates comparison to Python's `max()` instead of
tracking a running value in prose."""
))

cells.append(nbf.v4.new_code_cell(
"""code_trace, code_answer = run_long_codeact_loop()
for kind, text in code_trace:
    print(f"{kind}: {text}")
print(f"\\nAnswer: {code_answer}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""This makes the comparison explicit and testable; it does not make generated
code automatically correct. Replacing `max()` with `min()`, omitting a file,
or parsing values incorrectly would still produce a wrong result. Reliable
loops verify outcomes, not merely successful execution."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 4. Conceptual lineage

ReAct, PAL, Toolformer, and CodeAct address related but distinct questions:
interleaved acting, interpreter-aided computation, learned API use, and
executable code actions."""
))

cells.append(nbf.v4.new_code_cell(
"""print(render_timeline())"""
))

nb["cells"] = cells

with open("ch03_react_vs_codeact.ipynb", "w") as notebook_file:
    nbf.write(nb, notebook_file)

print("wrote ch03_react_vs_codeact.ipynb")
