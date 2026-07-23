# Chapter 3 — The Reason–Act–Observe Loop

## 1. Concept

**Reason-Act-Observe** is the interleaving pattern behind essentially every
modern agent loop: the model produces a **Thought** (reasoning about what to
do next), emits an **Action** based on that reasoning, the environment
executes the action and returns an **Observation**, and the cycle repeats
until the model itself decides to stop. Chapter 1 named this cycle "the loop"
in the abstract; this chapter gives it its specific, historically grounded
shape and traces how the *shape of the Action* evolved from text to code.

## 2. Why This Matters for Code-Executing Agents

Every code-executing agent in this guide is a Reason-Act-Observe loop where
the Action happens to be a code block. Understanding *why* the field arrived
there — not just that it did — means being able to reconstruct the argument
rather than cargo-culting "use code actions" as received wisdom. This chapter
does that reconstruction concretely: it hand-writes the *same task* as both a
ReAct trace and a CodeAct trace and runs both for real, so the difference is
observed, not asserted.

## 3. Mental Model

Think of Reason-Act-Observe as a fixed three-beat rhythm with one variable
slot:

```
Thought (reason) → Action (act) → Observation (observe) → repeat
                       ▲
                the only slot whose SHAPE changes
                across the ReAct → CodeAct lineage
```

The rhythm itself — reason, act, observe, repeat until the model signals
Finish — is the invariant. What changed historically is what counts as a
valid Action: one call into a small, fixed, text-parsed tool vocabulary
(ReAct), versus one arbitrary, composable program (CodeAct). Chapter 2's
action-space taxonomy is about that slot in isolation; this chapter is about
the loop that slot sits inside, and the lineage of ideas that changed it.

## 4. Architecture (place in the loop / context)

This chapter instantiates Chapter 1's abstract loop with the specific
vocabulary ("Thought," "Action," "Observation," "Finish") the rest of the
guide uses. It sits directly upstream of:

- **Chapter 4** ("Why Code Execution"), which argues for CodeAct's shape of
  Action specifically — this chapter shows the shift happened and what
  changed; Chapter 4 argues *why* it was the right shift.
- **Chapter 5** ("A Minimal Code-Executing Agent"), which builds a real
  version of `run_codeact_loop` — this chapter's `run_codeact_loop` is
  deliberately minimal (one action, no real model, no retry) so that
  Chapter 5's backbone agent has something concrete to extend.
- **Chapter 19** ("Parsing and Extracting Actions"), which is the general
  version of the `ReActStep`/code-block parsing this chapter does by hand.

## 5. Detailed Explanation

**ReAct.** `code/react_vs_codeact.py`'s `REACT_SCRIPT` hand-writes four
`ReActStep`s — `(thought, action, action_input)` triples, with the final step
carrying a `finish_answer` instead of an action. `run_react_loop` is a real
loop: it calls a (scripted) model, executes the returned action for real
against `FAKE_WORKSPACE`, and threads the real observation back into
`context` before the next call. This is the "Thought / Action / Observation
format" the chapter's fill-in pointers ask for, made runnable rather than
just described.

**Observation feedback.** Notice `context += f"\nAction: ...\nObservation:
{observation}"` inside `run_react_loop` — the observation isn't just printed,
it's concatenated into the string that will be passed to the model on the
*next* call. This is the mechanical detail behind Chapter 1's "the model's
own output determines its next input": here it's the *environment's*
response to that output that becomes the next input, one line of string
concatenation.

