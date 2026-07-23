"""Backbone regression smoke test (CLAUDE.md: "add a short regression check so
later chapters don't silently break it").

Run after any change to src/backbone_agent/: `python tests/test_backbone_smoke.py`.
Requires GROQ_API_KEY (or whatever BACKBONE_MODEL's provider needs) in the
environment — this makes one real, cheap model call.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backbone_agent import run_agent  # noqa: E402


def test_solves_a_trivial_arithmetic_task() -> None:
    answer = run_agent("What is 12 * 12? Compute it with code, don't just guess.")
    assert "144" in answer, f"expected '144' in the final answer, got: {answer!r}"


if __name__ == "__main__":
    test_solves_a_trivial_arithmetic_task()
    print("PASS: backbone smoke test")
