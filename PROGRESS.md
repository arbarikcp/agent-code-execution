# Progress

Source of truth for what's done and what's next. Read this before starting any
chapter (see `CLAUDE.md` → Per-Chapter Workflow).

## Chapter status

| Chapter | Title | Status | Notes |
|---|---|---|---|
| 01 | What Is an Agent? | done | No backbone code yet — deliverable is a data-driven comparison (`code/systems.py`) + one-page reference. |
| 02 | Action Spaces: Text, JSON, and Code | done | Still no backbone — deliverable is a measured comparison matrix (`code/action_spaces.py`, real `tiktoken` counts) of free text / JSON tool calls / code actions on one worked task. |
| 03 | The Reason–Act–Observe Loop | todo | |
| 04 | Why Code Execution | todo | |
| 05 | A Minimal Code-Executing Agent | todo | **Backbone agent v0 starts here.** Introduces `src/backbone_agent/` and the litellm-based model interface (see Backbone State below). |
| 06–66 | ... | todo | Not yet reached. |

## Backbone state

Not started. Chapter 5 creates `src/backbone_agent/` as a ~40-line
generate → extract → execute → observe → repeat loop.

**Decided for when Chapter 5 starts** (from human review of Chapter 1):
- Model calls go through **litellm** as the thin provider interface, so the
  backbone can switch models/providers via config rather than being hard-wired
  to one SDK. `litellm` gets added to `requirements.txt` at that point, along
  with whatever env var(s) it needs for the chosen default model.
- Full environment scaffolding (venv is already up; `src/backbone_agent/`
  package skeleton) is deferred to Chapter 5 — Chapters 1–4 don't need a
  running agent.

## Environment state

- `.venv/` created (Python 3.13.5), `requirements.txt` pinned with the minimum
  needed to execute notebooks through Chapter 4: `jupyter`, `nbclient`,
  `nbformat`, `ipykernel`, plus `tiktoken==0.13.0` (added in Chapter 2, used
  only as an approximate/reproducible tokenizer for action-space token-cost
  comparisons — not tied to whatever model the backbone ends up calling).
- No model-provider dependency yet — added in Chapter 5.

## For the next session

Next chapter to implement: **Chapter 3 — The Reason–Act–Observe Loop**
(Part I). Read its entry in `agent_code_execution_study_guide.md` before
starting; it does not depend on the (not-yet-built) backbone agent. Chapter 2's
`code/action_spaces.py` traces (JSON tool calling vs. a single code action) are
a useful reference point when Chapter 3 asks you to hand-write a ReAct trace
and rewrite it as a CodeAct trace — the JSON trace in `code/action_spaces.py`
is already close to a ReAct-style thought/action/observation shape.
