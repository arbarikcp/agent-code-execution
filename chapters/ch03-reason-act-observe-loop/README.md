# Chapter 3 — The Reason–Act–Observe Loop

## 1. Concept

**Reason-Act-Observe** is the interleaving pattern behind essentially every
modern agent loop: Thought (reasoning), Action (based on that reasoning),
Observation (the environment's real response), repeat until the model
signals Finish. Chapter 1 named this cycle abstractly; this chapter gives
it concrete shape by actually running it two ways — as a ReAct trace (text
actions) and as a CodeAct trace (code actions) — and then goes further than
either efficiency comparison: it constructs a real failure that ReAct is
structurally vulnerable to and CodeAct structurally is not, and grounds that
construction directly in a verified published claim (PAL's abstract).

## 2. Why This Matters for Code-Executing Agents

Chapter 2 already showed code actions cost fewer tokens and turns. If that
were the whole story, code actions would just be a cheaper way to do the
same thing ReAct does. This chapter's real contribution is showing they're
not just cheaper — they close off an entire class of error. That distinction
matters because it changes what kind of claim you're making to someone
deciding between action spaces: "code is more efficient" is a cost argument;
"code structurally prevents this specific failure mode" is a correctness
argument, and the two call for different levels of urgency.

## 3. Mental Model

```
Thought (reason) → Action (act) → Observation (observe) → repeat
    ▲                  ▲
    │                  └── the only slot whose SHAPE changes ReAct → CodeAct
    └── the only slot that's NEVER verified against ground truth in ReAct
```

The loop's rhythm is invariant. What §5 and §6 below establish is that the
Thought slot in a ReAct trace is unverified by construction: the loop
checks that an Action executes and produces a real Observation, but nothing
checks that a Thought's claim about what an Observation means is correct.
A CodeAct action doesn't have this exposed surface, because there's no
freestanding "claim about the data" — only code that either runs (and is
exact, by the language's own semantics) or raises.

## 4. Architecture (place in the loop / context)

This chapter instantiates Chapter 1's abstract loop with concrete vocabulary
and then stress-tests it. It sits directly upstream of:

- **Chapter 4** ("Why Code Execution"), whose "dynamic revision" argument
  (the interpreter's real error output drives a real fix) is the natural
  complement to this chapter's finding: Chapter 4 shows code actions still
  DO fail, and shows the loop recovering from an interpreter-reported error;
  this chapter shows a class of failure that never even reaches the
  interpreter in a ReAct trace, because it's a wrong Thought, not a wrong
  Action.
- **Chapter 5**, which builds a real (live-model) version of
  `run_codeact_loop` — deliberately minimal here (no live model, no retry)
  so Chapter 5's backbone has something concrete to extend.
- **Chapter 22** (self-debugging), which assumes errors surface as
  Observations the loop can act on — this chapter's failure class is the
  cautionary counterexample: some errors (a wrong Thought) never surface as
  an Observation at all, in either action space, unless something explicitly
  checks for them.

## 5. Detailed Explanation

**ReAct, and where its correctness actually lives.**
`code/react_vs_codeact.py`'s `run_react_loop` calls a (scripted) model,
executes the returned action for real, and threads the real observation
back into context. The mechanism is airtight for the ACTION/OBSERVATION
pair — `TOOLS[step.action](step.action_input)` is a real function call with
a real, correct return value, every time. What's NOT verified is the
THOUGHT: `step.thought` is appended to context as-is, with no check that it
correctly characterizes anything. This is not a bug in the implementation —
it's a structural property of free-text reasoning: there's no schema for a
Thought to conform to, so nothing CAN check it mechanically.

**The constructed failure: two 6-file scripts, one flipped comparison.**
`CORRECT_LONG_REACT_SCRIPT` and `FLAWED_LONG_REACT_SCRIPT` share identical
actions and identical (real, correct) observations at every step. They
differ at exactly one Thought: after observing `d.txt` = 55 (correctly), the
flawed script's Thought states "That's less than 42" — a plain
misjudgment, the kind a real model can plausibly make on a long chain of
text-based comparisons. Every subsequent Thought in the flawed script trusts
this wrong "running max" and continues comparing against it. The final
`Finish` answer is `a.txt`/`42`/`52` — wrong; ground truth (computed
independently via Python's own `max()` over `LONG_WORKSPACE`, not from
either script) is `d.txt`/`55`/`65`. Verified directly: every Observation in
the flawed trace matches `LONG_WORKSPACE` exactly; only the Finish answer is
wrong. This demonstrates, rather than asserts, that a ReAct loop's own
machinery cannot distinguish a run with a wrong Thought from a run without
one — both look identical from the loop's perspective (every action
succeeded, every observation was real).

**CodeAct's structural immunity to this specific class.**
`run_long_codeact_loop` performs the identical 6-file task as one action:
`max(values, key=values.get)`. There is no "running max" claim anywhere in
generated text for a later step to misremember, because there is no later
step — the entire comparison happens in one call to an exact language
primitive. This doesn't make code actions bug-free (see Chapter 4's dynamic
revision demo for a real code failure and recovery) — it means this
SPECIFIC failure shape (correct facts, silently wrong accumulated
interpretation of them, propagating across steps) has no surface to occur
on inside a single, non-iterative code action.

**This isn't a hypothetical — PAL's abstract names it directly.** Checked
against the arXiv abstract page this session: PAL (Gao et al., 2022) states
*"LLMs often make logical and arithmetic mistakes in the solution part,
even when the problem is decomposed correctly"* — precisely the shape of
the constructed failure above (the flawed script's DECOMPOSITION was
correct — it checked every file, in the right order — only its ARITHMETIC
at one step was wrong). PAL's verified fix and result: *"PAL using Codex
achieves state-of-the-art few-shot accuracy on the GSM8K benchmark ...
surpassing PaLM-540B which uses chain-of-thought by absolute 15% top-1"* —
a real, published, benchmarked number for exactly the "offload the
arithmetic to an interpreter" mechanism this chapter's CodeAct trace uses.

**Multi-turn iteration and observation feedback**, mechanically: each
`context += f"\nAction: ...\nObservation: {observation}"` line in
`run_react_loop` is what makes prior turns visible to later ones — remove it
and even the CORRECT script would fail, because nothing would remember
`a.txt` was 42 by the time c.txt is being compared. This is Chapter 1's
`observation_reenters_model_context` predicate, implemented as one line of
string concatenation, and it's exactly as unable to distinguish "a
correctly observed fact" from "a wrong claim about that fact" as the rest of
the loop.

**Related lineage.** `HISTORICAL_TIMELINE` now carries direct abstract
quotes rather than paraphrases for all four papers (ReAct, PAL, Toolformer,
CodeAct) — see `loop_lineage_diagram.md` §5 for the full annotated
timeline with every quote and date checked this session.

## 6. Minimal Implementation

`code/react_vs_codeact.py`:

- `ReActStep`, `REACT_SCRIPT`, `ScriptedReActModel`, `run_react_loop` — the
  original 3-file ReAct loop.
- `CODEACT_THOUGHT`, `CODEACT_CODE`, `run_codeact_loop` — the original
  3-file CodeAct rewrite.
- `LONG_WORKSPACE`, `CORRECT_LONG_REACT_SCRIPT`,
  `FLAWED_LONG_REACT_SCRIPT`, `run_long_react_loop`,
  `run_long_codeact_loop` — the constructed 6-file failure-class
  demonstration.
- `HISTORICAL_TIMELINE` (with verified direct quotes), `render_timeline()`.

Run it directly:

```bash
source .venv/bin/activate
python chapters/ch03-reason-act-observe-loop/code/react_vs_codeact.py
```

```
=== A real failure class: correct Observations, wrong Thought-level arithmetic ===
Ground truth (computed independently): d.txt has the largest number (55); 55 + 10 = 65.

CORRECT ReAct script finish:  'd.txt has the largest number (55); 55 + 10 = 65.'
  matches ground truth: True

FLAWED ReAct script finish:  'a.txt has the largest number (42); 42 + 10 = 52.'
  matches ground truth: False  <- wrong, despite every Observation being correct
  every Observation in the flawed trace was still correct: True

CodeAct (max() delegated to the interpreter): 'd.txt has the largest number (55); 55 + 10 = 65.'
  matches ground truth: True
```

## 7. Hands-on Lab

`notebooks/ch03_react_vs_codeact.ipynb` (executed, committed with outputs)
runs both the original 3-file comparison and the full 6-file
correct-vs-flawed-vs-CodeAct demonstration, printing the exact Thought where
the two 6-file scripts diverge side by side, then verifying the flawed
trace's observations were all individually correct despite its wrong
Finish answer.

To extend it yourself: write a THIRD 6-file script where the flaw is in a
different failure shape — e.g., correctly tracking the max but making an
arithmetic slip in the final `+ 10` — and check whether that failure is
"louder" (easier to catch by inspection) or "quieter" (easier to miss) than
the running-max misjudgment used here.

## 8. Failure Lab

The constructed failure above (§5-6) IS the failure lab for this chapter —
run, not just described. A second, related failure worth reproducing
yourself: break `run_react_loop`'s context-concatenation line (comment out
`context += ...`) and rerun `CORRECT_LONG_REACT_SCRIPT`. Because
`ScriptedReActModel` plays back a fixed script regardless of context, no
exception occurs — but if the model were live instead of scripted, this
would be indistinguishable from the flawed-Thought failure from the loop's
external behavior (a wrong final answer despite correct individual
Observations), even though the underlying cause is completely different
(no memory at all, vs. a specific wrong claim). This is worth sitting with:
two structurally different bugs (missing feedback vs. a wrong Thought) can
produce externally identical symptoms, which is exactly why Chapter 59's
tracing/observability work cares about capturing the full Thought/Action/
Observation sequence, not just the final answer.

## 9. Instrumentation (what to log / trace / measure)

Beyond turn/entry counts (Chapter 2's territory): for a ReAct-shaped loop
specifically, consider whether any Thought's claim can be cross-checked
against the Observations already in context — even a cheap heuristic check
(does the Thought's stated "current max" match the actual maximum of
observed values so far?) would have caught this chapter's constructed
failure without needing a smarter model. `run_long_react_loop`'s transcript
already contains everything needed for such a check post-hoc; nothing in
this chapter implements one, which is itself worth noting as a gap.

## 10. Design Considerations

- **"Fewer tokens" and "fewer failure modes" are different claims, and
  conflating them weakens both.** Chapter 2 established the former with
  real numbers; this chapter establishes the latter with a real constructed
  case tied to a verified published result (PAL). Keep the two arguments
  separate when explaining to someone why code actions are the default.
- **A loop's correctness guarantees only extend as far as what it actually
  verifies.** `run_react_loop` verifies that actions execute and observations
  are real; it does NOT verify that Thoughts correctly interpret those
  observations. Any system built on this loop shape inherits that exact gap
  unless something is added specifically to close it (see §9).
- **Constructing a failure case is more convincing than asserting a paper's
  claim.** This chapter could have simply cited PAL's abstract. Building a
  concrete, mechanically-verified instance of the failure it describes
  makes the claim inspectable rather than just cited.

## 11. Common Mistakes

- **Believing a full, coherent-looking Thought chain guarantees a correct
  answer.** The flawed script's Thoughts are fluent and locally
  plausible at every step — the error is only visible by checking against
  ground truth, not by reading the trace for "does this sound reasoning-y."
- **Treating code actions as immune to error rather than immune to THIS
  error.** §5's claim is scoped precisely: this failure CLASS (correct
  facts, wrong accumulated interpretation across steps) is structurally
  unavailable to a single code action; other failure classes (Chapter 4's
  dynamic-revision demo) are not.
- **Citing PAL's claim without checking whether your own system actually
  exhibits the mechanism.** This chapter didn't just cite "PAL says code
  helps arithmetic" — it built a case where that specific claim is true, at
  a specific, inspectable step.

## 12. Comparisons / Alternatives

| | ReAct-shaped loop | CodeAct-shaped loop |
|---|---|---|
| Actions needed (3-file task) | 3 | 1 |
| Where comparison logic lives | Thought text, re-derived each turn, unverified | One interpreter call, exact by construction |
| Vulnerable to "correct facts, wrong accumulated interpretation"? | Yes — demonstrated in §5-6 | No — no accumulated textual claim exists to be wrong |
| Still vulnerable to other bugs? | Yes | Yes (Chapter 4's dynamic-revision demo) |
| Published evidence | PAL: "logical and arithmetic mistakes in the solution part... even when decomposed correctly" | PAL: 15% absolute GSM8K improvement over CoT via interpreter offload |

## 13. Review Questions

1. In the flawed 6-file script, exactly which step's Thought is wrong, and
   what specifically does it get wrong — the file it checks, the value it
   observes, or the comparison it makes?
2. Why does `run_react_loop` have no way to detect the flawed script's error
   at the time it happens, even in principle, given the code as written?
3. PAL's mechanism (offload computation to an interpreter) is a single
   generate-then-execute step, not an iterated loop like ReAct. Why does
   this chapter still treat PAL's finding as directly relevant to a
   MULTI-STEP ReAct trace's failure mode?
4. Propose one instrumentation change to `run_react_loop` (not a model
   change) that would have caught the flawed script's error automatically,
   without needing the ground truth in advance.
5. Is there a failure shape that a CodeAct action IS vulnerable to that a
   ReAct trace structurally is not, symmetric to this chapter's finding?
   (Hint: think about what "no intermediate checkpoint" costs, not just
   what it saves — Chapter 8's rich-observation-capture material is a clue.)

## 14. Chapter Summary

Reason-Act-Observe is the shared rhythm behind ReAct and CodeAct; what
changes between them is the Action's shape (Chapter 2's territory) and,
this chapter shows, the loop's exposure to a specific failure class. A
constructed pair of 6-file ReAct scripts — sharing identical, individually
correct Observations, differing at exactly one Thought's arithmetic — showed
the loop finishing with a confidently wrong answer, because nothing in
ReAct's mechanism verifies a Thought's claim against the data it interprets.
The equivalent CodeAct action, delegating the same comparison to `max()`,
has no surface for this failure to occur on. This is not speculation: PAL's
own abstract (verified quote) names exactly this failure mode — "logical and
arithmetic mistakes in the solution part, even when the problem is
decomposed correctly" — and reports a verified 15% absolute accuracy
improvement on GSM8K from the same offload-to-interpreter mechanism this
chapter's CodeAct trace uses. The lineage (ReAct → PAL → Toolformer →
CodeAct) is now grounded in direct abstract quotes rather than paraphrase.

## 15. Chapter Deliverable

[`loop_lineage_diagram.md`](loop_lineage_diagram.md) — the annotated
Reason-Act-Observe loop diagram, the ReAct-shaped vs. CodeAct-shaped worked
comparison, the constructed correct-vs-flawed failure-class demonstration
grounded in PAL's verified abstract claim, and the ReAct → PAL → Toolformer
→ CodeAct lineage with direct quotes.

## 16. Further Reading

- Yao, Zhao, Yu, Du, Shafran, Narasimhan, Cao, *ReAct: Synergizing Reasoning
  and Acting in Language Models*, arXiv:2210.03629 (2022-10-06).
- Gao, Madaan, Zhou, Alon, Liu, Yang, Callan, Neubig, *PAL: Program-aided
  Language Models*, arXiv:2211.10435 (2022-11-18) — read the abstract
  directly; its claim about "logical and arithmetic mistakes in the solution
  part" and the verified 15%-absolute GSM8K result are this chapter's most
  load-bearing citation, not background color.
- Schick, Dwivedi-Yu, Dessi, Raileanu, Lomeli, Zettlemoyer, Cancedda,
  Scialom, *Toolformer: Language Models Can Teach Themselves to Use Tools*,
  arXiv:2302.04761 (2023-02-09).
- Wang, Chen, Yuan, Zhang, Li, Peng, Ji, *Executable Code Actions Elicit
  Better LLM Agents*, arXiv:2402.01030 (2024-02-01, ICML 2024) — Chapter 4
  covers this paper's thesis directly.
- Cobbe et al., *Training Verifiers to Solve Math Word Problems* (2021) —
  the paper that introduced GSM8K, the benchmark PAL's verified 15% result
  is measured on; worth reading to understand what GSM8K actually tests
  before treating the 15% figure as a general claim about all reasoning
  tasks rather than specifically grade-school math word problems.
