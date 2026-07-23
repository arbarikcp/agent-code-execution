# Progress

Source of truth for what's done and what's next. Read this before starting any
chapter (see `CLAUDE.md` → Per-Chapter Workflow).

## Chapter status

| Chapter | Title | Status | Notes |
|---|---|---|---|
| 01 | What Is an Agent? | done (revised) | No backbone code yet. Autonomy is now DERIVED from 5 `LoopPredicates` booleans (`classify_autonomy()`), not hand-labeled — checked against a hand-reasoned answer key for 6 systems. Two boundary cases stress-test it: `AGENTIC_RAG` (predicates identical to `CODING_AGENT` despite the misleading "RAG" name) and `THERMOSTAT` (identical loop-shape predicates to `CODING_AGENT`, differs only on `policy_is_a_language_model` — proves a closed feedback loop alone isn't sufficient for "agent"). |
| 02 | Action Spaces: Text, JSON, and Code | done (revised) | Replaced the single k=3 snapshot with: a real free-text parser scoring 4/8 (50%, with a distinct WRONG-not-just-MISSED category); a k=1..30 scaling sweep proving JSON's marginal token cost per file rises monotonically (superlinear, not just "large"); a heterogeneous-task honesty check showing code's token advantage shrinks from 92.8x to 7.3x without uniformity (turn advantage survives at 3.5x). |
| 03 | The Reason–Act–Observe Loop | done (revised) | Constructed a real failure class: two 6-file ReAct scripts with identical, individually-correct Observations, differing at one Thought's arithmetic — the flawed one finishes confidently wrong. Grounded directly in PAL's verified abstract quote ("logical and arithmetic mistakes in the solution part, even when decomposed correctly") and its verified 15%-absolute GSM8K result. Lineage upgraded to direct quotes for all 4 papers. |
| 04 | Why Code Execution | done (revised) | Replaced the single-budget (8) snapshot with `sweep_budgets()` across 3-24: JSON's success rate climbs monotonically 14%→100%; code stays 100% at every budget down to 2. Added `demo_nondeterminism()` — identical source code, two real different outputs (measured, not just asserted). |
| 05 | A Minimal Code-Executing Agent | done (revised) | **Backbone agent v0.** `src/backbone_agent/` — generate→extract→execute→observe→repeat. Beyond the original 3/3 task verification: 3-trial reliability (100% both, identical step counts), a real prompt ablation (one sentence steering toward stdlib: 100%→0% `ModuleNotFoundError` rate, 3→2 steps), and a real `max_steps=1` boundary confirming `StepBudgetExceeded`. Hit and handled Groq's real 12k-TPM rate limit. See Backbone State below. |
| 06 | Interpreters, REPLs, and Kernels | done (revised) | `executor.py`: `Executor` interface + `SubprocessExecutor` + `KernelExecutor` (real IPython kernel), alongside `InProcessExecutor` — now all three measured together (in-process ~2ms, subprocess ~47ms, kernel ~758ms startup, only kernel passes the state-dependent step). Real amortization sweep (N=1..160) found the actual breakeven at **N≈60** — correcting an earlier unmeasured guess ("a handful of actions") that was wrong by over an order of magnitude. A genuine `while True: pass` against the kernel produces an uncaught `queue.Empty`, a real documented gap left unfixed on purpose. |
| 07–66 | ... | todo | Not yet reached. |

**Depth revision pass (2026-07-23):** the user reviewed chapters 1-6 and
flagged them as too shallow — too many "Chapter X will cover this"
deferrals in place of real depth on each chapter's own content, and
notebooks that demonstrated once rather than explored. All six were
revised in place (see the `chN revision:` commits) to add real measurements,
constructed failure cases, and boundary/honesty checks — including one
correction of a previously unmeasured, wrong claim (ch06's amortization
breakeven was guessed as "a handful of actions"; measurement found N≈60).
This standard — real experiments, minimal forward-referencing, notebooks
that explore multiple angles rather than demonstrate once — applies to
every chapter from here forward, not just as a one-time cleanup.

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
  executor=None, system_prompt=None)` — `executor` pluggable, defaults to
  `InProcessExecutor()`; `system_prompt` (added during the depth-revision
  pass, for Ch5's prompt ablation) defaults to the module-level
  `SYSTEM_PROMPT`. Both default to v0's exact prior behavior when omitted;
  confirmed via the regression smoke test after every change. Loop control
  flow itself unchanged since Chapter 5.
- `executor.py::KernelExecutor(startup_timeout_s=60.0, execute_timeout_s=30.0)`
  — `execute_timeout_s` added during the depth-revision pass so Ch6's real
  kernel-hang failure is reproducible in 2s instead of 30s. `run()` still
  raises `queue.Empty` uncaught on a timeout — a known, documented gap, not
  yet fixed (see Ch6's README Failure Lab).
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
