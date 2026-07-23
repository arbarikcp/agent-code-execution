# Action-Space Comparison Matrix

*Chapter 2 deliverable: a comparison matrix of action spaces with worked examples.*

Three separate measurements back this matrix, all from
[`code/action_spaces.py`](code/action_spaces.py) and reproduced exactly as
run in this session. Token counts use `tiktoken`'s `cl100k_base` encoding —
a proxy for whatever model the backbone agent eventually uses (chosen in
Chapter 5 via litellm), used here only so every comparison is reproducible
rather than asserted.

## Matrix

| | Free text | JSON tool calling | Code action |
|---|---|---|---|
| **Control flow** | None | None — the harness decides what runs next between calls | Full (loops, conditionals) inside one action |
| **Data flow** | Implicit, described in prose | Explicit but manual — every result round-trips through the model | Explicit and direct — a variable holds the result |
| **Growth with task size k (measured)** | N/A — doesn't scale at all (see §1) | Turns: `k+2`, linear. Tokens: **superlinear** — marginal cost per file rises monotonically (see §2) | Turns: constant (2). Tokens: **constant (296)** for a uniform task (see §2) |
| **Growth on a heterogeneous task (measured)** | N/A | 7 turns, 2,647 tokens (see §3) | 2 turns, 361 tokens — advantage survives, smaller than the uniform case (see §3) |
| **Parsing burden (measured)** | High — a reasonable first-draft parser scores 50% (see §1) | Low — fixed JSON schema | Low — a fenced code block, but correctness still requires running it |
| **Failure surface** | Silent misparsing (looks correct, isn't) | Malformed JSON, wrong tool name/args | Syntax errors, runtime exceptions, hallucinated APIs (Ch 46) |
| **Best fit** | Prototyping only | Small, fixed, low-composition, high-auditability tool surfaces | Multi-step, stateful, or data-heavy tasks |

## §1. Free text — measured fragility, not asserted

`naive_parse_read_intent` — a realistic first-draft parser (keywords `read`,
`open`, plus a filename regex) — run against 8 phrasings a human parses
correctly without a second thought:

```
[CORRECT] 'I should start by reading the contents of a.txt so I know the first number.' -> got='a.txt'
[CORRECT] "Let's open a.txt and see what's inside."                         -> got='a.txt'
[MISSED ] 'First, can you get me a.txt?'                                    -> got=None
[CORRECT] 'Read: a.txt'                                                     -> got='a.txt'
[CORRECT] "I'll read the file called a.txt now."                            -> got='a.txt'
[MISSED ] "Could you check what's in a.txt for me?"                         -> got=None
[MISSED ] 'Peek into a.txt quickly.'                                        -> got=None
[WRONG  ] "Could you read the file named 'lab notes.txt'?"                  -> got='notes.txt'

4/8 correct (50%)
```

The `WRONG` result matters more than the 50% headline: the parser doesn't
fail loudly on `'lab notes.txt'` — it confidently returns `'notes.txt'`, a
plausible, well-formed, WRONG filename. A harness built on this parser
wouldn't error here; it would silently act on the wrong file. That's the
real shape of free-text fragility: not crashes, but confident wrongness.

## §2. Scaling sweep — the curve, not a snapshot

Measured across k = 1, 2, 3, 5, 8, 13, 21, 30 files (sum-k-files task):

```
  k | json turns | json tokens | code turns | code tokens | token ratio
-----------------------------------------------------------------------
  1 |          3 |         891 |          2 |         296 |        3.0x
  2 |          4 |        1261 |          2 |         296 |        4.3x
  3 |          5 |        1670 |          2 |         296 |        5.6x
  5 |          7 |        2605 |          2 |         296 |        8.8x
  8 |         10 |        4300 |          2 |         296 |       14.5x
 13 |         15 |        7905 |          2 |         296 |       26.7x
 21 |         23 |       15701 |          2 |         296 |       53.0x
 30 |         32 |       27455 |          2 |         296 |       92.8x
```

Code's token count is **exactly flat (296) at every k** — a generic
`sum(... for i in range(k))` loop doesn't grow with k, only its digits do.
JSON's token count grows 30.8x for a 30x growth in k — which looks roughly
linear from the raw ratio. It isn't. The **marginal** cost per additional
file — not the cumulative total — is what reveals the real shape:

```
up to k= 2: +   370 tokens per additional file
up to k= 3: +   409 tokens per additional file
up to k= 5: +   468 tokens per additional file
up to k= 8: +   565 tokens per additional file
up to k=13: +   721 tokens per additional file
up to k=21: +   974 tokens per additional file
up to k=30: +  1306 tokens per additional file

Strictly increasing at every step measured: True
```

File #30 costs 3.5x more, on its own, than file #2 did — the marginal cost
is **monotonically increasing**, confirming superlinear (not linear) growth.
The mechanism: a stateless call resends the full history every turn, so
adding file k+1 doesn't just add its own read-and-observe cost — it also
lengthens every turn still to come. The raw 30.8x total-growth ratio
understates this, because a large fixed prefix (system prompt + tool
schema) dilutes the ratio at small k while the accelerating marginal cost
dominates at large k.

## §3. Honesty check — does the advantage survive heterogeneity?

Every result above used a UNIFORM task (the same operation, k times) —
exactly what a `for` loop compresses best. On a HETEROGENEOUS task (three
files, three DIFFERENT operations — uppercase, reverse, word-count — no
generic loop possible):

```
JSON: 7 turns, 2647 tokens
Code: 2 turns, 361 tokens
Turn ratio:  3.5x
Token ratio: 7.3x
```

Code still wins, but the mechanism changed: in §2, code won because one
generic loop's SIZE didn't grow with k (compression). Here, the code
action's size DOES reflect all three bespoke operations — its win comes
purely from BUNDLING three unrelated operations into one action, with zero
per-operation round trips, not from compression. **Code's turn-count
advantage survives heterogeneity; its token-count advantage is largest when
the task is uniform enough to compress, and smaller — though still
real (7.3x here) — when it isn't.** Claiming "code always wins by ~90x"
from §2's k=30 result alone would have been an overclaim this section
exists specifically to correct.

## When JSON tool calling is still the right choice

Not just when tasks are small — the measurements above are specifically
about tasks with real composition or scale. JSON tool calling is still the
right choice when:

- **Auditability matters more than efficiency.** A single structured call is
  trivial to inspect, log, and gate behind human approval (Chapter 25) at
  the level of one operation; a code action bundles several effects into one
  block that either all run or (on error) partially run.
- **The task is genuinely small AND fixed.** §2's flat 296-token code cost
  only pays off once there's more than one or two operations to bundle —
  for a true one-shot call, the code action's own fixed overhead (importing,
  structuring output) can exceed a single JSON call's cost.
- **No code-execution environment is available**, or the trust boundary
  doesn't allow arbitrary code (Chapter 62).

The rest of this guide is built around code actions because most of its
target tasks are multi-step and data-heavy — exactly the regime §2 and §3
both show code actions winning in, honestly bounded by §3's finding that the
*margin* depends on how compressible the task actually is.
