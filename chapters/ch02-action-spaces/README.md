# Chapter 2 — Action Spaces: Text, JSON, and Code

## 1. Concept

An **action space** is the vocabulary of things an agent's model is allowed to
emit as an action. Chapter 1 established that an agent is a loop coupling a
model to an environment through actions and observations; this chapter asks
*what shape those actions take*. Three dominant shapes exist: free text, JSON
tool calls, and executable code. The choice is not cosmetic — it determines how
much a single action can accomplish, how many round trips a task needs, and how
much of the model's token budget goes to actually doing work versus re-stating
context.

## 2. Why This Matters for Code-Executing Agents

This guide is about the third action space specifically. Before arguing *why*
code is a good choice (Chapter 4), you need to see what it's being compared
against and on what axes. This chapter builds the comparison; Chapter 4 builds
the argument on top of it. Skipping straight to "code is better" without seeing
the mechanics of *why* — composability, round-trip cost, resent context — would
make Chapter 4 an assertion instead of a conclusion.

## 3. Mental Model

Think of each action space as answering two questions differently:

1. **How much can one action do?** Free text: whatever a human or fragile
   parser can extract from prose. JSON tool calls: exactly one predefined
   operation, with typed arguments. Code: anything the language's control flow
   and available functions can express — loops, conditionals, composition of
   many operations.
2. **Who decides what happens between operations?** Free text and JSON tool
   calls both hand control back to the harness after every single operation —
   the harness decides whether to call the model again and with what. Code
   keeps control *inside* the action until the code block ends — a `for` loop
   over three files doesn't need to ask the harness's permission between
   iterations.

Question 2 is the mechanical reason code actions need fewer round trips: they
push composition inside the action instead of outside it.

## 4. Architecture (place in the loop / context)

The action space is the format of one edge in Chapter 1's loop: the
model-emits-an-action edge. It directly shapes the harness built in Part IV
(Chapter 19, "Parsing and Extracting Actions," is entirely about turning one of
these three shapes into something executable) and the token economics of Part
VI (Chapter 36). Chapter 28 ("Tools as Code: Definition and Exposure") picks
this back up once tools exist to be called from inside a code action.

## 5. Detailed Explanation

**Free-text actions.** The earliest prompting style: the model describes its
intended action in prose, and a parser (regex, keyword matching, or another
model call) tries to extract a structured intent from it. `code/action_spaces.py`
demonstrates the fragility directly — four phrasings of "I'm about to read
a.txt" (`FREE_TEXT_AMBIGUOUS_VARIANTS`), all valid English, all requiring a
parser to somehow converge on the same extracted action. Free text was largely
abandoned for real tool use once structured calling became available, precisely
because this fragility doesn't improve with better prompting — it's inherent to
having no schema.

**Structured tool calling (JSON / function calling).** The model is given a
fixed set of tool schemas (name, description, typed parameters — see
`TOOL_SCHEMAS` in `code/action_spaces.py`) and constrained to emit one
call — `{"tool": name, "arguments": {...}}` — per turn. This fixes free text's
ambiguity: there's exactly one way to call `read_file`. The cost is control:
the model cannot decide to call three tools in sequence within one action; the
harness must call the model again after every single tool result, and that
next call resends the system prompt, the schema, and the growing history.

**Code actions.** The model emits a block of executable code instead of a
single call. Because the code has real control flow, one action can perform
many operations — the worked example's code action does 3 reads, a sum, and a
write in one block (`build_code_action_trace` in `code/action_spaces.py`).
Multiple operations that would each cost a JSON round trip cost nothing extra
inside a single code action, because the language's own semantics (not the
harness) sequence them.

**Expressiveness comparison.** The comparison matrix
(`comparison_matrix.md`) lays out control flow, data flow, composition,
parsing burden, and failure surface side by side. The short version: JSON
tool calling trades expressiveness for auditability per call; code trades
per-call auditability for expressiveness and fewer round trips.

**Cost and step-count implications.** Measured directly on the 3-file-sum
task (`render_comparison()` in `code/action_spaces.py`, real `tiktoken`
counts): JSON tool calling took **5 model turns and 1,627 tokens**; the single
code action took **2 model turns and 305 tokens** — 2.5x the turns and 5.3x
the tokens for an identical result. Both effects compound as task length
grows: more steps means more JSON round trips (linear growth) and a longer
resent history each time (quadratic-ish growth in cumulative input tokens),
while a code action's turn count stays flat as long as the steps still fit in
one block.

## 6. Minimal Implementation

`code/action_spaces.py` builds three real traces for the same task (sum three
files, write the result) and counts real tokens for two of them:

- `FREE_TEXT_AMBIGUOUS_VARIANTS` — four phrasings illustrating parse ambiguity.
- `build_json_tool_call_trace()` — 5 `Turn`s (3 reads, 1 write, 1 final
  answer), each `Turn.input_text` reconstructing the full context that model
  call would actually need (system prompt + tool schemas + history so far).
- `build_code_action_trace()` — 2 `Turn`s (1 code action, 1 final answer).
- `count_tokens()` — real token counts via `tiktoken`'s `cl100k_base`
  encoding (a proxy tokenizer, not tied to any specific model).
- `render_comparison()` — the turns/tokens table.

Run it directly:

```bash
source .venv/bin/activate
python chapters/ch02-action-spaces/code/action_spaces.py
```

```
Action space         |  Turns |  Input tok |  Output tok |  Total tok
---------------------+--------+------------+-------------+-----------
JSON tool calls      |      5 |       1538 |          89 |       1627
Single code action   |      2 |        249 |          56 |        305
```

## 7. Hands-on Lab

