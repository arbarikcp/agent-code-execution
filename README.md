# agent-code-execution

*Code Execution as an Agent's Action Space* — a chapter-by-chapter study guide and
backbone agent implementation. See `agent_code_execution_study_guide.md` for the
full index and `CLAUDE.md` for how this repo is built (one chapter at a time).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # also editable-installs src/backbone_agent (see pyproject.toml)
```

From Chapter 5 onward, the backbone agent makes live model calls via
[litellm](https://docs.litellm.ai). Copy `.env.example` to `.env` and fill in
a real key:

```bash
cp .env.example .env
# edit .env: GROQ_API_KEY=...
```

`.env` and `keys.txt` are both gitignored — never commit real keys. Load the
key into your shell before running anything that calls the model:

```bash
set -a && source .env && set +a
python -m backbone_agent "What is 17 * 23? Compute it, don't just guess."
```

The default model is `groq/llama-3.3-70b-versatile`; override with
`BACKBONE_MODEL=<litellm model string>` to use a different provider — litellm
resolves the matching API key from the environment automatically (e.g.
`ANTHROPIC_API_KEY` for an `"anthropic/..."` model).

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
