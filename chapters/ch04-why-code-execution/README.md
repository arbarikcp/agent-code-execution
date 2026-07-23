# Chapter 4 — Why Code Execution

## 1. Concept

Chapter 2 showed *what* the three action spaces are and measured one worked
task. Chapter 3 showed *how* the loop's action shape evolved from ReAct to
CodeAct. This chapter makes the argument explicit: **executable code should
be the default action space for a multi-step, data-touching agent loop**,
because composition, reuse, and self-correction can all happen *inside* one
action instead of being spread across many round trips supervised by the
harness. This is the CodeAct thesis (Wang et al., 2024) — this chapter
internalizes it with runnable evidence, not just a citation.

## 2. Why This Matters for Code-Executing Agents

This is the last chapter before the guide starts building an actual agent
(Chapter 5). Everything from here on assumes code is the action space without
re-arguing the point every chapter. If the argument in this chapter doesn't
land, the rest of the guide reads as an arbitrary implementation choice
instead of a reasoned one — this is the chapter where "why code" gets settled
so it can be assumed afterward.

## 3. Mental Model

Five separate arguments, each demonstrated with a small runnable example in
`code/why_code.py`:

```
Composability      → one code action does what k JSON calls would need
Tool reuse          → existing library functions need zero new registration
Pretraining alignment → models have seen far more code than any bespoke JSON schema
Dynamic revision    → the interpreter's real error output drives a real fix
Costs and risks     → wider failure surface; containment handed off to the sandbox guide
```

The first four are the case *for* code actions; the fifth is the honest
accounting of what that case costs. A rationale that only lists benefits
isn't a rationale — Chapter 4's deliverable includes both sides.

## 4. Architecture (place in the loop / context)

This chapter doesn't change the loop's shape (still Reason-Act-Observe, per
Chapter 3) — it justifies committing to one particular shape of Action for
the rest of the guide. Every later chapter's code assumes this decision:
Chapter 5's backbone agent extracts and executes code blocks specifically
because this chapter concluded that's the right default; Chapter 9's
executor interface, Chapter 28's tool-as-code pattern, and Part VII's code
generation quality work all build on code being the committed action space.

## 5. Detailed Explanation

**Composability.** `code/why_code.py`'s `run_benchmark` reruns the
"sum k files" task (Chapters 2–3) across k = 1, 3, 5, 6, 7, 10, 20 under a
shared 8-step budget. JSON tool calling needs `k + 2` steps (k reads, 1
write, 1 final answer) — a code action needs a constant 2. Measured result:
JSON tool calling succeeds for k ≤ 6 and fails outright for k ≥ 7 (exceeds
the budget); the code action succeeds at every k tested. Overall: **4/7
(57%)** for JSON tool calls vs. **7/7 (100%)** for the code action, on this
toy benchmark, under this step budget.

**Does that 57%-vs-100% gap generalize, or was budget=8 a special case?**
`sweep_budgets()` answers this directly by sweeping the budget itself from 3
to 24 (same task sizes, `code_as_action_rationale.md` has the full table).
Code's success rate is **100% at every single budget tested**, including the
tightest (3 steps) — its step count never scales with task size at all.
JSON's success rate climbs monotonically as the budget loosens — 14% → 29%
→ 57% → 71% → 86% → 100% — reaching parity with code only once the budget is
generous enough to fit every task size tested. The "largest k JSON can fit"
is exactly `budget - 2` at every point on this curve, a direct algebraic
consequence of the two step-cost formulas, not a statistical artifact. The
original 57%-vs-100% snapshot is one point on this line, not cherry-picked.

**Tool reuse.** `demo_tool_reuse()` runs `statistics.mean` — an ordinary
stdlib function — inside a code action with zero prior registration, and
gets a real, correct result (`13.2` for a fixed input list). The JSON-mode
equivalent, `HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN`, would need to be
defined and exposed *before* the model could perform the same operation.
Every new kind of computation a code-action agent needs is either already
available (any importable library) or a one-line `import`; every new kind a
JSON-mode agent needs is a new schema, a new registration, and — per
Chapter 2's token measurements — a real token cost to expose it.

**Alignment with pretraining.** Unlike the three points above, this one
isn't independently measured in this chapter — it's a claim about training
data composition (LLMs see vastly more code than any specific bespoke JSON
schema during pretraining) that this guide cannot verify by running code. It
is reported in `code_as_action_rationale.md` as the CodeAct paper's stated
motivation, explicitly flagged as unmeasured here rather than presented as a
number.

**Dynamic revision.** `demo_dynamic_revision()` runs a code action that
really divides by zero, captures the real traceback
(`traceback.format_exc()`), and runs a second code action — written to guard
the zero-count case — that really succeeds (`avg = 0.0`). The traceback
that drives the fix is the interpreter's actual output, not a canned string;
this is the mechanical seed of Chapter 22's self-debugging loop.

