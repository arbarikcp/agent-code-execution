# Chapter 1 — What Is an Agent?

## 1. Concept

An **agent** is a **loop** that couples a language model to an environment
through **actions** and **observations**, where the model's own prior output
determines its next input. That's the definition — but a definition you can't
apply to a real system is decoration. This chapter's actual work is turning
that sentence into a **decision procedure**: four yes/no structural
questions (`LoopPredicates` in `code/systems.py`) that any real system can be
run through to get a checkable answer, not an impression.

## 2. Why This Matters for Code-Executing Agents

Every later chapter assumes you can look at a system and say, precisely,
whether and how it's an agent. Getting this wrong in either direction has
real costs: over-calling something an "agent" gets you unwarranted
step-budget and guardrail machinery around a system that never needed it;
under-calling something an agent (because it's not called "agentic" or
doesn't look like a chatbot) means missing that it needs exactly that
machinery. This chapter builds a tool for making that call correctly,
and then deliberately tries to break the tool with two hard cases.

## 3. Mental Model

Four questions, in order, each one a real fork:

```
1. Is the policy a language model?           NO ─► NON_MODEL_CONTROL_LOOP (thermostat)
   │ YES
2. Does the model choose the action,          NO ─► has hardcoded pipeline
   or is it predetermined by a pipeline?           steps?  YES ─► FIXED_PIPELINE
   │ YES                                            NO ─► SINGLE_CALL
3. Does the loop repeat based on the          NO ─► SINGLE_TOOL_CALL
   model's own output, with the result
   re-entering ITS OWN next context?
   │ YES
4. -> AUTONOMOUS_LOOP
```

The critical discipline is: answer these from the system's **structure**,
never from its **name**. Section 5 below shows a system literally named
"RAG" (usually a fixed-pipeline term) landing in `AUTONOMOUS_LOOP`, and a
system with a textbook closed feedback loop (a thermostat) landing outside
the spectrum entirely, because the predicates don't read names or vibes —
only wiring.

## 4. Architecture (place in the loop / context)

This chapter's classification scheme is what every later chapter's code
implicitly assumes when it treats something as "the agent." The backbone
built starting Chapter 5 is, in this chapter's terms, a system whose
predicates are `policy_is_a_language_model=True`,
`model_chooses_the_action=True`, `loop_repeats_based_on_model_output=True`,
`observation_reenters_model_context=True` — i.e., `AUTONOMOUS_LOOP` by
construction. Confirming that now, precisely, is what makes it legitimate to
stop re-justifying "why does this agent need a step budget / a guardrail /
observation formatting" in every subsequent chapter — the classification
itself is the justification.

## 5. Detailed Explanation

**The five predicates** (`LoopPredicates` in `code/systems.py` — the
docstring calls out four "structural" ones plus the model-policy gate
first):

- `policy_is_a_language_model` — checked first and short-circuits everything
  else. A system can satisfy every other predicate and still not be an
  "agent" in this guide's sense if a fixed rule, not a model, is making the
  decision. This predicate exists specifically because loop-shape alone is
  not sufficient — see the thermostat case below.
- `has_hardcoded_pipeline_steps` — are there engineer-fixed stages (embed,
  retrieve, format) whose occurrence and order don't depend on the model?
- `model_chooses_the_action` — does the model pick WHICH action happens, as
  opposed to the action being predetermined and the model only filling in
  content?
- `loop_repeats_based_on_model_output` — is there more than one model
  decision point, where whether/how the system continues is itself
  something the model's own output determines?
- `observation_reenters_model_context` — does the result of an action come
  back to the SAME model, before its next call — not to a human, not to a
  log, specifically back into that model's own next context?

`classify_autonomy()` is a pure function over these five booleans — see
`code/systems.py` for the full decision tree. There is no fifth,
judgment-call step after the predicates are answered.

**Boundary case 1 — does the taxonomy classify by structure or by name?**
`AGENTIC_RAG` (in `code/systems.py`) is a RAG system where the model itself
decides, each turn, whether to retrieve again or answer — as opposed to
`RAG_PIPELINE`'s hardcoded embed→retrieve→generate sequence. Its predicates
are **identical** to `CODING_AGENT`'s three loop-shape fields
(`model_chooses_the_action=True`, `loop_repeats_based_on_model_output=True`,
`observation_reenters_model_context=True`) — confirmed directly in the
notebook by comparing the two `LoopPredicates` objects field-by-field. Both
classify as `AUTONOMOUS_LOOP`, despite one being "RAG" (a term this
chapter's OTHER example, `RAG_PIPELINE`, uses for a `FIXED_PIPELINE`
system) and the other being an obviously agentic coding tool. This is the
direct payoff of predicates over labels: a name can't fool a check that
never reads the name.

**Boundary case 2 — is a closed feedback loop sufficient for "agent"?**
`THERMOSTAT` measures temperature, compares to a setpoint, and turns heat
on/off — forever, each cycle conditioned on the last. Checked directly
against `CODING_AGENT` on the three loop-shape predicates alone (ignoring
`policy_is_a_language_model`), **all three agree**: the thermostat's own
action (heat on) changes its environment (the room warms), which changes
its next observation (a new reading), which determines its next action —
structurally indistinguishable from the coding agent's reason-act-observe
cycle. It's excluded from the autonomy spectrum entirely (not placed at
`SINGLE_CALL`, which would at least keep it in the family — it gets its own
`NON_MODEL_CONTROL_LOOP` bucket) purely because `policy_is_a_language_model`
is `False`. The lesson: closed feedback loops are not new — control theory
has built them for a century — so if your working definition of "agent" is
just "has a feedback loop," a thermostat already satisfies it. What's
actually new in the LLM sense is specifically that a *model* is the box
making the decision; this chapter's first predicate exists to make that
requirement explicit rather than implicit.

