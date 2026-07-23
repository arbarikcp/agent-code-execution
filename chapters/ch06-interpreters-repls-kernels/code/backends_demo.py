"""Three real measurements comparing execution backends:

1. The original hands-on direction: the same 3-action sequence against a
   fresh subprocess per action and a persistent IPython kernel — now with
   InProcessExecutor added as a third, real data point (previously only
   discussed, never measured).
2. An AMORTIZATION CURVE: at what number of actions does the kernel's
   one-time startup cost actually pay for itself against the subprocess
   backend's lower-but-repeated per-call cost? Computed AND verified by
   measurement, not just asserted from the single 3-action snapshot.
3. A real kernel-hang failure: an actual infinite loop through
   KernelExecutor, showing the uncaught `queue.Empty` this backend's `run()`
   genuinely raises rather than handling gracefully.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from backbone_agent.executor import (  # noqa: E402
    ExecutionResult,
    InProcessExecutor,
    KernelExecutor,
    SubprocessExecutor,
    observation_from_result,
)

# The same 3-step sequence run against all three backends: set two variables
# in separate "actions," then reference both together in a third. A backend
# with no state between calls cannot pass step 3; a backend with real
# persistent state can.
ACTION_SEQUENCE = [
    "x = 10",
    "y = 20",
    "print(x + y)",
]


def run_sequence(executor, actions: list[str]) -> list[ExecutionResult]:
    return [executor.run(action) for action in actions]


def render_results(label: str, results: list[ExecutionResult]) -> str:
    lines = [f"{label}:"]
    for i, (action, r) in enumerate(zip(ACTION_SEQUENCE, results), start=1):
        obs = observation_from_result(r)
        obs_oneline = obs.strip().splitlines()[-1] if obs.strip() else obs
        lines.append(
            f"  step {i}: {action!r:20} -> success={r.success!s:5} "
            f"duration={r.duration_s * 1000:6.1f}ms  observation={obs_oneline!r}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Amortization curve: N trivial actions, both backends, real measured totals
# ---------------------------------------------------------------------------


def measure_amortization(ns: list[int]) -> list[dict]:
    """For each N, measure total wall time for N trivial actions on both backends."""
    rows = []
    for n in ns:
        actions = [f"result_{i} = {i} * 2" for i in range(n)]

        sp = SubprocessExecutor()
        sp_start = time.monotonic()
        for a in actions:
            sp.run(a)
        sp_total = time.monotonic() - sp_start

        kernel = KernelExecutor()
        k_startup = kernel.startup_duration_s
        k_start = time.monotonic()
        for a in actions:
            kernel.run(a)
        k_run_total = time.monotonic() - k_start
        kernel.close()

        rows.append({
            "n": n,
            "subprocess_total_s": sp_total,
            "kernel_total_s": k_startup + k_run_total,
            "kernel_startup_s": k_startup,
        })
    return rows


def render_amortization(rows: list[dict]) -> str:
    lines = [f"{'N actions':>10} | {'subprocess total':>17} | {'kernel total':>13} | {'kernel wins?':>12}"]
    lines.append("-" * len(lines[0]))
    for r in rows:
        wins = r["kernel_total_s"] < r["subprocess_total_s"]
        lines.append(
            f"{r['n']:>10} | {r['subprocess_total_s'] * 1000:>14.0f}ms | "
            f"{r['kernel_total_s'] * 1000:>10.0f}ms | {'yes' if wins else 'no':>12}"
        )
    return "\n".join(lines)


def find_breakeven(rows: list[dict]) -> int | None:
    """The smallest N in `rows` where the kernel's total time is already lower."""
    for r in rows:
        if r["kernel_total_s"] < r["subprocess_total_s"]:
            return r["n"]
    return None


# ---------------------------------------------------------------------------
# A real kernel-hang failure
# ---------------------------------------------------------------------------


def demo_kernel_hang(execute_timeout_s: float = 2.0) -> dict:
    """Run a genuine infinite loop through KernelExecutor and show the real,
    uncaught exception this backend's `run()` produces on a hang — a real
    gap relative to the `Executor` base class's own contract.
    """
    kernel = KernelExecutor(execute_timeout_s=execute_timeout_s)
    start = time.monotonic()
    try:
        kernel.run("while True:\n    pass\n")
        return {"raised": False, "elapsed_s": time.monotonic() - start}
    except Exception as e:
        elapsed = time.monotonic() - start
        return {
            "raised": True,
            "exception_type": f"{type(e).__module__}.{type(e).__name__}",
            "elapsed_s": elapsed,
        }
    finally:
        kernel.close()  # confirms shutdown_kernel(now=True) really reclaims the hung process


if __name__ == "__main__":
    print("=== (a) Fresh subprocess per action ===")
    sp = SubprocessExecutor()
    sp_start = time.monotonic()
    sp_results = run_sequence(sp, ACTION_SEQUENCE)
    sp_wall = time.monotonic() - sp_start
    print(render_results("subprocess", sp_results))
    print(f"  total wall time for {len(ACTION_SEQUENCE)} actions: {sp_wall * 1000:.1f}ms")
    print(f"  step 3 succeeded: {sp_results[2].success}  (expect False — no state carries over)")

    print("\n=== (b) Persistent IPython kernel ===")
    kernel = KernelExecutor()
    print(f"  kernel startup cost (paid once): {kernel.startup_duration_s * 1000:.1f}ms")
    k_start = time.monotonic()
    k_results = run_sequence(kernel, ACTION_SEQUENCE)
    k_wall = time.monotonic() - k_start
    print(render_results("kernel", k_results))
    print(f"  total wall time for {len(ACTION_SEQUENCE)} actions (excl. startup): {k_wall * 1000:.1f}ms")
    print(f"  step 3 succeeded: {k_results[2].success}  (expect True — real persistent state)")
    kernel.close()

    print("\n=== (c) In-process exec() — the third backend, now measured too ===")
    ip = InProcessExecutor()
    ip_start = time.monotonic()
    ip_results = run_sequence(ip, ACTION_SEQUENCE)
    ip_wall = time.monotonic() - ip_start
    print(render_results("in-process", ip_results))
    print(f"  total wall time for {len(ACTION_SEQUENCE)} actions: {ip_wall * 1000:.1f}ms")
    print(f"  step 3 succeeded: {ip_results[2].success}  (expect False — fresh namespace per call, like subprocess)")

    print("\n=== Summary (3-action snapshot) ===")
    print(f"subprocess:  {sum(r.duration_s for r in sp_results) * 1000:6.1f}ms total, step 3 {'passed' if sp_results[2].success else 'FAILED (as expected)'}")
    print(f"kernel:      {kernel.startup_duration_s * 1000:6.1f}ms startup + {sum(r.duration_s for r in k_results) * 1000:.1f}ms, step 3 {'passed' if k_results[2].success else 'FAILED'}")
    print(f"in-process:  {sum(r.duration_s for r in ip_results) * 1000:6.1f}ms total, step 3 {'passed' if ip_results[2].success else 'FAILED (as expected)'}")

    print("\n=== Amortization curve: at what N does the kernel's startup pay off? ===")
    amort_rows = measure_amortization([1, 3, 5, 10, 20, 40, 60, 80, 120, 160])
    print(render_amortization(amort_rows))
    breakeven = find_breakeven(amort_rows)
    print(f"\nSmallest N tested where kernel's total time is already lower: {breakeven}")

    print("\n=== Real kernel-hang failure (infinite loop, 2s execute timeout) ===")
    hang_result = demo_kernel_hang(execute_timeout_s=2.0)
    print(hang_result)
