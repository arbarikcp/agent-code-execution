# Chapter 2 — Action Spaces: Text, JSON, and Code

## 1. Concept

An **action space** is the vocabulary of things an agent's model is allowed
to emit as an action. Three shapes dominate: free text, JSON tool calls, and
executable code. This chapter doesn't just compare them on one example — it
measures a scaling *curve* across task size, quantifies free text's
fragility as a real hit rate, and then deliberately tries to break the
"code always wins" conclusion with a task shaped to be hard for code. The
result is a comparison with actual edges, not a foregone conclusion.

## 2. Why This Matters for Code-Executing Agents

A single-snapshot comparison ("code wins on this one task") is easy to
overclaim from. The scaling sweep in this chapter answers a sharper
question — does code's advantage grow, shrink, or stay constant as tasks
get bigger? — with a real, monotonically-verified answer. The heterogeneity
check answers an even sharper one: is the advantage even real once you
remove the one structural gift (uniformity) the earlier example quietly
relied on? Both answers are load-bearing for the rest of this guide, which
commits to code as the default action space starting Chapter 4.

## 3. Mental Model

Two independent axes explain everything measured in this chapter:

```
Axis 1 — WHO decides what happens between operations?
   Free text / JSON: the harness does, after every single operation (a round trip each time)
   Code:              the action itself does, via real control flow (no round trip between operations)

Axis 2 — Does the action's SIZE grow with the number of operations it performs?
   A uniform task (same op, k times):     code compresses into a loop -> size ~constant in k
   A heterogeneous task (k different ops): code can't compress -> size grows with k, same as JSON's turn count would
```

Every number in this chapter's measurements is either axis 1 (why code needs
fewer turns, always) or axis 2 (why code's TOKEN advantage is sometimes
enormous and sometimes merely large, depending on how compressible the task
is). Conflating the two axes is exactly how you'd arrive at an overclaim
like "code always wins by 90x" — that number is real, but it's an axis-2
result from a maximally uniform task, not a general constant.

## 4. Architecture (place in the loop / context)

The action space is the format of one edge in Chapter 1's loop — the
model-emits-an-action edge — and this chapter's `LoopPredicates` connection
is direct: Chapter 1's `model_chooses_the_action` and
`observation_reenters_model_context` predicates are exactly what's being
measured here in token/turn terms. An `AUTONOMOUS_LOOP` system (Chapter 1)
pays the per-turn cost measured in §2 of `comparison_matrix.md` on every
single iteration — this is why the scaling sweep, not just a single-task
snapshot, is the number that actually matters for a real long-running agent.

## 5. Detailed Explanation

**Free text, measured.** `naive_parse_read_intent` (in `code/action_spaces.py`)
is a realistic first-draft parser — a two-keyword list (`read`, `open`) plus
a filename regex, not an intentionally weak strawman. Run against 8
phrasings a human parses correctly without hesitation, it scores **4/8
(50%) correct**, with two distinct failure categories: `MISSED` (no filename
found — 3 cases, e.g. "Could you check what's in a.txt for me?", where
"check" isn't a recognized keyword) and `WRONG` (a filename WAS found, but
the wrong one — 1 case, `'lab notes.txt'` parsed as `'notes.txt'` because the
regex stops at the first `\w+.\w+` pattern and never sees the space). The
`WRONG` case is the more important failure mode: it doesn't error, it
silently acts on the wrong target — see the Failure Lab for why that matters
more than the raw percentage.

