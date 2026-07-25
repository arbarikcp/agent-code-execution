"""The thin model-provider interface (CLAUDE.md: "handle the model/API layer
behind a thin interface so examples don't hard-depend on one provider").

Goes through litellm, so `BACKBONE_MODEL` can name any litellm-supported model
string (e.g. "groq/llama-3.3-70b-versatile", "anthropic/claude-...",
"openai/gpt-...") without changing any code here — litellm resolves the
matching provider API key from the environment itself (GROQ_API_KEY for a
"groq/..." model, ANTHROPIC_API_KEY for "anthropic/...", etc.). Nothing in
this module reads or stores a key directly.
"""

import os

DEFAULT_MODEL = "groq/llama-3.3-70b-versatile"


def call_model(messages: list[dict], model: str | None = None) -> str:
    """One model call: full message list in, assistant text out."""
    try:
        import litellm
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Live model calls require the project dependencies. "
            "Install them with `pip install -e .`."
        ) from error

    model = model or os.environ.get("BACKBONE_MODEL", DEFAULT_MODEL)
    response = litellm.completion(
        model=model,
        messages=messages,
        max_tokens=1024,
        temperature=0,  # deterministic-as-possible; see chapter README for caveats
    )
    return response.choices[0].message.content
