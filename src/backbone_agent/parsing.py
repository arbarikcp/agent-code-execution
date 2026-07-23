"""Extract the executable action from a model response.

v0's convention (stated in `loop.SYSTEM_PROMPT`): a turn is either exactly one
fenced code block (the action) or plain text with no code block (the final
answer). Chapter 19 generalizes this into a robust action parser; this is the
minimal version the chapter's spec asks for.
"""

import re

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(response_text: str) -> str | None:
    """Return the first fenced code block's contents, or None if there isn't one."""
    match = _CODE_BLOCK_RE.search(response_text)
    if match is None:
        return None
    return match.group(1).strip()