**Costs and risks.** Code actions can do anything the interpreter can do —
this is the flip side of composability. Non-determinism is now MEASURED, not
just claimed: `demo_nondeterminism()` runs the identical source text
(`import time; result = time.time()`) twice and gets two different results
(`1784809267.251519` vs. `1784809267.251528`). Identical code, genuinely
different output — a JSON tool-calling system's non-determinism is bounded
by whatever tools were actually registered; if nobody registered a
time-reading tool, that specific non-determinism is simply unavailable to
the agent, not merely discouraged. `code_as_action_rationale.md` covers
debugging cost and containment burden as the other two concrete costs, and
is explicit that **this guide does not implement runtime containment** —
that's the sibling guide, *Code Execution Sandboxing for AI Agents*.

## 6. Minimal Implementation

`code/why_code.py`:

- `run_benchmark`, `run_json_tool_solver`, `run_code_action_solver`,
  `summarize_benchmark`, `render_benchmark_table` — the step-budget
  composability benchmark, real execution, real success/failure.
- `sweep_budgets`, `render_budget_sweep` — sweeps the budget itself (3 to
  24) to confirm the single-snapshot result generalizes.
- `demo_tool_reuse`, `HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN` — the tool-reuse
  demonstration and its JSON-mode counterfactual.
- `demo_dynamic_revision` — the real-traceback-drives-real-fix demonstration.
- `demo_nondeterminism` — runs identical code twice, shows the real output
  differs.

Run it directly:

```bash
source .venv/bin/activate
python chapters/ch04-why-code-execution/code/why_code.py
```

```
=== 1. Composability under an 8-step budget ===
  k | json steps | json ok | code steps | code ok
-------------------------------------------------
  1 |          3 |    True |          2 |    True
  ...
  7 |          9 |   False |          2 |    True
 20 |         22 |   False |          2 |    True

json_tool_calls: 4/7 succeeded (57%), avg steps needed = 9.4
code_action: 7/7 succeeded (100%), avg steps needed = 2.0

=== 2. Tool reuse (statistics.mean, zero registration) ===
code action result: 13.2
...
=== 3. Dynamic revision (real traceback -> real fix) ===
First action's real traceback (tail):
  ZeroDivisionError: division by zero
Second action's result after the fix: 0.0
```

## 7. Hands-on Lab

`notebooks/ch04_why_code_execution.ipynb` (executed, committed with outputs)
carries out the chapter's hands-on direction and then goes further: runs the
original step-budget benchmark, then the full budget sweep (3 to 24) with a
discussion of why the "max k JSON can fit" column is exactly `budget - 2`,
then the tool-reuse and dynamic-revision demos, then the non-determinism
demo with a discussion of why a JSON tool-calling agent can't reproduce the
same non-determinism unless someone explicitly registers a
non-deterministic tool.

To extend it yourself: add a budget of 2 to the sweep and confirm code's
success rate stays 100% (its absolute floor — 1 action + 1 final answer) —
then try budget=1 and see both approaches fail outright, since even a code
action needs a second turn to state its final answer.

## 8. Failure Lab

