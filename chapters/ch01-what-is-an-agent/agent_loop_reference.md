# Agent Loop — One-Page Reference

*Chapter 1 deliverable: definitions of the agent loop and its vocabulary.*

## The definition

> An **agent** is a **loop** that couples a **model** to an **environment** through
> **actions** and **observations**, where the model's own prior output determines
> its next input.

"Agent" names the loop's shape, not the model inside it, and not any individual
tool call. A system with a very capable model but no such loop (a chatbot, a fixed
RAG pipeline) is not an agent by this definition, however good its output is.

## The four parts

| Part | Definition | Example (coding agent) |
|---|---|---|
| **Model** | The policy `pi(context) -> action`: maps the current context to the next action. Does not itself act on the world. | An LLM that emits a code block |
| **Loop** | The harness code that calls the model, executes its action, captures the result, and calls the model again with the result appended to context. Runs until a stop condition fires. | `while not done: action = model(context); obs = execute(action); context += obs` |
| **Tools / actions** | The vocabulary of things the model is allowed to emit as an action — a code block, a shell command, a structured JSON call. | `run_python(code)`, `read_file(path)` |
| **Environment** | Whatever the action acts on and the observation comes from — filesystem, interpreter, API, browser. | A workspace directory + Python interpreter |

## Action and observation

- **Action** — the unit of output the model emits that the loop treats as "do
  something," as opposed to a final answer. Chapter 2 covers the three dominant
  action spaces (free text, structured JSON/tool calls, code).
- **Observation** — whatever the environment returns after an action runs
  (stdout, a return value, a traceback, an API response). The observation is
  appended to context, becoming part of what the model sees on its next call.
  This feedback path — action → environment → observation → context → next
  action — *is* the loop.

## The autonomy spectrum

Ordered by how much control the model's own output has over what happens next:

```
SINGLE_CALL  <  FIXED_PIPELINE  <  SINGLE_TOOL_CALL  <  AUTONOMOUS_LOOP
(chatbot)       (RAG pipeline)     (one tool, no          (coding agent:
                                    iteration on result)   reason-act-observe,
                                                            repeats until the
                                                            model itself stops)
```

Only `AUTONOMOUS_LOOP` closes the feedback path: the model's action changes the
environment, the environment's response changes the model's next input. Everything
to the left of it is either no loop at all (`SINGLE_CALL`) or a loop whose *shape*
is decided by an engineer in advance, not by the model at runtime
(`FIXED_PIPELINE`, `SINGLE_TOOL_CALL`).

## The controller view

Treat the model as a **policy**: a function from context to next action,
`pi(context) -> action`. What distinguishes an agent is not that a policy exists
(a chatbot has one too) but that the policy's own output feeds back into its own
future input, closing a loop with the environment in between.

## Agent vs. pipeline (in one line)

A **pipeline** (or **workflow**) is a fixed orchestration graph: the engineer
decides the sequence of steps at design time, and the model fills in content
within that fixed structure. An **agent** is a loop where the model's output
decides the next step at *run* time. Same model, different control structure —
this is why "agent" is a claim about the loop, not the model.

## Common misconceptions

- **"An agent is just a prompt."** No — the prompt shapes what the model does
  inside one call. The loop is what makes it an agent; a great prompt on top of
  a fixed pipeline is still a pipeline.
- **"More tool calls = more agentic."** No — a workflow can call ten tools and
  still be a fixed graph if the *sequence* isn't decided by the model at runtime.
- **"Autonomy is binary."** No — see the spectrum above. `SINGLE_TOOL_CALL`
  systems are common and sit meaningfully between a pipeline and a full loop.

## Where code execution fits

Code is one specific **action space** (Chapter 2) — the vocabulary of actions the
model in the loop is allowed to emit. This guide's central claim, developed from
Chapter 2 onward, is that executable code is an unusually good action space for an
agent's loop because it is composable, reuses existing tools, and its interpreter
is a rich, structured source of observations.
