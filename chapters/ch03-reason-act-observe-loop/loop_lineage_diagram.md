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

## 4. Lineage: how the field got from §2 to §3

```
2022-10-06  ReAct           Yao et al., arXiv:2210.03629
            │                Interleaved Thought/Action/Observation loop;
            │                action = one call into a small fixed tool set,
            │                expressed and parsed as text.
            │
            ▼
2022-11-18  PAL              Gao et al., arXiv:2211.10435
            │                Not iterated like ReAct — one generate-then-execute
            │                step — but establishes the key idea §3 relies on:
            │                offload *computation* to a real Python interpreter
            │                instead of doing arithmetic/logic in the model's
            │                own text.
            │
            ▼
2023-02-09  Toolformer       Schick et al., arXiv:2302.04761
            │                Different axis: trains the *decision* of when/how
            │                to call a tool into the model itself (self-supervised
            │                fine-tuning) rather than eliciting it by prompting.
            │                Orthogonal to the text-vs-code action-shape question,
            │                included because it's part of the standard tool-use
            │                lineage this chapter's spec names.
            │
            ▼
2024-02-01  CodeAct          Wang et al., arXiv:2402.01030
                             The synthesis: keep ReAct's iterated
                             Reason-Act-Observe loop, but make the action
                             *itself* an arbitrary, composable Python program —
                             PAL's "offload computation to the interpreter" idea,
                             now embedded inside every turn of the loop instead
                             of used once. This is exactly the §2 → §3 rewrite
                             above.
```

All four titles, author lists, and submission dates were checked directly
against each paper's arXiv abstract page in this session, not recalled from
memory.

## 5. The one-sentence version

**ReAct** gave agents an iterated loop; **PAL** showed code beats text for
computation; **Toolformer** showed the tool-use decision can be learned into
the model; **CodeAct** combined the first two — code as the action *inside*
the iterated loop — which is why every chapter after this one in the guide
treats "the agent loop" and "the code-executing agent loop" as close to the
same subject.
