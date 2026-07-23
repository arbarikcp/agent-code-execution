# Chapter 1 — What Is an Agent?

## 1. Concept

An **agent** is a **loop** that couples a language model to an environment through
**actions** and **observations**, where the model's own prior output determines its
next input. That's the whole definition this chapter defends. Everything else in
this guide — code as an action space, execution backends, context engineering,
guardrails — is engineering *around* that loop. Get the loop's shape wrong in your
head and every later chapter will feel like a grab-bag of unrelated techniques
instead of one coherent system.

## 2. Why This Matters for Code-Executing Agents

This entire guide is about a specific kind of loop: one where the action the model
emits is *executable code*, and the observation is whatever running that code
produces. Before any of that makes sense, "loop" has to mean something precise. If
you think of "agent" as "an LLM with some tools bolted on," you'll misjudge which
parts of a code-executing agent actually matter (the loop and the feedback path)
versus which parts are incidental (which specific tools, which specific model).
Chapter 4 onward argues code is a *good action space for the loop* — that argument
only lands if you already see the loop as the object being engineered.

## 3. Mental Model

Picture three concentric layers:

```
 ┌─────────────────────────────────────────────┐
 │ Environment (filesystem, interpreter, APIs)  │
 │   ┌───────────────────────────────────────┐  │
 │   │ Loop (harness): calls model, executes  │  │
 │   │ action, captures result, repeats       │  │
 │   │   ┌─────────────────────────────────┐  │  │
 │   │   │ Model: pi(context) -> action     │  │  │
 │   │   └─────────────────────────────────┘  │  │
 │   └───────────────────────────────────────┘  │
 └─────────────────────────────────────────────┘
```

The model never touches the environment directly — the loop mediates every action
and every observation. The model is a pure function of context; all state, all
history, all "what happened last time" lives in the context the loop assembles and
feeds back in. This is why later chapters (Part IV, Part VI) spend so much effort
on the loop and the context, not the model.

## 4. Architecture (place in the loop / context)

This chapter *is* the architecture — it names the parts every later chapter refers
to without redefining them:

- **Model** → shows up again as "the controller" throughout, and specifically as
  the thing Part VII (Code Generation Quality) tries to get reliable output from.
