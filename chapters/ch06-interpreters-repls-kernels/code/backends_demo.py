"""Run the same sequence of actions against (a) a fresh subprocess each time
and (b) a persistent IPython kernel, per Chapter 6's hands-on direction.

Both executors are real: `SubprocessExecutor` really spawns `python -c ...`
per call; `KernelExecutor` really starts one IPython kernel (via
jupyter_client) and reuses it. Nothing here is simulated — the state-loss on
subprocess and state-persistence on the kernel are genuine consequences of
what each backend actually is, not scripted to look that way.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from backbone_agent.executor import (  # noqa: E402
    ExecutionResult,
    KernelExecutor,
    SubprocessExecutor,
    observation_from_result,
)

# The same 3-step sequence run against both backends: set two variables in
# separate "actions," then reference both together in a third. A backend
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

    print("\n=== Summary ===")
    print(f"subprocess: {sum(r.duration_s for r in sp_results) * 1000:.1f}ms total run time, "
          f"step 3 {'passed' if sp_results[2].success else 'FAILED (as expected)'}")
    print(f"kernel:     {kernel.startup_duration_s * 1000:.1f}ms startup + "
          f"{sum(r.duration_s for r in k_results) * 1000:.1f}ms total run time, "
          f"step 3 {'passed' if k_results[2].success else 'FAILED'}")
