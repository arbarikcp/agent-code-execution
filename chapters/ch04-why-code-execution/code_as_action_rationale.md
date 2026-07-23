# Why Code as an Agent's Action Space — Rationale and Benchmark Notes

*Chapter 4 deliverable: a written rationale for code-as-action, with own benchmark notes.*

## The thesis

Executable code should be the default action space for a multi-step,
data-touching agent loop, because it is the only one of the three spaces
compared in Chapter 2 where the *action itself* can carry composition, reuse
existing code, and be corrected mid-task using the interpreter's own output.
This is the CodeAct thesis (Wang et al., 2024, arXiv:2402.01030): "executable
code actions elicit better LLM agents" by unifying the action space around
code rather than a bespoke JSON schema per operation.

## The published empirical claim (verified)

Checked directly against the paper's arXiv abstract page in this session:

> CodeAct outperforms widely used alternatives — **up to 20% higher success
> rate** — evaluated on the API-Bank benchmark and a newly curated benchmark,
> across **17 LLMs**. The paper also introduces CodeActInstruct, an
> instruction-tuning dataset of **7k multi-turn interactions**, to train
> models specifically for code-action agentic behavior.

The abstract does not state a specific step/action-count reduction figure, so
none is claimed here beyond what the abstract says. This guide does not
reproduce the paper's own benchmark (API-Bank plus 17 LLMs is out of scope for
a toy chapter exercise); the notes below are a separate, much smaller,
self-contained demonstration of the same underlying mechanism.

## Our own benchmark notes

Ran in this session via `code/why_code.py::run_benchmark`, task: sum k files,
under a shared 8-step budget (a stand-in for a per-task step ceiling, per
Chapter 27's eventual budget model). Full output reproduced from a real run:

```
  k | json steps | json ok | code steps | code ok
-------------------------------------------------
  1 |          3 |    True |          2 |    True
  3 |          5 |    True |          2 |    True
  5 |          7 |    True |          2 |    True
  6 |          8 |    True |          2 |    True
  7 |          9 |   False |          2 |    True
 10 |         12 |   False |          2 |    True
 20 |         22 |   False |          2 |    True

json_tool_calls: 4/7 succeeded (57%), avg steps needed = 9.4
code_action:     7/7 succeeded (100%), avg steps needed = 2.0
```

**Reading this:** JSON tool calling needs `k + 2` steps (k reads + 1 write +
1 final answer); a code action needs a constant 2 steps regardless of k. At
k=6 JSON tool calling exactly fits the 8-step budget; at k=7 it needs 9 and
fails outright, not degrades — the harness would cut it off mid-task. The code
action never approaches the budget at any k tested. Every "success" above was
checked against the true expected sum via an `assert` in `run_benchmark`, not
just declared.

**Scope of this claim:** this demonstrates the *mechanism* — a fixed step
budget increasingly favors an action space whose step count doesn't grow with
task size — on a deliberately small, deterministic toy task. It is not a
claim about success rates on any real benchmark or with any real model; the
"up to 20% higher success rate" figure above is the one number in this
document backed by a real, independently published evaluation.

### Does the 8-step snapshot generalize? A full budget sweep

One budget (8) is one point on a curve. `sweep_budgets()` sweeps the budget
itself from 3 to 24, holding the same task sizes fixed:

```
budget |  json success rate |  code success rate | max k JSON can fit
---------------------------------------------------------------------
     3 |               14% |              100% |                  1
     4 |               14% |              100% |                  2
     6 |               29% |              100% |                  4
     8 |               57% |              100% |                  6
    10 |               71% |              100% |                  8
    12 |               86% |              100% |                 10
    16 |               86% |              100% |                 14
    24 |              100% |              100% |                 22
```

Code's success rate is **100% at every budget tested**, including the
tightest (3 steps) — a code action never needs more than 2 steps regardless
of task size. JSON's success rate climbs monotonically (14% → 29% → 57% →
71% → 86% → 100%) as the budget loosens, reaching parity with code only once
the budget is generous enough to fit every task size in the test set. The
"max k JSON can fit" column is exactly `budget - 2` at every row — not a
statistical pattern, a direct algebraic consequence of JSON's `k+2` step
formula versus code's constant `2`. The original 57%-vs-100% result is one
point on this line, not a cherry-picked snapshot.

