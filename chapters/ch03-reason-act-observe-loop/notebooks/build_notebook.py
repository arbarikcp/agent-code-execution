"""One-off script that generates ch03_react_vs_codeact.ipynb via nbformat.

Not part of the chapter's runnable deliverables — kept only so the notebook's
structure is reproducible/diffable from source instead of hand-edited JSON.
Run: python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 3 — The Reason–Act–Observe Loop

Hands-on lab: hand-write a ReAct trace for a small task, then rewrite it as
a CodeAct trace — and then push further into the chapter's real question:
*why* does the rewrite matter beyond turn count? [`../code/react_vs_codeact.py`](../code/react_vs_codeact.py)
answers that with a constructed failure class, verified against PAL's own
abstract, not just a diagram."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from react_vs_codeact import (
    TASK_PROMPT, REACT_SCRIPT, ScriptedReActModel, run_react_loop,
    CODEACT_THOUGHT, CODEACT_CODE, run_codeact_loop, read_file,
    HISTORICAL_TIMELINE, render_timeline,
    LONG_WORKSPACE, LONG_TASK_PROMPT, CORRECT_LONG_REACT_SCRIPT,
    FLAWED_LONG_REACT_SCRIPT, run_long_react_loop, run_long_codeact_loop,
)

print(TASK_PROMPT)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. The baseline: ReAct trace vs. CodeAct rewrite (3 files)

Same as before — `run_react_loop` really calls `read_file` per action;
`run_codeact_loop` really `exec()`s one code block. Both land on the same
correct answer; the interesting question this notebook actually investigates
is *why* the rewrite is more than a turn-count optimization."""
))

cells.append(nbf.v4.new_code_cell(
"""react_transcript = run_react_loop(ScriptedReActModel(REACT_SCRIPT))
for kind, text in react_transcript:
    print(f"{kind}: {text}")
n_actions = sum(1 for k, _ in react_transcript if k == "Action")
print(f"\\n{n_actions} actions, {len(react_transcript)} trace entries")"""
))

cells.append(nbf.v4.new_code_cell(
"""codeact_transcript = run_codeact_loop(CODEACT_THOUGHT, CODEACT_CODE, {"read_file": read_file})
for kind, text in codeact_transcript:
    print(f"{kind}: {text}")
n_actions = sum(1 for k, _ in codeact_transcript if k.startswith("Action"))
print(f"\\n{n_actions} action, {len(codeact_transcript)} trace entries")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. A real failure class, not just fewer round trips

PAL's own abstract (Gao et al., 2022 — quote verified against the arXiv
abstract page) names a specific failure mode of chain-of-thought-style
reasoning: **"LLMs often make logical and arithmetic mistakes in the
solution part, even when the problem is decomposed correctly."** ReAct is
vulnerable to exactly this: a running comparison ("is this bigger than the
max so far?") lives entirely in free-form Thought text, re-derived at every
step, with nothing in the loop verifying a Thought's claim against the data
it just observed.

Two 6-file scripts below share **identical, individually-correct**
Observations — every `read_file` call returns the true value in both. They
differ at exactly one Thought (step 5), where the flawed script misjudges
`55 > 42` as false."""
))

cells.append(nbf.v4.new_code_cell(
"""expected_max_file = max(LONG_WORKSPACE, key=lambda f: int(LONG_WORKSPACE[f]))
expected_max_value = int(LONG_WORKSPACE[expected_max_file])
print(f"Ground truth (computed independently of either script): "
      f"{expected_max_file} = {expected_max_value}, so answer should be {expected_max_value + 10}")

print("\\n--- Correct script's Thought at the critical step ---")
print(CORRECT_LONG_REACT_SCRIPT[4].thought)
print("\\n--- Flawed script's Thought at the SAME step (same Observation: 55) ---")
print(FLAWED_LONG_REACT_SCRIPT[4].thought)"""
))

cells.append(nbf.v4.new_code_cell(
"""correct_transcript = run_long_react_loop(CORRECT_LONG_REACT_SCRIPT)
correct_answer = correct_transcript[-1][1]
print(f"CORRECT script finish: {correct_answer!r}")
print(f"  correct: {correct_answer == f'{expected_max_file} has the largest number ({expected_max_value}); {expected_max_value} + 10 = {expected_max_value+10}.'}")

flawed_transcript = run_long_react_loop(FLAWED_LONG_REACT_SCRIPT)
flawed_answer = flawed_transcript[-1][1]
print(f"\\nFLAWED script finish:  {flawed_answer!r}")
print("  every single Observation in this trace was still correct — only one Thought's arithmetic was wrong")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""The flawed trace's `Finish` answer is wrong — `a.txt`/`52` instead of the
correct `d.txt`/`65` — despite every `Observation` entry being genuinely
correct. Nothing in `run_react_loop` (or in ReAct's design) checks a
Thought's claim against the Observations it's reasoning about; the loop
only verifies that an ACTION executes and returns a real result, never that
a THOUGHT correctly interprets that result. One bad comparison at step 5
propagates silently through every subsequent step, because each later
Thought trusts the (now-wrong) "running max" claimed by the step before it."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Does the CodeAct rewrite structurally avoid this?

The same 6-file task as one CodeAct action, using Python's `max()` instead
of a chain of textual comparisons:"""
))

cells.append(nbf.v4.new_code_cell(
"""codeact_long_transcript, codeact_long_answer = run_long_codeact_loop()
for kind, text in codeact_long_transcript:
    print(f"{kind}: {text}")
print(f"\\nmatches ground truth: {codeact_long_answer == f'{expected_max_file} has the largest number ({expected_max_value}); {expected_max_value} + 10 = {expected_max_value+10}.'}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Correct, and NOT because this particular code happens to be bug-free — it's
correct because the comparison logic was never re-derived in prose at all.
`max(values, key=values.get)` either runs (and is exact, by the language's
own semantics) or raises; there's no intermediate state where the "current
max" is a claim floating in generated text that a later step might
misremember or misjudge. This doesn't mean code actions can't have bugs —
Chapter 4's dynamic-revision demo shows a real one — but it does mean this
SPECIFIC failure class (correct facts, wrong running interpretation of
them, propagating silently across steps) is structurally unavailable to a
single code action the way it is available to a multi-step Thought chain.
This is a sharper, mechanism-level version of PAL's abstract claim, not
just a restatement of it."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 4. Lineage, with verified quotes this time

`HISTORICAL_TIMELINE` now carries direct abstract quotes (checked against
each paper's arXiv page this session) instead of paraphrases — including
PAL's exact claim above and its verified GSM8K result (15% absolute over
chain-of-thought PaLM-540B)."""
))

cells.append(nbf.v4.new_code_cell(
"""print(render_timeline())"""
))

nb['cells'] = cells

with open("ch03_react_vs_codeact.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch03_react_vs_codeact.ipynb")