**An honest gap, not a forced fit.** `classify_autonomy` raises `ValueError`
on one predicate combination: `model_chooses_the_action=False` while the
loop still repeats and re-feeds itself observations. This isn't a
theoretical impossibility — a real pattern fits it: a fixed pipeline
retried on failure (e.g., "re-run this exact extract-then-validate sequence
until a checksum passes, feeding the failure back into extraction each
time"). The pipeline's *steps* are still hardcoded (the model, if any,
never chooses what runs), but the *loop* genuinely repeats and feeds itself
feedback. This is a fifth class the four-way taxonomy has no name for. The
decision procedure raises instead of silently forcing this into
`FIXED_PIPELINE` or `SINGLE_TOOL_CALL` — an honest gap is more useful than a
wrong answer that looks confident.

## 6. Minimal Implementation

`code/systems.py`:

- `LoopPredicates` — the five-field frozen dataclass.
- `classify_autonomy(predicates) -> Autonomy` — the decision procedure,
  including the deliberate `ValueError` for the unmodeled combination.
- `AgentSystem` — now computes `autonomy` in `__post_init__` from its own
  `predicates`, so there is no way to construct a system whose label
  disagrees with its structure.
- Six systems: `CHATBOT` (SINGLE_CALL), `RAG_PIPELINE` (FIXED_PIPELINE),
  `AGENTIC_RAG` (AUTONOMOUS_LOOP — boundary case 1),
  `SINGLE_TOOL_CALL_EXAMPLE`, an email auto-tagger (SINGLE_TOOL_CALL —
  the one gap in v1 of this module, which asserted this category existed
  without ever instantiating an example of it), `CODING_AGENT`
  (AUTONOMOUS_LOOP), `THERMOSTAT` (NON_MODEL_CONTROL_LOOP — boundary case 2).
- `EXPECTED_CLASSIFICATION` — a hand-reasoned answer key, checked against
  the derived result for all six systems at runtime.

Run it directly:

```bash
source .venv/bin/activate
python chapters/ch01-what-is-an-agent/code/systems.py
```

```
System                                                 | Autonomy               | Model-driven loop? | ...
Customer-support chatbot                               | SINGLE_CALL            | no                  | ...
RAG question-answering pipeline                        | FIXED_PIPELINE         | no                  | ...
Agentic RAG (model decides whether to retrieve again)  | AUTONOMOUS_LOOP        | YES                 | ...
Email auto-tagger (one tool call, no loop)             | SINGLE_TOOL_CALL       | no                  | ...
Coding agent (writes and runs code to complete a task) | AUTONOMOUS_LOOP        | YES                 | ...
Home thermostat (closed loop, no model)                | NON_MODEL_CONTROL_LOOP | no                  | ...

=== Classification check: derived autonomy vs. hand-reasoned expectation ===
  ... (all 6) ... OK

All 6 systems: derived classification matches hand-reasoned expectation.
```

## 7. Hands-on Lab

