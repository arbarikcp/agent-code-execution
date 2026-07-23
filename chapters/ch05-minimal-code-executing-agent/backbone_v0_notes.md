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
recoverable for free: `execute_code` catches the exception and returns the
real traceback as the Observation; the model's *second* code action, in both
cases, switched to the stdlib `csv`/`statistics` modules and succeeded. This
is the chapter's answer to "the first thing that will go wrong": in a minimal
environment with no guaranteed library set, an agent trained on code that
commonly uses `pandas`/`numpy` will reach for them by default and needs the
traceback feedback loop to recover — which is exactly why "errors as
observations" (Chapter 22) isn't optional polish, it's load-bearing from the
very first real run.

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
