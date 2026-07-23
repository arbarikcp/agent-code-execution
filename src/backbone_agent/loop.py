"""The backbone agent: generate -> extract -> execute -> observe -> repeat.

Chapter 5 (v0): the whole loop in ~40 lines, one hardcoded execution backend.
Chapter 6: the execution backend is now pluggable — `run_agent` accepts any
`Executor` (default: `InProcessExecutor`, preserving v0's exact behavior) —
without changing the loop's own control flow at all.
"""

from .executor import Executor, InProcessExecutor, observation_from_result
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
    executor: Executor | None = None,
) -> str | tuple[str, list[dict]]:
    """Run the backbone loop on `task`; return the model's final plain-text answer.

    Each iteration is one full Reason-Act-Observe turn (Chapter 3's vocabulary):
    the model's reply IS the Thought+Action combined, `extract_code` separates
    them, `executor.run` produces the real Observation, and the loop appends
    that Observation to `messages` before calling the model again — the same
    context-growth mechanism `run_react_loop` and `run_codeact_loop` used in
    Chapter 3, now driven by a live model instead of a scripted one.

    `executor` defaults to `InProcessExecutor()` — v0's original backend — but
    any `Executor` (e.g. `SubprocessExecutor`, `KernelExecutor` from Chapter 6)
    can be passed in; the loop's control flow doesn't change either way, which
    is the entire point of the `Executor` interface.

    `return_trace=True` returns `(answer, messages)` instead of just `answer` —
    used by the chapters' hands-on labs to display what happened at each step.
    """
    executor = executor or InProcessExecutor()
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

        result = executor.run(code)
        observation = observation_from_result(result)
        messages.append({"role": "user", "content": f"Observation:\n{observation}"})

    raise StepBudgetExceeded(f"no final answer within {max_steps} steps")
