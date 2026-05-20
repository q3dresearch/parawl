"""Parse ``seed_urls.txt`` files (one URL per line, optional tab label)."""

from __future__ import annotations

from pathlib import Path


def parse_seed_urls_file(path: Path) -> list[tuple[str, str | None]]:
    """
    One URL per non-empty line. ``#`` starts a comment line.
    Optional ``URL<TAB>label``; if no tab, label is None.
    """
    if not path.is_file():
        return []
    out: list[tuple[str, str | None]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            url, label = line.split("\t", 1)
            url = url.strip()
            label = label.strip() or None
        else:
            url, label = line, None
        if not url or url.startswith("#"):
            continue
        out.append((url, label))
    return out
