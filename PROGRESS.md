# Progress

Source of truth for what's done and what's next. Read this before starting any
chapter (see `CLAUDE.md` → Per-Chapter Workflow).

## Chapter status

| Chapter | Title | Status | Notes |
|---|---|---|---|
| 01 | What Is an Agent? | done | No backbone code yet — deliverable is a data-driven comparison (`code/systems.py`) + one-page reference. |
| 02 | Action Spaces: Text, JSON, and Code | done | Still no backbone — deliverable is a measured comparison matrix (`code/action_spaces.py`, real `tiktoken` counts) of free text / JSON tool calls / code actions on one worked task. |
| 03 | The Reason–Act–Observe Loop | done | Still no backbone — `code/react_vs_codeact.py` runs a real ReAct loop and a real CodeAct loop (scripted model, real execution/observations) over the same task; deliverable is an annotated loop diagram + verified ReAct→PAL→Toolformer→CodeAct lineage (dates checked against arXiv abstract pages). |
| 04 | Why Code Execution | done | Last pre-backbone chapter. `code/why_code.py` runs a real step-budget benchmark (100% vs. 57% success, own toy task), a tool-reuse demo, and a real-traceback-drives-real-fix demo. Cites CodeAct's verified "up to 20% higher success rate" (API-Bank, 17 LLMs) as an external claim, kept explicitly separate from the chapter's own smaller benchmark. |
| 05 | A Minimal Code-Executing Agent | done | **Backbone agent v0 built.** `src/backbone_agent/` — generate→extract→execute→observe→repeat, ~40 lines of loop logic, real live model calls via litellm/Groq. Verified 3/3 on hands-on tasks (math, file transform, data stats) against independently computed ground truths. See Backbone State below. |
| 06–66 | ... | todo | Not yet reached. |

## Backbone state

**`src/backbone_agent/` — v0, built in Chapter 5.**

- `loop.py::run_agent(task, model=None, max_steps=10, return_trace=False)` —
  the loop: call model → `extract_code` → if code, `execute_code` and append
  the real result as the next Observation → repeat; if no code block, that
  reply is the final answer, stop. Hard `StepBudgetExceeded` at `max_steps`.
- `model.py::call_model` — thin litellm wrapper. `DEFAULT_MODEL =
  "groq/llama-3.3-70b-versatile"`, overridable via `BACKBONE_MODEL` env var.
  litellm resolves the provider API key from the environment automatically
  (`GROQ_API_KEY` for a `"groq/..."` model).
- `parsing.py::extract_code` — one regex, first fenced code block; `None`
  means "no action, this is the final answer."
- `executor.py::execute_code` — in-process `exec()`, fresh `{}` namespace
  every call (stateless — Chapter 7 changes this), stdout captured via
  `contextlib.redirect_stdout`, exceptions caught and returned as
  `traceback.format_exc()` (not raised) so errors become Observations.
- `__main__.py` — `python -m backbone_agent "<task>"` CLI entry point, works.
- Installed editable via `pyproject.toml` (`pip install -e .`), so `import
  backbone_agent` works from any chapter's code from here on.

**Explicitly NOT yet implemented** (targets for the chapters named):
stateful execution (Ch7), rich output capture beyond stdout/traceback (Ch8),
pluggable execution backends (Ch9), robust multi-block/malformed action
parsing (Ch19), real budget/termination controls beyond a hard step cap
(Ch21), any runtime containment (out of this guide's scope — sandbox guide).

**Regression check:** `tests/test_backbone_smoke.py` — one live call
(`12 * 12` → asserts `"144"` in the answer). Run after any change to
`src/backbone_agent/`:

```bash
source .venv/bin/activate && set -a && source .env && set +a
python tests/test_backbone_smoke.py
```

**The first real failure** (documented in Chapter 5's
`backbone_v0_notes.md`): on 2 of 3 hands-on tasks, the model's first code
action imported `pandas` or `numpy` (neither installed), hit a real
`ModuleNotFoundError`, and self-corrected to stdlib on the next turn using
only that traceback. Not staged — this is what actually happened running
this setup, and it's why the executor returns tracebacks as Observations
instead of raising.

## Environment state

- `.venv/` created (Python 3.13.5), `requirements.txt` pinned:
  `jupyter`, `nbclient`, `nbformat`, `ipykernel` (notebook execution),
  `tiktoken==0.13.0` (Ch2, approximate tokenizer for action-space
  comparisons only), `litellm==1.93.0` (Ch5, model-provider interface),
  `-e .` (editable install of `src/backbone_agent`, via `pyproject.toml`).
- **Secrets:** a real Groq API key is stored in the user's `keys.txt` (empty
  placeholder, gitignored) and loaded into `.env` (gitignored, `chmod 600`)
  as `GROQ_API_KEY`. `.env.example` at the repo root documents the expected
  shape with no real value. Never commit `.env` or `keys.txt`.
- To make a live model call in any shell: `set -a && source .env && set +a`
  before running Python — env vars do **not** persist across separate shell
  invocations in this environment, so this must be re-done per command/session
  unless the shell profile is changed to source it automatically.

## For the next session

Next chapter to implement: **Chapter 6 — Interpreters, REPLs, and Kernels**
(Part II: The Execution Substrate). Read its entry in
`agent_code_execution_study_guide.md` before starting. Its hands-on direction
("run the same sequence of actions against (a) a fresh subprocess each time
and (b) a persistent IPython kernel") extends `src/backbone_agent/executor.py`
— v0's `exec()`-in-process backend is exactly the "one-shot execution"
baseline this chapter needs to compare against a subprocess backend and a
persistent kernel backend. Chapter deliverable is "an execution-backend
interface with two implementations" — likely an `Executor` protocol/ABC in
`executor.py` with the current in-process `exec()` becoming one
implementation among several, wired into `loop.py` without changing
`run_agent`'s public behavior. Run `tests/test_backbone_smoke.py` after any
executor refactor to confirm the backbone still works.
