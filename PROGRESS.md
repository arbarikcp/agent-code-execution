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
| 06 | Interpreters, REPLs, and Kernels | done | `executor.py` gained the `Executor` interface + `SubprocessExecutor` + `KernelExecutor` (real IPython kernel via jupyter_client), alongside Ch5's `InProcessExecutor`. `loop.py::run_agent` takes a pluggable `executor` param, defaults unchanged (confirmed via smoke test). Measured: subprocess ~15-20ms/call but fails cross-call state; kernel ~730ms startup then ~4-8ms/call and correctly persists state. |
| 07–66 | ... | todo | Not yet reached. |

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
- `executor.py` — **(Chapter 6)** now an `Executor` ABC
  (`run(code) -> ExecutionResult`, optional `close()`) with three
  implementations:
  - `InProcessExecutor` — Ch5's original behavior unchanged (fresh `{}`
    namespace per call, `exec()`, stdout captured, exceptions returned as
    `traceback.format_exc()` via `ExecutionResult.error`).
  - `SubprocessExecutor` — one-shot: `python -c <code>` fresh every call, no
    state persists between calls (by construction — it's a new process).
  - `KernelExecutor` — persistent: one real IPython kernel (started via
    `jupyter_client.KernelManager`), reused across calls over the real
    `execute_request`/`iopub` protocol; state persists naturally.
  - `observation_from_result()` — shared formatting so `loop.py`'s
    observation text is identical regardless of backend.
- `loop.py::run_agent(task, model=None, max_steps=10, return_trace=False,
  executor=None)` — `executor` now pluggable, defaults to
  `InProcessExecutor()` (v0's exact prior behavior; confirmed via the
  regression smoke test after the refactor). Loop control flow unchanged.
- `__main__.py` — `python -m backbone_agent "<task>"` CLI entry point, works.
- Installed editable via `pyproject.toml` (`pip install -e .`), so `import
  backbone_agent` works from any chapter's code from here on.

**Explicitly NOT yet implemented** (targets for the chapters named):
stateful execution as a first-class feature beyond what `KernelExecutor`
happens to provide (Ch7 — deciding when/how the loop *uses* that
persistence, reset/checkpoint semantics), rich output capture beyond
stdout/traceback — no last-expression/return-value capture, no rich media
(Ch8), a third (remote/sandboxed) backend and a formal trade-off table (Ch9),
robust multi-block/malformed action parsing (Ch19), real budget/termination
controls beyond a hard step cap (Ch21), any runtime containment (out of this
guide's scope — sandbox guide). Note: `loop.py` still creates a fresh
`InProcessExecutor()` per `run_agent()` call by default, and even when a
`KernelExecutor` is passed in, the loop doesn't yet do anything special to
exploit its persistence (no chapter has told it to) — that's Chapter 7's job.

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

Next chapter to implement: **Chapter 7 — Stateful vs Stateless Execution**
(Part II continues). Read its entry in `agent_code_execution_study_guide.md`
before starting. Chapter 6 already built a real persistent-kernel executor
(`KernelExecutor`) but `run_agent` doesn't yet *use* its persistence
deliberately — it just creates a fresh `InProcessExecutor()` by default and
treats whatever `Executor` it's given uniformly. Chapter 7's hands-on
direction ("give the backbone agent a persistent kernel; have it load a
dataset once and reference it across several later actions") is likely where
`run_agent` starts defaulting to (or explicitly offering) `KernelExecutor`,
plus a reset/checkpoint control per the chapter's "Reset and checkpoint"
subtopic. Run `tests/test_backbone_smoke.py` after any change to confirm the
backbone still works — note the smoke test currently exercises only the
default `InProcessExecutor` path, so consider whether it needs a
kernel-backed counterpart once statefulness becomes a first-class feature.
