"""One-off script that generates ch02_action_spaces.ipynb via nbformat.

Not part of the chapter's runnable deliverables — kept only so the notebook's
structure is reproducible/diffable from source instead of hand-edited JSON.
Run: python build_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Chapter 2 — Action Spaces: Text, JSON, and Code

Hands-on lab, pushed past the original "compare turns and tokens on one
3-file task" direction into three real measurements:

1. A free-text parser's actual hit rate across 8 phrasings (not asserted fragility — measured).
2. A full scaling sweep, k=1..30, with the MARGINAL token cost per additional
   file computed directly — enough to actually confirm superlinear growth,
   not just eyeball a ratio.
3. An honesty check: does code's advantage survive when the task is
   heterogeneous (three different operations, no generic loop possible)?

All from [`../code/action_spaces.py`](../code/action_spaces.py)."""
))

cells.append(nbf.v4.new_code_cell(
"""import sys
sys.path.insert(0, "../code")

from action_spaces import (
    FREE_TEXT_VARIANTS, evaluate_free_text_parser, naive_parse_read_intent,
    sweep_k, render_sweep, marginal_json_token_cost,
    build_heterogeneous_json_trace, build_heterogeneous_code_trace, summarize,
    JSON_SYSTEM_PROMPT, CODE_SYSTEM_PROMPT,
)"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. Free text — measured, not just illustrated

`naive_parse_read_intent` is a first-draft parser: a two-word keyword list
(`read`, `open`) plus a filename regex — the kind of thing a developer
writes on the first pass, not an adversarially weak strawman. Run against 8
phrasings, tracking three outcomes: `CORRECT`, `MISSED` (no filename found
at all), and `WRONG` (a filename WAS found, but it's not the one intended —
a worse failure than missing, because it looks successful)."""
))

cells.append(nbf.v4.new_code_cell(
"""results = evaluate_free_text_parser(FREE_TEXT_VARIANTS)
for r in results:
    print(f"[{r['outcome']:7}] {r['text']!r:65} -> got={r['got']!r}")

n_correct = sum(1 for r in results if r["outcome"] == "CORRECT")
n_missed = sum(1 for r in results if r["outcome"] == "MISSED")
n_wrong = sum(1 for r in results if r["outcome"] == "WRONG")
print(f"\\n{n_correct} correct, {n_missed} missed, {n_wrong} wrong -- out of {len(results)} ({n_correct/len(results):.0%} correct)")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""**50% correct, on phrasings a human reads instantly and correctly, 100% of
the time.** The `WRONG` case (`'lab notes.txt'`) matters more than the raw
percentage: the parser confidently returns `'notes.txt'` — a plausible,
well-formed filename that is simply not the file the text named. A harness
built on this parser wouldn't error out here; it would silently act on the
wrong file. This is the concrete shape of "fragility": not "sometimes it
crashes," but "sometimes it's wrong in a way that looks right.\""""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 2. Scaling sweep — the full curve, not one snapshot

The original version of this comparison measured exactly one task size
(k=3 files) and reported one ratio. Here's the same measurement across
k = 1, 2, 3, 5, 8, 13, 21, 30 — enough points to see the SHAPE of the growth,
not just one number on it."""
))

cells.append(nbf.v4.new_code_cell(
"""rows = sweep_k([1, 2, 3, 5, 8, 13, 21, 30])
print(render_sweep(rows))"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Code's token count is **exactly flat (296) at every k measured** — the
generic loop `sum(int(read_file(f"f{i}.txt")) for i in range(k))` doesn't
grow with k at all; only the digits of `k` itself change. JSON's token count
grows from 891 to 27,455 — a 30.8x increase for a 30x increase in k, which
LOOKS roughly linear from the ratio alone. Is it actually linear, or does
that ratio hide something? Check the MARGINAL cost — how many extra tokens
each additional file costs, not the cumulative total:"""
))

cells.append(nbf.v4.new_code_cell(
"""deltas = marginal_json_token_cost(rows)
for k, dk, per_file in deltas:
    print(f"up to k={k:>2}: +{per_file:>6.0f} tokens per additional file (over the last {dk} added)")

is_rising = all(b[2] > a[2] for a, b in zip(deltas, deltas[1:]))
print(f"\\nMarginal cost strictly increasing at every step measured: {is_rising}")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""**The marginal cost per additional file rises monotonically: 370 -> 409 ->
468 -> 565 -> 721 -> 974 -> 1,306 tokens.** File #30 costs 3.5x more, on
its own, than file #2 did. This is the real mechanism, made visible instead
of asserted: every file that's already been read gets RESENT in the context
of every turn that comes after it (a stateless chat-completions call has no
memory of its own — Chapter 6 covers why), so adding file k+1 doesn't just
add file k+1's own read-and-observe cost, it also lengthens every one of the
turns still to come. The 30.8x-for-30x-k ratio from the raw totals actually
*understates* the effect, because the fixed prefix (system prompt + tool
schema, paid once per turn regardless of k) dilutes the ratio at small k
while the accelerating marginal cost dominates at large k."""
))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Honesty check — does code still win without a generic loop?

Every code-wins result so far used a UNIFORM task (the same operation,
repeated k times) — exactly the case a `for` loop compresses best. What
happens on a HETEROGENEOUS task, where each of three files needs a
DIFFERENT operation (uppercase, reverse, word-count) and no generic loop is
possible?"""
))

cells.append(nbf.v4.new_code_cell(
"""het_json = summarize(build_heterogeneous_json_trace())
het_code = summarize(build_heterogeneous_code_trace())

print(f"JSON: {het_json['turns']} turns, {het_json['total_tokens']} tokens")
print(f"Code: {het_code['turns']} turns, {het_code['total_tokens']} tokens")
print(f"Turn ratio:  {het_json['turns']/het_code['turns']:.1f}x")
print(f"Token ratio: {het_json['total_tokens']/het_code['total_tokens']:.1f}x")"""
))

cells.append(nbf.v4.new_markdown_cell(
"""Code still wins — 3.5x fewer turns, 7.3x fewer tokens — but the MECHANISM
is different from the scaling sweep above. There, code won because one
generic loop's SIZE didn't grow with k. Here, the code action's size DOES
reflect all three bespoke operations (three separate lines, not a loop) —
its win comes purely from BUNDLING three unrelated operations into one
action, with no per-operation round trip, not from compression. This is the
honest boundary of the composability claim: **code's turn-count advantage
survives heterogeneity (bundling doesn't require uniformity); its
token-count advantage is largest specifically when the task IS uniform
enough to compress into a loop, and smaller — though still real here — when
it isn't.** Claiming "code always wins by 90x" from the k=30 homogeneous
result alone would have been an overclaim; this task shows a more modest,
but still decisive, 7.3x."""
))

nb['cells'] = cells

with open("ch02_action_spaces.ipynb", "w") as f:
    nbf.write(nb, f)

print("wrote ch02_action_spaces.ipynb")
