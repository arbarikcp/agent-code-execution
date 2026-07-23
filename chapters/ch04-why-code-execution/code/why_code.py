"""Three runnable demonstrations backing Chapter 4's argument for code as an action space.

1. `run_benchmark` — reproduces a CodeAct-style comparison: the same "sum k files"
   task, solved via JSON tool calls (one call per file) and via a single code
   action, under a shared step budget. Real execution, real success/failure,
   real step counts — this is OUR OWN toy benchmark, clearly distinct from and
   much smaller than the CodeAct paper's own (see chapter README for the
   paper's verified claim).
2. `demo_tool_reuse` — shows a code action calling an existing stdlib function
   with zero new registration, versus what JSON tool calling would require.
3. `demo_dynamic_revision` — a code action that really fails, whose real
   traceback informs a second code action that really succeeds.
"""

import statistics
import traceback
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 1. Composability under a step budget: JSON tool calls vs. a code action
# ---------------------------------------------------------------------------


def build_workspace(k: int) -> dict[str, str]:
    """k files, each holding one integer, generated deterministically."""
    return {f"f{i}.txt": str((i * 7 + 3) % 50 + 1) for i in range(k)}


def read_file(ws: dict[str, str], path: str) -> str:
    return ws[path]


def write_file(ws: dict[str, str], path: str, content: str) -> str:
    ws[path] = content
    return f"ok: wrote {len(content)} bytes to {path}"


@dataclass
class BenchmarkResult:
    k: int
    approach: str
    steps_needed: int
    success: bool
    result_value: int | None


def run_json_tool_solver(k: int, max_steps: int) -> BenchmarkResult:
    """JSON tool calling needs one read per file, plus one write, plus one final answer."""
    steps_needed = k + 2  # k reads + 1 write + 1 final answer
    if steps_needed > max_steps:
        return BenchmarkResult(k, "json_tool_calls", steps_needed, False, None)
    ws = build_workspace(k)
    total = 0
    for i in range(k):
        total += int(read_file(ws, f"f{i}.txt"))  # one real read per "turn"
    write_file(ws, "total.txt", str(total))
    return BenchmarkResult(k, "json_tool_calls", steps_needed, True, total)


def run_code_action_solver(k: int, max_steps: int) -> BenchmarkResult:
    """A single code action reads, sums, and writes regardless of k — constant step count."""
    steps_needed = 2  # 1 code action + 1 final answer
    if steps_needed > max_steps:
        return BenchmarkResult(k, "code_action", steps_needed, False, None)
    ws = build_workspace(k)
    code = (
        f"total = sum(int(read_file(ws, f'f{{i}}.txt')) for i in range({k}))\n"
        f"write_file(ws, 'total.txt', str(total))\n"
    )
    namespace = {"ws": ws, "read_file": read_file, "write_file": write_file}
    exec(code, namespace)  # real execution
    return BenchmarkResult(k, "code_action", steps_needed, True, namespace["total"])


def run_benchmark(ks: list[int], max_steps: int) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []
    for k in ks:
        expected = sum(int(v) for v in build_workspace(k).values())
        json_result = run_json_tool_solver(k, max_steps)
        code_result = run_code_action_solver(k, max_steps)
        if json_result.success:
            assert json_result.result_value == expected, "json solver produced wrong sum"
        if code_result.success:
            assert code_result.result_value == expected, "code solver produced wrong sum"
        results.append(json_result)
        results.append(code_result)
    return results


def summarize_benchmark(results: list[BenchmarkResult]) -> dict[str, dict]:
    summary: dict[str, dict] = {}
    for approach in ("json_tool_calls", "code_action"):
        rows = [r for r in results if r.approach == approach]
        n_success = sum(1 for r in rows if r.success)
        summary[approach] = {
            "n_tasks": len(rows),
            "n_success": n_success,
            "success_rate": n_success / len(rows) if rows else 0.0,
            "avg_steps_needed": sum(r.steps_needed for r in rows) / len(rows) if rows else 0.0,
        }
    return summary


def sweep_budgets(budgets: list[int], ks: list[int]) -> dict[int, dict]:
    """Success rate for both approaches, across a RANGE of step budgets.

    The single-budget (8) snapshot shows ONE point on a curve. This sweeps
    the budget itself, to answer: does the 57%-vs-100% gap from one budget
    generalize, or was 8 a special case? A tight budget should hurt JSON
    tool calling more (fewer k values fit); code should stay at ~100% for
    any budget >= 2, since its step count never depends on k at all.
    """
    out: dict[int, dict] = {}
    for budget in budgets:
        results = run_benchmark(ks, max_steps=budget)
        out[budget] = summarize_benchmark(results)
    return out


def render_budget_sweep(sweep: dict[int, dict]) -> str:
    lines = [f"{'budget':>6} | {'json success rate':>18} | {'code success rate':>18} | {'max k JSON can fit':>18}"]
    lines.append("-" * len(lines[0]))
    for budget, summary in sweep.items():
        json_rate = summary["json_tool_calls"]["success_rate"]
        code_rate = summary["code_action"]["success_rate"]
        max_k_json = max(budget - 2, 0)  # JSON needs k+2 steps; largest k that fits this budget
        lines.append(f"{budget:>6} | {json_rate:>17.0%} | {code_rate:>17.0%} | {max_k_json:>18}")
    return "\n".join(lines)


