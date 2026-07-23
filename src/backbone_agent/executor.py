"""Run one code action and turn its result into an observation string.

v0 uses in-process `exec()` with a fresh namespace per call — the simplest,
least isolated backend (Chapter 6 compares it to a subprocess and a
persistent kernel; Chapter 9 makes the backend pluggable). No sandboxing is
applied here: this guide's scope is agent behavior, not containment — see
CLAUDE.md's "defer containment to the sibling guide."
"""

import contextlib
import io
import traceback


def execute_code(code: str, namespace: dict | None = None) -> str:
    """Execute `code`, returning captured stdout, or a formatted traceback on error."""
    namespace = {} if namespace is None else namespace
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(code, namespace)
    except Exception:
        return traceback.format_exc()

    output = buffer.getvalue()
    return output if output.strip() else "(code ran with no output; use print() to see a result)"
