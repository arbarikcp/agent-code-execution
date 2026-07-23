# agent-code-execution

*Code Execution as an Agent's Action Space* — a chapter-by-chapter study guide and
backbone agent implementation. See `agent_code_execution_study_guide.md` for the
full index and `CLAUDE.md` for how this repo is built (one chapter at a time).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This base environment is enough to run every chapter's notebook up through
Chapter 4. Chapter 5 onward introduces the backbone agent and a model-provider
dependency (litellm) — added to `requirements.txt` when that chapter lands.

## Running a chapter

Each chapter lives in `chapters/chNN-slug/`:

- `README.md` — the chapter text (Concept → ... → Chapter Deliverable → Further Reading).
- `code/` — runnable modules referenced by the chapter.
- `notebooks/` — one executed `.ipynb` per chapter; run top-to-bottom with the
  venv above active.

```bash
source .venv/bin/activate
jupyter nbconvert --to notebook --execute --inplace chapters/ch01-what-is-an-agent/notebooks/*.ipynb
```

## Progress

See `PROGRESS.md` for chapter status and the backbone agent's current state.
