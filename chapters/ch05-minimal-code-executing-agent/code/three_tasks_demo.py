"""Optional live-model evaluation of the Chapter 5 agent on three small tasks.

The tasks match the curriculum: computation, file transformation, and
API-free data analysis. Each result is checked independently.

Requires credentials for the provider selected by ``BACKBONE_MODEL``.
"""

import csv
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from backbone_agent import run_agent  # noqa: E402

WORKSPACE = Path(__file__).resolve().parent / "workspace"
SCORES_CSV = WORKSPACE / "scores.csv"
AVERAGE_TXT = WORKSPACE / "average.txt"


def numbers_in(text: str) -> list[float]:
    """Extract standalone decimal numbers from a final answer."""
    pattern = r"(?<![\w.])-?\d+(?:\.\d+)?(?!\w|\.\d)"
    return [float(value) for value in re.findall(pattern, text)]


def contains_number(text: str, expected: float, tolerance: float = 1e-9) -> bool:
    return any(abs(value - expected) <= tolerance for value in numbers_in(text))


def render_trace(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = {"user": "USER/OBSERVATION", "assistant": "ASSISTANT"}[m["role"]]
        lines.append(f"--- {role} ---")
        lines.append(m["content"].strip())
    return "\n".join(lines)


def task_1_math() -> dict:
    """A math problem: sum of the first 20 primes."""
    task = "Compute the sum of the first 20 prime numbers. State the final numeric answer clearly."
    answer, messages = run_agent(task, return_trace=True)

    # ground truth, computed independently of the agent
    def is_prime(n: int) -> bool:
        return n > 1 and all(n % d for d in range(2, int(n**0.5) + 1))

    primes = []
    n = 2
    while len(primes) < 20:
        if is_prime(n):
            primes.append(n)
        n += 1
    expected = sum(primes)

    success = contains_number(answer, expected)
    return {
        "name": "math (sum of first 20 primes)",
        "task": task,
        "answer": answer,
        "expected": expected,
        "success": success,
        "messages": messages,
    }


def task_2_file_transform(system_prompt: str | None = None) -> dict:
    """A file transform: average a CSV column, write the result to a real file.

    `system_prompt` defaults to the backbone's own SYSTEM_PROMPT; pass a
    different one to A/B a prompt variant against this exact task (used by
    `reliability_and_ablation.py`'s prompt-ablation experiment).
    """
    if AVERAGE_TXT.exists():
        AVERAGE_TXT.unlink()

    task = (
        f"Read the CSV file at {SCORES_CSV} (columns: name, score). "
        f"Compute the average of the 'score' column, rounded to 2 decimal places, "
        f"and write ONLY that number as text to {AVERAGE_TXT}. "
        f"Then state the final average in your answer."
    )
    answer, messages = run_agent(task, return_trace=True, system_prompt=system_prompt)

    with open(SCORES_CSV) as f:
        rows = list(csv.DictReader(f))
    expected = round(sum(int(r["score"]) for r in rows) / len(rows), 2)

    file_written = AVERAGE_TXT.exists()
    file_correct = False
    if file_written:
        try:
            file_correct = abs(float(AVERAGE_TXT.read_text().strip()) - expected) < 0.01
        except ValueError:
            file_correct = False

    success = file_written and file_correct
    return {
        "name": "file transform (average a CSV column)",
        "task": task,
        "answer": answer,
        "expected": expected,
        "success": success,
        "messages": messages,
        "file_written": file_written,
        "file_contents": AVERAGE_TXT.read_text().strip() if file_written else None,
    }


def task_3_data_stats() -> dict:
    """An API-free data task: mean/median/stdev of an inline list."""
    values = [12, 45, 7, 22, 9, 34, 18]
    task = (
        f"Given the list {values}, compute the mean, median, and population "
        f"standard deviation. Round each to 2 decimal places and state all "
        f"three clearly in your final answer."
    )
    answer, messages = run_agent(task, return_trace=True)

    expected_mean = round(statistics.mean(values), 2)
    expected_median = round(statistics.median(values), 2)
    expected_stdev = round(statistics.pstdev(values), 2)

    success = all(
        contains_number(answer, expected, tolerance=0.005)
        for expected in (expected_mean, expected_median, expected_stdev)
    )
    return {
        "name": "data task (mean/median/stdev of an inline list)",
        "task": task,
        "answer": answer,
        "expected": (expected_mean, expected_median, expected_stdev),
        "success": success,
        "messages": messages,
    }


if __name__ == "__main__":
    tasks = [task_1_math, task_2_file_transform, task_3_data_stats]
    results = []
    for task_fn in tasks:
        result = task_fn()
        results.append(result)
        print(f"=== {result['name']} ===")
        print(render_trace(result["messages"]))
        print(f"\nExpected: {result['expected']}")
        print(f"Success:  {result['success']}")
        print()

    n_success = sum(1 for r in results if r["success"])
    print(f"{n_success}/{len(results)} tasks solved correctly")