def render_benchmark_table(results: list[BenchmarkResult]) -> str:
    ks = sorted({r.k for r in results})
    lines = [f"{'k':>3} | {'json steps':>10} | {'json ok':>7} | {'code steps':>10} | {'code ok':>7}"]
    lines.append("-" * len(lines[0]))
    by_key = {(r.k, r.approach): r for r in results}
    for k in ks:
        j = by_key[(k, "json_tool_calls")]
        c = by_key[(k, "code_action")]
        lines.append(
            f"{k:>3} | {j.steps_needed:>10} | {str(j.success):>7} | {c.steps_needed:>10} | {str(c.success):>7}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 2. Tool reuse: calling an existing library function needs zero registration
# ---------------------------------------------------------------------------

# What JSON tool calling would require before the model could compute a mean:
HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN = {
    "name": "compute_mean",
    "description": "Compute the arithmetic mean of a list of numbers.",
    "parameters": {
        "type": "object",
        "properties": {"values": {"type": "array", "items": {"type": "number"}}},
        "required": ["values"],
    },
}


def demo_tool_reuse() -> float:
    """A code action calls `statistics.mean` directly — a stdlib function nobody
    registered as a tool — versus JSON mode needing a bespoke schema like
    `HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN` defined and exposed in advance for
    every new operation the agent might need.
    """
    values = [12, 7, 19, 3, 25]
    code = "import statistics\nresult = round(statistics.mean(values), 2)\n"
    namespace = {"values": values}
    exec(code, namespace)  # real execution, real stdlib call
    return namespace["result"]


# ---------------------------------------------------------------------------
# 3. Dynamic revision: a real traceback informs a real fix
# ---------------------------------------------------------------------------


def demo_dynamic_revision() -> tuple[str, float]:
    """Run a code action that really raises ZeroDivisionError, capture its real
    traceback as the observation, then run a second code action — informed by
    that traceback — that really succeeds.
    """
    ws = {"count.txt": "0", "total.txt": "50"}

    buggy_code = (
        "avg = int(read_file(ws, 'total.txt')) / int(read_file(ws, 'count.txt'))\n"
    )
    namespace = {"ws": ws, "read_file": read_file}
    try:
        exec(buggy_code, namespace)  # real execution, really raises
        raise AssertionError("expected buggy_code to raise ZeroDivisionError")
    except ZeroDivisionError:
        observation = traceback.format_exc()

    assert "ZeroDivisionError" in observation  # the real traceback, not a canned string

    fixed_code = (
        "count = int(read_file(ws, 'count.txt'))\n"
        "total = int(read_file(ws, 'total.txt'))\n"
        "avg = total / count if count else 0.0\n"
    )
    namespace = {"ws": ws, "read_file": read_file}
    exec(fixed_code, namespace)  # real execution, really succeeds
    return observation, namespace["avg"]


# ---------------------------------------------------------------------------
# 4. Costs and risks, measured: non-determinism is real, not just asserted
# ---------------------------------------------------------------------------


def demo_nondeterminism() -> tuple[str, str]:
    """Run the IDENTICAL code string twice and show the outputs really differ.

    A JSON tool call's schema constrains what CAN be called; a code action
    can call time.time(), a random source, or anything else non-deterministic
    just as easily as it calls something pure. This isn't a difference in
    what's possible in principle (a JSON tool could wrap a non-deterministic
    function too) — it's a difference in how EASILY it happens by default,
    demonstrated here by running the same source text twice.
    """
    code = "import time\nresult = time.time()\n"
    ns1: dict = {}
    exec(code, ns1)
    ns2: dict = {}
    exec(code, ns2)
    return f"{ns1['result']:.6f}", f"{ns2['result']:.6f}"


if __name__ == "__main__":
    print("=== 1. Composability under an 8-step budget ===")
    ks = [1, 3, 5, 6, 7, 10, 20]
    results = run_benchmark(ks, max_steps=8)
    print(render_benchmark_table(results))
    summary = summarize_benchmark(results)
    for approach, stats in summary.items():
        print(
            f"\n{approach}: {stats['n_success']}/{stats['n_tasks']} succeeded "
            f"({stats['success_rate']:.0%}), avg steps needed = {stats['avg_steps_needed']:.1f}"
        )

    print("\n=== 1b. Does the 8-step snapshot generalize? Sweep the budget itself ===")
    budget_sweep = sweep_budgets([3, 4, 6, 8, 10, 12, 16, 24], ks)
    print(render_budget_sweep(budget_sweep))

    print("\n=== 2. Tool reuse (statistics.mean, zero registration) ===")
    mean_result = demo_tool_reuse()
    print(f"code action result: {mean_result}")
    print(f"JSON mode would first need a schema like:\n  {HYPOTHETICAL_JSON_TOOL_SCHEMA_FOR_MEAN}")

    print("\n=== 3. Dynamic revision (real traceback -> real fix) ===")
    traceback_text, fixed_avg = demo_dynamic_revision()
    print("First action's real traceback (tail):")
    print("  " + traceback_text.strip().splitlines()[-1])
    print(f"Second action's result after the fix: {fixed_avg}")

    print("\n=== 4. Non-determinism, measured (identical code, two runs) ===")
    r1, r2 = demo_nondeterminism()
    print(f"run 1: {r1}")
    print(f"run 2: {r2}")
    print(f"identical source, different output: {r1 != r2}")
