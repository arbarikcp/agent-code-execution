"""Deterministic checks for the five mechanics introduced in Chapter 5.

The filename is retained for compatibility with existing chapter links. Earlier
versions ran repeated provider-specific prompt trials here. Those experiments
obscured the chapter's purpose and required network access. This module now
tests the loop itself:

    generate -> extract -> execute -> observe -> repeat/finish

Run from the repository root:
    python chapters/ch05-minimal-code-executing-agent/code/reliability_and_ablation.py
"""

import sys
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from backbone_agent import run_agent  # noqa: E402
from backbone_agent.loop import StepBudgetExceeded  # noqa: E402
from backbone_agent.parsing import extract_code  # noqa: E402

Reply = str | Callable[[list[dict]], str]


class ScriptedModel:
    """Return fixed replies while allowing assertions about accumulated context."""

    def __init__(self, *replies: Reply) -> None:
        self._replies = iter(replies)
        self.calls = 0

    def __call__(self, messages: list[dict], model: str | None = None) -> str:
        del model
        self.calls += 1
        reply = next(self._replies)
        return reply(messages) if callable(reply) else reply


def run_with_script(task: str, scripted_model: ScriptedModel, **kwargs):
    """Run the real agent loop while replacing only the external model call."""
    with patch("backbone_agent.loop.call_model", scripted_model):
        return run_agent(task, **kwargs)


def check_code_extraction() -> None:
    """The minimal parser extracts one fenced action and detects plain finish text."""
    assert extract_code("```python\nprint(6 * 7)\n```") == "print(6 * 7)"
    assert extract_code("The answer is 42.") is None


def check_observation_feedback() -> None:
    """Executed stdout must appear in context before the next model decision."""

    def finish_after_observation(messages: list[dict]) -> str:
        assert messages[-1] == {"role": "user", "content": "Observation:\n42\n"}
        return "The final answer is 42."

    model = ScriptedModel(
        "```python\nprint(6 * 7)\n```",
        finish_after_observation,
    )
    answer, trace = run_with_script(
        "Compute 6 * 7 with code.",
        model,
        return_trace=True,
    )

    assert answer == "The final answer is 42."
    assert model.calls == 2
    assert [message["role"] for message in trace] == [
        "system",
        "user",
        "assistant",
        "user",
        "assistant",
    ]


def check_error_recovery_path() -> None:
    """A real traceback becomes an observation that can drive a corrected action."""

    def fix_after_error(messages: list[dict]) -> str:
        observation = messages[-1]["content"]
        assert observation.startswith("Observation:\nTraceback")
        assert "ZeroDivisionError" in observation
        return "```python\nprint(10 / 2)\n```"

    def finish_after_fix(messages: list[dict]) -> str:
        assert messages[-1] == {"role": "user", "content": "Observation:\n5.0\n"}
        return "The corrected result is 5.0."

    model = ScriptedModel(
        "```python\nprint(10 / 0)\n```",
        fix_after_error,
        finish_after_fix,
    )
    answer = run_with_script("Compute 10 / 2.", model)

    assert answer == "The corrected result is 5.0."
    assert model.calls == 3


def check_termination_signal() -> None:
    """Plain text without a fenced block is the v0 finish protocol."""
    model = ScriptedModel("Finished without executing code.")
    answer = run_with_script("Return a final response.", model)

    assert answer == "Finished without executing code."
    assert model.calls == 1


def check_step_budget() -> None:
    """The controller stops a model that keeps emitting actions."""
    model = ScriptedModel("```python\nprint('still working')\n```")

    try:
        run_with_script("Never finish.", model, max_steps=1)
    except StepBudgetExceeded as error:
        assert str(error) == "no final answer within 1 step"
    else:
        raise AssertionError("expected StepBudgetExceeded")


CHECKS = [
    ("code extraction", check_code_extraction),
    ("observation feedback", check_observation_feedback),
    ("error recovery path", check_error_recovery_path),
    ("termination signal", check_termination_signal),
    ("step budget", check_step_budget),
]


if __name__ == "__main__":
    for name, check in CHECKS:
        check()
        print(f"PASS: {name}")