Reproduce a case where code actions genuinely *lose* to structured calling:
take `demo_tool_reuse` and imagine a tool surface where the agent must only
ever call one of three pre-approved, individually-audited operations (e.g. a
financial system that permits exactly "read balance," "read limit," "flag for
review," nothing else, ever). A code action here is strictly worse: it can
still only meaningfully call those three operations, but now a reviewer has
to read arbitrary Python to confirm *only* those three operations happened,
instead of reading three typed JSON calls. This is the concrete shape of
"when JSON tool calling is still the right choice" — Chapter 2's answer,
confirmed rather than contradicted by this chapter's benchmark, because the
benchmark's win condition (fewer steps under a budget) isn't the only thing
that matters in every context.

## 9. Instrumentation (what to log / trace / measure)

Per task: steps needed vs. steps used, success/failure against a ground
truth (not just "did it finish"), and — for code actions specifically —
whether execution raised an exception and what type. `run_benchmark`'s
`assert`-based correctness check and `demo_dynamic_revision`'s captured
`traceback.format_exc()` output are both minimal versions of what Chapter 59
formalizes as structured run tracing.

## 10. Design Considerations

- **A step budget is what makes composability matter.** Without any budget,
  JSON tool calling "only" costs more tokens and turns (Chapter 2's finding)
  but still eventually succeeds. Once a budget exists — as any production
  system needs, per Chapter 27 — composability becomes a success/failure
  question, not just a cost question, exactly as this chapter's benchmark
  shows.
- **The rationale should name its own limits.** `code_as_action_rationale.md`
  distinguishes the one verified external claim (CodeAct's "up to 20%")
  from this chapter's own much smaller toy benchmark, and separately flags
  the pretraining-alignment claim as unmeasured. Treat any future addition
  to this rationale the same way: cite what's verified, measure what can be
  measured, and label the rest as a stated-but-unverified claim.
- **Containment is a deliberate non-goal of this chapter and this guide's
  Parts I–X.** Design for it structurally (least-privilege tool exposure,
  approval gates — Chapters 62–63) but implement the actual isolation via
  the sandbox guide.

## 11. Common Mistakes

- **Treating the CodeAct paper's "up to 20%" as this chapter's own result.**
  It's a citation, not a reproduction — this chapter's own benchmark is a
  much smaller, self-contained demonstration of the same mechanism, and the
  README/rationale are careful to keep the two separate.
- **Forgetting the cost side of the argument.** A rationale that's all
  upside would itself be the kind of unverified claim CLAUDE.md warns
  against — Section 5's "Costs and risks" and the Failure Lab exist so the
  case for code actions isn't one-sided.
- **Assuming pretraining alignment is measured here.** It's explicitly
  flagged as the one argument in this chapter that isn't backed by a run —
  see Section 5.

## 12. Comparisons / Alternatives

| Claim | Evidence in this chapter | Status |
|---|---|---|
| Composability reduces steps/improves success under a budget | `run_benchmark`: 100% vs. 57% success, 7 tasks | Measured (own toy benchmark) |
| That gap holds generally, not just at budget=8 | `sweep_budgets`: monotonic 14%→100% JSON curve across budgets 3-24 | Measured (own toy benchmark) |
| CodeAct beats alternatives on a real benchmark | Paper abstract: "up to 20% higher success rate," API-Bank, 17 LLMs | Verified citation, not reproduced |
| Tool reuse needs zero registration | `demo_tool_reuse`: real `statistics.mean` call | Measured |
| Dynamic revision uses real interpreter feedback | `demo_dynamic_revision`: real traceback → real fix | Measured |
| Pretraining alignment improves code reliability | CodeAct paper's stated motivation | Cited, not independently measured |
| Code actions are genuinely more non-deterministic | `demo_nondeterminism`: identical code, two different real outputs | Measured |
| Code actions cost more in debugging/containment | Failure Lab; sandbox-guide handoff | Argued, not benchmarked (out of this guide's scope) |

## 13. Review Questions

1. Why does the step-budget benchmark show a success-rate *gap* (57% vs.
   100%) rather than just a token/turn-count difference like Chapter 2's
   comparison?
2. In the budget sweep, why is "max k JSON can fit" always exactly
   `budget - 2`, and why does code's success rate never depend on the
   budget at all (down to budget=2)?
3. What, specifically, makes `demo_tool_reuse`'s code action need "zero
   registration" — what would have to happen for JSON tool calling to call
   the same stdlib function?
4. `demo_nondeterminism` shows a JSON tool-calling agent CAN'T introduce the
   same non-determinism unless a tool exposes it. Is that a limitation of
   JSON tool calling, or a safety property? Argue both sides.
5. Which of this chapter's claims (composability, budget generality, tool
   reuse, pretraining alignment, dynamic revision, non-determinism) is the
   *only* one not backed by something this chapter actually ran? Why
   couldn't it be, even in principle, without external data this guide
   doesn't have access to?

## 14. Chapter Summary

Code should be the default action space for multi-step, data-touching agent
loops because composition, reuse, and correction happen inside one action
instead of being spread across harness-mediated round trips. This chapter
demonstrated its claims with real, runnable evidence rather than a single
snapshot: composability, checked not just at one budget but across a full
sweep (3 to 24 steps), shows JSON's success rate climbing monotonically from
14% to 100% as the budget loosens while code stays at 100% throughout —
confirming the original 57%-vs-100% result generalizes rather than being
cherry-picked; tool reuse (an unregistered stdlib call working immediately);
dynamic revision (a real traceback driving a real fix); and non-determinism
(identical source code producing two different real outputs). The chapter
also cited, without independently reproducing, the CodeAct paper's own
verified claim of "up to 20% higher success rate" on a real benchmark across
17 LLMs. One claim, alignment with pretraining, is reported as the paper's
stated rationale rather than measured, because it concerns training-data
composition this guide has no way to verify by running code. The remaining
costs — debugging difficulty and containment burden — are argued, not
benchmarked, and handed off explicitly to the sibling sandbox guide.

## 15. Chapter Deliverable

[`code_as_action_rationale.md`](code_as_action_rationale.md) — a written
rationale for code-as-action, combining the verified CodeAct paper claim with
this chapter's own benchmark notes (step-budget composability and its
generalization across a full budget sweep, tool reuse, dynamic revision, and
measured non-determinism) and an explicit costs/risks section with the
sandbox-guide handoff.

## 16. Further Reading

- Wang, Chen, Yuan, Zhang, Li, Peng, Ji, *Executable Code Actions Elicit
  Better LLM Agents*, arXiv:2402.01030 — this chapter's central citation;
  abstract re-checked in this session for its exact quantitative claim
  ("up to 20% higher success rate," API-Bank, 17 LLMs, CodeActInstruct
  dataset of 7k multi-turn interactions).
- Gao et al., *PAL: Program-Aided Language Models*, arXiv:2211.10435 —
  Chapter 3's lineage entry for "offload computation to a real interpreter,"
  the mechanism `demo_tool_reuse` and `demo_dynamic_revision` both exercise.
- The sibling guide, *Code Execution Sandboxing for AI Agents* — the
  explicit destination for the "costs and risks" section's containment
  concerns; not reproduced or summarized here beyond naming it, per this
  guide's handoff convention (see `CLAUDE.md` and Part XI of the guide
  index).