**Multi-turn iteration.** Each of the loop's 3 iterations (3 `read_file`
calls) accumulates state purely in `context` — there's no separate memory
structure yet (that's Part VI). By the fourth call, `context` contains the
full history of all three prior Thought/Action/Observation triples, which is
exactly why the ReAct trace needs no external bookkeeping to "remember" that
a.txt was 42 by the time it's comparing against c.txt's 8.

**From ReAct to CodeAct.** `run_codeact_loop` performs the identical task in
one Thought + one Action. The Action is a real Python code block
(`CODEACT_CODE`), `exec()`'d for real with `read_file` injected into its
namespace, its real stdout captured as the Observation. The rewrite in
`loop_lineage_diagram.md` §2→§3 shows precisely what moved: the
comparison/arithmetic logic that ReAct's Thought text had to spread across
three turns of natural-language reasoning becomes a `dict` comprehension and
`max(..., key=...)` inside one Action, executed by the interpreter instead of
reasoned about by the model.

**Related lineage.** `HISTORICAL_TIMELINE` records four papers with verified
titles, authors, and submission dates (checked against each paper's arXiv
abstract page in this session — see the chapter deliverable for the full
annotated version): ReAct (2022-10-06) established the iterated loop with
text-shaped actions; PAL (2022-11-18) showed that offloading computation to a
real interpreter beats doing it in the model's own text, but as a single
generate-then-execute step, not an iterated loop; Toolformer (2023-02-09)
explored training the tool-use *decision* into the model itself, orthogonal
to the text-vs-code question; CodeAct (2024-02-01) combined ReAct's iterated
loop with PAL's "offload to the interpreter" idea, applied on every turn
instead of once.

## 6. Minimal Implementation

`code/react_vs_codeact.py`:

- `ReActStep`, `REACT_SCRIPT`, `ScriptedReActModel`, `TOOLS`,
  `run_react_loop` — a real, runnable ReAct loop over a scripted model.
- `CODEACT_THOUGHT`, `CODEACT_CODE`, `run_codeact_loop` — a real, runnable
  CodeAct loop that actually executes code.
- `HISTORICAL_TIMELINE`, `render_timeline()` — the verified lineage data.

Run it directly:

```bash
source .venv/bin/activate
python chapters/ch03-reason-act-observe-loop/code/react_vs_codeact.py
```

```
=== ReAct trace ===
Thought: I need each file's value before I can compare them. Start with a.txt.
Action: read_file('a.txt')
Observation: 42
...
Finish: a.txt has the largest number (42); 42 + 10 = 52.

ReAct: 3 actions, 11 trace entries

=== CodeAct trace ===
Thought: I'll read all three files, compare them, and compute the answer in one action.
Action (code): values = {f: int(read_file(f)) for f in ["a.txt", "b.txt", "c.txt"]}
...
Observation: a.txt has the largest number (42); 42 + 10 = 52
Finish: a.txt has the largest number (42); 42 + 10 = 52

CodeAct: 1 actions, 4 trace entries
```

Both traces land on the identical, correctly computed answer.

## 7. Hands-on Lab

`notebooks/ch03_react_vs_codeact.ipynb` (executed, committed with outputs)
carries out the chapter's hands-on direction directly: runs the hand-written
ReAct trace, runs the hand-written CodeAct rewrite of the same task, compares
action/entry counts between them, and prints the verified historical
timeline with a short reading of the progression.

To extend it yourself: add a fourth file to `FAKE_WORKSPACE`, hand-write a
new `REACT_SCRIPT` step for it, and rewrite `CODEACT_CODE`'s comprehension to
include it — confirm the ReAct trace needs one more full Thought/Action/
Observation triple while the CodeAct trace's action count stays at 1.

## 8. Failure Lab

Break `run_react_loop`'s feedback path deliberately: comment out the line
`context += f"\nAction: ...\nObservation: {observation}"` inside the loop, so
observations are computed but never appended to context. Nothing raises an
exception — `ScriptedReActModel` still plays back its script regardless of
context, because it's scripted rather than actually reading context. But this
reproduces, in miniature, Chapter 1's Failure Lab: the loop still calls the
environment and gets real observations back, but if the model driving it were
real instead of scripted, it would be reasoning about a `context` that never
grew past the original task prompt — unable to know a.txt was 42 by the time
it's "deciding" what to check next. This is why `run_react_loop`'s context
concatenation is not incidental bookkeeping; it's the one line that makes the
loop a loop rather than three repeated, blind calls.

## 9. Instrumentation (what to log / trace / measure)

For any Reason-Act-Observe run: the count of Thought/Action/Observation
triples (a direct proxy for round trips and latency, as in Chapter 2), and
whether each terminal step was a genuine `Finish` versus a `max_steps`
exhaustion (`run_react_loop` raises `RuntimeError` if no `Finish` step is
reached — worth logging as a distinct failure category once Chapter 21
formalizes termination). `render_timeline()`'s structure (date, name,
citation, one-line contribution) is also a reusable pattern for tracing
*design lineage* in your own documentation, separate from runtime tracing.

## 10. Design Considerations

- **The loop shape is stable; only the Action's shape is a design choice.**
  Don't treat "should I use ReAct or CodeAct" as picking a different loop —
  it's picking what counts as a valid Action inside the same
  reason-act-observe rhythm. This reframes the decision as the Chapter 2
  action-space question, not an architecture question.
- **CodeAct's turn savings come from moving reasoning into code, which has
  a cost.** The ReAct trace's Thoughts are inspectable natural language at
  every step ("b.txt is 17, smaller than 42 so far"); the CodeAct trace's
  single Thought is a plan, and the actual comparison logic is only visible
  by reading the code. This is the same auditability trade-off Chapter 2's
  comparison matrix names, now visible inside the loop itself.
