"""One-off script that generates ch01_what_is_an_agent.ipynb via nbformat.

Not part of the chapter's runnable deliverables — kept only so the notebook's
structure is reproducible/diffable from source instead of hand-edited JSON.
Run: python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 1 — What Is an Agent?

Hands-on lab: diagram three real systems (a chatbot, a RAG pipeline, a coding agent)
and label **model**, **loop**, **tools**, and **environment** in each, per
`agent_code_execution_study_guide.md` Chapter 1's hands-on direction.

The definitions live in [`../code/systems.py`](../code/systems.py) as data, not prose,
so the comparison below is forced to be concrete rather than hand-wavy."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from systems import ALL_SYSTEMS, render_comparison_table

print(render_comparison_table(ALL_SYSTEMS))"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## Reading the table

Only the coding agent has `Model-driven loop? = YES`. That single column is the
whole argument of Chapter 1: **"agent" names the loop, not the model.** The chatbot
and the RAG pipeline both call a (possibly very capable) LLM, but in neither case
does the model's own output determine what happens next in the environment — a
human decides the chatbot's next turn, and an engineer's fixed graph decides the
RAG pipeline's next step. Only the coding agent feeds its own action's consequence
(the observation) back into its own next decision.

Let's look at each system's full breakdown."""
))

cells.append(nbf.v4.new_code_cell(
"""for system in ALL_SYSTEMS:
    print(f"=== {system.name} ===")
    print(f"  autonomy:            {system.autonomy.name}")
    print(f"  model_role:          {system.model_role}")
    print(f"  has_model_driven_loop: {system.has_model_driven_loop}")
    print(f"  loop:                {system.loop_description}")
    print(f"  tools:               {system.tools}")
    print(f"  environment:         {system.environment}")
    print(f"  action_unit:         {system.action_unit}")
    print(f"  observation_unit:    {system.observation_unit}")
    print()"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## The controller view

Chapter 1 also asks us to see the model as a **policy**: a function from context to
next action, `pi(context) -> action`. The three systems differ in what that policy
is allowed to condition on and what its output controls:

| System | `pi` conditions on | `pi`'s output controls |
|---|---|---|
| Chatbot | conversation so far | the next chat message only |
| RAG pipeline | retrieved passages + question (fixed input) | the final answer text only |
| Coding agent | full history of its **own prior actions and observations** | the next action, which changes the environment, which changes the next observation |

Only in the coding agent does `pi`'s output feed back into `pi`'s own future input.
That closed loop — action changes environment, environment changes observation,
observation changes context, context changes the next action — is what the rest of
this guide calls **the agent loop**, and it is orthogonal to how smart the
underlying model is."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## Sanity check: autonomy is an axis, not a binary

`Autonomy` in `systems.py` is ordered `SINGLE_CALL < FIXED_PIPELINE < SINGLE_TOOL_CALL
< AUTONOMOUS_LOOP`. A single JSON tool call (the model picks *one* tool, once, no
iteration on the result) sits between a fixed pipeline and a full autonomous loop —
it's more model-driven than a hardcoded graph, but it still isn't a loop, because
nothing feeds the tool's result back for the model to act on again. Print the
ordering to confirm it matches the enum's declaration order."""
))

cells.append(nbf.v4.new_code_cell(
"""from systems import Autonomy

for level in Autonomy:
    print(level.value, level.name)"""
))

nb['cells'] = cells

with open("ch01_what_is_an_agent.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch01_what_is_an_agent.ipynb")
