"""The backbone agent v0: generate -> extract -> execute -> observe -> repeat.

This is the whole loop (~40 lines of actual logic below the constants and
docstrings) — the smallest thing that can plausibly be called a
code-executing agent per Chapter 1's definition: the model's own output
(code, then its result) determines its next input, until the model itself
stops emitting code.
"""

from .executor import execute_code
from .model import call_model
from .parsing import extract_code

SYSTEM_PROMPT = """\
You are a coding agent. Solve the task by writing and running Python code.

On each turn:
- If you need to compute, inspect, or produce something, respond with a \
single ```python code block. It will be executed, and you will see its \
stdout (or an error traceback) as the next message.
- When the task is fully solved, respond with plain text and NO code block, \
stating the final answer. This ends the task.

Rules:
- Exactly one code block per turn — put all the logic for this step in it.
- Use print(...) for anything you need to see back; only printed output \
becomes visible to you.
- If your code raises an error, read the traceback in the next message, \
fix the code, and try again.
"""


class StepBudgetExceeded(RuntimeError):
    """Raised when the agent hasn't produced a final answer within max_steps."""


def run_agent(
    task: str,
    model: str | None = None,
    max_steps: int = 10,
    return_trace: bool = False,
) -> str | tuple[str, list[dict]]:
    """Run the backbone loop on `task`; return the model's final plain-text answer.

    Each iteration is one full Reason-Act-Observe turn (Chapter 3's vocabulary):
    the model's reply IS the Thought+Action combined, `extract_code` separates
    them, `execute_code` produces the real Observation, and the loop appends
    that Observation to `messages` before calling the model again — the same
    context-growth mechanism `run_react_loop` and `run_codeact_loop` used in
    Chapter 3, now driven by a live model instead of a scripted one.

    `return_trace=True` returns `(answer, messages)` instead of just `answer` —
    used by the chapter's hands-on lab to display what happened at each step;
    the loop's own control flow is identical either way.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for _ in range(max_steps):
        reply = call_model(messages, model=model)
        messages.append({"role": "assistant", "content": reply})

        code = extract_code(reply)
        if code is None:
            answer = reply.strip()  # no code block => the model is giving its final answer
            return (answer, messages) if return_trace else answer

        observation = execute_code(code, {})
        messages.append({"role": "user", "content": f"Observation:\n{observation}"})

    raise StepBudgetExceeded(f"no final answer within {max_steps} steps")
