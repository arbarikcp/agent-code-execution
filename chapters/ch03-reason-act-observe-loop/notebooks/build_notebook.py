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

Hands-on lab: hand-write a ReAct trace for a small task, then rewrite it as a
CodeAct trace, per `agent_code_execution_study_guide.md` Chapter 3's hands-on
direction.

Task: which of `a.txt`, `b.txt`, `c.txt` holds the largest number, and what is
that number plus 10? Both traces below run through a *real* loop against a
real (in-memory) environment — only the model's output is scripted (see
[`../code/react_vs_codeact.py`](../code/react_vs_codeact.py) for why that
distinction matters and is preserved throughout)."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from react_vs_codeact import (
    TASK_PROMPT,
    REACT_SCRIPT,
    ScriptedReActModel,
    run_react_loop,
    CODEACT_THOUGHT,
    CODEACT_CODE,
    run_codeact_loop,
    read_file,
    HISTORICAL_TIMELINE,
    render_timeline,
)

print(TASK_PROMPT)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. The ReAct trace

`REACT_SCRIPT` is hand-written: four `ReActStep`s, each pairing a `Thought`
with an `Action` (or, on the last step, a `Finish`). `ScriptedReActModel`
plays these back one at a time — standing in for a real model call, which
starts in Chapter 5 — but `run_react_loop` is a real loop: it really calls
`read_file` for each action and really threads the result back into context
as the next `Observation`, exactly per the "Thought / Action / Observation"
anatomy ReAct introduced."""
))

cells.append(nbf.v4.new_code_cell(
"""react_transcript = run_react_loop(ScriptedReActModel(REACT_SCRIPT))
for kind, text in react_transcript:
    print(f"{kind}: {text}")

n_actions = sum(1 for k, _ in react_transcript if k == "Action")
print(f"\\n{n_actions} actions, {len(react_transcript)} trace entries")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. The same task, rewritten as CodeAct

One `Thought`, one code block that does all three reads and the comparison in
Python's own control flow, then a `Finish`. `run_codeact_loop` really
`exec()`s `CODEACT_CODE` and captures its real stdout as the `Observation` —
nothing about the arithmetic or comparison is hand-computed ahead of time."""
))

cells.append(nbf.v4.new_code_cell(
"""print(CODEACT_CODE)"""
))

cells.append(nbf.v4.new_code_cell(
"""codeact_transcript = run_codeact_loop(CODEACT_THOUGHT, CODEACT_CODE, {"read_file": read_file})
for kind, text in codeact_transcript:
    print(f"{kind}: {text}")

n_actions = sum(1 for k, _ in codeact_transcript if k.startswith("Action"))
print(f"\\n{n_actions} action, {len(codeact_transcript)} trace entries")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Same answer, different shape

Both traces land on the identical, correctly computed answer
(`a.txt has the largest number (42); 42 + 10 = 52`) — the rewrite didn't
change *what* gets computed, only *how many actions* it took to get there:
ReAct needed 3 actions (one `read_file` per file) interleaved with 4
thoughts; CodeAct needed 1 action, because the comparison logic that ReAct
had to spread across 3 separate Thought steps is just ordinary Python control
flow (a dict comprehension + `max`) inside CodeAct's single code block. This
is the "From ReAct to CodeAct" shift the chapter's subtopic names: the
interleaving pattern (reason, act, observe, repeat) doesn't change — only the
action's *shape* does, from one-tool-call-per-turn to one-code-block-that-
composes-many-operations."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 4. Related lineage

The shift didn't happen in one step. `HISTORICAL_TIMELINE` in
`react_vs_codeact.py` records four papers in order, each verified (title,
authors, submission date) directly against their arXiv abstract pages rather
than recalled from memory:"""
))

cells.append(nbf.v4.new_code_cell(
"""print(render_timeline())"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Reading the progression: ReAct establishes the interleaved loop with
text-based actions. PAL (one month later) shows that offloading *computation*
specifically to a real Python interpreter beats doing arithmetic/logic in the
model's own text — but PAL is a single generate-then-execute step, not an
iterated loop. Toolformer explores training the tool-use decision into the
model itself rather than eliciting it via prompting. CodeAct (2024) is the
synthesis: keep ReAct's iterated loop, but make the action *itself* an
arbitrary, composable Python program the way PAL showed was more reliable for
computation — which is exactly the ReAct-trace-to-CodeAct-trace rewrite this
notebook just did by hand."""
))

nb['cells'] = cells

with open("ch03_react_vs_codeact.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch03_react_vs_codeact.ipynb")
