"""
Per-source configuration for parlimen.gov.my bill index pages.
"""

from __future__ import annotations

from pathlib import Path

from lib.parser.seed_txt import parse_seed_urls_file

SOURCE_ID = "parliament_my"

RESOURCE_KIND = "index"

# Appended to source_library.notes for each seed (init_db).
CRAWL_NOTES = (
    "Some clients see HTTP 403 or TLS verification failures; use browser-saved "
    "HTML or dev --insecure only as documented. Chamber-specific query strings "
    "(e.g. uweb=dr, arkib=yes) matter. The site may return HTTP 200 with an "
    "application error page; soft_200 in crawl_history (error_pages.py)."
)

BASE_URL = "https://www.parlimen.gov.my"

_SEED_FILE = Path(__file__).resolve().parent / "seed_urls.txt"
BILL_INDEX_URLS: tuple[str, ...] = tuple(u for u, _ in parse_seed_urls_file(_SEED_FILE))
if not BILL_INDEX_URLS:
    raise RuntimeError(
        f"No seed URLs in {_SEED_FILE} for adapter {SOURCE_ID!r}",
    )

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ms;q=0.8",
}

FETCH_TIMEOUT_S = 45
