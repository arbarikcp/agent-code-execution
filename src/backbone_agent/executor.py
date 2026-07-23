"""Execution backends: the machinery that actually runs a code action.

Chapter 5 (v0) had exactly one backend, hardcoded: in-process `exec()`. This
chapter (6) introduces the `Executor` interface and adds two more backends
that answer the same question — "how does code go in and a result come back
out?" — differently:

- `InProcessExecutor` — v0's original behavior, now behind the interface.
- `SubprocessExecutor` — one-shot execution: a fresh `python -c` process per
  call. No state persists between calls; each call pays full interpreter
  startup cost.
- `KernelExecutor` — a persistent IPython kernel (via `jupyter_client`),
  started once and reused across calls. State (variables, imports) persists
  naturally across calls, at the cost of managing a long-lived process.

Chapter 9 later expands this into a fully pluggable, three-backend interface
(adding a remote/sandboxed option); this chapter's job is narrower — get the
interface right and show the one-shot-vs-persistent trade-off for real.

No sandboxing is applied to any of these — this guide's scope is agent
behavior, not containment (see CLAUDE.md's sandbox-guide handoff).
"""

import contextlib
import io
import re
import subprocess
import sys
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """What any executor's `run()` produces — backend-agnostic by design."""

    stdout: str
    stderr: str
    success: bool
    error: str | None = None
    duration_s: float = 0.0


class Executor(ABC):
    """One code-execution backend. `run()` is the entire contract."""

    @abstractmethod
    def run(self, code: str) -> ExecutionResult:
        """Execute `code` and return its result. Must not raise on the code's own errors."""

    def close(self) -> None:
        """Release any resources (subprocess, kernel). No-op by default."""


def observation_from_result(result: ExecutionResult) -> str:
    """Turn an ExecutionResult into the observation string the loop appends to context.

    Matches v0's exact formatting so `loop.py` behaves identically regardless
    of which Executor produced the result.
    """
    if not result.success:
        return result.error or result.stderr or "(execution failed with no error output)"
    return result.stdout if result.stdout.strip() else "(code ran with no output; use print() to see a result)"


# ---------------------------------------------------------------------------
# In-process exec() — v0's original backend, unchanged behavior
# ---------------------------------------------------------------------------


class InProcessExecutor(Executor):
    """Run code via `exec()` in this process, fresh namespace every call (stateless)."""

    def run(self, code: str) -> ExecutionResult:
        namespace: dict = {}
        buffer = io.StringIO()
        start = time.monotonic()
        try:
            with contextlib.redirect_stdout(buffer):
                exec(code, namespace)
            return ExecutionResult(
                stdout=buffer.getvalue(), stderr="", success=True,
                duration_s=time.monotonic() - start,
            )
        except Exception:
            return ExecutionResult(
                stdout=buffer.getvalue(), stderr="", success=False,
                error=traceback.format_exc(), duration_s=time.monotonic() - start,
            )


# Backward-compatible function form (used by nothing in this repo anymore,
# kept only because Chapter 5's README/notebook reference it by name).
def execute_code(code: str, namespace: dict | None = None) -> str:
    namespace = {} if namespace is None else namespace
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(code, namespace)
    except Exception:
        return traceback.format_exc()
    output = buffer.getvalue()
    return output if output.strip() else "(code ran with no output; use print() to see a result)"


# ---------------------------------------------------------------------------
# Subprocess — one-shot execution, fresh process per call
# ---------------------------------------------------------------------------


class SubprocessExecutor(Executor):
    """Run code as `python -c <code>` in a brand-new process every call.

    Nothing persists between calls — not variables, not imports — because
    there is no "between calls": each call is a different OS process that
    exits when the code finishes.
    """

    def __init__(self, timeout_s: float = 30.0):
        self.timeout_s = timeout_s

    def run(self, code: str) -> ExecutionResult:
        start = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True, text=True, timeout=self.timeout_s,
            )
        except subprocess.TimeoutExpired as e:
            return ExecutionResult(
                stdout=e.stdout or "", stderr=e.stderr or "", success=False,
                error=f"TimeoutExpired after {self.timeout_s}s",
                duration_s=time.monotonic() - start,
            )
        success = proc.returncode == 0
        return ExecutionResult(
            stdout=proc.stdout, stderr=proc.stderr, success=success,
            error=proc.stderr if not success else None,
            duration_s=time.monotonic() - start,
        )


# ---------------------------------------------------------------------------
# Persistent IPython kernel — real execute_request/execute_reply protocol
# ---------------------------------------------------------------------------

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class KernelExecutor(Executor):
    """Run code against one persistent IPython kernel (via jupyter_client).

    The kernel process is started once, in `__init__` (or lazily on first
    `run()`), and reused for every subsequent `run()` — real state
    (variables, imports) persists across calls because it's the same live
    interpreter, not a `Executor`-level illusion of persistence.
    """

    def __init__(self, startup_timeout_s: float = 60.0):
        from jupyter_client import KernelManager

        start = time.monotonic()
        self._km = KernelManager()
        self._km.start_kernel()
        self._kc = self._km.client()
        self._kc.start_channels()
        self._kc.wait_for_ready(timeout=startup_timeout_s)
        self.startup_duration_s = time.monotonic() - start

    def run(self, code: str) -> ExecutionResult:
        start = time.monotonic()
        msg_id = self._kc.execute(code)
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        success = True
        error_text: str | None = None

        while True:
            msg = self._kc.get_iopub_msg(timeout=30)
            if msg["parent_header"].get("msg_id") != msg_id:
                continue  # message from a different (e.g. stale) request
            msg_type = msg["header"]["msg_type"]
            content = msg["content"]

            if msg_type == "stream":
                (stdout_parts if content["name"] == "stdout" else stderr_parts).append(content["text"])
            elif msg_type == "execute_result":
                stdout_parts.append(content["data"].get("text/plain", ""))
            elif msg_type == "error":
                success = False
                error_text = _ANSI_RE.sub("", "\n".join(content["traceback"]))
            elif msg_type == "status" and content["execution_state"] == "idle":
                break

        return ExecutionResult(
            stdout="".join(stdout_parts), stderr="".join(stderr_parts),
            success=success, error=error_text, duration_s=time.monotonic() - start,
        )

    def close(self) -> None:
        self._kc.stop_channels()
        self._km.shutdown_kernel(now=True)