**Structured tool calling, made k-sized.** `build_json_tool_call_trace(k)`
generalizes the original single-task version to any k: k `read_file` calls,
1 `write_file` call, 1 final answer, `k+2` turns total. Every turn's input
reconstructs the full context that call needs — system prompt, tool schema,
and everything resolved so far — because that's what a stateless
chat-completions call actually resends every turn (Chapter 6 covers why
there's no memory between calls without a persistent kernel).

**Code actions, made k-sized.** `build_code_action_trace(k)` uses a GENERIC
loop — `sum(int(read_file(f"f{i}.txt")) for i in range(k))` — instead of
enumerating k filenames. This one choice is the entire reason code's token
count stays flat: the action's own text barely changes as k grows, because
`k` only appears as a number being interpolated into `range(k)`, not as k
repetitions of similar text.

**The scaling sweep (k = 1..30).** JSON's total tokens grow from 891 to
27,455 (30.8x) as k grows 30x — which looks close to linear from the raw
ratio alone. It isn't: `marginal_json_token_cost` computes the cost of each
ADDITIONAL file specifically, and that series — 370, 409, 468, 565, 721,
974, 1,306 tokens per file — is **strictly increasing at every step
measured**, confirmed by direct comparison in the code, not eyeballed.
File #30 costs 3.5x more on its own than file #2 did. Mechanism: every
already-resolved file's read-and-observation gets resent in the context of
every LATER turn, so adding file k+1 doesn't just cost file k+1's own
turn — it lengthens every turn still to come. Code's token count, by
contrast, measured **exactly 296 at every single k tested** — not
"roughly flat," identically flat, because the loop's text genuinely doesn't
depend on k beyond a few digits.

**The honesty check — heterogeneity.** Every result above relied on the
task being UNIFORM (the same operation, k times) — exactly what a `for` loop
compresses. `build_heterogeneous_json_trace`/`build_heterogeneous_code_trace`
test a task with three files needing three DIFFERENT operations (uppercase,
reverse, word-count) — no generic loop possible. Measured: JSON needs 7
turns / 2,647 tokens; code needs 2 turns / 361 tokens — a 3.5x turn
advantage and 7.3x token advantage, both real, both smaller than the
uniform sweep's numbers at comparable task size. The mechanism shifted:
code's win here is pure BUNDLING (three unrelated operations, zero
per-operation round trips), not compression — its own action text now
scales with the number of distinct operations, just like JSON's turn count
does. This is the honest boundary: code's turn advantage is structural and
survives heterogeneity; its token advantage is largest specifically when
uniformity lets it compress, and merely large (not overwhelming) otherwise.

## 6. Minimal Implementation

`code/action_spaces.py`:

- `naive_parse_read_intent`, `FREE_TEXT_VARIANTS`,
  `evaluate_free_text_parser` — the measured free-text fragility check.
- `build_json_tool_call_trace(k)`, `build_code_action_trace(k)`,
  `sweep_k(ks)`, `marginal_json_token_cost(rows)` — the scaling sweep and
  its superlinearity check.
- `build_heterogeneous_json_trace`, `build_heterogeneous_code_trace` — the
  honesty check.
- `count_tokens` — real token counts via `tiktoken`'s `cl100k_base`
  encoding.

Run it directly:

```bash
source .venv/bin/activate
python chapters/ch02-action-spaces/code/action_spaces.py
```

Full output (free-text hit rate, the k=1..30 sweep with marginal costs, and
the heterogeneous comparison) is reproduced in `comparison_matrix.md`.

## 7. Hands-on Lab

`notebooks/ch02_action_spaces.ipynb` (executed, committed with outputs) runs
all three measurements with full narration: the free-text parser's 50% hit
rate broken into `CORRECT`/`MISSED`/`WRONG`, the k=1..30 sweep with the
marginal-cost series and its monotonicity check, and the heterogeneous-task
honesty check with an explicit discussion of why its ratio differs from the
uniform sweep's.

To extend it yourself: add a 4th outcome category to
`evaluate_free_text_parser` — e.g., `RIGHT_FOR_WRONG_REASON`, a case where
the regex finds the correct filename by accident despite the keyword check
having failed for the wrong reason — and see if any of the 8 variants (or a
new one you write) exposes it.

## 8. Failure Lab

The `WRONG` result from §1 (`'lab notes.txt'` → `'notes.txt'`) is the
chapter's sharpest failure case, and it's already been run, not left as an
exercise: a parser that returns `None` fails loudly (the harness knows
something went wrong and can re-prompt); a parser that returns a
plausible-but-wrong filename fails silently (the harness has no signal that
anything is amiss, and proceeds to read/write the wrong file). Reproduce the
consequence directly: imagine `naive_parse_read_intent`'s output feeding a
`read_file` call with no validation that the returned filename actually
matches user intent — the system would silently operate on `notes.txt`
while believing it satisfied a request about `'lab notes.txt'`. This is a
strictly worse failure than a crash, and it's why free text is excluded from
every other comparison in this chapter rather than carried forward as a
"weaker but usable" third option.

## 9. Instrumentation (what to log / trace / measure)

