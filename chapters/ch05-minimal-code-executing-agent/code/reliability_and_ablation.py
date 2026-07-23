"""Three deeper, real-live-model measurements beyond the original single-run
hands-on tasks (`three_tasks_demo.py`):

1. Multi-trial reliability: run the math and data-stats tasks 3x each and
   report a real pass@3-style success rate, instead of trusting one run.
2. A prompt ablation: does one added sentence steering the model toward the
   standard library reduce the real ModuleNotFoundError rate seen in
   Chapter 5's original run? A/B'd over 4 live trials per prompt.
3. A real step-budget boundary: call the file-transform task with
   max_steps=1 and confirm StepBudgetExceeded actually fires, since even a
   clean run needs a code action AND a separate final-answer turn.

Requires GROQ_API_KEY in the environment — every measurement here is a real
live call to groq/llama-3.3-70b-versatile via litellm.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

import litellm  # noqa: E402

from backbone_agent import run_agent  # noqa: E402
from backbone_agent.loop import SYSTEM_PROMPT, StepBudgetExceeded  # noqa: E402

from three_tasks_demo import task_1_math, task_2_file_transform, task_3_data_stats  # noqa: E402


def _with_backoff(fn, *args, max_retries: int = 5, **kwargs):
    """Groq's free tier has a real, low tokens-per-minute limit (observed:
    12,000 TPM) that this chapter's multi-trial experiments hit directly —
    a genuine finding, not a hypothetical. Retry with backoff rather than
    silently failing the experiment; this is a local accommodation for
    running many trials back-to-back, not the retry-policy design Chapter 22
    covers properly.
    """
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except litellm.exceptions.RateLimitError:
            wait = 5 * (attempt + 1)
            print(f"    (rate limited, waiting {wait}s before retry {attempt + 1}/{max_retries})")
            time.sleep(wait)
    return fn(*args, **kwargs)  # final attempt, let it raise if it still fails

ALT_SYSTEM_PROMPT = SYSTEM_PROMPT + (
    "\nPrefer Python's standard library (e.g. csv, statistics, json) over "
    "third-party packages like pandas or numpy — assume third-party packages "
    "are NOT installed unless you have already confirmed otherwise this run."
)


# ---------------------------------------------------------------------------
# 1. Multi-trial reliability (pass@N-style, our own small measurement)
# ---------------------------------------------------------------------------


def run_reliability_trials(task_fn, n_trials: int) -> dict:
    successes = 0
    step_counts = []
    for _ in range(n_trials):
        result = _with_backoff(task_fn)
        successes += int(result["success"])
        step_counts.append(sum(1 for m in result["messages"] if m["role"] == "assistant"))
        time.sleep(2)  # pace requests under Groq's free-tier TPM limit
    return {
        "n_trials": n_trials,
        "n_success": successes,
        "success_rate": successes / n_trials,
        "step_counts": step_counts,
        "avg_steps": sum(step_counts) / len(step_counts),
    }


# ---------------------------------------------------------------------------
# 2. Prompt ablation: does steering toward stdlib reduce the miss rate?
# ---------------------------------------------------------------------------


def run_prompt_ablation(n_trials: int) -> dict:
    def run_group(system_prompt) -> dict:
        successes = 0
        module_not_found_count = 0
        step_counts = []
        for _ in range(n_trials):
            result = _with_backoff(task_2_file_transform, system_prompt=system_prompt)
            successes += int(result["success"])
            step_counts.append(sum(1 for m in result["messages"] if m["role"] == "assistant"))
            hit_missing_module = any(
                "ModuleNotFoundError" in m["content"]
                for m in result["messages"] if m["role"] == "user"
            )
            module_not_found_count += int(hit_missing_module)
            time.sleep(2)  # pace requests under Groq's free-tier TPM limit
        return {
            "n_trials": n_trials,
            "n_success": successes,
            "success_rate": successes / n_trials,
            "module_not_found_rate": module_not_found_count / n_trials,
            "avg_steps": sum(step_counts) / len(step_counts),
            "step_counts": step_counts,
        }

    return {
        "default_prompt": run_group(None),
        "stdlib_steered_prompt": run_group(ALT_SYSTEM_PROMPT),
    }


# ---------------------------------------------------------------------------
# 3. A real step-budget boundary
# ---------------------------------------------------------------------------


def run_step_budget_boundary_demo() -> dict:
    task = (
        "Compute the sum of the first 20 prime numbers. "
        "State the final numeric answer clearly."
    )
    try:
        run_agent(task, max_steps=1)
        return {"raised": False}
    except StepBudgetExceeded as e:
        return {"raised": True, "message": str(e)}


if __name__ == "__main__":
    print("=== 1. Multi-trial reliability (3 trials each) ===")
    math_reliability = run_reliability_trials(task_1_math, n_trials=3)
    print(f"math task:  {math_reliability['n_success']}/{math_reliability['n_trials']} "
          f"({math_reliability['success_rate']:.0%}), step counts: {math_reliability['step_counts']}")

    stats_reliability = run_reliability_trials(task_3_data_stats, n_trials=3)
    print(f"stats task: {stats_reliability['n_success']}/{stats_reliability['n_trials']} "
          f"({stats_reliability['success_rate']:.0%}), step counts: {stats_reliability['step_counts']}")

    print("\n=== 2. Prompt ablation: default vs. stdlib-steered (3 trials each) ===")
    time.sleep(10)  # let the TPM window recover between experiment sections
    ablation = run_prompt_ablation(n_trials=3)
    for label, stats in ablation.items():
        print(f"{label}: {stats['n_success']}/{stats['n_trials']} succeeded "
              f"({stats['success_rate']:.0%}), "
              f"ModuleNotFoundError hit rate: {stats['module_not_found_rate']:.0%}, "
              f"avg steps: {stats['avg_steps']:.1f}, step counts: {stats['step_counts']}")

    print("\n=== 3. Real step-budget boundary (max_steps=1 on a 2+-step task) ===")
    boundary = run_step_budget_boundary_demo()
    print(f"StepBudgetExceeded raised: {boundary['raised']}")
    if boundary["raised"]:
        print(f"  message: {boundary['message']}")
