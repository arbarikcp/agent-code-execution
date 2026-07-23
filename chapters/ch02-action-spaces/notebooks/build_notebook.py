"""One-off script that generates ch02_action_spaces.ipynb via nbformat.

Not part of the chapter's runnable deliverables — kept only so the notebook's
structure is reproducible/diffable from source instead of hand-edited JSON.
Run: python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 2 — Action Spaces: Text, JSON, and Code

Hands-on lab: express the same three-step task as (a) JSON tool calls and
(b) a single code action, then compare turns and tokens, per
`agent_code_execution_study_guide.md` Chapter 2's hands-on direction.

Task: files `a.txt`, `b.txt`, `c.txt` each hold one integer; sum them and write
the result to `total.txt`. Definitions live in
[`../code/action_spaces.py`](../code/action_spaces.py); token counts below are
real measurements from `tiktoken`, not asserted numbers."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from action_spaces import (
    FREE_TEXT_AMBIGUOUS_VARIANTS,
    JSON_SYSTEM_PROMPT,
    TOOL_SCHEMAS,
    CODE_SYSTEM_PROMPT,
    build_json_tool_call_trace,
    build_code_action_trace,
    render_comparison,
    summarize,
)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. Free text — why it's fragile

Four different, equally plausible ways a model might phrase "I'm about to read
a.txt" in free text. None of these is wrong, but a hand-written parser has to
anticipate every one of them (and the ones the model will phrase differently
next time) to reliably extract "call read_file('a.txt')" as the intended
action. This is the fragility the chapter's subtopic refers to — there is no
schema, so extraction is guesswork."""
))

cells.append(nbf.v4.new_code_cell(
"""for variant in FREE_TEXT_AMBIGUOUS_VARIANTS:
    print(f"- {variant!r}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. JSON tool calling — the schema and one turn

Structured tool calling fixes the fragility above by giving the model a fixed
vocabulary (`TOOL_SCHEMAS`) and a fixed response shape. Here's the schema for
the two tools available, and the system prompt that constrains output to
exactly one JSON tool call per turn."""
))

cells.append(nbf.v4.new_code_cell(
"""print(JSON_SYSTEM_PROMPT)
print()
for schema in TOOL_SCHEMAS:
    print(schema)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Code action — the system prompt

Compare that to the code-action system prompt: no JSON schema to define at
all, because the "interface" is just two Python functions the model already
knows how to call from having seen millions of function calls in training."""
))

cells.append(nbf.v4.new_code_cell(
"""print(CODE_SYSTEM_PROMPT)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 4. Building both traces

`build_json_tool_call_trace()` reconstructs the task as 5 model turns (read
a.txt, read b.txt, read c.txt, write total.txt, final answer) — one tool call
per turn, the realistic minimum for 3 reads + 1 write + 1 final message.
`build_code_action_trace()` reconstructs it as 2 turns: one code action that
does all four operations, then a final answer.

Each turn's *input* is the full context that turn's model call would need —
system prompt + (for JSON) tool schemas + task + everything so far — because
that's what actually gets billed and actually grows every turn in a stateless
chat-completions call. This is "cost and step-count implications" made
concrete instead of asserted."""
))

cells.append(nbf.v4.new_code_cell(
"""json_trace = build_json_tool_call_trace()
code_trace = build_code_action_trace()

print(f"JSON mode: {len(json_trace)} model turns")
for t in json_trace:
    print(f"  - {t.label:<28} input={t.input_tokens:>4} tok  output={t.output_tokens:>3} tok")

print(f"\\nCode mode: {len(code_trace)} model turns")
for t in code_trace:
    print(f"  - {t.label:<28} input={t.input_tokens:>4} tok  output={t.output_tokens:>3} tok")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 5. The comparison matrix (Chapter Deliverable)

This table is the chapter's deliverable: turns and tokens, same task, two
action spaces."""
))

cells.append(nbf.v4.new_code_cell(
"""print(render_comparison())

json_summary = summarize(json_trace)
code_summary = summarize(code_trace)
turn_ratio = json_summary["turns"] / code_summary["turns"]
token_ratio = json_summary["total_tokens"] / code_summary["total_tokens"]
print(f"\\nJSON tool calling used {turn_ratio:.1f}x the turns and {token_ratio:.1f}x the tokens "
      f"of the single code action, for the identical task and identical final result.")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## Why the gap exists

Two compounding effects, visible directly in the per-turn breakdown above:

1. **Composition.** The code action does 3 reads + 1 sum + 1 write in one
   action because Python's control flow (a generator expression, a function
   call) *is* the composition mechanism. JSON tool calling has no control flow
   of its own — every individual operation needs its own round trip because
   the harness, not the model, decides what runs next between tool calls.
2. **Resent context.** Every JSON turn resends the system prompt, the full
   tool schema block, and the growing history of prior calls/results — that's
   why `input_tokens` climbs turn over turn (249 → 277 → 305 → 333 → 374 in
   the run above). The code action only ever needs 2 turns, so it only pays
   that resend cost twice.

Neither effect is specific to *this* task — they compound worse as the number
of steps grows, which is exactly Chapter 2's "cost and step-count
implications" subtopic, and exactly why Chapter 4 argues code scales better as
tasks get longer."""
))

nb['cells'] = cells

with open("ch02_action_spaces.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch02_action_spaces.ipynb")