Per turn: input tokens, output tokens, and — specifically for a free-text or
loosely-structured action space — whether the parser's confidence in its own
extraction is itself measurable (most naive parsers, including this
chapter's, have no confidence signal at all; `WRONG` and `CORRECT` are
indistinguishable from the parser's own output). For a scaling analysis:
don't log only the cumulative total per run — log the MARGINAL cost of each
additional step, the way `marginal_json_token_cost` does, since (as §2
shows) the total can look linear while the marginal cost is clearly
accelerating.

## 10. Design Considerations

- **A single-task comparison is a weak basis for a general claim.** The
  original version of this chapter measured k=3 once and reported one
  ratio; the sweep across k=1..30 is what actually supports a claim about
  how the advantage *scales*, which is the claim later chapters (4, 27, 36)
  depend on.
- **Marginal cost, not cumulative total, reveals the true growth shape.**
  A 30.8x-for-30x-k ratio is consistent with linear growth on its own; only
  the strictly-increasing marginal-cost series rules that out. This is a
  reusable analysis habit, not specific to this task.
- **Test your own strongest claim's boundary before publishing it.** §3
  exists because the k=30 sweep's 92.8x number, presented alone, would
  invite the reader to assume code always wins by that much. It doesn't;
  7.3x on a heterogeneous task is the more representative number for tasks
  that aren't perfectly uniform.

## 11. Common Mistakes

- **Generalizing from one task size.** A single k=3 snapshot can't
  distinguish linear from superlinear growth — only a sweep with a computed
  marginal-cost series can, as this chapter now does.
- **Treating "wins" as a single scalar.** Turn-count advantage and
  token-count advantage behave differently under heterogeneity (§3): the
  former survives essentially intact, the latter shrinks. Reporting only
  one of the two hides this.
- **Trusting a parser's success cases without checking its failure
  categories.** A 50% hit rate sounds bad; splitting it into `MISSED` vs.
  `WRONG` shows the more actionable problem is the 1 silently-wrong case,
  not the 3 loudly-missed ones.

## 12. Comparisons / Alternatives

See `comparison_matrix.md` for the full matrix plus all three measurements
(free-text hit rate, k=1..30 scaling sweep with marginal costs, and the
heterogeneous-task honesty check) reproduced with real numbers from this
session's run.

## 13. Review Questions

1. Why does the RAW ratio (30.8x tokens for 30x k) understate how fast
   JSON's cost grows, and what specifically reveals the understatement?
2. Explain, in one sentence each, the two DIFFERENT mechanisms behind code's
   win in §2 (the uniform sweep) versus §3 (the heterogeneous task).
3. Why is the `WRONG` free-text parsing result (`'lab notes.txt'` →
   `'notes.txt'`) arguably worse than a `MISSED` result, even though both
   count as failures?
4. If a task had 100 distinct, unrelated operations (maximally
   heterogeneous), would you expect code's token-count advantage over JSON
   to shrink toward 1x, stay around 7x, or something else? Justify it from
   §3's mechanism, not just intuition.
5. What would you have to change in `build_json_tool_call_trace` to make
   its token growth genuinely linear (not superlinear) in k? (Hint: what
   specifically causes the marginal cost to rise?)

## 14. Chapter Summary

Three real measurements, not one snapshot: a realistic free-text parser
scores 50% (4/8) on phrasings a human parses instantly, with its one wrong
answer (not just missed answers) showing why free text is excluded from
serious comparison. A k=1..30 scaling sweep shows JSON tool calling's total
token cost is not merely large but SUPERLINEAR — the marginal cost per
additional file rises monotonically (370 → 1,306 tokens) — while a
code action's token cost stays exactly flat (296) for a uniform task, because
one generic loop compresses arbitrarily many operations into constant-size
text. A deliberate honesty check on a HETEROGENEOUS task (no generic loop
possible) confirms code's turn-count advantage is structural and survives
(3.5x), while its token-count advantage — driven by compression, not
bundling alone — shrinks from the uniform sweep's 92.8x down to a still-real
but far more modest 7.3x. The chapter's conclusion is narrower and more
defensible than "code always wins": code's turn advantage is close to
unconditional; its token advantage depends on how compressible the task is.

## 15. Chapter Deliverable

[`comparison_matrix.md`](comparison_matrix.md) — the full matrix plus all
three measurements (free-text hit rate, scaling sweep with marginal-cost
analysis, heterogeneous-task honesty check) with real numbers reproduced
from this session's run.

## 16. Further Reading

- Wang et al., *Executable Code Actions Elicit Better LLM Agents* (CodeAct,
  2024) — Chapter 4 covers this paper's thesis directly; its empirical claim
  (fewer actions, higher success versus JSON-style tool calling) is the same
  turn/token effect this chapter measures directly, including this chapter's
  finding that the size of the effect is task-dependent.
- Gao et al., *PAL: Program-Aided Language Models* (2022) — an early
  demonstration that offloading composition/computation to executable code
  improves reliability; a precursor to the code-action argument this chapter
  measures rather than merely restates.
- OpenAI's and Anthropic's function-calling / tool-use documentation — worth
  reading directly for how a production JSON tool-calling schema and
  response format compare to the simplified `TOOL_SCHEMAS` used here, and
  whether production schemas' extra fields (strict typing, enum constraints)
  would change the token-growth curve measured in §2.
