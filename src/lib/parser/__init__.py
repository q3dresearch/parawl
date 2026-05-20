"""
Shared parsing helpers (seed URL lists, future HTML/PDF utilities).

Site-specific extractors stay under ``lib.sources.<region>.<adapter>``.
"""

from __future__ import annotations

from lib.parser.seed_txt import parse_seed_urls_file

__all__ = ["parse_seed_urls_file"]
