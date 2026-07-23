# The Reason–Act–Observe Loop: Annotated Diagram and ReAct → CodeAct Lineage

*Chapter 3 deliverable: an annotated loop diagram with the ReAct→CodeAct lineage.*

## 1. The loop, generically

```
                 ┌─────────────────────────────────────────────┐
                 │                  context                     │
                 │  (task + accumulated Thought/Action/Obs...)  │
                 └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │  model (policy)        │
                              │  emits: Thought +      │
                              │  Action  — OR — Finish │
                              └───────────┬─────────────┘
                                          │
                     Finish? ──yes──►  done, return answer
                                          │ no
                                          ▼
                              ┌───────────────────────┐
                              │  environment executes  │
                              │  the Action             │
                              └───────────┬─────────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │  Observation produced   │
                              └───────────┬─────────────┘
                                          │
                        append Thought + Action + Observation
                        to context, loop back to "model"
                                          │
                                          └──────────────► (repeat)
```

This is the loop `run_react_loop` and `run_codeact_loop` in
[`code/react_vs_codeact.py`](code/react_vs_codeact.py) both actually execute —
the diagram isn't aspirational, it's what the code does, annotated. The two
functions differ only in what "Action" and "environment executes" mean, per
the two annotated variants below.

## 2. ReAct-shaped loop (one tool call per turn)

```
Thought: I need each file's value before I can compare them. Start with a.txt.
Action:  read_file('a.txt')          ◄── one call, from a small fixed tool set,
Observation: 42                           expressed as text and parsed by the harness

Thought: a.txt is 42. Now check b.txt.
Action:  read_file('b.txt')
Observation: 17

Thought: b.txt is 17, smaller than 42 so far. Now check c.txt.
Action:  read_file('c.txt')
Observation: 8

Thought: c.txt is 8. The largest value seen is 42, from a.txt. 42 + 10 = 52.
Finish:  a.txt has the largest number (42); 42 + 10 = 52.
```

**Annotation:** 3 actions, 4 thoughts, 11 trace entries. Every comparison
("is 42 > 17?", "is 42 still the max after seeing 8?") happens as reasoning
*in the Thought text*, in natural language, because the Action itself can only
be one `read_file` call — it has no way to also carry out a comparison. The
loop has to come back to the model after every single file read for the model
to reason about what it just saw and decide the next step.

## 3. CodeAct-shaped loop (one composable action)

```
Thought: I'll read all three files, compare them, and compute the answer in one action.
Action (code):
    values = {f: int(read_file(f)) for f in ["a.txt", "b.txt", "c.txt"]}
    largest_file = max(values, key=values.get)
    result = values[largest_file] + 10
    print(f"{largest_file} has the largest number ({values[largest_file]}); "
          f"{values[largest_file]} + 10 = {result}")
Observation: a.txt has the largest number (42); 42 + 10 = 52
Finish:  a.txt has the largest number (42); 42 + 10 = 52
```

**Annotation:** 1 action, 1 thought, 4 trace entries — same interleaving
pattern (Thought → Action → Observation → Finish), same correct answer, but
the three reads *and* the max-comparison *and* the arithmetic all happen
inside one Action, because Python's own control flow (a dict comprehension,
`max(..., key=...)`) does the composing that ReAct's Thought text had to do
in prose across three separate turns.

**What did and didn't change, going from §2 to §3:** the loop shape (reason,
act, observe, repeat until Finish) is identical — this is still a
Reason-Act-Observe loop. What changed is the *action's shape*: from
"one call into a small fixed tool vocabulary, parsed from text" to "one
arbitrary, composable program." The comparison logic didn't move to a smarter
model or a cleverer prompt; it moved from the Thought (text, reasoned by the
model one file at a time) into the Action (code, executed all at once by the
interpreter).

## 4. Why the rewrite is more than a turn-count optimization

