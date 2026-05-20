"""
Repository root resolution (single source of truth for path math).

**Why here:** ``repo_root()`` is imported by ``artifacts``, DB defaults, and crawls so
relative paths (e.g. ``data/``, ``stateconscious.db``) resolve the same from any module.
"""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Project root (parent of ``src/``). This file: ``src/lib/paths.py``."""
    return Path(__file__).resolve().parents[2]
