"""
Parliament portal sometimes returns HTTP 200 with an application-level error page
(soft 404). Detect that so ``crawl_history.outcome`` is ``error``, not ``ok``.
"""

from __future__ import annotations

# Substrings in HTML body (case-insensitive). Tune when the site copy changes.
_SOFT_MARKERS: tuple[tuple[str, str], ...] = (
    ("an error has occurred", "error_page: generic"),
    ("the requested page cannot be found", "error_page: not_found_en"),
    ("ralat telah berlaku", "error_page: generic_ms"),
    ("halaman yang diminta tidak dapat dijumpai", "error_page: not_found_ms"),
)


def soft_error_label(html: str) -> str | None:
    """
    If HTML looks like a parliament error shell (200 but not real content), return a short label.
    Otherwise return None.
    """
    if not html or not html.strip():
        return "error_page: empty_body"
    folded = html.casefold()
    for needle, label in _SOFT_MARKERS:
        if needle in folded:
            return label
    return None
