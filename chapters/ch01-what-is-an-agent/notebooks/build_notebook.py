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

Hands-on lab: diagram three real systems (a chatbot, a RAG pipeline, a coding
agent) and label model, loop, tools, and environment in each, per
`agent_code_execution_study_guide.md` Chapter 1's hands-on direction — pushed
further here: instead of hand-labeling each system's autonomy, we DERIVE it
from four structural predicates (`../code/systems.py`), then deliberately
throw two boundary cases at the derivation to see whether it holds up."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from systems import (
    ALL_SYSTEMS, Autonomy, LoopPredicates, classify_autonomy,
    render_comparison_table, EXPECTED_CLASSIFICATION,
)

print(render_comparison_table(ALL_SYSTEMS))"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. The four predicates, and why hand-labeling isn't good enough

The first draft of this module just wrote `autonomy=Autonomy.FIXED_PIPELINE`
directly on each system. That's a claim with no way to check it — nothing
stops a mislabeled system from sitting there silently wrong. `LoopPredicates`
replaces that with four yes/no structural questions
(`policy_is_a_language_model`, `has_hardcoded_pipeline_steps`,
`model_chooses_the_action`, `loop_repeats_based_on_model_output`,
`observation_reenters_model_context` — five, actually), and
`classify_autonomy()` is a pure decision procedure over them. Answering the
predicates honestly for a new system is still a judgment call — but the
*classification itself* no longer is."""
))

cells.append(nbf.v4.new_code_cell(
"""for system in ALL_SYSTEMS:
    print(f"{system.name}")
    print(f"  {system.predicates}")
    print(f"  -> {system.autonomy.name}\\n")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. Checking the derivation against hand-reasoned expectations

Since the classification is now a pure function of the predicates, we can
check it: for each system, does the DERIVED autonomy match what careful
reasoning about that system says it should be? This isn't a unit test for its
own sake — it's the only thing standing between "the taxonomy is principled"
and "the taxonomy just happens to agree with itself.\""""
))

cells.append(nbf.v4.new_code_cell(
"""all_match = True
for system in ALL_SYSTEMS:
    expected = EXPECTED_CLASSIFICATION[system.name]
    match = system.autonomy == expected
    all_match &= match
    print(f"{system.name:<55} derived={system.autonomy.name:<22} expected={expected.name:<22} "
          f"{'OK' if match else 'MISMATCH'}")

assert all_match
print("\\nAll match.")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Boundary case 1 — "agentic RAG": does the NAME lie?

`AGENTIC_RAG` is built to test whether the taxonomy classifies by structure
or by branding. It's named "RAG" (which in `RAG_PIPELINE` above classified
as `FIXED_PIPELINE`), but its predicates describe a model that decides,
each turn, whether to issue another retrieval query or answer — exactly the
shape of `model_chooses_the_action=True`,
`loop_repeats_based_on_model_output=True`,
`observation_reenters_model_context=True` that `CODING_AGENT` has too, just
with a different action type (a search query instead of code)."""
))

cells.append(nbf.v4.new_code_cell(
"""agentic_rag = next(s for s in ALL_SYSTEMS if "Agentic RAG" in s.name)
rag_pipeline = next(s for s in ALL_SYSTEMS if s.name == "RAG question-answering pipeline")
coding_agent = next(s for s in ALL_SYSTEMS if "Coding agent" in s.name)

print(f"RAG_PIPELINE autonomy:  {rag_pipeline.autonomy.name}")
print(f"AGENTIC_RAG autonomy:   {agentic_rag.autonomy.name}")
print(f"CODING_AGENT autonomy:  {coding_agent.autonomy.name}")
print()
print("Same predicates that make AGENTIC_RAG an AUTONOMOUS_LOOP, minus retrieval specifics:")
print(f"  AGENTIC_RAG:  {agentic_rag.predicates}")
print(f"  CODING_AGENT: {coding_agent.predicates}")
print(f"  Identical except for names/environment -> {agentic_rag.predicates == coding_agent.predicates}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""`AGENTIC_RAG` and `CODING_AGENT` land in the same `Autonomy` class via
*identical* predicate values — despite one being "RAG" (a term usually
associated with fixed pipelines) and the other being an obviously agentic
coding tool. The taxonomy doesn't care what either system is called; two
systems with the same four structural answers are the same class, full stop.
This is the payoff of operationalizing the definition instead of asserting
it: it can't be fooled by a name, because it never looks at the name."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 4. Boundary case 2 — the thermostat: is loop-shape sufficient?

`THERMOSTAT` is built to break a sloppier version of the definition: "an
agent is a system with a closed feedback loop." A thermostat has EXACTLY
that — its own action (heat on) changes its environment (room temperature),
which changes its next observation, which determines its next action,
forever. Check its predicates against `CODING_AGENT`'s on the three
loop-shape questions alone (ignoring `policy_is_a_language_model`):"""
))

