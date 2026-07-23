# Chapter 5 — A Minimal Code-Executing Agent

## 1. Concept

Build the smallest possible working code-executing agent: prompt a model,
extract the code it emits, run that code, feed the real result back, repeat
— until the model itself stops emitting code. This is Chapters 1–4's theory
made real: a live model call, driving a real Reason-Act-Observe loop
(Chapter 3), with code as the action space (Chapter 4), for the first time in
this guide.

## 2. Why This Matters for Code-Executing Agents

Every chapter from here forward extends this exact agent — `src/backbone_agent/`
— rather than building a new one. Per `CLAUDE.md`'s backbone-continuity rule,
this is the one and only place in the guide where the loop gets built from
nothing; everything else is an extension. Getting the smallest version right,
and understanding precisely what it does and doesn't do yet, is what makes
every later chapter's diff legible.

## 3. Mental Model

```
task ──► [system prompt + task] ──► model ──► reply
                    ▲                            │
                    │                   code block found?
        append Observation                       │
                    │                 ┌───yes─────┴────no───┐
                    │                 ▼                     ▼
                    │           execute code           treat reply as
                    │           (real exec(),           final answer,
                    │            real stdout/            STOP
                    │            traceback)
                    │                 │
                    └─────────────────┘
```

The entire "harness" (Chapter 18's term, arriving properly in Part IV) is
four small modules: `model.py` (call the model), `parsing.py` (find the code
block), `executor.py` (run it, capture the result), `loop.py` (wire the three
together and decide when to stop). Nothing here is more complicated than it
needs to be — statefulness, rich output, pluggable backends, and robust
parsing are explicitly deferred to later chapters (see `backbone_v0_notes.md`).

## 4. Architecture (place in the loop / context)

This chapter instantiates every box from Chapter 1's diagram for the first
time with a live model:

- **Model** → `model.py::call_model`, a thin litellm wrapper (`DEFAULT_MODEL
  = "groq/llama-3.3-70b-versatile"`, overridable via `BACKBONE_MODEL`).
- **Loop** → `loop.py::run_agent`, the generate→extract→execute→observe→repeat
  cycle.
- **Action space** → `parsing.py::extract_code`, one fenced code block per
  turn (Chapter 2's "code action" made concrete).
- **Environment** → `executor.py::execute_code`, in-process `exec()` — the
  simplest of the backends Chapter 6 will compare.

Chapter 6 replaces "environment" with a real comparison of execution
backends; Chapter 7 makes execution stateful; Chapter 8 replaces "stdout
only" with rich observation capture. None of those chapters restart this
loop — they edit these same four files.

## 5. Detailed Explanation

**The core loop.** `run_agent` (in `loop.py`) is close to the literal
pseudocode from Chapter 1 and Chapter 3, now real: build `messages`, call the
model, check whether the reply contains a code block, and either execute it
and continue or return it as the final answer. The system prompt
(`SYSTEM_PROMPT`) states this contract explicitly to the model: one code
block per turn to act, plain text with no code block to finish.

**Code extraction.** `parsing.py::extract_code` is a single regex —
`` ```(?:python)?\s*\n(.*?)``` `` — over the model's raw reply. It returns
`None` when there's no fenced block, which `run_agent` treats as the stop
signal. This is deliberately the simplest thing that could work; Chapter 19
handles multiple blocks, malformed fencing, and mixed reasoning/action.

**Execution.** `executor.py::execute_code` runs the extracted code via
`exec()` in a namespace dict, with `contextlib.redirect_stdout` capturing
printed output. On an exception, it returns `traceback.format_exc()` instead
of raising — the traceback itself becomes the next Observation, which is
exactly what let the agent recover from the real `ModuleNotFoundError`s
documented below.

**Observation formatting.** Minimal: the executor's return string (stdout or
traceback) is wrapped as `f"Observation:\n{observation}"` and appended as a
new user message. Chapter 20 formalizes formatting (truncation, structure,
error emphasis); v0 does none of that yet.

**Termination.** The stop signal is "no code block in the reply." There's
also a hard `max_steps` ceiling (`StepBudgetExceeded`) as a backstop against
a model that never stops emitting code — a primitive version of what
Chapter 21 formalizes properly.

**The first thing that went wrong.** Documented in full, with real
tracebacks, in `backbone_v0_notes.md`: on 2 of the 3 hands-on tasks, the
model's first code action imported `pandas` or `numpy` — neither installed in
this minimal environment — hit a real `ModuleNotFoundError`, and
self-corrected to stdlib on the very next turn using nothing but that
traceback as feedback. This was not staged; it's what happened running the
exact setup in this chapter, and it's a direct, load-bearing demonstration of
why errors-as-observations (Chapter 22) matters starting from the smallest
possible agent, not as a later add-on.

## 6. Minimal Implementation

`src/backbone_agent/`:

- `model.py` — `call_model(messages, model=None)`, thin litellm wrapper.
- `parsing.py` — `extract_code(text)`, one regex.
- `executor.py` — `execute_code(code, namespace=None)`, `exec()` + stdout/
  traceback capture.
- `loop.py` — `run_agent(task, model=None, max_steps=10, return_trace=False)`,
  the loop itself, plus `SYSTEM_PROMPT`.
- `__main__.py` — `python -m backbone_agent "<task>"` CLI entry point.

Installed editable (`pip install -e .`, via `pyproject.toml`) so `import
backbone_agent` works from anywhere in the venv, including every future
chapter's code.

```bash
source .venv/bin/activate
set -a && source .env && set +a   # loads GROQ_API_KEY
python -m backbone_agent "What is 17 * 23? Compute it, don't just guess."
```

```
=== FINAL ANSWER ===
The result of 17 * 23 is indeed 391.
```

## 7. Hands-on Lab

`notebooks/ch05_minimal_agent.ipynb` (executed, committed with outputs, real
live model calls) runs a minimal trace first, then the chapter's required
three tasks via `code/three_tasks_demo.py`: a math problem (sum of the first
20 primes), a file transform (average a real CSV column, write a real file),
and an API-free data task (mean/median/population stdev of an inline list).
Every result is checked against a ground truth computed independently of the
agent — **3/3 tasks solved correctly** in the run committed here. Full
transcripts, including the real `ModuleNotFoundError` recoveries, are in the
notebook and in `backbone_v0_notes.md`.

To extend it yourself: lower `max_steps` to 1 and rerun the file-transform
task — since that task empirically needs 2 turns (the `pandas` miss, then the
stdlib fix), it should now raise `StepBudgetExceeded` instead of completing,
letting you see the hard ceiling fire for real.

## 8. Failure Lab

Beyond the organic `ModuleNotFoundError` recoveries: give `run_agent` a task
it structurally cannot solve within budget, e.g.
`run_agent("Count to 1,000,000 one number per code action, printing only the current number each time, then tell me the final count.", max_steps=5)`.
Because v0's system prompt never tells the model it's allowed to solve a
task in one big loop *inside* a single code block versus many small turns,
a model that (reasonably) interprets "one number per code action" literally
will exhaust `max_steps` and raise `StepBudgetExceeded` — a real, reproducible
demonstration of why an unbounded or naively-bounded loop is dangerous, and
exactly the motivation for Chapter 21's real termination controls and
Chapter 26's guardrail catalog.

## 9. Instrumentation (what to log / trace / measure)

Nothing formal yet (Chapter 59 is where tracing becomes its own subject),
but `return_trace=True` on `run_agent` already exposes the one thing worth
watching at this stage: the full `messages` list, which lets you count turns,
inspect every code action and its real observation, and see exactly where a
run succeeded or (via `StepBudgetExceeded`) failed to terminate.

## 10. Design Considerations

- **Statelessness is a deliberate choice, not an oversight.** A fresh `{}`
  namespace per `execute_code` call means the file-transform task's model had
  to re-derive everything each attempt rather than build on partial state —
  simpler to reason about for v0, at the cost of redundant work across turns.
  Chapter 7 changes this deliberately, not by accident.
- **`exec()` with no restriction is a real, documented risk, held open on
  purpose.** This guide's scope stops at agent behavior; runtime containment
  is the sibling sandbox guide's job (`CLAUDE.md`, Chapter 62). v0 does not
  pretend otherwise.
- **The system prompt is already doing real work.** "Exactly one code block
  per turn" and "no code block = final answer" are the entire termination and
  parsing contract; get this prompt wrong and both `extract_code` and the
  stop condition silently misbehave. Chapter 42 (prompt architecture)
  revisits this prompt specifically.

## 11. Common Mistakes

- **Assuming the agent's own claimed answer is correct.** All three hands-on
  tasks in this chapter are verified against an independently computed
  ground truth, not the agent's stated number — this is a habit worth keeping
  for every later chapter's evaluation too (Chapter 58 formalizes it).
- **Treating a `ModuleNotFoundError` as a bug in the harness.** It isn't —
  `execute_code` correctly caught it and returned it as an Observation; the
  "failure" was entirely the model's first library choice, and the loop's
  design is what made the recovery free.
- **Forgetting `return_trace` exists and trying to reconstruct a run's steps
  from just the final answer.** The final answer alone (the normal
  `run_agent` return value) discards everything needed to debug a run.

## 12. Comparisons / Alternatives

| | v0's choice | What later chapters change it to |
|---|---|---|
| Execution backend | in-process `exec()` | pluggable (Chapter 9); compared against subprocess/kernel (Chapter 6) |
| State across turns | none (fresh namespace per call) | persistent kernel-style state (Chapter 7) |
| Observation content | stdout or traceback only | streams + return values + rich media + size limits (Chapter 8) |
| Action parsing | one regex, first code block | robust multi-block/malformed handling (Chapter 19) |
| Termination | no-code-block, or hard `max_steps` | budgets, no-progress detection, verified completion (Chapter 21) |

## 13. Review Questions

1. Walk through `run_agent`'s source and identify the exact line where an
   Observation gets appended to `messages` — why does this line, specifically,
   make the loop a loop rather than a single scripted call?
2. Why did the file-transform and data-stats tasks each need 2 model calls
   instead of 1, and what would have to change in the environment for them to
   need only 1?
3. What happens, mechanically, if the model's reply contains *two* fenced
   code blocks? (Check `parsing.py`'s regex behavior — this is a deliberate
   simplification, not an oversight.)
4. Why is verifying task success against an independently computed value
   (rather than the agent's stated answer) especially important for a chapter
   whose whole point is "trust but verify" methodology?
5. Name one thing `execute_code` does that a subprocess-based executor
   (Chapter 6) would have to do differently, and why that difference matters
   for isolation.

## 14. Chapter Summary

The backbone agent v0 is a ~40-line loop — generate, extract a code block,
execute it for real, observe the real result, repeat until the model stops
emitting code — built on a thin litellm interface (default
`groq/llama-3.3-70b-versatile`, configurable via `BACKBONE_MODEL`) so no
later chapter is locked to one provider. Verified on three real hands-on
tasks (a math problem, a file transform, an API-free data task) against
independently computed ground truths, all three solved correctly. The first
real failure — the model reaching for uninstalled `pandas`/`numpy` — happened
organically during that verification and self-corrected for free, because
the loop already threads real tracebacks back as Observations. Everything
this v0 deliberately doesn't do yet (state, rich output, pluggable backends,
robust parsing, real budgets, containment) is enumerated in
`backbone_v0_notes.md` as the explicit target list for Chapters 6 onward.

## 15. Chapter Deliverable

**The backbone agent v0** — `src/backbone_agent/` (installable, `python -m
backbone_agent "<task>"` works) — with
[`backbone_v0_notes.md`](backbone_v0_notes.md) documenting its verified
behavior on the three hands-on tasks and the real first failure it hit.

## 16. Further Reading

- litellm documentation (`https://docs.litellm.ai`) — for the provider
  routing this chapter relies on (`"groq/<model>"` strings resolving to the
  right API and env var automatically); worth reading directly if swapping
  `BACKBONE_MODEL` to a different provider later.
- Groq's model catalog — for what `groq/llama-3.3-70b-versatile` is and its
  alternatives; this guide picked it for being fast and freely available
  during development, not for any benchmarked superiority claimed here.
- Revisit Wang et al., *Executable Code Actions Elicit Better LLM Agents*
  (Chapter 4) — `SYSTEM_PROMPT`'s "one code block per turn, plain text to
  finish" contract is this guide's own minimal instantiation of that paper's
  action-space argument, now running against a live model for the first time.