`notebooks/ch02_action_spaces.ipynb` (executed, committed with outputs) walks
through the chapter's hands-on direction end to end: prints the free-text
ambiguity examples, prints the JSON tool schema and code-mode system prompt
side by side, builds both traces, prints the per-turn token breakdown, renders
the comparison matrix, and computes the turn/token ratios (2.5x / 5.3x).

To extend it yourself: add a fourth file (`d.txt`) to `FAKE_WORKSPACE` and the
task, rebuild both traces, and check whether the token-ratio gap widens or
narrows as the task grows by one step — it should widen, per the "cost and
step-count implications" argument above.

## 8. Failure Lab

Reproduce the free-text failure mode directly: take
`FREE_TEXT_AMBIGUOUS_VARIANTS` and write a keyword-matching parser (e.g.
`if "read" in text and ".txt" in text: extract_filename(text)`) that tries to
recover the filename from all four. It will work on some, fail or misfire on
others (e.g. "First, can you get me a.txt?" has no natural-language "read"
keyword at all), and every fix you add to catch one phrasing risks
misclassifying a different one. This is not a bug in your parser — it's the
structural failure mode of an action space with no schema, and it's *why*
structured tool calling and code actions both exist: they replace guessing at
intent with a format a parser can handle deterministically (Chapter 19).

## 9. Instrumentation (what to log / trace / measure)

For any action space, per turn: input tokens, output tokens, and whether the
turn was itself an action or a final answer. Summed across a run, these three
numbers are exactly what `summarize()` computes in `code/action_spaces.py` and
are the seed of Chapter 36's per-component token accounting and Chapter 27's
budget tracking. The turn count alone is a useful cheap proxy for latency,
since each turn is a full model round trip.

## 10. Design Considerations

- **The gap grows with task length, not just task count.** A 3-step task
  showed a 5.3x token gap; a 10-step task would show a much larger one,
  because JSON mode's cumulative input tokens grow with the *square* of step
  count (each turn resends a longer history) while a single code action's
  turn count can stay flat. Estimate this before choosing an action space for
  a genuinely long-horizon task.
- **Auditability is a real cost of code actions, not just a footnote.** A
  JSON tool call is trivially loggable and gateable per operation
  (Chapter 25); a code action bundles several effects into one block that
  either all run or (on error) partially run. Production systems that need
  per-operation approval gates may deliberately pay the token/turn cost of
  JSON calling for that property.
- **Free text should not appear in a production comparison at all** — it's
  included here only to show why it was abandoned, not as a live option.

## 11. Common Mistakes

- **Assuming code actions are strictly better because they're cheaper here.**
  The comparison matrix's "Best fit" row exists because token cost is one
  axis, not the only one — auditability, environment availability, and trust
  boundaries matter too (see the "When JSON tool calling is still the right
  choice" section of `comparison_matrix.md`).
- **Measuring only marginal tokens, not cumulative.** The real cost of JSON
  mode isn't turn 5's tokens in isolation — it's that turn 5 has to resend
  everything turns 1–4 already established. Always sum across the whole trace.
- **Treating free text as a lightweight middle ground.** It isn't a
  compromise between JSON and code; it's strictly worse than both on
  reliability, with none of code's expressiveness benefit.

## 12. Comparisons / Alternatives

See `comparison_matrix.md` for the full matrix (control flow, data flow,
composition, turns, tokens, parsing burden, failure surface, best fit) across
all three action spaces, with worked examples and measured numbers for each.

## 13. Review Questions

1. Why does a JSON tool-calling turn's input tokens grow every turn, even
   though the *new* information each turn (one tool result) is small and
   roughly constant?
2. In the code action's system prompt, no tool schema is defined at all —
   why not, and what replaces it?
3. Rank the three action spaces by "who decides what happens between
   operations" (harness vs. the action itself), and explain what that ranking
   predicts about round-trip count.
4. Give a concrete scenario (not from this chapter) where JSON tool calling's
   token cost is worth paying despite code actions being cheaper.
5. If you added a 4th file to the worked task, would you expect the turn-count
   gap between JSON and code mode to grow by one turn, or by more than one?
   Why?

## 14. Chapter Summary

Three action spaces exist: free text (fragile, no schema, effectively
abandoned for real tool use), JSON tool calls (one predefined operation per
model turn, schema-constrained, easy to audit per call), and code actions
(arbitrary control flow inside one action, composing many operations without
extra round trips). Measured on an identical 3-read/1-write task, JSON tool
calling needed 5 turns and 1,627 tokens where a single code action needed 2
turns and 305 tokens — a 2.5x turn gap and 5.3x token gap that widens as tasks
grow longer, because code pushes composition inside the action while JSON
pushes it outside, back to the harness, at the cost of a round trip and a
resent history each time.

## 15. Chapter Deliverable

[`comparison_matrix.md`](comparison_matrix.md) — a comparison matrix of the
three action spaces with worked examples and measured turn/token counts for
the JSON-tool-calling and code-action traces.

## 16. Further Reading

- Wang et al., *Executable Code Actions Elicit Better LLM Agents* (CodeAct,
  2024) — the paper Chapter 4 covers directly; its central empirical claim
  (fewer actions needed, higher success rate, versus JSON-style tool calling)
  is exactly the turn/token effect this chapter measures on a toy task.
- Gao et al., *PAL: Program-Aided Language Models* (2022) — an early
  demonstration that offloading composition/computation to executable code,
  rather than doing it in the model's own text, improves reliability; a
  precursor to the code-action argument.
- OpenAI and Anthropic's function-calling / tool-use documentation — worth
  reading directly for how a real JSON tool-calling schema and response
  format are specified in production APIs, to compare against the simplified
  `TOOL_SCHEMAS` used in this chapter's worked example.
