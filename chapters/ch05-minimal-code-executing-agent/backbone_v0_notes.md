# Backbone Agent v0 — Notes

*Chapter 5 deliverable: the backbone agent v0 — a minimal, working code-executing loop.*

The deliverable itself is the code: `src/backbone_agent/` (`loop.py`,
`model.py`, `parsing.py`, `executor.py`, `__main__.py`). This document records
what it does, how it was verified, and the first real failure it hit.

## What it is

A ~40-line loop (excluding docstrings/constants — see `loop.py`):
generate → extract code → execute → observe → repeat, until the model
responds with plain text instead of a code block.

```bash
source .venv/bin/activate
export GROQ_API_KEY=...        # or: set -a; source .env; set +a
python -m backbone_agent "What is 17 * 23? Compute it, don't just guess."
```

```
=== FINAL ANSWER ===
The result of 17 * 23 is indeed 391.
```

## Verification: three hands-on tasks, real model, ground-truth checked

Run via `chapters/ch05-minimal-code-executing-agent/code/three_tasks_demo.py`
against `groq/llama-3.3-70b-versatile`. Each task's success is checked against
a value this script computed independently — not the agent's own claim.

| Task | Expected (computed independently) | Agent's answer contained it? |
|---|---|---|
| Math: sum of first 20 primes | `639` | Yes |
| File transform: average a real CSV column, write a real file | `79.6` | Yes — `average.txt` was written with `79.6` |
| Data task: mean/median/pop. stdev of `[12,45,7,22,9,34,18]` | `21.0`, `18.0`, `12.96` | Yes, all three |

**3/3 tasks solved correctly**, full transcripts in
`notebooks/ch05_minimal_agent.ipynb`.

## The first thing that went wrong (real, not staged)

On both the file-transform task and the data-stats task, the model's *first*
code action reached for a library that isn't installed in this minimal
environment — `pandas` for the CSV task, `numpy` for the stats task — and hit
a real `ModuleNotFoundError`:

```
Traceback (most recent call last):
  File ".../executor.py", line 21, in execute_code
    exec(code, namespace)
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'pandas'
```

This wasn't staged or anticipated in the system prompt — it's what actually
happened running this exact setup. The loop's design meant this was
recoverable for free: the executor catches the exception and returns the
real traceback as the Observation; the model's *second* code action, in both
cases, switched to the stdlib `csv`/`statistics` modules and succeeded. This
is the chapter's answer to "the first thing that will go wrong": in a minimal
environment with no guaranteed library set, an agent trained on code that
commonly uses `pandas`/`numpy` will reach for them by default and needs the
traceback feedback loop to recover — errors-as-observations is load-bearing
from the very first real run, not optional polish.

## Beyond one run: reliability, a prompt ablation, and a real boundary

A single successful run doesn't establish that a task is reliably solvable.
`code/reliability_and_ablation.py` runs three deeper, real-live-model
measurements (all against `groq/llama-3.3-70b-versatile`; full output in
`notebooks/ch05_minimal_agent.ipynb`):

**Multi-trial reliability (3 trials each, our own small pass@3-style
measurement):**

```
math task:  3/3 (100%), step counts: [2, 2, 2]
stats task: 3/3 (100%), step counts: [3, 3, 3]
```

Both tasks solved correctly every trial, with identical step counts each
time — these particular tasks are simple enough that behavior is highly
consistent. That consistency is a finding, not an assumption: running the
trials is what established it, rather than trusting the single run above.

**Prompt ablation — does steering the model toward the standard library
reduce the `ModuleNotFoundError` rate?** One sentence added to
`SYSTEM_PROMPT` ("Prefer Python's standard library ... assume third-party
packages are NOT installed unless you have already confirmed otherwise"),
A/B'd against the file-transform task, 3 live trials each:

```
default_prompt:         3/3 succeeded (100%), ModuleNotFoundError rate: 100%, avg steps: 3.0
stdlib_steered_prompt:  3/3 succeeded (100%), ModuleNotFoundError rate:   0%, avg steps: 2.0
```

**The one-sentence prompt change eliminated the `ModuleNotFoundError`
entirely across all 3 trials** — both prompts reach the correct final answer
100% of the time, but the default prompt wastes a full turn on a doomed
`pandas` import in every single trial, while the steered prompt reaches the
minimum possible 2 steps every time. This is a real, measured instance of
what Chapter 44 (prompting for reliable code) generalizes — not a preview
promise, a result already in hand.

**A real step-budget boundary.** `run_agent(task, max_steps=1)` on the
file-transform task raises `StepBudgetExceeded` for real
(`"no final answer within 1 steps"`) — confirmed rather than assumed, since
even a perfectly-behaved run needs at least 2 turns (one code action, one
separate final-answer turn) to satisfy `SYSTEM_PROMPT`'s "no code block =
final answer" contract.

**A real infrastructure finding along the way:** running these trials
back-to-back hit Groq's actual free-tier rate limit (12,000 tokens/minute)
directly — a genuine `RateLimitError`, not a hypothetical concern. The
experiment script now paces requests and retries with backoff
(`_with_backoff` in `reliability_and_ablation.py`) as a local accommodation,
explicitly flagged there as distinct from the real retry-policy design
Chapter 22 covers.

## What v0 deliberately does not do yet

Per the guide's chapter-by-chapter progression, all still to come:

- **Stateful execution** (Chapter 7) — each `execute_code` call gets a fresh
  `{}` namespace; nothing persists between turns within a run.
- **Rich output capture** (Chapter 8) — only stdout is captured; no
  return-value/last-expression capture, no rich media.
- **Pluggable execution backends** (Chapter 9) — `exec()` in-process only.
- **Robust action parsing** (Chapter 19) — one regex, first code block only;
  multiple/malformed blocks aren't specially handled.
- **Real termination controls** (Chapter 21) — `max_steps` is a hard cap with
  a raised exception, no budget-aware behavior.
- **Any runtime containment** — `exec()` runs with full process privileges;
  this is explicitly out of scope for this guide (see the sandbox-guide
  handoff in `CLAUDE.md` and Chapter 62).