- **Scripted models are a legitimate tool for testing loop mechanics**, not
  just a stopgap until Chapter 5. `ScriptedReActModel`'s pattern (play back a
  fixed sequence of outputs) is exactly how you'd unit-test a harness's
  parsing and execution logic without paying for or depending on a live
  model call — worth keeping past this chapter.

## 11. Common Mistakes

- **Treating ReAct and CodeAct as unrelated frameworks.** They share the
  identical loop rhythm; conflating "loop" with "action shape" makes it
  easy to miss that CodeAct is a special case of Reason-Act-Observe, not a
  competitor to it.
- **Assuming the model's Thought explains everything that happened.** In
  the CodeAct trace, the real decision logic (which file is largest) lives
  in the code, not the Thought text — reading only the Thought would
  underestimate what the action actually does.
- **Forgetting the observation-feedback step.** As the Failure Lab shows,
  a loop that executes actions but never appends results to context isn't
  a loop at all in the sense Chapter 1 defined — it's a fixed script that
  happens to call an environment.

## 12. Comparisons / Alternatives

| | ReAct-shaped loop | CodeAct-shaped loop |
|---|---|---|
| Action per turn | One call into a small, fixed, text-parsed tool set | One arbitrary, composable code block |
| Actions needed for the worked task | 3 | 1 |
| Trace entries for the worked task | 11 | 4 |
| Where comparison logic lives | Spread across Thought text, reasoned by the model | Inside the code, executed by the interpreter |
| Auditability per step | High — every reasoning step is inspectable text | Lower — must read code to see the logic |

(See `loop_lineage_diagram.md` for the full annotated diagrams and the
ReAct → PAL → Toolformer → CodeAct lineage.)

## 13. Review Questions

1. What is the one invariant between the ReAct trace and the CodeAct trace in
   this chapter's worked example, and what is the one thing that changed?
2. Where, mechanically, does "the model's own output determines its next
   input" (Chapter 1) happen inside `run_react_loop`'s source code?
3. Why is PAL described as *not* an iterated loop, even though it also uses a
   real Python interpreter for computation?
4. What does Toolformer contribute to this lineage that is orthogonal to the
   text-vs-code action-shape question?
5. If you added a fifth file to the worked task, would the ReAct trace's
   Thought/Action/Observation triple count grow by exactly one? Would the
   CodeAct trace's action count?

## 14. Chapter Summary

Reason-Act-Observe is the interleaving pattern (Thought → Action →
Observation → repeat until Finish) underneath essentially every modern agent
loop, established by ReAct (2022) and run for real in this chapter via
`run_react_loop`. The ReAct → CodeAct lineage is a change in what counts as a
valid Action — from one call into a small, fixed, text-parsed tool vocabulary
to one arbitrary, composable program — not a change in the loop's rhythm. On
this chapter's worked task, that shift took the trace from 3 actions/11
entries down to 1 action/4 entries, with the comparison logic moving from
model-reasoned Thought text into interpreter-executed code. The shift traces
through PAL (offload computation to a real interpreter) and Toolformer (train
the tool-use decision into the model), converging in CodeAct (2024), which
combines both ideas inside the iterated loop.

## 15. Chapter Deliverable

[`loop_lineage_diagram.md`](loop_lineage_diagram.md) — an annotated loop
diagram (generic Reason-Act-Observe, then the ReAct-shaped and CodeAct-shaped
variants side by side) plus the verified ReAct → PAL → Toolformer → CodeAct
historical lineage.

## 16. Further Reading

- Yao, Zhao, Yu, Du, Shafran, Narasimhan, Cao, *ReAct: Synergizing Reasoning
  and Acting in Language Models*, arXiv:2210.03629 (submitted 2022-10-06).
- Gao, Madaan, Zhou, Alon, Liu, Yang, Callan, Neubig, *PAL: Program-aided
  Language Models*, arXiv:2211.10435 (submitted 2022-11-18).
- Schick, Dwivedi-Yu, Dessi, Raileanu, Lomeli, Zettlemoyer, Cancedda, Scialom,
  *Toolformer: Language Models Can Teach Themselves to Use Tools*,
  arXiv:2302.04761 (submitted 2023-02-09).
- Wang, Chen, Yuan, Zhang, Li, Peng, Ji, *Executable Code Actions Elicit
  Better LLM Agents*, arXiv:2402.01030 (submitted 2024-02-01, accepted ICML
  2024) — Chapter 4 covers this paper's thesis directly.

All four citations above were checked against their arXiv abstract pages in
this session (title, author list, submission date), not recalled from memory.
