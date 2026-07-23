"""backbone_agent — the one evolving agent this study guide builds, chapter by chapter.

Chapter 5 introduces it as a ~generate -> extract -> execute -> observe -> repeat~
loop (`loop.run_agent`). Later chapters extend these same modules in place;
see PROGRESS.md at the repo root for the backbone's current capabilities.
"""

from .loop import run_agent

__all__ = ["run_agent"]
