# Action-Space Comparison Matrix

Use this matrix to select an action space, not to rank them.

## Decision matrix

| Dimension | Free text | Structured tool calls | Code actions |
|---|---|---|---|
| Contract | Natural-language convention | Tool names plus argument schemas | Programming language plus exposed APIs |
| Machine interpretation | Requires intent parsing | Direct, schema-validatable | Requires parsing, validation, and execution |
| Local control flow | Described, not executed | Usually limited; may batch independent calls | Loops, branches, functions, exceptions |
| Intermediate data | Implicit in prose/context | Usually returns through the harness | Variables and in-process values |
| Composition | Parser/harness dependent | Harness, later turns, or multi-call response | Native to the action |
| Pre-execution validation | Difficult | Strong for shape; semantics still need checks | Possible but substantially broader |
| Per-effect approval | Ambiguous | Natural boundary | Harder when effects are bundled |
| Typical failure | Misinterpreted intent | Valid shape but wrong tool/argument | Syntax, runtime, API, or partial-effect failure |
| Strong fit | Human-reviewed plans, conversation | Small bounded operations, sensitive effects | Multi-step computation and data-heavy workflows |
| Poor fit | Direct machine execution without grounding | Deep data-dependent orchestration | One simple high-risk mutation |

Structured APIs may emit multiple or parallel calls in one response. Code is
not automatically cheaper or more reliable; it permits more orchestration
inside one action.

## Worked example

Task: read three integer files, compute their sum, and write `total.txt`.

### Free text

```text
Read f0.txt, f1.txt, and f2.txt, add the values, and save the result in
total.txt.
```

A parser must recover the exact operations, arguments, ordering, and data flow.

### Structured calls: one-call-per-turn protocol

```text
Turn 1  read_file(f0.txt) → "4"
Turn 2  read_file(f1.txt) → "11"
Turn 3  read_file(f2.txt) → "18"
Turn 4  write_file(total.txt, "33") → ok
Turn 5  final answer
```

This is easy to inspect and gate operation by operation. If the protocol
supports parallel independent calls, the three reads can share a response.

### Code action

```python
total = sum(int(read_file(f"f{i}.txt")) for i in range(3))
write_file("total.txt", str(total))
print(total)
```

The loop compresses repeated reads and variables carry data. The executor must
validate a compound action and account for partial side effects.

## Reproducible trace-accounting experiment

Run:

```bash
python chapters/ch02-action-spaces/code/action_spaces.py
```

The script constructs messages and counts their text with `cl100k_base`. It is
a deterministic protocol simulation. It does not invoke a model, execute the
file operations, measure latency, test success rates, account for prompt
caching, or reproduce a provider bill.

### Free-text demonstration set

```text
[CORRECT] "I should start by reading ... a.txt ..."  → a.txt
[CORRECT] "Let's open a.txt ..."                     → a.txt
[MISSED ] "First, can you get me a.txt?"             → None
[CORRECT] "Read: a.txt"                              → a.txt
[CORRECT] "I'll read ... a.txt now."                 → a.txt
[MISSED ] "Could you check what's in a.txt ...?"     → None
[MISSED ] "Peek into a.txt quickly."                 → None
[WRONG  ] "read ... 'lab notes.txt'"                 → notes.txt

4 correct, 3 missed, 1 wrong
```

This selected set demonstrates failure categories. It is not a population
estimate of free-text parsing accuracy.

### Uniform-task sweep

Assumptions:

- one structured tool call per model turn;
- each represented turn includes accumulated conversation history;
- code can express the repeated operation with a loop;
- both traces include a final-answer turn;
- counts use a proxy tokenizer and ignore provider caching.

| `k` files | Structured turns | Structured tokens | Code turns | Code tokens | Count ratio |
|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 891 | 2 | 296 | 3.0× |
| 2 | 4 | 1,261 | 2 | 296 | 4.3× |
| 3 | 5 | 1,670 | 2 | 296 | 5.6× |
| 5 | 7 | 2,605 | 2 | 296 | 8.8× |
| 8 | 10 | 4,300 | 2 | 296 | 14.5× |
| 13 | 15 | 7,905 | 2 | 296 | 26.7× |
| 21 | 23 | 15,701 | 2 | 296 | 53.0× |
| 30 | 32 | 27,455 | 2 | 296 | 92.8× |

The marginal structured-trace increase is 370, 409, 468, 565, 721, 974,
and 1,306 counted tokens per additional file across the sampled intervals.
It rises because later turns repeat a longer represented history.

The proper conclusion is conditional:

> In this one-call-per-turn, full-history trace model, a loop keeps the sampled
> code trace compact while the structured trace accumulates repeated context.

Do not generalize the 92.8× count ratio to production cost.

### Heterogeneous-task boundary check

The script also models three different operations—uppercase, reverse, and word
count—that cannot be compressed into one generic loop.

```text
Structured trace: 7 turns, 2,647 counted tokens
Code trace:       2 turns,   361 counted tokens
```

Code still bundles the operations, but its text contains each operation. This
separates **bundling** from **compression** and shows why the advantage depends
on task structure.

## Selection guide

Choose **free text** when a person will interpret or approve open-ended intent.

Choose **structured calls** when bounded operations, argument validation,
auditing, or per-effect approval dominate.

Choose **code actions** when the task genuinely benefits from local data flow,
loops, branching, or library use.

Choose a **hybrid** when code should perform computation but sensitive effects
must cross narrow, separately governed tool boundaries.
