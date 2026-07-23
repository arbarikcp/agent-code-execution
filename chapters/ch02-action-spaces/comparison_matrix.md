# Action-Space Comparison Matrix

*Chapter 2 deliverable: a comparison matrix of action spaces with worked examples.*

Task used for the worked example: files `a.txt`, `b.txt`, `c.txt` each hold one
integer (42, 17, 8); sum them and write the result to `total.txt`. Full traces and
measurement code: [`code/action_spaces.py`](code/action_spaces.py). Token counts
are real measurements from `tiktoken`'s `cl100k_base` encoding — a proxy for
whatever model the backbone agent eventually uses (chosen in Chapter 5 via
litellm), used here only so the comparison is reproducible rather than asserted.

## Matrix

| | Free text | JSON tool calling | Code action |
|---|---|---|---|
| **Control flow** | None — one sentence of intent per turn | None — the harness decides what runs next between calls | Full (loops, conditionals, generator expressions) inside one action |
| **Data flow** | Implicit, described in prose | Explicit but manual — each result must round-trip through the model to reach the next call | Explicit and direct — a variable holds the result, no round trip needed |
| **Composition (this task)** | Not attempted at scale — doesn't compose reliably past one step (see Worked Example 1) | 4 tool calls, 4 round trips (3 reads + 1 write) | 3 reads + 1 sum + 1 write in a single action |
| **Turns for this task** | N/A (fragile past step 1) | **5** (4 tool calls + 1 final answer) | **2** (1 code action + 1 final answer) |
| **Total tokens for this task** | N/A | **1,627** (1,538 in / 89 out) | **305** (249 in / 56 out) |
| **Parsing burden** | High — free-form text, no schema, must guess intent | Low — fixed JSON schema, easy to validate | Low — a fenced code block, but validating *correctness* requires running it |
| **Failure surface** | Misparsed intent | Malformed JSON, wrong tool name/args | Syntax errors, runtime exceptions, hallucinated APIs (Ch 46) |
| **Best fit** | Prototyping only; not used in production agents | A small, fixed, low-composition tool surface where auditability per call matters | Multi-step, stateful, or data-heavy tasks where composition saves round trips |

## Worked Example 1 — Free text (fragility)

Four equally plausible ways a model might express "I'm about to read a.txt":

```
- "I should start by reading the contents of a.txt so I know the first number."
- "Let's open a.txt and see what's inside."
- "First, can you get me a.txt?"
- "Read: a.txt"
```

A hand-written parser must anticipate every phrasing to reliably extract the
same action. There's no schema constraining the model's output, so composing
this into a 4-step task (3 reads, 1 write) multiplies the ambiguity rather than
resolving it — which is why free text isn't carried through the rest of this
comparison as a serious contender.

## Worked Example 2 — JSON tool calling (5 turns, 1,627 tokens)

Tool schema (both tools):

```json
{"name": "read_file", "description": "Read the entire contents of a text file in the workspace.",
 "parameters": {"type": "object", "properties": {"path": {"type": "string", "...": "..."}}, "required": ["path"]}}
{"name": "write_file", "description": "Write text content to a file in the workspace, overwriting it if it exists.",
 "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}
```

Per-turn breakdown (measured):

| Turn | Action | Input tokens | Output tokens |
|---|---|---|---|
| 1 | `read_file(path="a.txt")` | 249 | 17 |
| 2 | `read_file(path="b.txt")` | 277 | 17 |
| 3 | `read_file(path="c.txt")` | 305 | 17 |
| 4 | `write_file(path="total.txt", content="67")` | 333 | 23 |
| 5 | final answer (plain text) | 374 | 15 |
| | **Total** | **1,538** | **89** |

Input tokens climb every turn (249 → 277 → 305 → 333 → 374) because a stateless
tool-calling call resends the system prompt, the full tool schema, and the
growing history on every single turn.

## Worked Example 3 — Code action (2 turns, 305 tokens)

```python
total = sum(int(read_file(f).strip()) for f in ["a.txt", "b.txt", "c.txt"])
write_file("total.txt", str(total))
print(total)
```

| Turn | Action | Input tokens | Output tokens |
|---|---|---|---|
| 1 | the code block above | 99 | 41 |
| 2 | final answer (plain text) | 150 | 15 |
| | **Total** | **249** | **56** |

One action performs all three reads, the sum, and the write — no tool schema
needed at all, because the "interface" is two ordinary Python functions the
model already knows how to call.

## Headline numbers

For this identical 3-read/1-write task, with an identical final result:

- **Turns:** JSON tool calling used **2.5x** as many model turns as the code action (5 vs. 2).
- **Tokens:** JSON tool calling used **5.3x** as many total tokens as the code action (1,627 vs. 305).

## When JSON tool calling is still the right choice

This comparison is not an argument that code actions always win:

- **Small, fixed, low-composition tool surfaces.** If a task genuinely needs
  one or two isolated calls with no data flowing between them, JSON's fixed
  schema is easier to validate and audit per call than a code block is.
- **Auditability and approval gates.** A single structured call is trivial to
  inspect, log, and gate behind human approval before it runs (Chapter 25).
  A code action bundles several effects into one block, which is harder to
  gate at the level of an individual operation.
- **No code-execution environment available.** If there's no sandboxed
  interpreter to run code in, JSON tool calling may be the only option
  regardless of its token cost.
- **Untrusted or adversarial contexts.** Structured calls constrain the
  action space to exactly the tools you defined; code widens the attack
  surface (Chapter 62) in exchange for expressiveness.

The rest of this guide is built around code actions because most of the tasks
it targets are multi-step and data-heavy — exactly the regime where this
matrix shows code actions winning by the widest margin.