`notebooks/ch01_what_is_an_agent.ipynb` (executed, committed with outputs)
goes beyond the chapter's original hands-on direction (diagram three systems)
by deriving autonomy from predicates for six systems, verifying the
derivation against hand-reasoned expectations, and running both boundary
cases as live comparisons: `AGENTIC_RAG` vs. `CODING_AGENT`'s predicates
(confirmed identical on the loop-shape fields, §3 of the notebook) and
`THERMOSTAT` vs. `CODING_AGENT`'s predicates (confirmed identical on the
three loop-shape fields, different only on `policy_is_a_language_model`,
§4). It also runs the deliberately-impossible predicate combination through
`classify_autonomy` and shows the `ValueError`, then reasons through a real
pattern (a retried fixed pipeline) that would need a fifth class.

To extend it yourself: write `LoopPredicates` for a system you actually use
(a build system, an IDE's autocomplete, a game NPC's AI) and see which class
it lands in — then check whether that classification matches your intuition,
and if it doesn't, figure out which predicate you'd have answered
differently before writing the code.

## 8. Failure Lab

Two failures, both already exercised above rather than left as reader
exercises:

1. **Classifying by name instead of structure** (§3 of the notebook): if you
   trusted "RAG" to mean `FIXED_PIPELINE` without checking `AGENTIC_RAG`'s
   actual predicates, you'd misclassify a genuinely autonomous system as a
   fixed one — and then under-build it (no step budget, no loop-detection
   guardrail, no termination protocol), because you'd have concluded it
   didn't need any of that.
2. **Trusting loop-shape alone** (§4 of the notebook): if your definition of
   "agent" stopped at "has a closed feedback loop," a thermostat would
   qualify. This isn't a hypothetical slip — "has memory and reacts to
   its environment" is a genuinely common informal definition of agent, and
   it's exactly the definition the thermostat is built to break.

A third failure, deliberately induced: **forcing an unmodeled system into
the wrong bucket.** The `ValueError` in `classify_autonomy` for the
"loops and feeds itself observations but the model never chooses the
action" combination exists because forcing that combination into
`FIXED_PIPELINE` (wrong: it DOES repeat and self-feed, which no other
`FIXED_PIPELINE` example does) or `SINGLE_TOOL_CALL` (wrong: it's not a
single call) would both be silently incorrect. Raising is the honest
choice; see Section 5's retried-pipeline example for what a real instance
of this gap looks like.

## 9. Instrumentation (what to log / trace / measure)

