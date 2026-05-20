"""Pytest hooks: load ``PARLIAMENT_LIVE_*`` from repo ``.env`` (pytest does not read ``.env`` by itself)."""

from __future__ import annotations

import os
from pathlib import Path


def _strip_inline_comment(val: str) -> str:
    v = val.strip()
    if "#" not in v:
        return v
    # drop trailing # comment only when quoted segment is closed
    in_dq = in_sq = False
    for i, ch in enumerate(v):
        if ch == '"' and not in_sq:
            in_dq = not in_dq
        elif ch == "'" and not in_dq:
            in_sq = not in_sq
        elif ch == "#" and not in_dq and not in_sq:
            return v[:i].strip()
    return v


def load_parliament_live_env_from_dotenv() -> None:
    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key.startswith("PARLIAMENT_LIVE_"):
            continue
        val = _strip_inline_comment(val)
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        os.environ.setdefault(key, val)


load_parliament_live_env_from_dotenv()