Chapters 2 and much of the rest of §2/§3 above frame the ReAct→CodeAct
rewrite as a token/turn efficiency win. There's a second, structural reason,
demonstrated (not just claimed) in `code/react_vs_codeact.py`'s
`CORRECT_LONG_REACT_SCRIPT` / `FLAWED_LONG_REACT_SCRIPT` pair: a 6-file
version of the same task, where both scripts share **identical, individually
correct** Observations, but the flawed script's Thought at one step
misjudges a single comparison (`55 > 42` read as false). Every subsequent
Thought trusts that wrong "running max," and the trace finishes with a
confidently wrong answer — `a.txt`/`42`/`52` instead of the correct
`d.txt`/`55`/`65` — despite `run_react_loop` never receiving a single
incorrect Observation. **Nothing in the ReAct loop verifies a Thought's
claim against the data it's reasoning about** — only actions produce
verified, real Observations; the *interpretation* of those observations
lives in unchecked free text.

The equivalent CodeAct action for the same 6-file task delegates the
comparison to `max(values, key=values.get)` and gets it right — not because
this specific code is bug-free (Chapter 4's dynamic-revision demo shows code
actions have their own real failure modes), but because there is no
intermediate "running max" claim floating in generated text for a later step
to misremember. This specific failure class — correct facts, silently wrong
running interpretation of them — is structurally unavailable to a single
code action the way it's available to a multi-step Thought chain.

This isn't speculation dressed up as a demo: PAL's own abstract (verified
quote, checked against the arXiv page) names precisely this failure mode —
**"LLMs often make logical and arithmetic mistakes in the solution part,
even when the problem is decomposed correctly"** — and reports a concrete,
verified result from delegating computation to a real interpreter instead:
**"PAL using Codex achieves state-of-the-art few-shot accuracy on the GSM8K
benchmark of math word problems, surpassing PaLM-540B which uses
chain-of-thought by absolute 15% top-1."** The `FLAWED_LONG_REACT_SCRIPT`
demo is a small, hand-constructed instance of exactly the failure mode PAL's
published, benchmarked result is about.

## 5. Lineage: how the field got from §2 to §3

```
2022-10-06  ReAct           Yao et al., arXiv:2210.03629
            │                Interleaved Thought/Action/Observation loop;
            │                action = one call into a small fixed tool set,
            │                expressed and parsed as text.
            │
            ▼
2022-11-18  PAL              Gao et al., arXiv:2211.10435
            │                Verified abstract quote: "LLMs often make logical
            │                and arithmetic mistakes in the solution part, even
            │                when the problem is decomposed correctly." Not
            │                iterated like ReAct — one generate-then-execute
            │                step — but establishes the exact mechanism §4
            │                demonstrates: offload computation to a real Python
            │                interpreter instead of doing arithmetic/logic in
            │                the model's own text. Verified result: "PAL using
            │                Codex ... surpassing PaLM-540B which uses
            │                chain-of-thought by absolute 15% top-1" on GSM8K.
            │
            ▼
2023-02-09  Toolformer       Schick et al., arXiv:2302.04761
            │                Different axis: verified abstract quote — the
            │                model learns, self-supervised, "which APIs to
            │                call, when to call them, what arguments to pass,
            │                and how to best incorporate the results into
            │                future token prediction," from "a handful of
            │                demonstrations for each API." Trains the
            │                *decision* to call a tool into the model itself
            │                rather than eliciting it by prompting — orthogonal
            │                to the text-vs-code action-shape question, but
            │                part of the same tool-use lineage.
            │
            ▼
2024-02-01  CodeAct          Wang et al., arXiv:2402.01030
                             The synthesis: keep ReAct's iterated
                             Reason-Act-Observe loop, but make the action
                             *itself* an arbitrary, composable Python program —
                             PAL's "offload computation to the interpreter" idea,
                             now embedded inside every turn of the loop instead
                             of used once. This is exactly the §2 → §3 rewrite
                             above, and it structurally closes off the failure
                             class §4 demonstrates.
```

All four titles, author lists, and submission dates — and the direct PAL and
Toolformer abstract quotes above — were checked against each paper's arXiv
abstract page in this session, not recalled from memory.

## 6. The one-sentence version

**ReAct** gave agents an iterated loop; **PAL** showed code beats text for
computation; **Toolformer** showed the tool-use decision can be learned into
the model; **CodeAct** combined the first two — code as the action *inside*
the iterated loop — which is why every chapter after this one in the guide
treats "the agent loop" and "the code-executing agent loop" as close to the
same subject.
