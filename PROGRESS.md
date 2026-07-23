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

Next chapter to implement: **Chapter 5 — A Minimal Code-Executing Agent**
(Part I finale, Part II starts after). This is the first chapter that builds
`src/backbone_agent/` and needs a real model call. Before starting: add
`litellm` to `requirements.txt` (pinned), confirm which env var(s) it needs
for whatever default model is chosen, and read Chapter 5's entry in
`agent_code_execution_study_guide.md` (target: end-to-end loop under ~100
lines — generate → extract code → execute → observe → repeat — with a system
prompt, a code-block parser, `exec`/subprocess execution, and a stop signal).
Chapters 1–4 built (but did not wire into a real agent): a 4-part system
comparison (Ch1), an action-space token/turn comparison (Ch2), a real
ReAct/CodeAct loop over a scripted model (Ch3), and a step-budget benchmark
plus tool-reuse/dynamic-revision demos (Ch4) — all real, runnable, but none
of them call a live model yet. Chapter 5 is where a live model call enters
the guide for the first time.