- **Loop / harness** → becomes its own subject in Part IV (Chapter 18, "Anatomy of
  the Harness"), where it's decomposed into concrete responsibilities.
- **Tools / action space** → becomes Chapter 2 immediately next, then all of Part V.
- **Environment** → becomes Part II (execution substrate) and Part III (workspace,
  filesystem, CLI).
- **Observation** → becomes Chapter 8 and all of Part VI (context engineering).

Every part of this guide is one of these four boxes, expanded.

## 5. Detailed Explanation

**Model, loop, tools, environment — separated.** The model is stateless across
calls; it only knows what's in the context it's given this call. The loop is the
piece of ordinary code that (a) assembles context, (b) calls the model, (c) parses
the model's output into an action, (d) executes that action against the
environment, (e) turns the result into an observation, (f) appends the observation
to context, and (g) decides whether to repeat. Tools are the vocabulary of actions
the model is allowed to emit — see `code/systems.py` in this chapter, where
`AgentSystem.tools` and `.action_unit` name that vocabulary per system. The
environment is whatever actually changes state and produces the observation — a
chat transcript, a vector store, or (for the systems this guide builds) a
filesystem plus a code interpreter.

**Autonomy spectrum.** Systems differ in how much of "what happens next" is decided
by the model at *runtime* versus by an engineer at *design* time:

- `SINGLE_CALL` — one model call, no loop at all (a chatbot's single reply).
- `FIXED_PIPELINE` — a hardcoded sequence of steps; the model fills in content,
  not control flow (a RAG pipeline: retrieve → augment → generate, always in that
  order).
- `SINGLE_TOOL_CALL` — the model picks zero or one tool per turn, but nothing
  feeds the tool's result back for the model to act on again within that turn.
- `AUTONOMOUS_LOOP` — the model's own output determines the next action,
  repeatedly, until the model itself signals done (or a budget stops it). This is
  the only point on the spectrum with a closed feedback loop.

`chapters/ch01-what-is-an-agent/code/systems.py` encodes this ordering as the
`Autonomy` enum and assigns each of three real systems a level, forcing a concrete
answer instead of a vibe.

**Action and observation.** An *action* is the unit of model output the loop
treats as "do something" (as opposed to a final answer meant for a human). An
*observation* is whatever the environment returns after that action runs, and
which the loop appends to context for the next call. The action → environment →
observation → context → next action cycle is the loop; nothing else in the system
needs to be complicated for something to qualify as an agent.

**The controller view.** Treat the model as a policy `pi(context) -> action`. This
framing (borrowed from reinforcement learning, informally) is useful because it
makes "is this an agent?" a question about whether `pi`'s own output feeds back
into `pi`'s own future input — not a question about model capability, prompt
quality, or how many tools are wired up.

**Agent vs. pipeline.** A pipeline (workflow) is a fixed orchestration graph: an
engineer decides the sequence of steps in advance, and the model's job is
constrained to filling in content inside that fixed structure. An agent is a loop
where the model's own output decides the *next step*, at run time, not just the
content of a predetermined step. The RAG pipeline in `systems.py` illustrates this
precisely: it calls an LLM, but the LLM never decides to retrieve again, retrieve
differently, or do anything except "produce the final text" — so by this
chapter's definition it is not an agent, no matter how good the retrieval is.

## 6. Minimal Implementation

There is no runnable *agent* yet in this guide — that arrives in Chapter 5. This
chapter's "minimal implementation" is the smallest code that makes the four-part
breakdown concrete rather than asserted: `code/systems.py` defines an
`AgentSystem` dataclass (`model_role`, `loop_description`,
`has_model_driven_loop`, `tools`, `environment`, `action_unit`,
`observation_unit`) and an `Autonomy` enum, then instantiates three real systems —
a chatbot, a RAG pipeline, and a coding agent — as data. `render_comparison_table`
renders the model/loop/tools/environment breakdown as a table. Run it directly:

```bash
source .venv/bin/activate
python chapters/ch01-what-is-an-agent/code/systems.py
```

```
System                                                  | Autonomy        | Model-driven loop? | Action unit                                                   | Observation unit
--------------------------------------------------------+-----------------+---------------------+----------------------------------------------------------------+--------------------------------------------------------------------------
Customer-support chatbot                                | SINGLE_CALL     | no                  | A chat message                                                  | The human's next message (not a consequence of the agent's own action)
RAG question-answering pipeline                         | FIXED_PIPELINE  | no                  | N/A — the model does not choose actions, only generates text   | N/A — retrieved passages are pipeline input, not a returned observation
Coding agent (writes and runs code to complete a task)  | AUTONOMOUS_LOOP | YES                 | A block of executable code                                     | stdout/stderr/return value/traceback from running that code
```

Only the coding agent has `Model-driven loop? = YES` — that column is the whole
argument of this chapter, expressed as data instead of prose.

## 7. Hands-on Lab

`notebooks/ch01_what_is_an_agent.ipynb` (executed, committed with outputs) carries
out the chapter's hands-on direction — diagram three real systems and label model,
loop, tools, and environment in each — using `systems.py`:

1. Renders the comparison table above.
2. Prints the full per-system breakdown (`model_role`, `loop_description`,
   `has_model_driven_loop`, `tools`, `environment`, `action_unit`,
   `observation_unit`) for all three systems.
3. Works through the controller view (`pi(context) -> action`) as a table of what
   each system's policy conditions on and controls.
4. Prints the `Autonomy` enum in declared order as a sanity check that the
   spectrum in this README matches the code.

To extend it yourself: add a fourth `AgentSystem` for something you use daily
(an IDE autocomplete, a build system, a game NPC) and decide, using the same four
fields, whether it belongs on the autonomy spectrum and where.

## 8. Failure Lab

The failure mode this chapter cares about is *conceptual*, not a runtime crash:
mislabeling a fixed pipeline as an agent (or vice versa) because it has an LLM in
it. Two ways to reproduce this failure deliberately:

1. Take the RAG pipeline in `systems.py` and mentally "sell" it as an agent
   (`has_model_driven_loop=True`) by pointing at its `vector_search` tool.
   Then ask: *does the model's output ever change which step runs next?* It
   doesn't — the graph is fixed. Flipping the flag would be a category error, and
   it's the exact error that leads teams to build "agents" that never actually
   need agentic infrastructure (retries, budgets, guardrails) because nothing in
   them loops.
2. Take the coding agent and imagine removing the feedback path — the loop still
   calls the interpreter, but the result is discarded instead of being appended to
   context. What's left has an environment and an action, but no observation
   reaching the model, so `pi`'s next call can't condition on what just happened.
   That system is a single tool call repeated blindly, not a loop — it would keep
   re-emitting the same action forever because nothing it does can change its own
   next input. This is the shape of the "stuck in a rut" failure mode Chapter 26
   returns to.

Both failures come from skipping the question this chapter insists on: *does the
model's own output feed back into its own next input?*

## 9. Instrumentation (what to log / trace / measure)

Nothing runs yet that needs runtime tracing (that starts in Chapter 5 and becomes
its own subject in Chapter 59). What *is* worth "instrumenting" at this stage is
conceptual: for any system you're evaluating, record its `Autonomy` level and
`has_model_driven_loop` value before deciding what infrastructure it needs. A
`SINGLE_CALL` or `FIXED_PIPELINE` system doesn't need step budgets, loop-detection
guardrails, or observation truncation — those are loop problems. Misclassifying a
pipeline as a loop leads to over-building; misclassifying a loop as a pipeline
leads to missing termination and budget controls entirely (Chapters 21, 26, 27).

## 10. Design Considerations

- **Don't loop things that don't need to loop.** A fixed pipeline is easier to
  test, cheaper to run, and more predictable than a loop. Only reach for an
  autonomous loop when the *sequence* of steps genuinely can't be decided in
  advance — which is most of what the rest of this guide is about, but it is a
  deliberate trade against determinism and cost, not a default.
- **The autonomy spectrum is a design knob, not just a taxonomy.** You can
  deliberately build a `SINGLE_TOOL_CALL` system instead of a full loop when you
  want most of the benefit of model-chosen actions with none of the runaway-cost
  or non-termination risk of an open-ended loop (Chapter 26).
- **The four-part separation pays off later.** Keeping "model," "loop," "tools,"
  and "environment" as distinct concerns now is what makes Chapter 9's pluggable
  executor interface and Chapter 18's harness abstraction feel natural instead of
  arbitrary — they're just formalizing boundaries this chapter already drew.

## 11. Common Mistakes

- **"An agent is just a prompt."** The prompt shapes one model call. The loop —
  specifically, whether the model's output feeds back into its own future input —
  is what makes something an agent. A great prompt on a fixed pipeline is still a
  pipeline.
- **Counting tool calls as a proxy for "agentic."** A workflow can invoke many
  tools and still be a fixed graph if an engineer, not the model, decided the
  sequence at design time.
- **Treating autonomy as binary.** "Is it an agent, yes or no" is usually the
  wrong question; "where on the `SINGLE_CALL → FIXED_PIPELINE → SINGLE_TOOL_CALL →
  AUTONOMOUS_LOOP` spectrum does it sit" is more precise and more useful for
  deciding what infrastructure the system needs.
- **Conflating the model's capability with the system's agency.** A very capable
  model wrapped in a `SINGLE_CALL` system is still not an agent; a weak model
  wrapped in a genuine feedback loop is.

## 12. Comparisons / Alternatives

| System | Autonomy | Model-driven loop? | Why it's classified this way |
|---|---|---|---|
| Chatbot | `SINGLE_CALL` | No | A human, not the model's own output, decides the next turn. |
| RAG pipeline | `FIXED_PIPELINE` | No | The retrieve→generate sequence is hardcoded; the model can't alter it. |
| Single JSON tool call | `SINGLE_TOOL_CALL` | No | The model picks one action, but nothing feeds its result back for another model-driven decision within that turn. |
| Coding agent | `AUTONOMOUS_LOOP` | Yes | The model's own output (code) produces an observation that re-enters its own context, repeatedly, until it stops itself. |

(Full data behind this table: `code/systems.py`.)

## 13. Review Questions

1. In your own words, what is the one property that separates an `AUTONOMOUS_LOOP`
   system from a `FIXED_PIPELINE` system that also calls an LLM?
2. Why is "an agent is just a prompt" wrong? What would you point to in a system
   to prove or disprove it?
3. Take a system you use or have built. Assign it a point on the autonomy
   spectrum and justify it using the `AgentSystem` fields (`model_role`,
   `has_model_driven_loop`, `action_unit`, `observation_unit`).
4. Why does removing the "observation feeds back into context" step turn a coding
   agent into something closer to a single repeated tool call, per the Failure Lab?
5. Where does code execution fit into this four-part model — is it a new fifth
   part, or does it belong to one of the four? (Chapter 2 will answer this
   directly; try to answer it yourself first.)

## 14. Chapter Summary

An agent is a loop, not a model. The loop couples a model (a policy
`pi(context) -> action`) to an environment through actions and observations, and
what makes it an *agent's* loop specifically is that the model's own output
determines its own next input — a closed feedback path. Real systems sit at
different points on an autonomy spectrum (`SINGLE_CALL`, `FIXED_PIPELINE`,
`SINGLE_TOOL_CALL`, `AUTONOMOUS_LOOP`) depending on how much of "what happens
next" is decided by the model at runtime versus by an engineer in advance. Only
`AUTONOMOUS_LOOP` systems need the loop-engineering, budget, and guardrail
machinery the rest of this guide builds — which is exactly why getting this
classification right, early, matters.

## 15. Chapter Deliverable

[`agent_loop_reference.md`](agent_loop_reference.md) — a one-page reference
defining the agent loop and its vocabulary (model, loop, tools, environment,
action, observation, autonomy spectrum, agent-vs-pipeline, common
misconceptions), written to be re-readable on its own without this README.

## 16. Further Reading

- Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*
  (2022/2023) — the reasoning-and-acting loop this guide's Chapter 3 traces in
  detail; useful now for seeing an early, precise definition of the action/
  observation cycle.
- Wang et al., *Executable Code Actions Elicit Better LLM Agents* (CodeAct, 2024)
  — the paper this whole guide is downstream of; Chapter 4 covers its thesis
  directly, but it's worth skimming now for how it frames "agent" the same way
  this chapter does (a loop over actions and observations), just with code as the
  action space.
- Anthropic, *Building Effective Agents* (engineering blog, 2024) — draws a
  similar workflow-vs-agent distinction (fixed control flow vs. model-directed
  control flow) in production terms; a good sanity check against this chapter's
  `FIXED_PIPELINE` vs. `AUTONOMOUS_LOOP` split.