cells.append(nbf.v4.new_code_cell(
"""thermostat = next(s for s in ALL_SYSTEMS if "thermostat" in s.name.lower())

loop_shape_fields = ["model_chooses_the_action", "loop_repeats_based_on_model_output",
                      "observation_reenters_model_context"]
for field in loop_shape_fields:
    t_val = getattr(thermostat.predicates, field)
    c_val = getattr(coding_agent.predicates, field)
    print(f"{field:<38} thermostat={t_val!s:5}  coding_agent={c_val!s:5}  {'SAME' if t_val==c_val else 'DIFFERENT'}")

print(f"\\npolicy_is_a_language_model          thermostat={thermostat.predicates.policy_is_a_language_model!s:5}  "
      f"coding_agent={coding_agent.predicates.policy_is_a_language_model!s:5}")
print(f"\\nthermostat classifies as: {thermostat.autonomy.name}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""All three loop-shape predicates agree between the thermostat and the coding
agent — a thermostat is, structurally, exactly as loop-shaped as a coding
agent. It's excluded from the autonomy spectrum entirely (not placed at
`SINGLE_CALL`, which would at least keep it "in the family" — it gets its
own `NON_MODEL_CONTROL_LOOP` bucket) purely because `policy_is_a_language_model`
is `False`. Control theory has built closed feedback loops for a century;
what's specifically new about *agents* in this guide's sense isn't the loop
shape at all — control systems already had that — it's that the box making
the decision is a language model rather than a fixed rule. If your own
mental definition of "agent" is just "has a feedback loop," a thermostat
already satisfies it; the model requirement is doing real, necessary work."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 5. What happens with an impossible combination?

`classify_autonomy` raises on one predicate combination:
`model_chooses_the_action=False` while the loop still repeats and feeds
itself observations. Is that combination actually impossible, or just
unmodeled? Worth checking directly, because a taxonomy that raises on
inputs it hasn't thought through is being honest about its own limits —
better than silently misclassifying them."""
))

cells.append(nbf.v4.new_code_cell(
"""weird = LoopPredicates(
    policy_is_a_language_model=True,
    has_hardcoded_pipeline_steps=False,
    model_chooses_the_action=False,             # the model never picks the action...
    loop_repeats_based_on_model_output=True,    # ...yet it keeps looping...
    observation_reenters_model_context=True,    # ...and sees the results.
)
try:
    classify_autonomy(weird)
except ValueError as e:
    print(f"Raised as expected: {e}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Is this combination actually impossible? Consider: a fixed pipeline where
step order is hardcoded (`model_chooses_the_action=False`) but the NUMBER of
iterations is dynamic — e.g., "keep re-running the same fixed
extract-then-validate pipeline until a checksum passes, feeding the failure
back into the extraction step each time." That's a real pattern (retry
loops around a fixed pipeline), and it does seem to satisfy exactly these
three predicates — the loop repeats, feeds itself observations, but the
model (if there even is one inside the pipeline) never chooses what
runs next; only whether to run the *same* fixed thing again. That's a fifth
class this taxonomy doesn't have a name for, deliberately left as an open
gap rather than forced into one of the four — see the chapter README's
Common Mistakes section for why forcing a fit here would be worse than
raising."""
))

nb['cells'] = cells

with open("ch01_what_is_an_agent.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch01_what_is_an_agent.ipynb")