### Tool reuse (measured)

`demo_tool_reuse()` runs `import statistics; result = round(statistics.mean(values), 2)`
as a real code action against `values = [12, 7, 19, 3, 25]` and gets
`result = 13.2` — computed via a stdlib function that was never registered as
a tool. The JSON-mode equivalent would require defining and exposing a schema
like:

```json
{"name": "compute_mean", "description": "Compute the arithmetic mean of a list of numbers.",
 "parameters": {"type": "object", "properties": {"values": {"type": "array", "items": {"type": "number"}}}, "required": ["values"]}}
```

*before* the model could perform this operation at all. Every new kind of
computation an agent might need (mean, median, a regex, a date parse) is
either already available to a code action (if the language/library has it) or
requires a new schema, a new registration, and a new round trip to add to a
JSON-mode agent.

### Dynamic revision (measured)

`demo_dynamic_revision()` runs a code action that genuinely raises
`ZeroDivisionError` (dividing by a real `count.txt` value of `"0"`), captures
the real traceback via `traceback.format_exc()`, and then runs a second code
action — written to guard the zero-count case — that really succeeds,
producing `avg = 0.0`. The observation that drove the fix (`ZeroDivisionError:
division by zero`) is the interpreter's actual output, not a scripted string.
This is the mechanical basis of Chapter 22's self-debugging loop: the
interpreter itself supplies the signal an agent needs to correct course.

## Alignment with pretraining (not independently measured)

The CodeAct paper's stated motivation includes that LLMs are extensively
pretrained on code, giving them stronger prior competence at producing valid,
well-formed code than at producing an arbitrary bespoke JSON schema invented
for a specific tool set. This claim is about training-data composition and is
not something this chapter can independently verify by running code — it is
reported here as the paper's stated rationale, not as a number this guide
measured.

## Costs and risks — non-determinism now measured, not just claimed

Code actions widen the failure surface relative to JSON tool calls:

- **Non-determinism (measured).** `demo_nondeterminism()` executes the exact
  same source text (`import time; result = time.time()`) twice and compares
  the results:

  ```
  run 1: 1784809267.251519
  run 2: 1784809267.251528
  identical source, different output: True
  ```

  Identical code, genuinely different output — not a hypothetical, a
  one-line reproduction. `exec()` places no constraint on what a code action
  can call; a JSON tool-calling system's non-determinism is bounded by
  whatever was actually registered as a tool — if nobody registered a
  time-reading tool, that specific non-determinism is simply unavailable to
  the agent, by construction, not by discipline.
- **Debugging cost.** A JSON tool call's effect is legible from its arguments
  alone; a code action's effect requires reading (or running) the code, as
  the tool-reuse and dynamic-revision demos above illustrate.
- **Containment burden.** A code action can do anything the interpreter can
  do — arbitrary filesystem access, network calls, subprocess spawning —
  unless something constrains it. **This guide does not implement that
  constraint.** Runtime isolation and sandboxing are the explicit subject of
  the sibling guide, *Code Execution Sandboxing for AI Agents* — see Part XI
  of this guide's own index for where the handoff happens formally.

## When JSON tool calling is still the right choice

Unchanged from Chapter 2's conclusion, restated with this chapter's evidence:
a small, fixed, low-composition, high-auditability tool surface — or any
context where no sandboxed code-execution environment is available — still
favors JSON tool calls despite their token and step cost, precisely because
their effects are legible from the call itself without executing anything.

## Bottom line

Composability (measured: 100% vs. 57% success under a shared step budget on a
toy task), tool reuse (measured: an unregistered stdlib call working
immediately), and dynamic revision (measured: a real traceback driving a real
fix) are three concrete, runnable reasons code actions scale better than JSON
tool calls as tasks grow in size and complexity — consistent with, though far
smaller in scope than, the CodeAct paper's own verified "up to 20% higher
success rate" result. The cost is a wider failure and containment surface,
which this guide addresses at the loop-engineering level (Parts IV, VI, VII)
and hands off entirely, for runtime isolation, to the sandbox guide.