For any system under evaluation: record its five `LoopPredicates` values,
not just its final `Autonomy` label. The label alone can't be audited later
(did the classifier change? did the system's actual behavior change?) but
the predicates can be independently re-checked against the system's real
code path. This is a direct instance of a habit this whole guide returns to:
prefer a decision procedure whose inputs you can re-verify over a
conclusion you can only take on faith.

## 10. Design Considerations

- **A taxonomy that can't be fooled by names is worth the extra
  indirection.** `LoopPredicates` is more code than just writing
  `autonomy=Autonomy.FIXED_PIPELINE`, but Section 5's `AGENTIC_RAG` result
  is only trustworthy because the predicates never look at the string
  `"RAG"`.
- **An honest `ValueError` beats a silently wrong classification.** The
  temptation when building a decision procedure is to make it total (handle
  every input, never raise). Resist that when the domain genuinely has gaps
  — Section 5's retried-pipeline example shows the gap is real, not
  hypothetical, and a taxonomy that pretends otherwise would eventually
  misclassify something that actually happens.
- **The model-policy predicate is doing more work than it looks like.**
  It's checked first and short-circuits everything else, which is a
  modeling choice: it says "a system's LOOP SHAPE is irrelevant to whether
  it's an agent if there's no model." An alternative design could have kept
  loop-shape and model-presence as two independent axes instead of a
  short-circuit — worth noticing that this chapter picked one specific
  design, not the only possible one.

## 11. Common Mistakes

- **"An agent is just a prompt."** Neither a prompt nor a model alone
  appears in any of the five predicates as sufficient on its own —
  `policy_is_a_language_model=True` is necessary but nowhere near
  sufficient (three more predicates have to hold for `AUTONOMOUS_LOOP`).
- **Counting tool calls, or the presence of a feedback loop, as a proxy for
  "agentic."** Section 4's thermostat has a feedback loop and zero tool
  calls in the LLM sense and still isn't an agent by this definition;
  Section 3's `AGENTIC_RAG` has one tool (`vector_search`) and clearly is.
  Tool count predicts nothing here.
- **Treating a name ("agentic X") as evidence.** Section 3 exists
  specifically to demonstrate that the taxonomy has to ignore names to be
  trustworthy — a system's marketing name is not one of the five
  predicates and never should be.
- **Forcing every system into one of the four labeled classes.** Section 5's
  retried-pipeline example doesn't fit any of them; pretending it does
  (by picking whichever is "closest") throws away real information about
  the system's actual structure.

## 12. Comparisons / Alternatives

| System | `policy_is_a_language_model` | `has_hardcoded_pipeline_steps` | `model_chooses_the_action` | `loop_repeats_based_on_model_output` | `observation_reenters_model_context` | Autonomy |
|---|---|---|---|---|---|---|
| Chatbot | T | F | F | F | F | SINGLE_CALL |
| RAG pipeline | T | T | F | F | F | FIXED_PIPELINE |
| Agentic RAG | T | F | T | T | T | AUTONOMOUS_LOOP |
| Email auto-tagger | T | F | T | F | F | SINGLE_TOOL_CALL |
| Coding agent | T | F | T | T | T | AUTONOMOUS_LOOP |
| Thermostat | F | T | T | T | T | NON_MODEL_CONTROL_LOOP |

Read down the "Agentic RAG" and "Coding agent" rows, and down the
"Thermostat" and "Coding agent" rows, to see the two boundary cases as raw
predicate diffs rather than prose.

## 13. Review Questions

1. Without looking at the answer key, write out `LoopPredicates` for a voice
   assistant that can only ever answer one question per wake word (no
   follow-up without a new wake word) but CAN call a weather API or a timer
   API depending on what you asked. Which class does it land in, and why?
2. `AGENTIC_RAG` and `CODING_AGENT` have identical loop-shape predicates.
   Name one structural (not cosmetic) difference between them that the
   current five predicates do NOT capture — i.e., a way they genuinely
   differ that this taxonomy is silent about.
3. Why does `policy_is_a_language_model` get checked FIRST, before any
   loop-shape predicate, rather than last?
4. Construct your own predicate combination that you believe
   `classify_autonomy` mishandles or can't classify sensibly — besides the
   one already shown to raise `ValueError`. Is there one? If not, why not?
5. The thermostat satisfies three of five predicates identically to the
   coding agent. If a future chapter needed to distinguish "systems with a
   real feedback loop" from "systems with an LLM as the policy" as two
   SEPARATE axes rather than one gated definition, what would break in the
   current `classify_autonomy` design?

## 14. Chapter Summary

"Agent" is operationalized here as a pure function of five structural
predicates, not a label applied by judgment: is the policy a language model,
are there hardcoded pipeline steps, does the model choose the action, does
the loop repeat based on the model's own output, and does the observation
re-enter that same model's context. Two boundary cases stress-tested this
directly: `AGENTIC_RAG`, whose predicates are identical to `CODING_AGENT`'s
despite the misleading "RAG" name, confirming the taxonomy reads structure
and not labels; and `THERMOSTAT`, whose loop-shape predicates are ALSO
identical to `CODING_AGENT`'s, confirming that a closed feedback loop alone
(control theory's oldest idea) is not sufficient for "agent" in this guide's
sense — the model-as-policy requirement is doing real, load-bearing work,
not decoration. A sixth, deliberately unmodeled predicate combination raises
rather than silently misclassifying, because a real pattern (a retried fixed
pipeline) genuinely doesn't fit any of the four labeled classes.

## 15. Chapter Deliverable

[`agent_loop_reference.md`](agent_loop_reference.md) — a one-page reference
defining the agent loop and its vocabulary, including the five-predicate
decision procedure and both boundary cases, written to be re-readable on its
own without this README.

## 16. Further Reading

- Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*
  (2022/2023) — the reasoning-and-acting loop Chapter 3 traces in detail;
  read now for an early, precise definition of the action/observation cycle
  this chapter's `observation_reenters_model_context` predicate names.
- Wang et al., *Executable Code Actions Elicit Better LLM Agents* (CodeAct,
  2024) — frames "agent" the same way this chapter does (a loop over
  actions and observations); Chapter 4 covers its thesis directly.
- Anthropic, *Building Effective Agents* (engineering blog, 2024) — draws a
  workflow-vs-agent distinction in production terms that maps closely onto
  this chapter's `FIXED_PIPELINE` vs. `AUTONOMOUS_LOOP` split; useful for
  seeing the same structural distinction argued from a production-systems
  angle rather than a definitional one.
- Any introductory control theory reference on closed-loop (feedback)
  control systems — worth reading specifically because the thermostat
  boundary case in this chapter is a real instance of a much older idea;
  seeing how control theory formalizes "feedback loop" independently of any
  learned policy sharpens exactly the distinction Section 5 makes.
