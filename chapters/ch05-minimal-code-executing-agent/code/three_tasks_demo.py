"""Run the backbone agent (Chapter 5, v0) on three small tasks, for real, against
a live model (Groq via litellm — see `../../../src/backbone_agent/model.py`).

Per the chapter's hands-on direction: a math problem, a file transform, and an
API-free data task. Each task is independently verified against a
ground-truth computed by this script — not by trusting the agent's own claim.

Requires GROQ_API_KEY in the environment (see repo root .env, gitignored).
"""

import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from backbone_agent import run_agent  # noqa: E402

WORKSPACE = Path(__file__).resolve().parent / "workspace"
SCORES_CSV = WORKSPACE / "scores.csv"
AVERAGE_TXT = WORKSPACE / "average.txt"


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

    success = str(expected) in answer
    return {
        "name": "math (sum of first 20 primes)",
        "task": task,
        "answer": answer,
        "expected": expected,
        "success": success,
        "messages": messages,
    }


def task_2_file_transform() -> dict:
    """A file transform: average a CSV column, write the result to a real file."""
    if AVERAGE_TXT.exists():
        AVERAGE_TXT.unlink()

    task = (
        f"Read the CSV file at {SCORES_CSV} (columns: name, score). "
        f"Compute the average of the 'score' column, rounded to 2 decimal places, "
        f"and write ONLY that number as text to {AVERAGE_TXT}. "
        f"Then state the final average in your answer."
    )
    answer, messages = run_agent(task, return_trace=True)

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
        str(v) in answer for v in (expected_mean, expected_median, expected_stdev)
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
